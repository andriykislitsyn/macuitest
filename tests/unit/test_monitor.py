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
