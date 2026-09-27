import os
from types import SimpleNamespace
from unittest import mock

import pytest
import Quartz

from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.elements import screen_element
from macuitest.lib.elements.ui import ocr_manager as ocr_module
from macuitest.lib.elements.ui.ocr_manager import OCRManager

# Fake capture origin. Negative coordinates catch offset bugs, like a display left of the main one.
REGION = Region(-3008, -376, -2608, -256)


@pytest.fixture
def screen(monkeypatch):
    """Serve `screen["image"]` as the capture of any region."""
    images = {}
    monkeypatch.setattr(ocr_module.monitor, "capture", lambda region: images["image"])
    return images


def fake_observation(line):
    candidate = SimpleNamespace(
        string=lambda: line,
        boundingBoxForRange_error_=lambda range_, error: (None, None),
    )
    box = SimpleNamespace(
        origin=SimpleNamespace(x=0.1, y=0.5), size=SimpleNamespace(width=0.2, height=0.25)
    )
    return SimpleNamespace(topCandidates_=lambda count: [candidate], boundingBox=lambda: box)


def test_find_text_returns_the_label_box_in_global_points(screen, text_image):
    screen["image"] = text_image([("Book OK", 200, 70)], 400, 120)

    (box,) = OCRManager().find_text("book", REGION)

    assert box.x1 == pytest.approx(REGION.x1 + 200, abs=4)
    assert box.y1 == pytest.approx(REGION.y1 + 70, abs=6)
    assert box.x2 - box.x1 == pytest.approx(36, abs=6)


def test_find_text_reads_a_1x_capture(screen, text_image):
    screen["image"] = text_image([("Book OK", 200, 70)], 400, 120, scale=1)

    (box,) = OCRManager().find_text("OK", REGION)

    assert box.x1 == pytest.approx(REGION.x1 + 241, abs=6)


def test_find_text_matches_whole_words_only(screen, text_image):
    screen["image"] = text_image([("Book a demo", 20, 20)], 400, 120)

    assert OCRManager().find_text("OK", REGION) == []


def test_find_text_ignores_case_whitespace_and_a_leading_icon(screen, text_image):
    screen["image"] = text_image([("Э Migrate back to LRS", 40, 30)], 400, 120)

    (box,) = OCRManager().find_text("migrate   BACK to lrs", REGION)

    assert box.x1 > REGION.x1 + 45  # Starts after the "Э" that stands in for an icon.


def test_find_text_orders_matches_topmost_then_leftmost(screen, text_image):
    screen["image"] = text_image([("Send", 300, 10), ("Send", 200, 70), ("Send", 20, 70)], 400, 120)

    boxes = OCRManager().find_text("Send", REGION)

    assert [round(box.x1 - REGION.x1, -1) for box in boxes] == [300, 20, 200]


def test_find_text_reads_each_display_and_orders_matches_globally(text_image, monkeypatch):
    left, main = Region(-400, 200, 0, 320), Region(0, 0, 400, 120)
    images = {
        left.x1: text_image([("Send", 20, 10)], 400, 120),
        main.x1: text_image([("Send", 20, 10)], 400, 120),
    }
    monkeypatch.setattr(ocr_module.monitor, "capture", lambda region: images[region.x1])
    monkeypatch.setattr(type(ocr_module.monitor), "displays", [main, left])

    boxes = OCRManager().find_text("Send")

    assert [round(box.x1, -1) for box in boxes] == [20, -380]


def test_find_text_defaults_to_the_configured_search_region(monkeypatch):
    captured = []
    monkeypatch.setattr(settings.screen, "search_region", REGION)
    monkeypatch.setattr(ocr_module, "_capture", lambda region: captured.append(region))
    monkeypatch.setattr(OCRManager, "_read", lambda self, image, level: [])

    OCRManager().find_text("Send")

    assert captured == [REGION]


def test_accurate_pass_runs_only_when_the_fast_pass_misses(monkeypatch):
    reads = {ocr_module._FAST: [], ocr_module._ACCURATE: [fake_observation("Send")]}
    levels = []

    def read(self, image, level):
        levels.append(level)
        return reads[level]

    monkeypatch.setattr(ocr_module, "_capture", lambda region: None)
    monkeypatch.setattr(OCRManager, "_read", read)

    assert len(OCRManager().find_text("Send", REGION)) == 1
    assert levels == [ocr_module._FAST, ocr_module._ACCURATE]

    levels.clear()
    reads[ocr_module._FAST] = [fake_observation("Send")]
    OCRManager().find_text("Send", REGION)
    assert levels == [ocr_module._FAST]


def test_fast_pass_is_skipped_for_languages_fast_mode_cannot_read(monkeypatch):
    levels = []
    monkeypatch.setattr(ocr_module, "_capture", lambda region: None)
    monkeypatch.setattr(OCRManager, "_read", lambda self, image, level: levels.append(level) or [])

    OCRManager(languages=("uk-UA",)).find_text("Надіслати", REGION)

    assert levels == [ocr_module._ACCURATE]


def test_a_failed_range_lookup_falls_back_to_the_line_box(monkeypatch):
    monkeypatch.setattr(ocr_module, "_capture", lambda region: None)
    monkeypatch.setattr(OCRManager, "_read", lambda self, image, level: [fake_observation("Send")])

    (box,) = OCRManager().find_text("Send", Region(0, 0, 100, 100))

    assert (box.x1, box.y1, box.x2, box.y2) == pytest.approx((10, 25, 30, 50))


def test_capture_upscales_a_1x_capture_to_2x(monkeypatch, text_image):
    monkeypatch.setattr(
        ocr_module.monitor, "capture", lambda region: text_image([], 400, 120, scale=1)
    )

    image = ocr_module._capture(REGION)

    assert (Quartz.CGImageGetWidth(image), Quartz.CGImageGetHeight(image)) == (800, 240)


def test_reading_order_groups_boxes_on_one_line():
    right, left, below = Region(200, 10.4, 240, 26), Region(20, 10, 60, 26), Region(0, 40, 40, 56)

    assert ocr_module._reading_order([below, right, left]) == [left, right, below]


def test_to_region_maps_a_bottom_left_normalized_box_into_the_region():
    box = SimpleNamespace(
        origin=SimpleNamespace(x=0.25, y=0.5), size=SimpleNamespace(width=0.5, height=0.25)
    )

    assert ocr_module._to_region(box, Region(-100, -50, 300, 150)) == Region(0, 0, 200, 50)


def test_utf16_range_counts_surrogate_pairs():
    line = "🚀 Deploy now"
    start = line.index("Deploy")

    assert ocr_module._utf16_range(line, start, start + len("Deploy")) == (3, 6)


def test_unsupported_language_raises():
    with pytest.raises(ValueError, match="xx-XX"):
        OCRManager(languages=("en-US", "xx-XX"))


@pytest.mark.parametrize("text", ["", "   "])
def test_blank_text_raises(text):
    with pytest.raises(ValueError):
        OCRManager().find_text(text, REGION)


def test_recognize_joins_lines_top_to_bottom(screen, text_image):
    screen["image"] = text_image([("Console", 20, 10), ("Services", 20, 70)], 400, 120)

    assert OCRManager().recognize(REGION) == f"Console{os.linesep}Services"


def test_a_failed_vision_request_raises(monkeypatch):
    error = SimpleNamespace(localizedDescription=lambda: "boom")
    vision = mock.Mock()
    handler = vision.VNImageRequestHandler.alloc.return_value.initWithCGImage_options_.return_value
    handler.performRequests_error_.return_value = (False, error)
    monkeypatch.setattr(ocr_module, "Vision", vision)

    with pytest.raises(RuntimeError, match="boom"):
        OCRManager()._read(None, ocr_module._ACCURATE)


@pytest.mark.parametrize("boxes, expected", [([Region(0, 0, 1, 1)], True), ([], False)])
def test_wait_text_reports_whether_the_text_appeared(monkeypatch, boxes, expected):
    monkeypatch.setattr(OCRManager, "find_text", lambda self, text, region=None: boxes)

    assert OCRManager().wait_text("Send", REGION, timeout=0) is expected


@pytest.mark.parametrize("label", ["Don’t Save", "Settings…", "“Quoted”", "Pages 1–3"])
def test_find_text_matches_typographic_punctuation_that_vision_reads_as_ascii(
    screen, text_image, label
):
    screen["image"] = text_image([(label, 40, 30)], 400, 120)

    assert len(OCRManager().find_text(label, REGION)) == 1


@pytest.mark.parametrize(
    "needle, line", [("Don't", "Don’t"), ("Settings...", "Settings…"), ("1-3", "1—3")]
)
def test_pattern_treats_ascii_and_typographic_punctuation_alike(needle, line):
    assert ocr_module._pattern(needle).search(line)


def test_find_text_rejects_an_empty_region():
    with pytest.raises(ValueError, match="empty"):
        OCRManager().find_text("Send", Region(0, 0, 0, 100))


def test_a_bare_language_string_raises_with_the_tuple_form():
    with pytest.raises(TypeError, match=r"\('en-US',\)"):
        OCRManager(languages="en-US")


def test_find_text_searches_the_configured_display(monkeypatch):
    displays = [Region(0, 0, 400, 120), REGION]
    captured = []
    monkeypatch.setattr(type(screen_element.monitor), "displays", displays)
    monkeypatch.setattr(settings.screen, "display", 1)
    monkeypatch.setattr(ocr_module, "_capture", lambda region: captured.append(region))
    monkeypatch.setattr(OCRManager, "_read", lambda self, image, level: [])

    OCRManager().find_text("Send")

    assert captured == [REGION]


def test_default_languages_follow_the_ocr_setting_at_call_time(monkeypatch):
    levels = []
    manager = OCRManager()
    monkeypatch.setattr(settings.ocr, "languages", ("uk-UA",))
    monkeypatch.setattr(ocr_module, "_capture", lambda region: None)
    monkeypatch.setattr(OCRManager, "_read", lambda self, image, level: levels.append(level) or [])

    manager.find_text("Send", REGION)

    assert manager.languages == ("uk-UA",)
    assert levels == [ocr_module._ACCURATE]


def test_an_unsupported_configured_language_raises_on_use(monkeypatch):
    monkeypatch.setattr(settings.ocr, "languages", ("xx-XX",))

    with pytest.raises(ValueError, match=r"xx-XX.*settings\.ocr\.languages"):
        OCRManager().find_text("Send", REGION)


def test_recognize_checks_the_configured_languages(monkeypatch):
    monkeypatch.setattr(settings.ocr, "languages", ("xx-XX",))

    with pytest.raises(ValueError, match="settings.ocr.languages"):
        OCRManager().recognize(REGION)
