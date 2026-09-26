import importlib
import os
import sys
from unittest import mock

import numpy
import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.ui import ocr_manager as ocr_module
from macuitest.lib.elements.ui.ocr_manager import OCRManager

REGION = Region(0, 0, 4, 4)


@pytest.fixture
def pytesseract(monkeypatch):
    fake = mock.Mock()
    fake.image_to_string.return_value = "first\n\nsecond\n"
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    monkeypatch.setattr(
        ocr_module.monitor,
        "make_snapshot",
        lambda region: numpy.zeros((4, 4, 4), dtype=numpy.uint8),
    )
    return fake


def test_import_has_no_side_effects():
    with (
        mock.patch("os.system") as system,
        mock.patch("pathlib.Path.mkdir") as mkdir,
        mock.patch("subprocess.run") as run,
    ):
        importlib.reload(ocr_module)

    system.assert_not_called()
    mkdir.assert_not_called()
    run.assert_not_called()


def test_recognize_without_the_ocr_extra_explains_how_to_install_it(monkeypatch):
    monkeypatch.setitem(sys.modules, "pytesseract", None)

    with pytest.raises(ImportError, match=r"macuitest\[ocr\]"):
        OCRManager().recognize(REGION)


def test_recognize_drops_blank_lines(pytesseract):
    assert OCRManager().recognize(REGION) == f"first{os.linesep}second"


def test_recognize_inverts_white_text(pytesseract):
    OCRManager().recognize(REGION, is_font_white=True)

    image = pytesseract.image_to_string.call_args.args[0]
    assert (image == 255).all()
