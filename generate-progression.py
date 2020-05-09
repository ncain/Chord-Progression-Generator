#!/bin/python3
import random
from functools import reduce
from fretboardgtr import ScaleGtr
from operator import ior
from os import mkdir, path
from pydub import AudioSegment
from synthesizer import Synthesizer, Waveform, Writer
from synthesizer.frequency import frequency_from_scale

all_notes = ['G#', 'G', 'F#', 'F', 'E', 'D#', 'D', 'C#', 'C', 'B', 'A#', 'A']
debug = True

def rotate_right(number: int, distance: int) -> int:
    """
    Rotate number to the right by distance bits, with radius 12.
    The radius is 12 because there are 12 chromatic tones in Western music.
    I'm writing this as a creative aid for songwriting on a guitar, so microtones aren't useful to me.
    """
    distance = distance % 12
    return (number >> distance)|(number << (12 - distance)) & 0b111111111111  # The twelve-ones bitmask is the chromatic scale.


def rotate_left(number: int, distance: int) -> int:
    """
    Rotate number to the left by distance bits, with radius 12.
    The radius is 12 because there are 12 chromatic tones in Western music.
    I'm writing this as a creative aid for songwriting on a guitar, so microtones aren't useful to me.
    """
    distance = distance % 12
    return (number << distance)|(number >> (12 - distance)) & 0b111111111111


def deserialize_chord(chord: str):
    """
    Given a line from chord-mappings.txt, return a three-element tuple.
    Element 0: The name of the chord.
    Element 1: The quality of the chord.
    Element 2: The numeric representation of the chord rooted at 0b000000000001.
    """
    chord = chord.split(',')
    name = chord[0]
    quality = chord[1]
    bitmask = 0
    for bit in [1 << steps for steps in [int(digit) for digit in chord[2].split()]]:
        bitmask = bitmask | bit
    return name, quality, bitmask


def int_to_binary_string(number: int) -> str:
    """
    Given a numeric representation of a chord or scale, return a the binary representation in a string.
    """
    return bin(number)[2:].zfill(12)


def chord_in_scale(chord: int, scale: int, degree: int) -> bool:
    """
    Given a chord and a scale as numeric representations,
    determine whether the chord rooted at degree half-steps
    above the scale root contains only tones in the scale.

    "Degree" is probably the wrong word, since scale degree has a different meaning.
    """
    return (rotate_left(chord, degree) | scale) == scale


def list_notes(rotated_notes: list, mask: int) -> list:
    """
    Given a chromatic scale rotated to the correct root, return the notes indicated by the given mask.
    """
    notes = list()
    for index in range(12):
        if int_to_binary_string(mask)[index] == '1':
            notes.append(rotated_notes[index])
    return notes


def choose_scale():
    """
    Randomly select a scale and compute all of the chords comprised of the notes in the scale.
    """
    with open('scale-mappings.txt', 'r') as mappings:
        scales = mappings.read().splitlines()
        scale = random.choice(scales)
        scale_name = scale.split(None, 1)[1]  # Passing None implies split on whitespace, at most 1 time
        scale = int(scale.split(None, 1)[0])
    return scale, scale_name


def list_chords(scale: int) -> list:
    """
    Given a scale, produce a list of deserialized chords containing only tones from the scale.
    Each element in the list is another list (NOTE: consider tuples for immutability?):
    Index 0: A result from deserialize_chord(), or a tuple with three elements:
        Element 0: The name of the chord.
        Element 1: The quality of the chord.
        Element 2: The numeric representation of the chord rooted at 0b000000000001.
    Index 1: The chord (index 0, element 2) rotated to the correct root.
    Index 2: The distance above the scale root, in half steps, of the chord root.
    """
    with open('chord-mappings.txt', 'r') as chord_mappings:
        all_chords = [deserialize_chord(chord) for chord in chord_mappings.read().splitlines()]
    chords = list()
    for half_steps in range(12):
        for chord in all_chords:
            if chord_in_scale(chord[2], scale, half_steps):
                chords.append([chord, rotate_left(chord[2], half_steps), half_steps])
    return chords


def rotate_notes(root: str) -> list:
    """
    Given a note (an element of `notes` as defined above), return a chromatic scale rotated to have root at the last element.
    """
    rotated_notes = all_notes
    while rotated_notes[11] != root:
        rotated_notes = rotated_notes[1:] + rotated_notes[:1]  # rotate the list left one step at a time
    return rotated_notes


def choose_progression(scale: int, chords: list) -> list:
    """
    Given a scale and the chords in it, choose a sequence of chords containing all the notes in the scale.
    """
    progression = list()
    # 3. Choose a random chord in the scale to start from.
    progression.append(random.choice(chords))
    roots = 2 ** progression[0][2]
    accumulator = progression[0][1]
    # 4. Until all of the notes in the scale are used in the chord progression:
    while accumulator != scale:
        chord_is_chosen = False
    #   a. Until a next chord is chosen:
        unused_notes = accumulator ^ scale
    #          i. Choose one of the notes in the scale that isn't in a chord that's been chosen.
        new_note = 0
        for guess in sorted(list(range(12)), key=lambda _: random.random()):
            if (2 ** guess) & unused_notes != 0:
                new_note = 2 ** guess
                break
    #         ii. Choose a chord containing the new note and a note from the previous chord which doesn't share a previously-chosen chord root.
        for chord in sorted(chords, key=lambda _: random.random()):
            if new_note & chord[1] != 0 and chord[1] & progression[-1][1] != 0 and (2 ** chord[2]) & roots == 0:
                progression.append(chord)
                accumulator = accumulator | chord[1]
                roots = roots | (2 ** chord[2])
                chord_is_chosen = True
                break
    #        iii. If no such chord exists, just choose a chord containing the new note at random with a previously-unused root.
        if not chord_is_chosen:
            for chord in sorted(chords, key=lambda _: random.random()):
                if new_note & chord[1] != 0 and (2 ** chord[2]) & roots == 0:
                    progression.append(chord)
                    accumulator = accumulator | chord[1]
                    roots = roots | (2 ** chord[2])
                    chord_is_chosen = True
                    break
    #         iv. If no such chord exists, just choose a chord containing the new note at random.
        if not chord_is_chosen:
            for chord in sorted(chords, key=lambda _: random.random()):
                if new_note & chord[1] != 0:
                    progression.append(chord)
                    accumulator = accumulator | chord[1]
                    roots = roots | (2 ** chord[2])
                    break
    return progression


def write_scale_svg(scale_notes: list, root: str, filepath: str, tuning: list) -> None:
    """
    Given a list of notes in a scale and a scale root, draw the scale pattern on an SVG guitar fretboard.
    """
    writer = ScaleGtr(scale = scale_notes, root = root)
    writer.customtuning(tuning)
    writer.theme(show_note_name = True)  # show note names, rather than scale degrees
    writer.theme(show_ft = False)  # don't display fret numbers below the diagram
    writer.theme(open_color_scale = True)  # color the open strings if they're in the scale
    writer.pathname(filepath)
    writer.draw()
    writer.save()
    return


def write_scale_diagrams(root: str, scale_name: str, scale_notes: list) -> None:
    """
    Put SVG drawings of the scale into the directory structure:
    <root> <scale name> (directory) (e.g. C#_Aeolian)
        └> bass_E_standard.svg (EADG)
        └> bass_drop_D.svg (DADG)
        └> bass_D_standard.svg (DGCF)
        └> bass_drop_C.svg (CGCF)
        └> guitar_E_standard.svg (EADGBE)
        └> guitar_drop_D.svg (DADGBE)
        └> guitar_D_standard.svg (DGCFAD)
        └> guitar_DADGAD.svg (DADGAD)
        └> guitar_CGCFGC.svg (CGCFGC)
    """
    dir = root + ' ' + scale_name
    mkdir(dir)
    write_scale_svg(scale_notes, root, dir + "/bass_E_standard.svg",   ['E', 'A', 'D', 'G'])
    write_scale_svg(scale_notes, root, dir + "/bass_drop_D.svg",       ['D', 'A', 'D', 'G'])
    write_scale_svg(scale_notes, root, dir + "/bass_D_standard.svg",   ['D', 'G', 'C', 'F'])
    write_scale_svg(scale_notes, root, dir + "/bass_drop_C.svg",       ['C', 'G', 'C', 'F'])
    write_scale_svg(scale_notes, root, dir + "/guitar_E_standard.svg", ['E', 'A', 'D', 'G', 'B', 'E'])
    write_scale_svg(scale_notes, root, dir + "/guitar_drop_D.svg",     ['D', 'A', 'D', 'G', 'B', 'E'])
    write_scale_svg(scale_notes, root, dir + "/guitar_D_standard.svg", ['D', 'G', 'C', 'F', 'A', 'D'])
    write_scale_svg(scale_notes, root, dir + "/guitar_DADGAD.svg",     ['D', 'A', 'D', 'G', 'A', 'D'])
    write_scale_svg(scale_notes, root, dir + "/guitar_CGCFGC.svg",     ['C', 'G', 'C', 'F', 'G', 'C'])
    return


def write_progression(progression: list, notes: list, dir: str) -> None:
    """
    Write a text file named progression_#.txt where # is a sequential integer starting from 1.
    The text file will be placed under the "<root> <scale name>" directory made in write_scale_diagrams()
    The contents of the file are as follows:
        For each chord in the progression:
            <chord root> <chord name> (<chord quality>): <chord notes>, separated by commas and spaces
    For example:
    F# Dream chord (Just): C#, C, B, F#
    D# Minor seventh chord (Minor): C#, A#, F#, D#
    D Ninth flat fifth chord (M3+d5): C, G#, F#, E, D
    E Diminished seventh chord (leading-tone and secondary chord) (Diminished): C#, A#, G, E
    """
    def next_filename(dir: str) -> str:
        """
        Perform a linear search of the files in the directory, finding the first unused integer.
        """
        count = 1
        while path.exists(dir + "/progression_" + str(count) + ".txt"):
            count = count + 1
        return dir + "/progression_" + str(count) + ".txt"
    with open(next_filename(dir), 'w') as file:
        for chord in progression:
            file.write(notes[11 - chord[2]] + ' ' + chord[0][0] + ' (' + chord[0][1] + '): ' + ', '.join(list_notes(notes, chord[1])) + '\n')
    return


def write_scale_audio(root: str, scale_notes: list, dir: str) -> None:
    """
    Given a list of note names, write a .wav file containing each of them in sequence ascending, and descending.
    Each tone should sound for one quarter of a second.
    """
    scientific_notation = list()  # a list of notes in scientific pitch notation
    octave = '3'  # start in the octave of a guitar's lowest string
    root_frequency = frequency_from_scale(root + octave)
    for note in reversed(scale_notes):
        if frequency_from_scale(note + '3') < root_frequency:
            octave = '4'
        scientific_notation.append(note + octave)
    scientific_notation.append(root + '4')  # hard-coded because if the scale root is C octave never increments
    synthesizer = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=False)
    writer = Writer()
    for note in scientific_notation:
        writer.write_wave("/tmp/" + note + ".wav", synthesizer.generate_chord([note], 0.25))
    pause = AudioSegment.silent(duration=250)  # duration is in milliseconds
    scale_sounds = pause
    for note in scientific_notation:
        scale_sounds += AudioSegment.from_wav("/tmp/" + note + ".wav")
        scale_sounds += pause
    scale_sounds += pause  # add an extra quarter second to delineate ascending and descending runs
    for note in reversed(scientific_notation):
        scale_sounds += AudioSegment.from_wav("/tmp/" + note + ".wav")
        scale_sounds += pause
    scale_sounds.export(dir + "/" + dir + ".flac", format="flac")
    return


def main():
    # Make a dang ol' chord progression.
    # 1. Choose a root, and rotate the chromatic scale until it starts from the root.
    root = random.choice(all_notes)
    notes = rotate_notes(root)
    # 2. Until a suitable scale is chosen:
    suitable = False
    while not suitable:
    #   a. Choose a scale.
        scale, scale_name = choose_scale()
        scale_notes = list_notes(notes, scale)
    #   b. Enumerate all the chords in the scale.
        chords = list_chords(scale)
    #   c. Inclusive-OR all of the chords in the scale together.
    #   d. If the chords in the scale don't include all the notes in the scale, choose a new scale.
        accumulator = 0
        for chord in chords:
            accumulator = accumulator | chord[1]
        suitable = (accumulator == scale)
    if debug:
        print(scale_name + ': ' + int_to_binary_string(scale) + ' (scale number ' + str(scale) + ')')
        print('Scale root: ' + root)
        print('Scale notes: ' + ",".join(scale_notes) + ' (' + str(len(scale_notes)) + ' tones)')
        for chord in chords:
            chord_notes = list_notes(notes, chord[1])
            print(chord[0][0] + ' rooted at ' + notes[11 - chord[2]])
            print('\t' + int_to_binary_string(chord[1]) + ', or ' + ",".join(chord_notes))
    # 3. Make the rest of the dang progression.
    progression = choose_progression(scale, chords)
    if debug:
        print('Generated a ' + str(len(progression)) + '-chord progression:')
        for chord in progression:
            print(notes[11 - chord[2]] + ' ' + chord[0][0] + ' (' + chord[0][1] + '): ' + ','.join(list_notes(notes, chord[1])))
    write_scale_diagrams(root, scale_name, scale_notes)
    write_progression(progression, notes, root + ' ' + scale_name)
    write_scale_audio(root, scale_notes, root + ' ' + scale_name)


if __name__ == "__main__":
    main()
