import time
from typing import Optional

import AppKit
import Quartz

from macuitest.config.settings import settings
from macuitest.lib.elements.controllers.keyboard_mappings import KEYBOARD_KEYS
from macuitest.lib.elements.controllers.keyboard_mappings import SPECIAL_KEYS


class KeyBoardController:
    # Apps act on these as keys, not text, so they go out as virtual keycodes.
    KEYCODE_CHARS = frozenset("\t\n\r")

    def __init__(self):
        pass

    def write(self, message: str, pause: Optional[float] = None):
        """Type `message` as Unicode text, independent of the keyboard layout.

        Tabs and line breaks go out as their physical keys. `pause` separates key events and
        defaults to `settings.keyboard.pause`.
        """
        pause = settings.keyboard.pause if pause is None else pause
        for char in message:
            send = self.__send_key_event if char in self.KEYCODE_CHARS else self.send_unicode_event
            send(char, "down")
            time.sleep(pause)
            send(char, "up")
            time.sleep(pause)

    def hotkey(self, *args):
        """Calling `hotkey('command', 'shift', 'a')` performs a "CMD-Shift-A" shortcut press.

        Keys already down are released even when a later key fails, so no modifier stays held.
        """
        pressed = []
        try:
            for c in args:
                if len(c) > 1:
                    c = c.lower()
                self.__send_key_event(c, "down")
                pressed.append(c)
                time.sleep(0.025)
        finally:
            for c in reversed(pressed):
                self.__send_key_event(c, "up")
                time.sleep(0.025)

    @staticmethod
    def send_unicode_event(char: str, event_type: str):
        """Post `char` as a text keystroke with no modifier flags.

        Args:
            char: The character to type.
            event_type: "down" for key down, anything else for key up.
        """
        event = Quartz.CGEventCreateKeyboardEvent(None, 0, event_type == "down")
        Quartz.CGEventSetFlags(event, 0)
        Quartz.CGEventKeyboardSetUnicodeString(event, len(char.encode("utf-16-le")) // 2, char)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def __send_key_event(self, key: str, event: str):
        send = self.send_special_key_event if key in SPECIAL_KEYS else self.send_regular_key_event
        send(key, event)

    def send_regular_key_event(self, key: str, event_type):
        if KEYBOARD_KEYS.get(key) is None:
            raise ValueError(f'Key "{key}" is not available')
        if self.is_shift_char(key):
            key_code = KEYBOARD_KEYS[key.lower()]
            event = Quartz.CGEventCreateKeyboardEvent(
                None, KEYBOARD_KEYS["shift"], event_type == "down"
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            time.sleep(0.03)  # Tiny sleep to let OS X catch up on us pressing shift
        else:
            key_code = KEYBOARD_KEYS[key]
        event = Quartz.CGEventCreateKeyboardEvent(None, key_code, event_type == "down")
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    @staticmethod
    def send_special_key_event(key, event_type):
        """Helper method for special keys."""
        key_code = SPECIAL_KEYS[key]
        ev = AppKit.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(  # noqa: E501
            Quartz.NSSystemDefined,  # type
            (0, 0),  # location
            0xA00 if event_type == "down" else 0xB00,  # flags
            0,  # timestamp
            0,  # window
            0,  # ctx
            8,  # subtype
            (key_code << 16) | ((0xA if event_type == "down" else 0xB) << 8),  # data1
            -1,  # data2
        )
        Quartz.CGEventPost(0, ev.CGEvent())

    @staticmethod
    def is_shift_char(character: str):
        """Returns True if the key character is uppercase or shifted."""
        return character.isupper() or character in '~!@#$%^&*()_+{}|:"<>?'


keyboard = KeyBoardController()
