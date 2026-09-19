import ctypes
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, Container, VerticalGroup
from textual.widgets import Static 
from pynput import keyboard

try:
    clib = ctypes.CDLL("./libplayback.so")
except OSError:
    print("Error: libplayback.so not found.")
    exit(1)

######################
# Defining functions #
######################

# init_engine(void) -> audio_handle* 
init_engine = clib.init_engine
init_engine.argtypes = []
init_engine.restype = ctypes.c_void_p

# cleanup_engine(audio_handle* handle) -> void
cleanup_engine = clib.cleanup_engine
cleanup_engine.argtypes = [ctypes.c_void_p]
cleanup_engine.restype = None

# start_note(audio_handle* handle, int note_index) -> void
start_note = clib.start_note
start_note.argtypes = [ctypes.c_void_p, ctypes.c_int32]
start_note.restype = None

# stop_note(audio_handle* handle, int note_index) -> void
stop_note = clib.stop_note
stop_note.argtypes = [ctypes.c_void_p, ctypes.c_int32]
stop_note.restype = None


# set_wave(audio_handle* handle, int type) -> void
set_wave = clib.set_wave
set_wave.argtypes = [ctypes.c_void_p, ctypes.c_int32]
set_wave.restype = None

####################
# Helper Functions #
####################

def play_note(handle:ctypes.c_void_p, note_index:int, wavetype:int):
    print(f"Playing wavetype {wavetype} @ index {note_index}...")
    stop_note(handle, note_index)
    start_note(handle, note_index)

def sanitize_class_name(char: str) -> str:
    """Converts a keyboard character into a valid CSS class name."""
    mapping = {
        ';': 'semi',
        "'": 'quote',
        '[': 'lbracket',
        ']': 'rbracket',
        '\\': 'backslash',
        ',': 'comma',
        '.': 'dot',
        '/': 'slash',
        '`': 'backtick',
        '-': 'minus',
        '=': 'equals',
    }
    # If it's a standard alphanumeric, keep it. Otherwise use mapping or hex.
    if char.isalnum():
        return f"key-{char}"
    elif char in mapping:
        return f"key-{mapping[char]}"
    else:
        # Fallback for any other weird char: use hex code
        return f"key-hex{ord(char)}"

###############
# Textual APP #
###############

class Keypad(VerticalGroup):
    """ A Keypad Widget."""

    can_focus = True

    def __init__(self, pointer:ctypes.c_void_p):
        self.pointer = pointer
        self.validkeys = ['z', 'x', 'c', 'a', 'w', 's', 'e', 'd', 'f', 't', 'g'
                          , 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p', ';', "'"]
        self.keys = [keyboard.KeyCode.from_char(c) for c in self.validkeys]
        self.octavenotes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        self.pitches = self.constructpitches()
        self.is_pressed = [False for _ in range(len(self.keys))] 
        self.offset_ = 40
        self.octave = ( (self.offset_ + 1) // 12) + 1
        self.wavetype = 1
        self.wavetypes = ["SINE", "SQUARE", "TRIANGLE", "SAWTOOTH"]
        self.info_pitches = Static(f"{self.constructactivepitches()}", classes="pitches")
        self.info_wave = Static(f"Wave: {self.wavetypes[self.wavetype - 1]}", id="wave-info")
        self.info_octave = Static(f"Octave: {self.octave}", id="octave-info")
        self.piano_structure = [('a', 'w'), ('s', 'e'), ('d', None), ('f', 't'),
                                ('g', 'y'), ('h', 'u'), ('j', None), ('k', 'o'), 
                                ('l', 'p'), (';', None), ("'", None) ] 
        super().__init__()

    def constructpitches(self):
        pitches = []
        octavenotes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for i in range(102):
            octave = (i // 12) - 1  # MIDI note 0 is C-1, note 12 is C0, etc.
            note = octavenotes[i % 12]
            pitches.append(f"{note}{octave}")
        return pitches

    def constructactivepitches(self):
        activepitches = []
        i = 3
        while i < len(self.is_pressed):
            if self.is_pressed[i]:
                midi_note = self.offset_ + 20 + i - 3
                activepitches.append(self.pitches[midi_note])
            i += 1
        return activepitches

    def update_info(self):
        self.octave = ( (self.offset_ + 1) // 12) + 1
        self.info_wave.update(f"Wave: {self.wavetypes[self.wavetype - 1]}")
        self.info_octave.update(f"Octave: {self.octave}")
        self.info_pitches.update(f"{self.constructactivepitches()}")

    def on_press(self, key) -> None:
        if not self.has_focus:
            return 
        try:
            index = self.keys.index(key) # Checks wether the key pressed is valid

            if self.is_pressed[index]: # Prevents retriggering 
                return

            if index == 0: # z key raises octave
                self.offset_ += 12
                if self.offset_ > 64:
                    self.offset_ = 64 
            elif index == 1:# x key lowers octave 
                self.offset_ -= 12
                if self.offset_ < 4:
                    self.offset_ = 4
            elif index == 2:
                self.wavetype += 1
                if self.wavetype > 4 :
                    self.wavetype = 1
                set_wave(self.pointer, self.wavetype)
            else: # other valid keys are notes
                play_note(self.pointer, self.offset_ + index - 3, 1)
                class_name = sanitize_class_name(self.validkeys[index])
                widget = self.query_one(f".key-{class_name}")
                if widget:
                    widget.add_class("pressed")
            self.is_pressed[index] = True
            self.update_info()
        except Exception as _: # Non-interactive key pressed
            pass

    def on_release(self, key):
        try:
            index = self.keys.index(key)
            self.is_pressed[index] = False 
            stop_note(self.pointer, self.offset_ + index - 3)
            if index > 2:
                class_name = sanitize_class_name(self.validkeys[index])
                widget = self.query_one(f".key-{class_name}")
                if widget:
                    widget.remove_class("pressed")
            self.update_info()
        except:
            pass

    def on_mount(self):
        listener = keyboard.Listener(
        on_press=self.on_press,
        on_release=self.on_release)
        listener.start()

    def compose(self) -> ComposeResult:
        yield self.info_pitches
        with HorizontalGroup(classes="keys-container"):
            i = 3
            while i < len(self.validkeys):
                white_key_char = self.validkeys[i]
                black_key_char = None
                class_name = sanitize_class_name(white_key_char)

                if i + 1 < len(self.validkeys):
                    next_char = self.validkeys[i+1]
                    if next_char in ['w', 'e', 't', 'y', 'u', 'o', 'p']:
                        black_key_char = next_char
                        i += 2 
                    else:
                        i += 1
                else:
                    i += 1
                white_widget = Static(white_key_char, classes=f"white-key key-{class_name}")

                slot_children = [white_widget]
                if black_key_char:
                    black_class_name = sanitize_class_name(black_key_char)
                    black_widget = Static(black_key_char, classes=f"black-key key-{black_class_name}")
                    slot_children.append(black_widget)

                with Container(classes="key-slot"):
                    for child in slot_children:
                        yield child

        yield HorizontalGroup( self.info_octave, self.info_wave, classes = "info")

class SynthKeyboard(App):
    """ A textual app that displays a synthesizer keyboard."""

    CSS_PATH = "keys.tcss"
    ANSI_COLOR = True

    def action_set_wave(self, wavetype: int) -> None:
        set_wave(self.pointer, wavetype)

    def __init__(self, pointer:ctypes.c_void_p):
        self.pointer = pointer
        super().__init__()

    def compose(self) -> ComposeResult:
        """ Called to add widgets to the app."""
        yield Keypad(self.pointer)


###################
# MAIN SOUND LOOP #
###################


if __name__ == "__main__":
    print("Initializing engine...")
    pointer = init_engine()

    set_wave(pointer, 1)

    if not pointer:
        print("Initialization failure, exiting program.")

    print("Launching interface...")
    app = SynthKeyboard(pointer)
    app.run()

    print("Cleaning engine...")
    cleanup_engine(pointer)

    print("Goodbye!")
