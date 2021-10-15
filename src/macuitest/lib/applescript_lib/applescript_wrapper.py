import time

from Foundation import NSAppleScript
from Foundation import NSAppleScriptErrorBriefMessage
from Foundation import NSAppleScriptErrorMessage
from Foundation import NSAppleScriptErrorNumber

from macuitest.lib.applescript_lib.aeconverter import ae_converter


class AppleScriptError(Exception):
    """Indicates an AppleScript compilation/execution error."""

    def __init__(self, error_info):
        self._error_info = dict(error_info)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._error_info})"

    @property
    def message(self) -> str:
        msg = self._error_info.get(NSAppleScriptErrorMessage)
        if not msg:
            msg = self._error_info.get(NSAppleScriptErrorBriefMessage, "Script Error")
        return msg

    @property
    def number(self):
        """ "int | None -- the error number, if given")"""
        return self._error_info.get(NSAppleScriptErrorNumber)


class AppleScriptWrapper:
    """Wrapper for AppleScript with a set of easy to use methods."""

    allowed_modifier_keys = ("control", "shift", "option", "command")
    key_codes: dict = {
        "return": 36,
        "esc": 53,
        "delete": 51,
        "left": 123,
        "right": 124,
        "up": 126,
        "down": 125,
        "tab": 48,
    }
    __pass_as_key_code = {'"': (39, True), "'": (39, False)}

    def typewrite(self, phrase: str) -> None:
        """Type `phrase` with a delay between key presses."""
        for char in phrase:
            time.sleep(0.005)
            if char in self.__pass_as_key_code:
                key_code, is_shift_required = self.__pass_as_key_code[char]
                self.send_keycode(key_code, "shift") if is_shift_required else self.send_keycode(
                    key_code
                )
            else:
                self.send_keystroke(char)

    def send_keystroke(self, phrase: str, *args) -> None:
        """Send keystroke event with the specified `phrase` (type it using AppleScript)."""
        self.__send_event("keystroke", phrase, *args)

    def send_keycode(self, key_code: int, *args) -> None:
        """Send keystroke event with the specified `key_code` (type it using AppleScript)."""
        self.__send_event("key code", key_code, *args)

    def __send_event(self, event_type: str, message: [str, int], *args):
        for modifier in args:
            if modifier not in self.allowed_modifier_keys:
                raise KeyError(f'{modifier} is not a modifier key.')
        _cmd = f'{event_type} "{message}"'
        if args:
            _cmd = (
                f'{event_type} "{message}" using '
                f'{{{", ".join([f"{modifier_key} down" for modifier_key in args])}}}'
            )
        return self.tell_sys_events(_cmd)

    def tell_app_process(self, command: str, app_process: str):
        return self.execute(
            f'tell app "System Events" to tell application process "{app_process}" to {command}'
        )

    def tell_app(self, app: str, command: str, ignoring_responses: bool = False):
        _tell_what = (
            f'tell application "{app}" to {command}'
            if not ignoring_responses
            else f'ignoring application responses\ntell application "{app}" '
            f"to {command}\nend ignoring"
        )
        return self.execute(_tell_what)

    def tell_sys_events(self, command: str):
        return self.execute(f'tell application "System Events" to {command}')

    @staticmethod
    def execute(cmd: str):
        """Execute AppleScript command abd returns exitcode, stdout and stderr.
        :param str cmd: apple script
        :return: exitcode, stdout and stderr"""
        result, error = NSAppleScript.alloc().initWithSource_(cmd).executeAndReturnError_(None)
        if error:
            raise AppleScriptError(error)
        return ae_converter.unpack(result)


as_wrapper = AppleScriptWrapper()
