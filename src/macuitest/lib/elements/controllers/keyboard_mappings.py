import string

KEY_NAMES = [
    "\t",
    "\n",
    "\r",
    " ",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "{",
    "|",
    "}",
    "~",
    "accept",
    "add",
    "alt",
    "altleft",
    "altright",
    "apps",
    "backspace",
    "browserback",
    "browserfavorites",
    "browserforward",
    "browserhome",
    "browserrefresh",
    "browsersearch",
    "browserstop",
    "capslock",
    "clear",
    "convert",
    "ctrl",
    "ctrlleft",
    "ctrlright",
    "decimal",
    "del",
    "delete",
    "divide",
    "down",
    "end",
    "enter",
    "esc",
    "escape",
    "execute",
    "f1",
    "f10",
    "f11",
    "f12",
    "f13",
    "f14",
    "f15",
    "f16",
    "f17",
    "f18",
    "f19",
    "f2",
    "f20",
    "f21",
    "f22",
    "f23",
    "f24",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "final",
    "fn",
    "hanguel",
    "hangul",
    "hanja",
    "help",
    "home",
    "insert",
    "junja",
    "kana",
    "kanji",
    "launchapp1",
    "launchapp2",
    "launchmail",
    "launchmediaselect",
    "left",
    "modechange",
    "multiply",
    "nexttrack",
    "nonconvert",
    "num0",
    "num1",
    "num2",
    "num3",
    "num4",
    "num5",
    "num6",
    "num7",
    "num8",
    "num9",
    "numlock",
    "pagedown",
    "pageup",
    "pause",
    "pgdn",
    "pgup",
    "playpause",
    "prevtrack",
    "print",
    "printscreen",
    "prntscrn",
    "prtsc",
    "prtscr",
    "return",
    "right",
    "scrolllock",
    "select",
    "separator",
    "shift",
    "shiftleft",
    "shiftright",
    "sleep",
    "space",
    "stop",
    "subtract",
    "tab",
    "up",
    "volumedown",
    "volumemute",
    "volumeup",
    "win",
    "winleft",
    "winright",
    "yen",
    "command",
    "option",
    "optionleft",
    "optionright",
]

KEYBOARD_KEYS = dict([(key, None) for key in KEY_NAMES])

""" Taken from events.h
/System/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/Events.h

The *KB dictionaries in a string that can be passed to keyDown(),
keyUp(), or press() into the code used for the OS-specific keyboard function.

They should always be lowercase, and the same keys should be used across all OSes."""

KEYBOARD_KEYS.update(
    {
        "a": 0x00,  # kVK_ANSI_A
        "s": 0x01,  # kVK_ANSI_S
        "d": 0x02,  # kVK_ANSI_D
        "f": 0x03,  # kVK_ANSI_F
        "h": 0x04,  # kVK_ANSI_H
        "g": 0x05,  # kVK_ANSI_G
        "z": 0x06,  # kVK_ANSI_Z
        "x": 0x07,  # kVK_ANSI_X
        "c": 0x08,  # kVK_ANSI_C
        "v": 0x09,  # kVK_ANSI_V
        "b": 0x0B,  # kVK_ANSI_B
        "q": 0x0C,  # kVK_ANSI_Q
        "w": 0x0D,  # kVK_ANSI_W
        "e": 0x0E,  # kVK_ANSI_E
        "r": 0x0F,  # kVK_ANSI_R
        "y": 0x10,  # kVK_ANSI_Y
        "t": 0x11,  # kVK_ANSI_T
        "1": 0x12,  # kVK_ANSI_1
        "!": 0x12,  # kVK_ANSI_1
        "2": 0x13,  # kVK_ANSI_2
        "@": 0x13,  # kVK_ANSI_2
        "3": 0x14,  # kVK_ANSI_3
        "#": 0x14,  # kVK_ANSI_3
        "4": 0x15,  # kVK_ANSI_4
        "$": 0x15,  # kVK_ANSI_4
        "6": 0x16,  # kVK_ANSI_6
        "^": 0x16,  # kVK_ANSI_6
        "5": 0x17,  # kVK_ANSI_5
        "%": 0x17,  # kVK_ANSI_5
        "=": 0x18,  # kVK_ANSI_Equal
        "+": 0x18,  # kVK_ANSI_Equal
        "9": 0x19,  # kVK_ANSI_9
        "(": 0x19,  # kVK_ANSI_9
        "7": 0x1A,  # kVK_ANSI_7
        "&": 0x1A,  # kVK_ANSI_7
        "-": 0x1B,  # kVK_ANSI_Minus
        "_": 0x1B,  # kVK_ANSI_Minus
        "8": 0x1C,  # kVK_ANSI_8
        "*": 0x1C,  # kVK_ANSI_8
        "0": 0x1D,  # kVK_ANSI_0
        ")": 0x1D,  # kVK_ANSI_0
        "]": 0x1E,  # kVK_ANSI_RightBracket
        "}": 0x1E,  # kVK_ANSI_RightBracket
        "o": 0x1F,  # kVK_ANSI_O
        "u": 0x20,  # kVK_ANSI_U
        "[": 0x21,  # kVK_ANSI_LeftBracket
        "{": 0x21,  # kVK_ANSI_LeftBracket
        "i": 0x22,  # kVK_ANSI_I
        "p": 0x23,  # kVK_ANSI_P
        "l": 0x25,  # kVK_ANSI_L
        "j": 0x26,  # kVK_ANSI_J
        "'": 0x27,  # kVK_ANSI_Quote
        '"': 0x27,  # kVK_ANSI_Quote
        "k": 0x28,  # kVK_ANSI_K
        ";": 0x29,  # kVK_ANSI_Semicolon
        ":": 0x29,  # kVK_ANSI_Semicolon
        "\\": 0x2A,  # kVK_ANSI_Backslash
        "|": 0x2A,  # kVK_ANSI_Backslash
        ",": 0x2B,  # kVK_ANSI_Comma
        "<": 0x2B,  # kVK_ANSI_Comma
        "/": 0x2C,  # kVK_ANSI_Slash
        "?": 0x2C,  # kVK_ANSI_Slash
        "n": 0x2D,  # kVK_ANSI_N
        "m": 0x2E,  # kVK_ANSI_M
        ".": 0x2F,  # kVK_ANSI_Period
        ">": 0x2F,  # kVK_ANSI_Period
        "`": 0x32,  # kVK_ANSI_Grave
        "~": 0x32,  # kVK_ANSI_Grave
        " ": 0x31,  # kVK_Space
        "space": 0x31,
        "\r": 0x24,  # kVK_Return
        "\n": 0x24,  # kVK_Return
        "enter": 0x24,  # kVK_Return
        "return": 0x24,  # kVK_Return
        "\t": 0x30,  # kVK_Tab
        "tab": 0x30,  # kVK_Tab
        "backspace": 0x33,  # kVK_Delete, which is "Backspace" on OS X.
        "\b": 0x33,  # kVK_Delete, which is "Backspace" on OS X.
        "esc": 0x35,  # kVK_Escape
        "escape": 0x35,  # kVK_Escape
        "command": 0x37,  # kVK_Command
        "shift": 0x38,  # kVK_Shift
        "shiftleft": 0x38,  # kVK_Shift
        "capslock": 0x39,  # kVK_CapsLock
        "option": 0x3A,  # kVK_Option
        "optionleft": 0x3A,  # kVK_Option
        "alt": 0x3A,  # kVK_Option
        "altleft": 0x3A,  # kVK_Option
        "ctrl": 0x3B,  # kVK_Control
        "ctrlleft": 0x3B,  # kVK_Control
        "shiftright": 0x3C,  # kVK_RightShift
        "optionright": 0x3D,  # kVK_RightOption
        "ctrlright": 0x3E,  # kVK_RightControl
        "fn": 0x3F,  # kVK_Function
        "f17": 0x40,  # kVK_F17
        "volumeup": 0x48,  # kVK_VolumeUp
        "volumedown": 0x49,  # kVK_VolumeDown
        "volumemute": 0x4A,  # kVK_Mute
        "f18": 0x4F,  # kVK_F18
        "f19": 0x50,  # kVK_F19
        "f20": 0x5A,  # kVK_F20
        "f5": 0x60,  # kVK_F5
        "f6": 0x61,  # kVK_F6
        "f7": 0x62,  # kVK_F7
        "f3": 0x63,  # kVK_F3
        "f8": 0x64,  # kVK_F8
        "f9": 0x65,  # kVK_F9
        "f11": 0x67,  # kVK_F11
        "f13": 0x69,  # kVK_F13
        "f16": 0x6A,  # kVK_F16
        "f14": 0x6B,  # kVK_F14
        "f10": 0x6D,  # kVK_F10
        "f12": 0x6F,  # kVK_F12
        "f15": 0x71,  # kVK_F15
        "help": 0x72,  # kVK_Help
        "home": 0x73,  # kVK_Home
        "pageup": 0x74,  # kVK_PageUp
        "pgup": 0x74,  # kVK_PageUp
        "del": 0x75,  # kVK_ForwardDelete
        "delete": 0x75,  # kVK_ForwardDelete
        "f4": 0x76,  # kVK_F4
        "end": 0x77,  # kVK_End
        "f2": 0x78,  # kVK_F2
        "pagedown": 0x79,  # kVK_PageDown
        "pgdn": 0x79,  # kVK_PageDown
        "f1": 0x7A,  # kVK_F1
        "left": 0x7B,  # kVK_LeftArrow
        "right": 0x7C,  # kVK_RightArrow
        "down": 0x7D,  # kVK_DownArrow
        "up": 0x7E,  # kVK_UpArrow
    }
)

for char in string.ascii_lowercase:  # Add mappings for uppercase letters.
    KEYBOARD_KEYS[char.upper()] = KEYBOARD_KEYS[char]

# Taken from ev_keymap.h
# http://www.opensource.apple.com/source/IOHIDFamily/IOHIDFamily-86.1/IOHIDSystem/IOKit/hidsystem/ev_keymap.h
SPECIAL_KEYS = {
    "KEYTYPE_SOUND_UP": 0,
    "KEYTYPE_SOUND_DOWN": 1,
    "KEYTYPE_BRIGHTNESS_UP": 2,
    "KEYTYPE_BRIGHTNESS_DOWN": 3,
    "KEYTYPE_CAPS_LOCK": 4,
    "KEYTYPE_HELP": 5,
    "POWER_KEY": 6,
    "KEYTYPE_MUTE": 7,
    "UP_ARROW_KEY": 8,
    "DOWN_ARROW_KEY": 9,
    "KEYTYPE_NUM_LOCK": 10,
    "KEYTYPE_CONTRAST_UP": 11,
    "KEYTYPE_CONTRAST_DOWN": 12,
    "KEYTYPE_LAUNCH_PANEL": 13,
    "KEYTYPE_EJECT": 14,
    "KEYTYPE_VIDMIRROR": 15,
    "KEYTYPE_PLAY": 16,
    "KEYTYPE_NEXT": 17,
    "KEYTYPE_PREVIOUS": 18,
    "KEYTYPE_FAST": 19,
    "KEYTYPE_REWIND": 20,
    "KEYTYPE_ILLUMINATION_UP": 21,
    "KEYTYPE_ILLUMINATION_DOWN": 22,
    "KEYTYPE_ILLUMINATION_TOGGLE": 23,
}
