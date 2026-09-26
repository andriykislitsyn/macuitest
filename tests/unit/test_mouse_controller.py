from types import SimpleNamespace
from unittest import mock

import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.controllers import mouse_controller
from macuitest.lib.elements.controllers.mouse_controller import MouseController

VIRTUAL_DESKTOP = Region(-3008, -376, 1728, 1316)


@pytest.fixture
def sent_events():
    events = []
    with (
        mock.patch.object(mouse_controller, "monitor", SimpleNamespace(bounds=VIRTUAL_DESKTOP)),
        mock.patch.object(
            MouseController, "position", new_callable=mock.PropertyMock, return_value=(100, 100)
        ),
        mock.patch.object(
            MouseController,
            "_send_mouse_event",
            side_effect=lambda _event, x, y, _button: events.append((x, y)),
        ),
        mock.patch.object(mouse_controller.time, "sleep"),
    ):
        yield events


@pytest.mark.parametrize(
    "target, expected",
    [
        ((-1500, 200), (-1500, 200)),
        ((-5000, 5000), (-3008, 1315)),
        ((9000, -900), (1727, -376)),
    ],
    ids=["secondary display", "past bottom-left corner", "past top-right corner"],
)
def test_move_to_clamps_to_virtual_desktop(sent_events, target, expected):
    MouseController().move_to(*target, duration=0)

    assert sent_events[-1] == expected


@pytest.fixture
def timed_events():
    now = [0.0]
    events = []

    def sleep(seconds):
        now[0] += seconds

    with (
        mock.patch.object(mouse_controller, "monitor", SimpleNamespace(bounds=VIRTUAL_DESKTOP)),
        mock.patch.object(
            MouseController, "position", new_callable=mock.PropertyMock, return_value=(0, 0)
        ),
        mock.patch.object(
            MouseController,
            "_send_mouse_event",
            side_effect=lambda _event, x, y, _button: events.append((now[0], x, y)),
        ),
        mock.patch.object(mouse_controller.time, "sleep", side_effect=sleep),
        mock.patch.object(mouse_controller.time, "perf_counter", side_effect=lambda: now[0]),
    ):
        yield events


@pytest.mark.parametrize("target", [(10, 0), (1700, 1300)], ids=["10 px", "2100 px"])
def test_move_lasts_duration_at_a_steady_event_rate_whatever_the_distance(timed_events, target):
    MouseController().move_to(*target, duration=0.5)

    assert len(timed_events) == 60
    last_time, *last_point = timed_events[-1]
    assert last_time == pytest.approx(0.5)
    assert tuple(last_point) == target
