#   Gary Davenport preferredsoundplayer functions 7/8/2021
#
#   This module has no dependencies, other than what comes with Windows 10, 
#       the standard Linux kernel, MacOS 10.5 or later, and the 
#       Python Standard Library.
#
#   ----------------Windows----------------
#   Windows 10 uses the Windows winmm.dll Multimedia API to play sounds and the Python 'winsound' module to loop background .
#   (Windows will only loop one background sound at a time.)
#       See references:
#       “Programming Windows: the Definitive Guide to the WIN32 API, 
#           Chapter 22 Sound and Music Section III Advanced Topics 
#           ‘The MCI Command String Approach.’”
#           Programming Windows: the Definitive Guide to the WIN32 API, 
#           by Charles Petzold, Microsoft Press, 1999. 
#       https://github.com/michaelgundlach/mp3play
#       & https://github.com/TaylorSMarks/playsound/blob/master/playsound.py
#
#       To loop sounds, Windows10 uses winsound.Playsound() which does limit
#       background loops to only 1 at a time compared to the other OS and only .wav
#
#   ----------------Linux------------------
#   Linux uses ALSA and gstreamer, part of Linux kernel, also may use ffmpg if available

#   -Linux will always play .wavs with ALSA
#   Otherwise:
#   -Linux will use the first available player in this order: gst-1.0-play, ffmpeg, gst playbin(built on the fly) or ALSA
#   -Linux will try to use gst-1.0-play first (usually present), if not present then
#   -Linux will try to use ffmpeg as its player (usually present), if not present then
#   -Linux will initialize a gstreamer playbin player (is supposed to always be present), if not present then
#   -Linux will play the sound with ALSA, and if not a .wav file will sound like white noise.
#
#   ----------------MacOS-------------------
#   -MacOS uses the afplay module which is present OS X 10.5 and later
#       

from random import random
from platform import system
import subprocess
from subprocess import Popen, PIPE
import os
from threading import Thread
from time import sleep
import sndhdr
if system()=="Linux":
    import shutil
    try:
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
    except:
        pass
    import os

if system()=="Windows":
    from ctypes import c_buffer, windll
    from sys import getfilesystemencoding
    from threading import Thread
    from time import sleep
    import winsound

# This module creates a single sound with winmm.dll API and returns the alias to the sound
class SingleSoundWindows:
    def __init__(self):
        self.isSongPlaying=False
        self.sync=False
        self.P=None
        self.fileName=""
        self.isSongPlaying=False

    # typical process for using winmm.dll
    def _processWindowsCommand(self,commmandString):
        buf = c_buffer(255)
        command = commmandString.encode(getfilesystemencoding())
        windll.winmm.mciSendStringA(command, buf, 254, 0)
        return buf.value

    # this function is invoked to make sure that when the end of the song
    # is reached, the sound is stopped (maybe not needed), then closed.
    #
    # it is sent of by a thread.  In the meantime, if the sound is already 
    # closed or stopped, it will still execute, but causes no harm.
    # it is to try and ensure that the sound will not remain open in memory.
    def _closeAliasAfterDuration(self):
        sleep(float(self.durationInMS) / 1000.0)   
        str1="stop "+self.alias
        self._processWindowsCommand(str1)
        str1="close "+self.alias
        self._processWindowsCommand(str1)

    # make an alias, set the time format, get the length of the song,
    # play the song.
    # For Sync play - sleep until song over, then stop and close alias.
    # For Async - send off thread that will close alias after the sounds
    #   duration, whether the sound was already closed or not.
    def soundplay(self,fileName, block=True):
        self.fileName=fileName
        alias = 'playwave_' + str(random())
        str1="open \""+self.fileName+"\""+" alias "+alias
        self._processWindowsCommand(str1)
        str1="set "+alias+" time format milliseconds"
        self._processWindowsCommand(str1)
        str1="status "+alias+" length"
        durationInMS=self._processWindowsCommand(str1)
        str1="play "+alias+" from 0 to " + str(durationInMS.decode())
        self._processWindowsCommand(str1)

        if block==True:
            sleep(float(durationInMS) / 1000.0)
            str1="stop "+alias
            self._processWindowsCommand(str1)
            str1="close "+alias
            self._processWindowsCommand(str1)

        else:
            self.alias=alias
            self.durationInMS=durationInMS
            T=Thread(target=self._closeAliasAfterDuration)
            T.setDaemon(True)
            T.start() 
            self.P=alias
            return self.P

    # issue stop and close commands using the sound's alias
    def stopsound(self,sound):
        try:    
            str1="stop "+sound
            self._processWindowsCommand(str1)
            str1="close "+sound
            self._processWindowsCommand(str1)
        except:
            pass

    # return True or False if song alias 'status' is 'playing'
    def getIsPlaying(self,song):
        try:
            str1="status "+song+" mode"
            myvalue=self._processWindowsCommand(str1)
            if myvalue==b"playing":
                self.isSongPlaying=True
            else:
                self.isSongPlaying=False
        except:
            self.isSongPlaying=False
        return self.isSongPlaying

class MusicLooper:
    def __init__(self, fileName):
        self.fileName = fileName
        self.playing = False
        self.songProcess = None

    def _playwave(self):
        self.songProcess=playwave(self.fileName)

    def _playloop(self):
        while self.playing==True:
            self.songProcess=playwave(self.fileName)
            sleep(self._getWavDurationFromFile())

    # start looping a wave
    def startMusicLoopWave(self):
        if self.playing==True: # don't allow more than one background loop per instance of MusicLooper
            print("Already playing, stop before starting new.")
            return
        else:
            self.playing=True
            t = Thread(target=self._playloop)
            t.setDaemon(True)
            t.start()
    # stop looping a wave
    def stopMusicLoop(self):
        if self.playing==False:
            print(str(self.songProcess)+" already stopped, play before trying to stop.")
            return
        else:
            self.playing=False  # set playing to False, which stops loop
            stopwave(self.songProcess) #issue command to stop the current wave file playing also, so song does not finish out

    # get length of wave file in seconds
    def _getWavDurationFromFile(self):
        frames = sndhdr.what(self.fileName)[3]
        rate = sndhdr.what(self.fileName)[1]
        duration = float(frames)/rate
        return duration

    def getSongProcess(self):
        return(self.songProcess)

    def getPlaying(self):
        return(self.playing)

# I just this custom class to pass back and forth this
# tracker since the winsound module is implemented in a different
# way (i.e. you don't pass back and for a winsound.Playsound() object, you send
# the fileName "None" to it to stop sounds.
# This is only used when looping sounds in Windows 10 using the winsound module.
class customVariableTracker:
    def __init__(self):
        self.looping=False

    def _setlooping(self,TrueorFalse):
        self.looping=TrueorFalse

    def _getlooping(self):
        return(self.looping)

###### 
class SingleSoundLinux:
    def __init__(self):
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
        self.pl=None
        self.gst=Gst.init()
        self.playerType=""

    def _gstPlayProcess(self):
        self.pl.set_state(Gst.State.PLAYING)
        bus = self.pl.get_bus()
        bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        self.pl.set_state(Gst.State.NULL)

    def soundplay(self,fileName, block=True):
        if self.getIsPlaying(self.pl)==False:
            self.pl = Gst.ElementFactory.make("playbin", "player")
            self.pl.set_property('uri','file://'+os.path.abspath(fileName))
            self.playerType="gstreamer"
            self.T=Thread(target=self._gstPlayProcess,daemon=True)
            self.T.start()
            if block==True:
                self.T.join()
            return([self.pl,self.playerType])
        else:
            print("already playing, open new SingleSound if you need to play simoultaneously")

    def stopsound(self,sound):
        #print(sound[1])
        if sound[1]=="gstreamer":sound[0].set_state(Gst.State.NULL)

    def getIsPlaying(self,song):
        if song is None:return False
        #print(song[1])
        if song[1]=="gstreamer":
            state=(str(song[0].get_state(Gst.State.PLAYING)[1]).split()[1])
            if state=="GST_STATE_READY" or state=="GST_STATE_PLAYING":
                return True
            else:
                return False

#########################################################################
# These function definitions are intended to be used by the end user,   #
# but an instance of the class players above can be used also.          #
#########################################################################       

# plays a wave file and also returns the alias of the sound being played, async method is default
"""
def playwave(fileName, block=False):
    fileName=fileName
    if system()=="Linux": command = "exec aplay --quiet " + os.path.abspath(fileName)
    elif system()=="Windows":
        song=SingleSoundWindows().soundplay(fileName, block)
        return(song)       
    elif system()=="Darwin": command = "exec afplay \'" + os.path.abspath(fileName)+"\'"
    else: print(str(system()+" unknown to wavecliplayer"));return None
    if block==True: P = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=PIPE, stderr=PIPE).communicate()
    else: P = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=PIPE, stderr=PIPE)
    return P
"""

# plays a sound file and also returns the alias of the sound being played, async method is default
def soundplay(fileName, block=False):
    ##if system()=="Linux": command = "exec aplay --quiet " + os.path.abspath(fileName)
    if system()=="Linux":
        print(fileName[-4:])
        if fileName[-4:]==".wav": #use alsa if .wav
            print("using alsa because its a wav")
            command = "exec aplay --quiet " + os.path.abspath(fileName)
        elif (shutil.which("gst-play-1.0") is not None)==True: #use gst-play-1.0 if available
            print("using gst-play-1.0 since available")
            command = "exec gst-play-1.0 " + os.path.abspath(fileName)
        elif (shutil.which("ffplay") is not None)==True:       #use ffplay if present
            print("using ffplay since available")
            command = "exec ffplay -nodisp -autoexit -loglevel quiet " + os.path.abspath(fileName)
        else:
            try:
                import gi
                gi.require_version('Gst', '1.0')
                from gi.repository import Gst
                song=SingleSoundLinux().soundplay(fileName, block)
                print("using gst playbin - successful try")
                return(song)
            except:
                print("must use ALSA, all else failed")
                command = "exec aplay --quiet " + os.path.abspath(fileName)
    elif system()=="Windows":
        song=SingleSoundWindows().soundplay(fileName, block)
        return(song)       
    elif system()=="Darwin": command = "exec afplay \'" + os.path.abspath(fileName)+"\'"
    else: print(str(system()+" unknown to preferredsoundplayer"));return None

    if block==True: P = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=PIPE, stderr=PIPE).communicate()
    else: P = subprocess.Popen(command, universal_newlines=True, shell=True,stdout=PIPE, stderr=PIPE)
    return P

# stops the wave being played, 'process' in the case of windows is actually the alias to the song
# otherwise process is a process in other operating systems.
def stopsound(process):
    if process is not None:
        try:
            if process is not None:
                if system()=="Windows":
                    SingleSoundWindows().stopsound(process)
                elif system()=="Linux":
                    #see if process is GSTPlaybin
                    if str(process).find("gstreamer") != -1: SingleSoundLinux().stopsound(process)
                    else:
                        process.terminate() # Linux but not GSTPlaybin 
                else:
                    process.terminate() # MacOS
        except:
            pass
            #print("process is not playing")
    else:
        pass
        #print("process ", str(process), " not playing")

"""
def stopwave(process):
    if process is not None:
        try:
            if process is not None:
                if system()=="Windows":
                    SingleSoundWindows().stopsound(process)          
                else: process.terminate()
        except:
            pass
            #print("process is not playing")
    else:
        pass
        #print("process ", str(process), " not playing")
"""
# pass the process or alias(windows) to the song and return True or False if it is playing
def getIsPlaying(process):
    if system()=="Windows":
        return SingleSoundWindows().getIsPlaying(process)
    else:
        isSongPlaying=False
        if process is not None:
            #see if process is GSTPlaybin
            if system()=="Linux":
                #see if process is GSTPlaybin
                if str(process).find("gstreamer") != -1: return SingleSoundLinux().getIsPlaying(process)
                else: #Linux but not GSTPlaybin
                    try: return(process.poll() is None)
                    except: pass
        return isSongPlaying



# this function will loop a wave file and return an instance of a MusicLooper object that loops music,
# or in the case of Windows it returns an object containing variables used to track if the song is playing
def loopwave(fileName):
    if system()=="Windows":
        Thread(target=winsound.PlaySound, args=[fileName, winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC]).start()
        looptrack=customVariableTracker()
        looptrack._setlooping(True)
        return(looptrack)
    else:
        looper=MusicLooper(fileName)
        looper.startMusicLoopWave()
        return(looper)

# pass an instance of a MusicLooper object and stop the loop, in Windows, pass an instance of the customVariableTracker that is keeping
# track of whether or not the song is looping.
def stoploop(looperObject):
    if looperObject is not None:
        if system()=="Windows":
            winsound.PlaySound(None,winsound.SND_FILENAME)
            looperObject._setlooping(False)
        else:
            looperObject.stopMusicLoop()
    else:
        pass
        #print("looperObject ", str(looperObject), " not playing")

# checks to see if song process is playing, (or if song alias's status is 'playing' in the case of Windows), returns True or False
def getIsLoopPlaying(looperObject):
    if looperObject is not None:
        if system()=="Windows":
            return looperObject._getlooping()
        else:
            return(looperObject.getPlaying())
    else:
        return False

### definitely these names used by MusicLooper, might also be typed in by user
playwave=soundplay
stopwave=stopsound

# This just references the command 'playsound' to 'soundplay' with default to block/sync behaviour in case you want to use this in place
# of the playsound module, which last I checked was not being maintained.
def playsound(fileName, block=True):
    return(soundplay(fileName, block))
