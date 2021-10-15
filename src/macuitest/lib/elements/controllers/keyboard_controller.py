import time

import AppKit
import Quartz

from macuitest.lib.elements.controllers.keyboard_mappings import KEYBOARD_KEYS
from macuitest.lib.elements.controllers.keyboard_mappings import SPECIAL_KEYS


class KeyBoardController:
    def __init__(self):
        pass

    def write(self, message: str, pause: float = 0.001):
        """Press key for each of the characters in message."""
        for char in message:
            self.__send_key_event(char, "down")
            time.sleep(pause)
            self.__send_key_event(char, "up")
            time.sleep(pause)

    def hotkey(self, *args):
        """Calling `hotkey('command', 'shift', 'a')` performs a "CMD-Shift-A" shortcut press."""
        for c in args:
            if len(c) > 1:
                c = c.lower()
            self.__send_key_event(c, "down")
            time.sleep(0.025)
        for c in reversed(args):
            if len(c) > 1:
                c = c.lower()
            self.__send_key_event(c, "up")
            time.sleep(0.025)

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
