import os
import warnings
from pathlib import Path
from typing import ClassVar

import cv2
import pytesseract

from macuitest.config.constants import Region
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.ui.monitor import monitor


class OCRManager:
    ocr_engine_mode: ClassVar[int] = 3
    page_segmentation_mode: ClassVar[int] = 6
    tesseract_config: ClassVar[str] = f"--oem {ocr_engine_mode} --psm {page_segmentation_mode}"

    def __init__(self, language: str = "eng"):
        if os.system("tesseract --help > /dev/null 2>&1") != 0:
            warnings.warn("Tesseract is not installed, please install: brew install tesseract")
        self.language = language
        self.trained_data = f"{self.language}.traineddata"
        self.trained_data_path: Path = Path("/usr/local/share/tessdata")
        self.__assert_trained_data_present()

    def wait_text(self, text: str, where: Region, timeout: int = 10) -> bool:
        return wait_condition(lambda: self.recognize(region=where) == text, timeout=timeout)

    def recognize(self, region: Region, is_font_white: bool = False) -> str:
        img_gray = cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGR2GRAY)
        if (
            is_font_white
        ):  # We want to invert font color to get better character recognition results.
            img_gray = cv2.bitwise_not(img_gray)
        payload = pytesseract.image_to_string(
            img_gray, config=self.tesseract_config, lang=self.language
        )
        return os.linesep.join([s for s in payload.splitlines() if s])

    def __assert_trained_data_present(self):
        if not self.trained_data_path.joinpath(self.trained_data).exists():
            Path(self.trained_data_path).mkdir(parents=True, exist_ok=True)
            raise FileNotFoundError(
                f"Download trained data from: "
                f"https://github.com/tesseract-ocr/tessdata_best/raw/master/{self.trained_data}"
                f"and save it to: {self.trained_data_path.joinpath(self.trained_data)}"
            )


ocr_manager = OCRManager()
