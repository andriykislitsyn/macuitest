"""Python wrapper for NSAppleScript."""

import struct

from Foundation import NSAppleScript, NSAppleEventDescriptor, NSAppleScriptErrorMessage, \
    NSAppleScriptErrorBriefMessage, NSAppleScriptErrorNumber, NSAppleScriptErrorAppName, NSAppleScriptErrorRange

from . import kae
from .aecodecs import Codecs

__all__ = ['AppleScript', 'ScriptError']


class AppleScript:
    """
        Represents compiled AppleScript. The script object is persistent.
        Its handlers may be called multiple times and its top-level properties
        will retain current state until the script object's disposal.
    """
    codecs = Codecs()

    def __init__(self, source=None):
        self._script = NSAppleScript.alloc().initWithSource_(source)
        if not self._script.isCompiled():
            error_info = self._script.compileAndReturnError_(None)[1]
            if error_info:
                raise ScriptError(error_info)

    def _new_event(self, suite, code, args):
        evt = NSAppleEventDescriptor.appleEventWithEventClass_eventID_targetDescriptor_returnID_transactionID_(
            self.four_char_code(suite),
            self.four_char_code(code),
            NSAppleEventDescriptor.nullDescriptor(), 0, 0
        )
        evt.setDescriptor_forKeyword_(self.codecs.pack(args), self.four_char_code(kae.keyDirectObject))
        return evt

    source_code = property(lambda self: str(self._script.source()))

    def run(self):
        return self._unpack_result(*self._script.executeAndReturnError_(None))

    def _unpack_result(self, result, error_info):
        if not result:
            raise ScriptError(error_info)
        return self.codecs.unpack(result)

    @staticmethod
    def four_char_code(code: bytes) -> int:
        """
        Convert four-char code for use in NSAppleEventDescriptor methods.
            code: four-char code, e.g. b'utxt'
            Result : int -- OSType, e.g. 1970567284
        """
        return struct.unpack('>I', code)[0]


class ScriptError(Exception):
    """ Indicates an AppleScript compilation/execution error. """

    def __init__(self, error_info):
        self._error_info = dict(error_info)

    def __repr__(self):
        return f'ScriptError({self._error_info})'

    @property
    def message(self) -> str:
        msg = self._error_info.get(NSAppleScriptErrorMessage)
        if not msg:
            msg = self._error_info.get(NSAppleScriptErrorBriefMessage, 'Script Error')
        return msg

    number = property(lambda self: self._error_info.get(NSAppleScriptErrorNumber),
                      doc="int | None -- the error number, if given")

    app_name = property(lambda self: self._error_info.get(NSAppleScriptErrorAppName),
                        doc="str | None -- the name of the application that reported the error, where relevant")

    @property
    def range(self):
        """ (int, int) -- the start and end points (1-indexed) within the source code where the error occurred """
        range_ = self._error_info.get(NSAppleScriptErrorRange)
        if range_:
            start = range_.rangeValue().location
            end = start + range_.rangeValue().length
            return start, end
        else:
            return None

    def __str__(self):
        msg = self.message
        for s, v in [(' ({})', self.number), (' app={!r}', self.app_name), (' range={0[0]}-{0[1]}', self.range)]:
            if v is not None:
                msg += s.format(v)
        return msg
