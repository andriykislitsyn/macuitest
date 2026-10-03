from unittest import mock

import pytest

from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.apps import application
from macuitest.lib.apps.application import Application
from macuitest.lib.elements import applescript_element

STANDARD_WINDOW = '(first window whose subrole is "AXStandardWindow")'


@pytest.fixture
def tell_app_process():
    with (
        mock.patch.object(application.as_wrapper, "tell_app_process") as tell,
        mock.patch.object(
            Application,
            "is_frontmost",
            new_callable=mock.PropertyMock,
            side_effect=AssertionError("not needed"),
        ),
    ):
        yield tell


def test_window_targets_the_first_standard_window():
    assert Application("Google Chrome").window.locator == STANDARD_WINDOW


def test_window_stays_one_reference_inside_attribute_and_child_commands():
    window = Application("Google Chrome").window
    with mock.patch.object(applescript_element.as_wrapper, "tell_app_process") as tell:
        window.get_attribute_value("AXPosition")
        window.perform_action("AXRaise")

    assert [call.kwargs["command"] for call in tell.call_args_list] == [
        f'get value of attribute "AXPosition" of {STANDARD_WINDOW}',
        f'perform action "AXRaise" of {STANDARD_WINDOW}',
    ]


@pytest.mark.parametrize(
    "method, value, command",
    [
        ("set_window_size", "{1920, 1220}", f"set size of {STANDARD_WINDOW} to {{1920, 1220}}"),
        ("set_window_position", "{0, 25}", f"set position of {STANDARD_WINDOW} to {{0, 25}}"),
    ],
)
def test_window_setters_act_on_the_standard_window_without_needing_focus(
    tell_app_process, method, value, command
):
    getattr(Application("Google Chrome"), method)(value)

    tell_app_process.assert_called_once_with(command, "Google Chrome")


@pytest.mark.parametrize("method", ["set_window_size", "set_window_position"])
def test_window_setters_raise_when_system_events_fails(tell_app_process, method):
    tell_app_process.side_effect = AppleScriptError({})

    with pytest.raises(AppleScriptError):
        getattr(Application("Google Chrome"), method)("{1, 1}")


@pytest.mark.parametrize("name", ["is_frontmost", "is_hidden"])
def test_state_reads_are_properties(name):
    with mock.patch.object(Application, "_read_attribute", return_value=True):
        assert getattr(Application("Finder"), name) is True


@pytest.mark.parametrize("name, reads", [("frontmost", "is_frontmost"), ("hidden", "is_hidden")])
def test_state_twins_read_through_the_is_properties(name, reads):
    with (
        mock.patch.object(Application, "_read_attribute", return_value=False),
        mock.patch.object(Application, reads, new_callable=mock.PropertyMock, return_value=True),
    ):
        assert getattr(Application("Finder"), name) is True
