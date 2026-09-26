from unittest import mock

import cv2
import numpy
import pytest

from macuitest.config.constants import Frame
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib.elements import applescript_element
from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.operating_system import color_meter
from macuitest.lib.operating_system.color_meter import get_color
from macuitest.lib.operating_system.color_meter import get_most_common_color


def capture(*rows_of_rgb):
    rgb = numpy.array(rows_of_rgb, dtype=numpy.uint8)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGRA)


@pytest.fixture
def make_snapshot():
    with mock.patch.object(color_meter, "monitor") as monitor:
        yield monitor.make_snapshot


def test_get_color_captures_only_the_pixel_at_the_point(make_snapshot):
    make_snapshot.return_value = capture([(0, 0, 128)])

    assert get_color(Point(-1500, 200)) == "navy"
    make_snapshot.assert_called_once_with(Region(-1500, 200, -1499, 201))


@pytest.mark.parametrize(
    "rgb, name",
    [((255, 0, 0), "red"), ((238, 237, 231), "linen"), ((0, 0, 139), "darkblue")],
)
def test_get_color_names_the_perceptually_closest_color(make_snapshot, rgb, name):
    make_snapshot.return_value = capture([rgb])

    assert get_color(Point(0, 0)) == name


def test_most_common_color_counts_pixels_and_skips_ignored_colors(make_snapshot):
    make_snapshot.return_value = capture([(0, 0, 128)] * 7 + [(255, 255, 255)] * 3)

    assert get_most_common_color(0, 0, 10, 1) == "navy"
    assert get_most_common_color(0, 0, 10, 1, ignore_colors=("navy",)) == "white"
    make_snapshot.assert_called_with(Region(0, 0, 10, 1))


def test_most_common_color_raises_when_every_pixel_is_ignored(make_snapshot):
    make_snapshot.return_value = capture([(0, 0, 128)] * 4)

    with pytest.raises(LookupError):
        get_most_common_color(0, 0, 4, 1, ignore_colors=("navy",))


def test_applescript_element_passes_its_frame_in_x1_y1_x2_y2_order():
    frame = Frame(10, 20, 110, 60, Point(60, 40), 100, 40)
    with (
        mock.patch.object(
            BaseUIElement, "frame", new_callable=mock.PropertyMock, return_value=frame
        ),
        mock.patch.object(applescript_element, "get_most_common_color") as get_most_common,
    ):
        BaseUIElement("button 1", process="Finder").most_common_color()

    get_most_common.assert_called_once_with(10, 20, 110, 60, None)
