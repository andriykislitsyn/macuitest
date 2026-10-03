from unittest import mock

import pytest

from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.config.settings import settings
from macuitest.lib.applescript_lib import applescript_wrapper
from macuitest.lib.applescript_lib.aeconverter import AEType
from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.elements import applescript_element
from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.elements.applescript_element import Window

LOCATOR = 'button "OK" of window 1'


def cant_get(number=-1728):
    return AppleScriptError({applescript_wrapper.NSAppleScriptErrorNumber: number})


class FakeSystemEvents:
    """Answer element commands like System Events, for an element that may appear late."""

    def __init__(self, appears_after_checks=0, attributes=None, missing_error=-1728):
        self.checks_until_present = appears_after_checks
        self.missing_error = missing_error
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
            raise cant_get(number=self.missing_error)
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


def test_an_exists_check_that_fails_propagates_its_error(system_events, element, monkeypatch):
    def fail(command, app_process):
        raise cant_get(number=-1719)

    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fail)

    with pytest.raises(AppleScriptError):
        _ = element.frame


def test_a_whose_locator_that_matches_nothing_yet_waits_for_the_element(system_events, element):
    # `first button whose ...` raises -1719 (invalid index) instead of -1728 while nothing matches.
    system_events.missing_error = -1719
    system_events.checks_until_present = 3

    element.click()

    assert system_events.commands[-1] == f"click {LOCATOR}"


def test_invalid_index_on_a_present_element_propagates(system_events, element, monkeypatch):
    def fail(command, app_process):
        if command.startswith("return exists"):
            return True
        raise cant_get(number=-1719)

    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fail)

    with pytest.raises(AppleScriptError):
        element.click()


def test_errors_that_dont_mean_missing_propagate_at_once(system_events, element, monkeypatch):
    def fail(command, app_process):
        raise cant_get(number=-10006)

    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fail)

    with pytest.raises(AppleScriptError):
        element.click()


def test_lookup_error_keeps_system_events_message(system_events, element):
    system_events.checks_until_present = 10**6
    with (
        mock.patch.object(BaseUIElement, "wait_displayed", return_value=False),
        pytest.raises(LookupError) as missing,
    ):
        element.click()

    assert isinstance(missing.value.__cause__, AppleScriptError)


@pytest.fixture
def mouse():
    with mock.patch.object(applescript_element, "mouse") as fake:
        yield fake


@pytest.mark.parametrize(
    "method, controller, options",
    [
        ("click_mouse", "click", {"hold": 1, "duration": 2, "pause": 3}),
        ("right_click_mouse", "right_click", {"hold": 1, "duration": 2, "pause": 3}),
        ("double_click_mouse", "double_click", {"duration": 2}),
        ("hover_mouse", "hover", {"duration": 2}),
    ],
)
def test_mouse_methods_pass_their_options(
    system_events, element, mouse, method, controller, options
):
    getattr(element, method)(1, 1, **options)

    getattr(mouse, controller).assert_called_once_with(31, 36, **options)


@pytest.mark.parametrize(
    "method", ["click_mouse", "right_click_mouse", "double_click_mouse", "hover_mouse"]
)
def test_mouse_options_are_keyword_only(system_events, element, mouse, method):
    with pytest.raises(TypeError):
        getattr(element, method)(0, 0, 0.5)


def test_is_visible_checks_once_without_waiting(monkeypatch, element):
    events = FakeSystemEvents(appears_after_checks=2)
    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", events)

    assert element.is_visible is False
    assert events.commands == [f"return exists {LOCATOR}"]


def test_exists_reads_a_handler_error_as_false(element, monkeypatch):
    def fail(command, app_process):
        raise cant_get(number=-10000)

    monkeypatch.setattr(applescript_element.as_wrapper, "tell_app_process", fail)

    assert element.exists is False


@pytest.mark.parametrize(
    "method, setting", [("wait_displayed", "timeout"), ("wait_vanish", "vanish_timeout")]
)
def test_waits_default_to_the_elements_timeouts(
    system_events, element, monkeypatch, method, setting
):
    monkeypatch.setattr(settings.elements, setting, 7)
    with mock.patch.object(applescript_element, "wait_condition", autospec=True) as wait:
        getattr(element, method)()

    assert wait.call_args.kwargs["timeout"] == 7


def test_reads_wait_for_the_configured_timeout(system_events, element, monkeypatch):
    monkeypatch.setattr(settings.elements, "timeout", 7)
    system_events.checks_until_present = 2
    with mock.patch.object(
        applescript_element, "wait_condition", wraps=applescript_element.wait_condition
    ) as wait:
        assert element.title == "OK"

    assert wait.call_args.kwargs["timeout"] == 7


@pytest.mark.parametrize(
    "name, attribute", [("is_minimized", "AXMinimized"), ("is_full_screen", "AXFullScreen")]
)
def test_window_state_reads_are_properties(system_events, name, attribute):
    system_events.attributes = {attribute: True}

    assert getattr(Window(LOCATOR, process="Finder"), name) is True


def test_set_full_screen_writes_the_full_screen_attribute(system_events):
    Window(LOCATOR, process="Finder").full_screen = True

    assert any('"AXFullScreen"' in command for command in system_events.commands)
