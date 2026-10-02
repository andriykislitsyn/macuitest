import textwrap
from pathlib import Path

import pytest

from macuitest.lib.elements.locators.check import Report
from macuitest.lib.elements.locators.check import check
from macuitest.lib.elements.locators.check import load_module

SOURCE = """
from macuitest.lib.elements.locators import Screen, ax, image, text

class Main(Screen, app="Calculator"):
    ok = image()
    send = image("send_btn")
    label = text("Send")
    seven = ax(identifier="Seven")
"""


@pytest.fixture
def screens(tmp_path):
    """Write SOURCE as screens.py with every declared PNG, and return the image folder."""
    (tmp_path / "screens.py").write_text(textwrap.dedent(SOURCE))
    folder = tmp_path / "screens" / "main"
    folder.mkdir(parents=True)
    for name in ("ok", "send_btn"):
        (folder / f"{name}.png").write_bytes(b"png")
    return folder


def run(folder: Path) -> Report:
    return check(load_module(folder.parent.parent / "screens.py"))


def test_a_complete_module_is_clean(screens):
    report = run(screens)

    assert report == Report(missing=[], undeclared=[])
    assert report.clean


def test_a_declared_image_missing_on_disk_is_reported(screens):
    (screens / "ok.png").unlink()

    assert run(screens).missing == [screens / "ok.png"]


def test_a_png_no_element_declares_is_reported(screens):
    (screens / "stray.png").write_bytes(b"png")

    assert run(screens).undeclared == [screens / "stray.png"]


def test_variants_and_pngs_of_other_element_kinds_count_as_declared(screens):
    for name in ("ok@dark", "seven", "label", "send"):
        (screens / f"{name}.png").write_bytes(b"png")

    assert run(screens).clean


def test_pngs_of_a_screen_that_no_longer_exists_are_reported(screens):
    old = screens.parent / "old_screen"
    old.mkdir()
    (old / "ok.png").write_bytes(b"png")

    assert run(screens).undeclared == [old / "ok.png"]


def test_a_file_that_isnt_python_cannot_be_loaded(tmp_path):
    with pytest.raises(ImportError):
        load_module(tmp_path / "notes.txt")
