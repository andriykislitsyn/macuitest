from unittest import mock

import cv2
import numpy
import pytest

from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.elements import screen_element
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


@pytest.mark.parametrize("match, expected", [(None, False), (Region(0, 0, 1, 1), True)])
def test_is_visible_reflects_whether_the_pattern_matched(
    fake_monitor, screen, tmp_path, match, expected
):
    element = UIElement(save_template(screen, tmp_path))
    with mock.patch.object(UIElement, "locate", return_value=match):
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


def test_locate_returns_the_match_box_in_points(fake_monitor, screen, tmp_path):
    element = UIElement(save_template(screen, tmp_path))

    assert element.locate(REGION) == Region(
        REGION.x1 + 100, REGION.y1 + 50, REGION.x1 + 120, REGION.y1 + 66
    )


def test_wait_displayed_returns_the_match_box(fake_monitor, screen, tmp_path):
    element = UIElement(save_template(screen, tmp_path))

    assert element.wait_displayed(region=REGION) == element.locate(REGION)


def test_detect_on_screen_defaults_to_the_configured_search_region(
    fake_monitor, screen, tmp_path, monkeypatch
):
    configured = Region(0, 0, 300, 200)  # Differs from the fake monitor's bounds.
    monkeypatch.setattr(settings.screen, "search_region", configured)

    UIElement(save_template(screen, tmp_path)).detect_on_screen()

    fake_monitor.make_snapshot.assert_called_once_with(configured)


def test_click_mouse_clicks_the_box_center(fake_monitor, screen, tmp_path):
    element = UIElement(save_template(screen, tmp_path))
    with mock.patch.object(screen_element, "mouse") as mouse:
        element.click_mouse(x_off=1, region=REGION)

    mouse.click.assert_called_once_with(
        REGION.x1 + 110 + 1, REGION.y1 + 58, hold=None, duration=None, pause=None
    )


def test_detect_on_screen_searches_the_configured_display(
    fake_monitor, screen, tmp_path, monkeypatch
):
    second = Region(0, 0, 300, 200)  # Differs from the fake monitor's bounds.
    fake_monitor.displays = [REGION, second]
    monkeypatch.setattr(screen_element, "monitor", fake_monitor)
    monkeypatch.setattr(settings.screen, "display", 1)

    UIElement(save_template(screen, tmp_path)).detect_on_screen()

    fake_monitor.make_snapshot.assert_called_once_with(second)


@pytest.mark.parametrize("similarity, expected", [(None, 0.99), (0.5, 0.5)])
def test_similarity_defaults_to_the_elements_setting_at_call_time(
    fake_monitor, screen, tmp_path, monkeypatch, similarity, expected
):
    element = UIElement(save_template(screen, tmp_path), similarity=similarity)
    monkeypatch.setattr(settings.elements, "similarity", 0.99)
    with mock.patch.object(ui_element, "find_template", return_value=None) as find:
        element.detect_on_screen(REGION)

    assert find.call_args.args[2] == expected


def test_repr_shows_the_similarity_in_effect(fake_monitor, screen, tmp_path, monkeypatch):
    monkeypatch.setattr(settings.elements, "similarity", 0.8)

    assert "similarity=0.8>" in repr(UIElement(save_template(screen, tmp_path)))


def test_similarity_reads_the_value_in_effect(fake_monitor, screen, tmp_path, monkeypatch):
    monkeypatch.setattr(settings.elements, "similarity", 0.8)
    element = UIElement(save_template(screen, tmp_path))

    assert element.similarity == 0.8
    element.similarity = 0.6
    assert element.similarity == 0.6
