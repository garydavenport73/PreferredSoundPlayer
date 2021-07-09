# PreferredSoundPlayer
This is my preferential player when I need to play various sound files in a project.

It is multi-platform and has no dependencies, other than what comes with Windows 10, the standard Linux kernel, MacOS 10.5 or later, and the Python Standard Library.

It contains enough functions to be useful, but not too many to be confusing, and I tried to keep the syntax and implementation
super-simple and human readable.

When I built this module, I considered many factors that were important to me, 
like maintenance of code, ease of use, reliability and so forth.  I used these methods below as they seem to be the best 
choices, considering the above factors.

For looping, I would recommend only using .wav files.  Other files will likely work on MacOs and Linux, and will not work on Windows.  Although looping can be done in Windows with non-wave files, I do not implement this because too many other problems can arise in the code due to the way the multiprocessing module differs in the Windows OS.  I want the module to work the same on every OS, and I have to try and anticipate future usability, so I simply limited this package to only loop .wav files.  This is for looping only.

In a nutshell:

#### -Windows 10 uses the Windows winmm.dll Multimedia API to play sounds and the Python 'winsound' module to loop background .  
(Windows will only loop one background sound at a time.)

#### -Linux will use the first available player in this order: gst-1.0-play, ffmpeg, gst playbin(built on the fly) or ALSA
-Linux will try to use gst-1.0-play first (usually present), if not present then

-Linux will try to use ffmpeg as its player (usually present), if not present then

-Linux will initialize a gstreamer playbin player (is supposed to always be present), if not present then

-Linux will play the sound with ALSA, and if not a .wav file will sound like white noise.

#### -MacOS uses the afplay module which is present OS X 10.5 and later

To use the module simply add:
```
from preferredsound.preferredsoundplayer import *
```
and this will import all its functions.

The module essentially contains 3 functions for playing sound files:
```
soundplay("yourfilename.mp3")

stopsound(yourSound)

getIsPlaying(yourSound)
```
And a few more for looping .wav files:

```
backgroundSong = loopwave("yourfilename.wav")

and

stoploop(backgroundSong)
```

Here are some examples on how to use them.
Note that with 'soundplay' it can be used as a standalone function, but if you want to stop the file from playing,
you will have to use the return value of soundplay.  Read a little further and the examples hopefully will make sense.

### Examples:

#### To play a sound file:
```
soundplay("coolhipstersong.mp3") #-> this plays the mp3 file

mysong=soundplay("coolhipstersong.mp3") #-> this plays the mp3 and also returns a reference to the song.
```

#### To stop your song:
```
stopsound(mysong) # -> this stops mysong, which you created in the line above
```

#### To find out if your wave file is playing:

```
isitplaying = getIsPlaying(mysong) -> sets a variable to True or False, depending on if process is running

print(getIsPlaying(mysong)) -> prints True or False depending on if process is running

if getIsPlaying(mysong)==True:
    print("Yes, your song is playing")
else:
    print("Your song is not playing")
```

#### To play a sound file synchronously (main progam halts while sound plays):
```
soundplay("coolhipsong.mp3",1) #-> this plays the mp3 file synchronously

or

soundplay("coolhipsong.mp3",block=True)


* Note: commands below will work, but you cannot stop the song, because your progam will be blocked until the song is done playing

mysong=soundplay("coolhipstersong.mp3",1) #-> this plays the wav file synchronously and also returns the song reference

or 

mysong=soundplay("coolhipstersong.mp3",block=True) #-> this plays the wav file synchronously and also returns the song reference

```
#### To play a wave file in a continuous loop:
```
myloop=loopwave("mybackgroundsong.wav")
```
This starts a background loop playing, but also returns a reference to the background process so it can be stopped.
#### To stop the continuous loop from playing:
```
stoploop(myloop)
```
### Discussion - A little more about why I picked these methods:

### Windows 10
Windows10 functions use the winmm.dll Windows Multimedia API calls using c function calls to play sounds.

See references:

“Programming Windows: the Definitive Guide to the WIN32 API, Chapter 22 Sound and Music Section III Advanced Topics ‘The MCI Command String Approach.’” Programming Windows: the Definitive Guide to the WIN32 API, by Charles Petzold, Microsoft Press, 1999. 
    
https://github.com/michaelgundlach/mp3play

& https://github.com/TaylorSMarks/playsound/blob/master/playsound.py

#### Playing Sounds in Windows:
This method of playing sounds allows for multiple simultaneous sounds, works well and has been used successfully in several projects.  As long as this dynamically linked library is bundled with the current version of Windows, I plan to use this as the preferred method of playing sounds unless there is a compelling reason to change.  In this case, I am using the reasoning "If it's not broke, don't fix it.".  Another advantage is it plays mp3s and other formats as well, not just .wav files.  It works well, is stable, loads and executes quickly, and has essentially never caused me any problems.  

The Python `winsound` module on the other hand, is at least to me a bit odd in its syntax, less intuitive, and only uses wave files.  You basically can't play more than one wave at a time asynchronously.  This is severely limiting, so I don't prefer it for playing sounds.

Calling the winsound.PlaySound module through the OS system works, but not does not execute as quickly.  This may not be a bad approach, however, for background sounds whose fine-timing is not critical.

#### Looping Sounds in Windows:

In this case, I do use the Python `winsound` module to loop sounds.  This is easy to implement, it does not conflict with sounds produced with the winmm.dll library, and starts and stops quickly.  It is however, limited to just one background at a time, but considering alternatives, this seems like the best choice (see below if you really need more than one background loop at at time).

##### Problems using winmm.dll to loop sounds.

It is possible to use windmm.dll for looping also with multiprocessing.  However, this requires very careful consideration when implementing the code in a GUI, as the multiprocessing module behaves differently under the Windows OS.

For example, I have used the winmm.dll sound playing function to loop sounds and I used the Python multiprocessing module to achieve this.  I started off by making a looping process with a while loop.  I started and stopped the process using the multiprocessing module.  I used process.terminate() to stop the loop.  This did work, but the problem with this method is you have to be really careful about how you are implementing the process in a user interface.  If you are using tkinter for example, when you start the process, the process will inherit its parent's resources.  Sometimes for example, a whole new root window will appear when a process is launched.  This can be worked around, but it requires structuring your GUI in a very specific way, so as to initialize the GUI outside of the main process (eg.  `if __name__ ==__'main'__: put your GUI here`, etc).  So I don't think this is a good solution - forcing someone only to design a GUI in a certain way just to use your sound module.  So I have avoided this approach.  Really the main issue is that multiprocessing is not actually implemented exactly the same in all 3 operating systems (Windows, MacOS, and Linux.)

##### Using OS System calls in Windows to loop sounds.

You can loop sounds by using OS system calls in the style of using command line instructions.

See https://pypi.org/project/oswaveplayer/ for an example.

This is not a bad approach, but there is a little delay with the sound launch using the command line version.  This may not be a big issue for you when playing background music.  If you really need multiple background sounds at once, your best bet would be to use another module or to add the oswaveplayer to your project with the import statement:

```
from oswave import oswaveplayer        #(this can be installed with "pip install oswaveplayer")
```
then use:
```
backgroundSong = oswaveplayer.loopwave("yourfilename.wav")
```
and
```
oswaveplayer.stoploop(backgroundSong)
```
This is not a bad approach, but due to the perceptible delay in playing the sound, it is not preferred to me.  You can also look over the source code to see how to launch sounds using this approach, as it is very basic.

### Linux
As far as I know the gst-1.0-play command is usually available on linux distributions.  It has almost always has been for me and its part of the gstreamer library.  My understanding is it can be built from the gstreamer library and that library has been included with the standard Linux kernel for a long time.  It may not be built and ready to go in a Linux disto though or even on path.  So I first try this player.  If that does not work, I try to play the file with ffmpeg command from the ffmpeg project.  As far as I know, it is not part of the standard Linux kerrnel, but is usually present on most distros.  If these 2 commands are not present, which is unusual, the program will use the gstreamer library, which should be present to make a playbin player using the gstreamer library.  I do this a little differently than some other players, as I initialize a gst playbin player for each sound.  (Otherwise, you will get quite a few warnings, some critical related to the internal looping of the gst player). If this fails for some reason (maybe in the future, some import statement changes, who knows??) it will play with the ALSA player.  mp3s will not sound right, but like white noise.


### MacOS

`afplay` system calls work great on 'MacOS'.  I see no reason to invoke different methods at this point in time.  I do not want to concern myself with trying to make this module work with significantly older versions of MacOS before `afplay` was available.  My perception is that people typically would rather use Linux on an old computer systems instead of loading old versions of MacOS.  `afplay` has been present for some time now on MacOS.  Please contact me if you think this really needs to work on older versions of MacOS.

#### You may not need a looping function to loop sounds:
##### A note on looping sounds in general:
If you using a game loop in game building, you don't actually need to use these looping functions at all (although it may be a little more convenient).  You may notice that this module, and other packages I have written, all contain a function called getIsPlaying(yoursound).  You can simply implement a check in your game loop to see if yoursong is playing.  If it is, don't do anything.  If it is not, play the sound with `yoursound=soundplay("yourfilename.wav")`.  Maybe check every 10 frames or something like that in the game loop.

### Notes about using this module as a replacement in the playsound module:

Additionally, I included an alias/reference to the function named 'playsound', and if used, the default block will be true, or synchronous play.  This way, the
module can be used in place of the playsound module (https://github.com/TaylorSMarks/playsound/blob/master/playsound.py) with the same syntax.  If the playsound module is no longer maintained or otherwise does not work for you, you can load this module and use the import statement.

Use:
```
from preferredwave.preferredwaveplayer import playsound
```
for backwards compatibility with the playsound module.

I do not worry about playing urls with this module though.
