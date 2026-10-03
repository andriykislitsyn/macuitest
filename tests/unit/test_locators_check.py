import textwrap
from pathlib import Path
from unittest import mock

import pytest

from macuitest.lib import app_actions
from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.elements.locators import AXLocator
from macuitest.lib.elements.locators.check import Report
from macuitest.lib.elements.locators.check import check
from macuitest.lib.elements.locators.check import check_live
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


LIVE_SOURCE = """
from macuitest.lib.elements.locators import Screen, applescript, ax, image, text

class Main(Screen, app="Calculator"):
    seven = ax(identifier="Seven")
    result = ax(identifier="Result")
    mode = applescript('menu item "Basic" of menu "View"')
    label = text("Send")
    logo = image()

class Loose(Screen):
    ok = ax(identifier="OK")
"""


@pytest.fixture
def live_module(tmp_path):
    (tmp_path / "screens.py").write_text(textwrap.dedent(LIVE_SOURCE))
    return load_module(tmp_path / "screens.py")


@pytest.fixture
def calculator_running():
    with mock.patch.object(app_actions, "running", return_value=[object()]) as running:
        yield running


def fake_find(missing=()):
    def find(locator):
        return None if locator.name in missing else object()

    return mock.patch.object(AXLocator, "find", autospec=True, side_effect=find)


def fake_exists(value):
    return mock.patch.object(
        BaseUIElement, "exists", new_callable=mock.PropertyMock, return_value=value
    )


def test_live_check_finds_every_checkable_element(live_module, calculator_running):
    with fake_find(), fake_exists(True):
        report = check_live(live_module)

    assert report.found == ["Main.seven", "Main.result", "Main.mode"]
    assert report.missing == []
    assert report.clean


def test_live_check_reports_the_ax_elements_it_cant_find(live_module, calculator_running):
    with fake_find(missing={"result"}), fake_exists(True):
        report = check_live(live_module)

    assert report.missing == ["Main.result"]
    assert report.found == ["Main.seven", "Main.mode"]
    assert not report.clean


def test_live_check_reports_an_applescript_element_system_events_doesnt_find(
    live_module, calculator_running
):
    with fake_find(), fake_exists(False):
        report = check_live(live_module)

    assert report.missing == ["Main.mode"]


def test_live_check_skips_text_and_image_elements_and_screens_without_an_app(
    live_module, calculator_running
):
    with fake_find(), fake_exists(True):
        report = check_live(live_module)

    assert report.skipped == ["Main.label", "Main.logo", "Loose.ok"]


def test_live_check_names_an_app_that_isnt_running_instead_of_listing_every_miss(live_module):
    with mock.patch.object(app_actions, "running", return_value=[]):
        with fake_find() as find, fake_exists(True):
            report = check_live(live_module)

    assert report.not_running == ["Calculator"]
    assert report.missing == []
    assert report.found == []
    assert not report.clean
    find.assert_not_called()
