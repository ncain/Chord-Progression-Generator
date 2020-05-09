# Project Title

A Simple Chord Progression Generator

## Description

When executed, the Python script in generate-progression.py will choose a scale at random from scale-mappings.txt and one of the twelve chromatic notes as a scale root.
Then, generate-progression will enumerate all of the chords contained in that scale.
Next, generate-progression will select one of those chords as a starting point.
Choosing subsequent chords containing at least one note in common with the previous, generate-progression will select a sequence of chords which contain all of the notes in the scale.
Then, generate-progression creates a subdirectory in the current working directory (I never tested running this from outside the project directory; please be careful with your filesystem).
Into that subdirectory (named for the chosen scale), generate-progression drops a number of SVG scale diagrams for various guitar and bass tunings.
Furthermore, generate-progression creates a FLAC file containing the scale played in ascending and descending pitch order.
Finally, generate-progression leaves a text file, progression_#.txt, listing the chords and notes in each chord in the progression generated.

## Getting Started

### Dependencies

Oh boy, I'm not 100% certain. I developed this in nano in the Windows Subsystem for Linux, so I never got audio playback working, but here's what I installed to get it to run:
Ubuntu packages:
* python3
* ffmpeg
Pip packages:
* fretboardgtr
* pydub
* synthesizer

If that's not enough, please let me know and I'll update the list.

### Installing

Clone this git repository.
That's it, you've got it.

### Executing program

```
python3 generate-progression.py
```

There are no options, there is no command-line interface. You just run the thing, it goes, and you pick through the console output and files it makes to see if there's something you like.
If you need a guitar or bass tuning I didn't hard-code, feel free to write one (it should be pretty easy- take a look in write_scale_diagrams() and edit one to suit your needs.)
The console output should only happen when the "debug" variable near the top of the file is set to True, so if you don't like it change that to False and you'll get a bunch of silently-generated files.

## Help

I'm sorry if you need help.
Hit me up on Twitter if the thing is bad, I guess, but I don't know how helpful I can be. I don't know how to do the thing good.
I just wanted to write songs in a lazy way.

## Authors

[Noah Cain](https://github.com/ncain) [@ImbecillicusRex](https://twitter.com/ImbecillicusRex)

## Version History

* This One
    * Initial Release; there will assuredly be more detail here if I ever add to this

## License

I don't really care to license this in any particular way.
It would be nice for you to credit me if you use this.
If you make something cool using this, please tell me about it.

## Acknowledgments

I took this readme template from [DomPizzie here on GitHub](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
I couldn't have gotten my head around this problem without [Ian Ring](https://ianring.com/musictheory/scales/)
The folks who made the packages I imported saved me a mountain of time, so thanks an awful lot to [jiaaro](https://github.com/jiaaro), [yuma-m](https://github.com/yuma-m), and [antscloud](https://github.com/antscloud)!
