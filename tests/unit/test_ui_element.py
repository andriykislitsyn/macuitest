from unittest import mock

import cv2
import numpy
import pytest

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib.elements import ui_element
from macuitest.lib.elements.ui_element import UIElement

# A 2x retina capture of a region whose origin sits on a secondary display.
REGION = Region(-3008, -376, -2708, -176)
TEMPLATE_PX = (200, 100)  # Top-left of the template inside the capture, in pixels.
TEMPLATE_SIZE_PX = (40, 32)


@pytest.fixture
def screen():
    gray = numpy.random.default_rng(seed=7).integers(0, 256, size=(400, 600), dtype=numpy.uint8)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGRA)


@pytest.fixture
def fake_monitor(screen):
    fake = mock.Mock(is_retina=True, bounds=REGION)
    fake.make_snapshot.return_value = screen
    with mock.patch.object(ui_element, "monitor", fake):
        yield fake


def save_template(screen, tmp_path, x=TEMPLATE_PX[0], y=TEMPLATE_PX[1]):
    width, height = TEMPLATE_SIZE_PX
    path = tmp_path / "template.png"
    cv2.imwrite(str(path), cv2.cvtColor(screen[y : y + height, x : x + width], cv2.COLOR_BGRA2GRAY))
    return path


def test_detect_on_screen_converts_pixels_to_points_from_region_origin(
    fake_monitor, screen, tmp_path
):
    element = UIElement(save_template(screen, tmp_path))

    assert element.detect_on_screen(REGION) == Point(REGION.x1 + 100, REGION.y1 + 50)


def test_detect_on_screen_defaults_to_whole_virtual_desktop(fake_monitor, screen, tmp_path):
    UIElement(save_template(screen, tmp_path)).detect_on_screen()

    fake_monitor.make_snapshot.assert_called_once_with(fake_monitor.bounds)


def test_get_center_offsets_by_half_the_template_size_in_points(fake_monitor, screen, tmp_path):
    element = UIElement(save_template(screen, tmp_path))

    assert element.get_center(REGION) == Point(REGION.x1 + 100 + 10, REGION.y1 + 50 + 8)


def test_detect_on_screen_returns_none_without_a_match(fake_monitor, screen, tmp_path):
    unrelated = numpy.random.default_rng(seed=8).integers(
        0, 256, size=(400, 600), dtype=numpy.uint8
    )
    element = UIElement(save_template(cv2.cvtColor(unrelated, cv2.COLOR_GRAY2BGRA), tmp_path))

    assert element.detect_on_screen(REGION) is None


@pytest.mark.parametrize("match, expected", [(False, False), (Point(0, 0), True)])
def test_is_visible_reflects_whether_the_pattern_matched(
    fake_monitor, screen, tmp_path, match, expected
):
    element = UIElement(save_template(screen, tmp_path))
    with mock.patch.object(UIElement, "wait_displayed", return_value=match):
        assert element.is_visible is expected


def test_detect_on_screen_rescales_a_retina_pattern_for_a_1x_capture(
    fake_monitor, screen, tmp_path
):
    element = UIElement(save_template(screen, tmp_path))
    fake_monitor.make_snapshot.return_value = cv2.resize(
        screen, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA
    )
    region = Region(0, 0, 300, 200)

    assert element.detect_on_screen(region) == Point(100, 50)
