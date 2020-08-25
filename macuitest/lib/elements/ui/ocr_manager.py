import os
import tempfile
from dataclasses import astuple
from pathlib import Path
from typing import ClassVar, Optional, Tuple, Union

import cv2
import numpy as np
import pytesseract
import requests
from macuitest.config.constants import Region

from macuitest.lib.elements.ui.monitor import monitor


class OCRManager:
    ocr_engine_mode: ClassVar[int] = 3
    page_segmentation_mode: ClassVar[int] = 6
    # Source: https://www.pyimagesearch.com/2017/07/10/using-tesseract-ocr-python
    config: ClassVar[str] = f'--oem {ocr_engine_mode} --psm {page_segmentation_mode}'

    def __init__(self, language: str = 'eng'):
        self.language = language
        self.trained_data = f'{self.language}.traineddata'
        self.trained_data_path: Path = Path('/usr/local/share/tessdata')
        self.url_tesseract_dataset = f"https://github.com/tesseract-ocr/tessdata_best/raw/master/{self.trained_data}"
        self.__assert_trained_data_present()

    def recognize(self, region: Optional[Union[Tuple[int, int, int, int], Region]] = None):
        _, screenshot = tempfile.mkstemp()
        _region_ = astuple(region) if type(region) is Region else region
        monitor.save_screenshot(where=screenshot, region=_region_)
        image = cv2.imread(screenshot)
        if self.is_dark(image):
            image = cv2.bitwise_not(image)
        payload = pytesseract.image_to_string(image, config=self.config, lang=self.language)
        recognized = os.linesep.join([s for s in payload.splitlines() if s])
        os.unlink(screenshot)
        return recognized

    @staticmethod
    def is_dark(image) -> bool:
        """Check whether image is dark: https://stackoverflow.com/a/52506830/9215267
            Since the image is dark, we need to invert it.
            Tesseract is better at finding text on images with light background and dark text.
            Source: https://stackoverflow.com/a/40954142/9215267
        """
        threshold: int = 127
        return np.mean(image) < threshold

    def __assert_trained_data_present(self):
        if not self.trained_data_path.joinpath(self.trained_data).exists():
            response = requests.get(self.url_tesseract_dataset)  # Download Tesseract trained dataset.
            with open(self.trained_data_path.joinpath(self.trained_data), 'wb') as dataset:
                dataset.write(response.content)


ocr_manager = OCRManager()
