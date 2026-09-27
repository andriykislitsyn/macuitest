from unittest import mock

import pytest

from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.elements import screen_element
from macuitest.lib.elements.screen_element import UIElementNotFoundOnScreen
from macuitest.lib.elements.text_element import TextElement
from macuitest.lib.elements.ui.ocr_manager import OCRManager

REGION = Region(-400, 0, 0, 300)


@pytest.fixture
def ocr():
    return mock.Mock(spec=OCRManager)


def test_locate_returns_the_topmost_match(ocr):
    ocr.find_text.return_value = [Region(10, 20, 50, 40), Region(10, 90, 50, 110)]

    assert TextElement("Send", ocr=ocr).locate(REGION) == Region(10, 20, 50, 40)
    ocr.find_text.assert_called_once_with("Send", REGION)


def test_locate_returns_none_without_a_match(ocr):
    ocr.find_text.return_value = []

    assert TextElement("Send", ocr=ocr).locate() is None


def test_click_mouse_clicks_the_text_center(ocr):
    ocr.find_text.return_value = [Region(10, 20, 50, 40)]
    with mock.patch.object(screen_element, "mouse") as mouse:
        TextElement("Send", ocr=ocr).click_mouse(y_off=2)

    mouse.click.assert_called_once_with(30, 32, hold=None, pause=None)


def test_get_center_raises_when_the_text_never_appears(ocr):
    ocr.find_text.return_value = []
    with (
        mock.patch.object(screen_element, "wait_condition", return_value=False),
        pytest.raises(UIElementNotFoundOnScreen, match="Send"),
    ):
        TextElement("Send", ocr=ocr).get_center()


def test_wait_vanish_reports_when_the_text_is_gone(ocr):
    ocr.find_text.return_value = []

    assert TextElement("Send", ocr=ocr).wait_vanish(timeout=0) is True


@pytest.mark.parametrize(
    "wait, setting", [("wait_displayed", "timeout"), ("wait_vanish", "vanish_timeout")]
)
def test_waits_default_to_the_elements_timeouts(ocr, monkeypatch, wait, setting):
    monkeypatch.setattr(settings.elements, setting, 7)
    with mock.patch.object(screen_element, "wait_condition", return_value=False) as wait_condition:
        getattr(TextElement("Send", ocr=ocr), wait)()

    assert wait_condition.call_args.kwargs["timeout"] == 7
