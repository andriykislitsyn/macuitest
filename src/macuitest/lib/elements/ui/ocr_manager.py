import os
from typing import ClassVar

import cv2

from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.ui.monitor import monitor


class OCRManager:
    """Read text from the screen with Tesseract.

    Requires the `ocr` extra (`pip install "macuitest[ocr]"`) and a Tesseract install
    (`brew install tesseract`).
    """

    ocr_engine_mode: ClassVar[int] = 3
    page_segmentation_mode: ClassVar[int] = 6
    tesseract_config: ClassVar[str] = f"--oem {ocr_engine_mode} --psm {page_segmentation_mode}"

    def __init__(self, language: str = "eng"):
        self.language = language

    def wait_text(self, text: str, where: Region, timeout: int = 10) -> bool:
        return wait_condition(lambda: self.recognize(region=where) == text, timeout=timeout)

    def recognize(self, region: Region, is_font_white: bool = False) -> str:
        """Return the text Tesseract reads in `region`, without blank lines.

        Raises:
            ImportError: The `ocr` extra isn't installed.
        """
        try:
            import pytesseract
        except ImportError as e:
            raise ImportError('OCR needs the ocr extra: pip install "macuitest[ocr]"') from e
        img_gray = cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGR2GRAY)
        if is_font_white:  # Tesseract reads dark text on a light background best.
            img_gray = cv2.bitwise_not(img_gray)
        payload = pytesseract.image_to_string(
            img_gray, config=self.tesseract_config, lang=self.language
        )
        return os.linesep.join([s for s in payload.splitlines() if s])


ocr_manager = OCRManager()
