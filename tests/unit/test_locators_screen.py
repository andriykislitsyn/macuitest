import importlib.util
import sys
import textwrap
from pathlib import Path

import cv2
import numpy
import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.applescript_element import BaseUIElement
from macuitest.lib.elements.applescript_element import Button
from macuitest.lib.elements.locators import Screen
from macuitest.lib.elements.locators import applescript
from macuitest.lib.elements.locators import factories
from macuitest.lib.elements.locators import text
from macuitest.lib.elements.locators.screen import image_folder
from macuitest.lib.elements.locators.screen import snake_case
from macuitest.lib.elements.ui_element import UIElement
from macuitest.lib.elements.visible_text import VisibleText


def load(path: Path, source: str):
    """Import `source`, written to `path`, as a module."""
    path.write_text(textwrap.dedent(source))
    spec = importlib.util.spec_from_file_location(f"screens_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), numpy.full((20, 40), 128, numpy.uint8))


def test_screens_are_not_instantiated():
    class Main(Screen):
        pass

    with pytest.raises(TypeError, match="Main is a Screen"):
        Main()


def test_a_screen_records_its_app():
    class Main(Screen, app="Calculator"):
        pass

    assert Main.app == "Calculator"


def test_elements_must_be_declared_on_a_screen():
    with pytest.raises(TypeError, match="Screen subclass"):

        class NotAScreen:
            ok = text("OK")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("UseCases", "use_cases"),
        ("HTTPServer", "http_server"),
        ("main, SidebarNavigationSplitView", "main_sidebar_navigation_split_view"),
        ("All Clear", "all_clear"),
        ("Готово", ""),
    ],
)
def test_snake_case(name, expected):
    assert snake_case(name) == expected


def test_images_live_next_to_the_module_in_a_folder_per_screen():
    folder = image_folder(Path("/x/apps/calculator.py"), "UseCases")

    assert folder == Path("/x/apps/calculator/use_cases")


def test_text_reads_as_the_same_visible_text_every_time():
    class Main(Screen):
        ok = text("OK")

    assert isinstance(Main.ok, VisibleText)
    assert Main.ok is Main.ok
    assert Main.ok.text == "OK"


def test_single_character_text_fails_at_declaration():
    with pytest.raises(ValueError, match="single character"):

        class Main(Screen):
            seven = text("7")


def test_text_without_an_app_uses_the_default_search_area():
    class Main(Screen):
        ok = text("OK")

    assert Main.ok.scope is None


def test_text_on_an_app_screen_searches_the_app_window(monkeypatch):
    monkeypatch.setattr(factories, "standard_window_frame", lambda app: Region(0, 0, 9, 9))

    class Main(Screen, app="Calculator"):
        ok = text("OK")

    assert Main.ok.scope is not None
    assert Main.ok.scope() == Region(0, 0, 9, 9)


def test_image_loads_the_png_named_after_the_attribute(tmp_path):
    write_png(tmp_path / "screens" / "main" / "send.png")
    module = load(
        tmp_path / "screens.py",
        """
        from macuitest.lib.elements.locators import Screen, image

        class Main(Screen):
            send = image(similarity=0.9)
        """,
    )

    assert isinstance(module.Main.send, UIElement)
    assert Path(module.Main.send.path) == tmp_path / "screens" / "main" / "send.png"
    assert module.Main.send.similarity == 0.9


def test_image_takes_an_explicit_file_name(tmp_path):
    write_png(tmp_path / "screens" / "main" / "send_btn.png")
    module = load(
        tmp_path / "screens.py",
        """
        from macuitest.lib.elements.locators import Screen, image

        class Main(Screen):
            send = image("send_btn")
        """,
    )

    assert Path(module.Main.send.path).name == "send_btn.png"


def test_a_missing_png_fails_on_first_read_naming_the_path(tmp_path):
    module = load(
        tmp_path / "screens.py",
        """
        from macuitest.lib.elements.locators import Screen, image

        class Main(Screen):
            send = image()
        """,
    )

    with pytest.raises(FileNotFoundError, match=str(tmp_path / "screens" / "main" / "send.png")):
        _ = module.Main.send


def test_applescript_takes_its_process_from_the_app():
    class Main(Screen, app="Calculator"):
        ok = applescript('button "OK" of window 1', kind=Button)

    assert isinstance(Main.ok, Button)
    assert (Main.ok.locator, Main.ok.process) == ('button "OK" of window 1', "Calculator")


def test_applescript_defaults_to_the_base_element():
    class Main(Screen, app="Calculator"):
        ok = applescript('button "OK" of window 1')

    assert type(Main.ok) is BaseUIElement


def test_applescript_takes_an_explicit_process():
    class Main(Screen):
        ok = applescript('button "OK" of window 1', process="Finder")

    assert Main.ok.process == "Finder"


def test_applescript_needs_an_app_or_a_process():
    class Main(Screen):
        ok = applescript('button "OK" of window 1')

    with pytest.raises(TypeError, match="Main.ok"):
        _ = Main.ok


def test_image_without_an_app_uses_the_default_search_area(tmp_path):
    write_png(tmp_path / "screens" / "main" / "send.png")
    module = load(
        tmp_path / "screens.py",
        """
        from macuitest.lib.elements.locators import Screen, image

        class Main(Screen):
            send = image()
        """,
    )

    assert module.Main.send.scope is None


def test_image_on_an_app_screen_searches_the_app_window(tmp_path, monkeypatch):
    monkeypatch.setattr(factories, "standard_window_frame", lambda app: Region(0, 0, 9, 9))
    write_png(tmp_path / "screens" / "main" / "send.png")
    module = load(
        tmp_path / "screens.py",
        """
        from macuitest.lib.elements.locators import Screen, image

        class Main(Screen, app="Calculator"):
            send = image()
        """,
    )

    assert module.Main.send.scope is not None
    assert module.Main.send.scope() == Region(0, 0, 9, 9)
