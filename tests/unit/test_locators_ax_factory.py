import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.locators import Screen
from macuitest.lib.elements.locators import ax
from macuitest.lib.elements.locators import factories
from macuitest.lib.elements.locators import image
from macuitest.lib.elements.locators import text
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement
from macuitest.lib.elements.native_element import Button
from macuitest.lib.elements.native_element import NativeElement


class FakeAX:
    """An accessibility element with fixed attributes."""

    def __init__(self, *children, **attributes):
        self.attributes = {"AXChildren": list(children), **attributes}

    def get_ax_attribute(self, name):
        return self.attributes.get(name)


@pytest.fixture
def app_windows(monkeypatch):
    """Serve a mutable list as the app's windows."""
    served = []
    monkeypatch.setattr(factories, "windows", lambda app: served)
    return served


def test_ax_reads_as_the_matching_element_wrapped_in_its_kind(app_windows):
    seven = FakeAX(AXIdentifier="Seven", AXRole="AXButton")
    app_windows.append(FakeAX(FakeAX(seven)))

    class Calculator(Screen, app="Calculator"):
        seven = ax(identifier="Seven", kind=Button)

    assert isinstance(Calculator.seven, Button)
    assert Calculator.seven.item is seven


def test_ax_defaults_to_native_element(app_windows):
    app_windows.append(FakeAX(FakeAX(AXIdentifier="Seven")))

    class Calculator(Screen, app="Calculator"):
        seven = ax(identifier="Seven")

    assert type(Calculator.seven) is NativeElement


def test_ax_finds_the_element_again_on_every_read(app_windows):
    first, second = FakeAX(AXIdentifier="Seven"), FakeAX(AXIdentifier="Seven")
    app_windows.append(FakeAX(first))

    class Calculator(Screen, app="Calculator"):
        seven = ax(identifier="Seven")

    assert Calculator.seven.item is first
    app_windows[:] = [FakeAX(second)]
    assert Calculator.seven.item is second


def test_child_narrows_to_a_descendant(app_windows):
    value = FakeAX(AXRole="AXStaticText", AXValue="‎42")
    app_windows.append(FakeAX(FakeAX(AXRole="AXStaticText"), FakeAX(value, AXIdentifier="Display")))

    class Calculator(Screen, app="Calculator"):
        display = ax(identifier="Display").child(role="AXStaticText")

    assert Calculator.display.value == "‎42"


def test_a_missing_element_raises_naming_the_screen_and_filter(app_windows):
    class Calculator(Screen, app="Calculator"):
        seven = ax(identifier="Seven")

    missing = r"Calculator\.seven: no element with AXIdentifier='Seven'"
    with pytest.raises(LookupError, match=missing):
        _ = Calculator.seven


def test_ax_needs_an_app_screen(app_windows):
    class Main(Screen):
        seven = ax(identifier="Seven")

    with pytest.raises(TypeError, match="Main.seven"):
        _ = Main.seven


def test_ax_needs_an_attribute():
    with pytest.raises(TypeError, match="at least one"):
        ax()


def test_within_scopes_a_lookup_to_that_elements_frame(app_windows):
    keypad = FakeAX(AXIdentifier="Keypad", AXPosition=(10, 20), AXSize=(100, 200))
    app_windows.append(FakeAX(keypad))

    class Calculator(Screen, app="Calculator"):
        keypad = ax(identifier="Keypad")
        all_clear = text("AC", within=keypad)

    assert Calculator.all_clear.scope is not None
    assert Calculator.all_clear.scope() == Region(10, 20, 110, 220)


def test_within_an_element_that_isnt_there_finds_nothing(app_windows):
    class Calculator(Screen, app="Calculator"):
        keypad = ax(identifier="Keypad")
        all_clear = text("AC", within=keypad)

    assert Calculator.all_clear.locate() is None


def test_within_takes_an_element_of_the_same_screen():
    class Other(Screen, app="Calculator"):
        keypad = ax(identifier="Keypad")

    with pytest.raises(TypeError, match="within="):

        class Calculator(Screen, app="Calculator"):
            all_clear = text("AC", within=Other.__dict__["keypad"])


def test_image_within_takes_an_element_of_the_same_screen():
    class Other(Screen, app="Calculator"):
        keypad = ax(identifier="Keypad")

    with pytest.raises(TypeError, match="within="):

        class Calculator(Screen, app="Calculator"):
            logo = image(within=Other.__dict__["keypad"])


def test_image_within_scopes_a_lookup_to_that_elements_frame(app_windows, tmp_path):
    import importlib.util
    import sys
    import textwrap

    import cv2
    import numpy

    keypad = FakeAX(AXIdentifier="Keypad", AXPosition=(10, 20), AXSize=(100, 200))
    app_windows.append(FakeAX(keypad))
    png = tmp_path / "screens" / "calculator" / "logo.png"
    png.parent.mkdir(parents=True)
    cv2.imwrite(str(png), numpy.full((20, 40), 128, numpy.uint8))
    source = tmp_path / "screens.py"
    source.write_text(
        textwrap.dedent(
            """
            from macuitest.lib.elements.locators import Screen, ax, image

            class Calculator(Screen, app="Calculator"):
                keypad = ax(identifier="Keypad")
                logo = image(within=keypad)
            """
        )
    )
    spec = importlib.util.spec_from_file_location("screens_within", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module.Calculator.logo.scope is not None
    assert module.Calculator.logo.scope() == Region(10, 20, 110, 220)


class Vanishing(FakeAX):
    """An element that raises for every attribute, like one whose window just closed."""

    def get_ax_attribute(self, name):
        raise AXErrorInvalidUIElement("gone")


def test_an_element_that_vanishes_mid_search_reads_as_missing(app_windows):
    app_windows.append(Vanishing())

    class Calculator(Screen, app="Calculator"):
        keypad = ax(identifier="Keypad")
        all_clear = text("AC", within=keypad)

    assert Calculator.all_clear.locate() is None
    with pytest.raises(LookupError):
        _ = Calculator.keypad
