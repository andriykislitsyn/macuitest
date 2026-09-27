from unittest import mock

import pytest

from macuitest.config.settings import settings
from macuitest.lib.elements.controllers import mouse as mouse_module
from macuitest.lib.elements.controllers.mouse import Mouse


@pytest.fixture
def sleep():
    with mock.patch.object(mouse_module.time, "sleep") as sleep:
        yield sleep


@pytest.fixture
def controller(sleep):
    return mock.Mock()


def test_hover_reads_move_duration_from_config_at_call_time(controller, monkeypatch):
    monkeypatch.setattr(settings.mouse, "move", 0.5)

    Mouse(controller).hover(1, 2)

    controller.move_to.assert_called_once_with(1, 2, duration=0.5)


def test_explicit_duration_overrides_config(controller, monkeypatch):
    monkeypatch.setattr(settings.mouse, "move", 0.5)

    Mouse(controller).hover(1, 2, duration=0.1)

    controller.move_to.assert_called_once_with(1, 2, duration=0.1)


def test_click_reads_pause_and_hold_from_config_at_call_time(controller, sleep, monkeypatch):
    monkeypatch.setattr(settings.mouse, "pause", 0.9)
    monkeypatch.setattr(settings.mouse, "hold", 0.7)

    Mouse(controller).click(1, 2)

    sleeps = [call.args[0] for call in sleep.call_args_list]
    assert sleeps[0] == 0.9
    assert 0.7 in sleeps
