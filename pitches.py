from pynput import keyboard

class Thingy:
    def __init__(self):
        self.validkeys = ['z', 'x', 'c', 'a', 'w', 's', 'e', 'd', 'f', 't', 'g'
                            , 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p', ';', "'"]
        self.keys = [keyboard.KeyCode.from_char(c) for c in self.validkeys]
        self.octavenotes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        self.pitches = self.constructpitches()
        self.is_pressed = [False for _ in range(len(self.keys))]
        self.offset_ = 40
        self.piano_structure = [('a', 'w'), ('s', 'e'), ('d', None), ('f', 't'),
                                ('g', 'y'), ('h', 'u'), ('j', None), ('k', 'o'),
                                ('l', 'p'), (';', None), ("'", None)]

    def constructpitches(self):
        pitches = []
        octavenotes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for i in range(88):
            octave = (i // 12) - 1  # MIDI note 0 is C-1, note 12 is C0, etc.
            note = octavenotes[i % 12]
            pitches.append(f"{note}{octave}")
        return pitches

    def constructactivepitches(self) :
        activepitches = []
        i = 3
        while i < len(self.is_pressed):
            if self.is_pressed[i]:
                midi_note = self.offset_ + 20 + i - 3
                activepitches.append(self.pitches[midi_note])
            i += 1
        return activepitches

# Test
bob = Thingy()
# Simulate pressing 'a' (index 3)
bob.is_pressed[3] = True
print(bob.constructactivepitches())  # Should print ['E2']
