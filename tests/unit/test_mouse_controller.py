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
