from unittest import mock

import pytest

from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.lib.applescript_lib import applescript_wrapper
from macuitest.lib.applescript_lib.aeconverter import AEType
from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.elements import applescript_element
from macuitest.lib.elements.applescript_element import BaseUIElement

LOCATOR = 'button "OK" of window 1'


def cant_get(number=-1728):
    return AppleScriptError({applescript_wrapper.NSAppleScriptErrorNumber: number})


class FakeSystemEvents:
    """Answer element commands like System Events, for an element that may appear late."""

    def __init__(self, appears_after_checks=0, attributes=None):
        self.checks_until_present = appears_after_checks
        self.attributes = {"AXTitle": "OK"} if attributes is None else attributes
        self.commands = []

    @property
    def present(self):
        return self.checks_until_present <= 0

    def __call__(self, command, app_process):
        self.commands.append(command)
        if command.startswith("return exists"):
            self.checks_until_present -= 1
            return self.present
        if not self.present:
            raise cant_get()
        if command.startswith("get properties of"):
            return {AEType(b"posn"): [10, 20], AEType(b"ptsz"): [40, 30]}
        if command.startswith("get value of attribute"):
            name = command.split('"')[1]
            if name not in self.attributes:
                raise cant_get()
            return self.attributes[name]
        return None


@pytest.fixture
def system_events(monkeypatch):
    fake = FakeSystemEvents()
    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fake)
    monkeypatch.setattr(applescript_element.time, "sleep", lambda seconds: None)
    return fake


@pytest.fixture
def element():
    return BaseUIElement(LOCATOR, process="Finder")


def test_frame_reads_position_and_size_in_one_call(system_events, element):
    assert element.frame == Frame(10, 20, 50, 50, Point(30, 35), 40, 30)
    assert system_events.commands == [f"get properties of {LOCATOR}"]


def test_attribute_properties_read_in_one_call(system_events, element):
    assert element.title == "OK"
    assert system_events.commands == [f'get value of attribute "AXTitle" of {LOCATOR}']


def test_a_missing_attribute_on_a_present_element_reads_as_none(system_events, element):
    assert element.help is None
    assert system_events.commands == [
        f'get value of attribute "AXHelp" of {LOCATOR}',
        f"return exists {LOCATOR}",
    ]


def test_reads_wait_for_an_element_that_appears_late(system_events, element):
    system_events.checks_until_present = 3

    assert element.title == "OK"
    assert system_events.commands[-1] == f'get value of attribute "AXTitle" of {LOCATOR}'


def test_commands_run_once_when_the_element_is_present(system_events, element):
    element.click()

    assert system_events.commands == [f"click {LOCATOR}"]


def test_reads_raise_lookup_error_when_the_element_never_appears(system_events, element):
    system_events.checks_until_present = 10**6
    with (
        mock.patch.object(BaseUIElement, "wait_displayed", return_value=False),
        pytest.raises(LookupError),
    ):
        _ = element.frame


def test_other_errors_on_a_present_element_propagate(system_events, element, monkeypatch):
    def fail(command, app_process):
        raise cant_get(number=-1719)

    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fail)

    with pytest.raises(AppleScriptError):
        _ = element.frame
