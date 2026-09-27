from types import SimpleNamespace
from unittest import mock

import numpy
import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.ui import monitor as monitor_module
from macuitest.lib.elements.ui.monitor import Monitor


def rect(x, y, width, height):
    return SimpleNamespace(
        origin=SimpleNamespace(x=x, y=y), size=SimpleNamespace(width=width, height=height)
    )


@pytest.mark.parametrize(
    "displays, expected",
    [
        ({1: rect(0, 0, 1728, 1117)}, Region(0, 0, 1728, 1117)),
        (
            {1: rect(0, 0, 1728, 1117), 3: rect(-3008, -376, 3008, 1692)},
            Region(-3008, -376, 1728, 1316),
        ),
    ],
    ids=["single display", "secondary display at negative offset"],
)
def test_bounds_spans_every_display(displays, expected):
    with (
        mock.patch.object(
            monitor_module,
            "CGGetActiveDisplayList",
            return_value=(0, list(displays), len(displays)),
        ),
        mock.patch.object(monitor_module, "CGDisplayBounds", side_effect=displays.get),
    ):
        assert Monitor().bounds == expected


def test_make_snapshot_uses_captured_pixel_dimensions():
    # A 2x capture whose rows carry one pixel of stride padding.
    width, height, row_stride = 4, 2, 5
    pixels = numpy.arange(height * row_stride * 4, dtype=numpy.uint8)
    with (
        mock.patch.object(
            Monitor, "get_pixel_data", return_value=(pixels.tobytes(), row_stride, width, height)
        ),
        mock.patch.object(Monitor, "size", new_callable=mock.PropertyMock) as size,
    ):
        snapshot = Monitor().make_snapshot(Region(0, 0, 2, 1))

    assert snapshot.shape == (height, width, 4)
    assert (snapshot == pixels.reshape(height, row_stride, 4)[:, :width]).all()
    size.assert_not_called()


def test_is_retina_reads_the_menu_bar_display():
    menu_bar, other = mock.Mock(), mock.Mock()
    menu_bar.backingScaleFactor.return_value = 1.0
    other.backingScaleFactor.return_value = 2.0
    with mock.patch.object(monitor_module.AppKit, "NSScreen") as ns_screen:
        ns_screen.screens.return_value = [menu_bar, other]
        ns_screen.mainScreen.return_value = other

        assert Monitor().is_retina is False


def test_displays_lists_every_display_menu_bar_first():
    displays = {1: rect(0, 0, 1728, 1117), 3: rect(-3008, -376, 3008, 1692)}
    with (
        mock.patch.object(monitor_module, "CGGetActiveDisplayList", return_value=(0, [1, 3], 2)),
        mock.patch.object(monitor_module, "CGDisplayBounds", side_effect=displays.get),
    ):
        assert Monitor().displays == [Region(0, 0, 1728, 1117), Region(-3008, -376, 0, 1316)]


def test_capture_requests_the_region_in_points():
    with mock.patch.object(monitor_module.CoreGraphics, "CGWindowListCreateImage") as create:
        Monitor.capture(Region(-10, -20, 30, 40))

    assert create.call_args.args[0] == monitor_module.CoreGraphics.CGRectMake(-10, -20, 40, 60)


def test_unit_tests_cannot_capture_the_screen():
    with pytest.raises(RuntimeError, match="must not capture the screen"):
        Monitor.capture(Region(0, 0, 10, 10))


@pytest.mark.parametrize("region", [Region(0, 0, 0, 100), Region(0, 50, 100, 20)])
def test_capture_rejects_an_empty_region(region):
    with pytest.raises(ValueError, match="empty"):
        Monitor.capture(region)
