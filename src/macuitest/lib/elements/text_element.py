"""Screen elements found by their visible text."""

from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements.screen_element import ScreenElement
from macuitest.lib.elements.ui.ocr_manager import OCRManager
from macuitest.lib.elements.ui.ocr_manager import ocr_manager


class TextElement(ScreenElement):
    """Visible text, found with Apple Vision.

    Matching ignores case, treats any run of whitespace as one space, and respects word
    boundaries, so `TextElement("OK")` doesn't match "Book". When the text appears more than
    once, the topmost, then leftmost, match wins. Pass an `OCRManager` built for other languages
    as `ocr`.
    """

    def __init__(self, text: str, ocr: OCRManager = ocr_manager):
        self.text = text
        self.ocr = ocr

    def __repr__(self):
        return f'<TextElement "{self.text}">'

    def locate(self, region: Optional[Region] = None) -> Optional[Region]:
        boxes = self.ocr.find_text(self.text, region)
        return boxes[0] if boxes else None
