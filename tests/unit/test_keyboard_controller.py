from unittest import mock

import pytest

from macuitest.lib.elements.controllers import keyboard_controller
from macuitest.lib.elements.controllers.keyboard_controller import KeyBoardController
from macuitest.lib.elements.controllers.keyboard_mappings import KEYBOARD_KEYS


@pytest.fixture
def quartz():
    with (
        mock.patch.object(keyboard_controller, "Quartz") as quartz,
        mock.patch.object(keyboard_controller.time, "sleep"),
    ):
        yield quartz


@pytest.mark.parametrize("char, utf16_units", [("a", 1), ("é", 1), ("Ж", 1), ("😀", 2)])
def test_write_sends_text_as_unicode_events(quartz, char, utf16_units):
    KeyBoardController().write(char)

    assert (
        quartz.CGEventKeyboardSetUnicodeString.call_args_list
        == [mock.call(quartz.CGEventCreateKeyboardEvent.return_value, utf16_units, char)] * 2
    )
    assert [call.args[2] for call in quartz.CGEventCreateKeyboardEvent.call_args_list] == [
        True,
        False,
    ]
    quartz.CGEventSetFlags.assert_called_with(quartz.CGEventCreateKeyboardEvent.return_value, 0)


def test_write_sends_line_breaks_as_their_physical_key(quartz):
    KeyBoardController().write("\n")

    quartz.CGEventKeyboardSetUnicodeString.assert_not_called()
    assert [call.args[1] for call in quartz.CGEventCreateKeyboardEvent.call_args_list] == [
        KEYBOARD_KEYS["\n"]
    ] * 2
