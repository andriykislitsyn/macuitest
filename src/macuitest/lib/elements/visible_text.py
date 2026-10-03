"""Screen elements found by their visible text."""

import unicodedata
from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements.screen_element import ScreenElement
from macuitest.lib.elements.ui.ocr_manager import OCRManager
from macuitest.lib.elements.ui.ocr_manager import ocr_manager


class VisibleText(ScreenElement):
    """Visible text, found with Apple Vision.

    Matching ignores case, treats any run of whitespace as one space, and respects word
    boundaries, so `VisibleText("OK")` doesn't match "Book". When the text appears more than
    once, the topmost, then leftmost, match wins. Pass an `OCRManager` built for other languages
    as `ocr`.
    """

    def __init__(self, text: str, ocr: OCRManager = ocr_manager):
        """Create an element for `text`.

        Raises:
            ValueError: `text` is a single character, which Vision doesn't read reliably.
        """
        if len(unicodedata.normalize("NFC", text.strip())) == 1:
            raise ValueError(
                f"Vision can't reliably read the single character {text.strip()!r}. "
                "Find it with an accessibility locator or an image instead."
            )
        self.text = text
        self.ocr = ocr

    def __repr__(self):
        return f'<VisibleText "{self.text}">'

    def _locate(self, region: Optional[Region]) -> Optional[Region]:
        boxes = self.ocr.find_text(self.text, region)
        return boxes[0] if boxes else None
