import os
import textwrap

import cv2
import numpy
import pytest

from macuitest.lib.elements import native_element
from macuitest.lib.elements import native_element as native
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.capture import _literal
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import TextLocator
from macuitest.lib.elements.locators.target import parse_locator
from macuitest.lib.elements.locators.target import resolve


def test_parse_locator_reads_an_ax_call_with_its_kind():
    locator = parse_locator('ax(description="Search", role="AXButton", kind=Button)')

    assert isinstance(locator, AXLocator)
    assert locator.queries[0].attributes == (("AXDescription", "Search"), ("AXRole", "AXButton"))
    assert locator.kind is native_element.Button


def test_parse_locator_rejects_applescript_since_it_runs_as_script():
    with pytest.raises(ValueError, match="Screen module"):
        parse_locator('applescript("(do shell script \\"touch /tmp/pwned\\")")')


def test_parse_locator_reads_text_within_an_ax_element():
    locator = parse_locator('text("AC", within=ax(identifier="CalculatorKeypadView"))')

    assert isinstance(locator, TextLocator)
    assert isinstance(locator.within, AXLocator)


@pytest.mark.parametrize("label", ['say "hi"', "back\\slash", "Grüße", "日本語"])
def test_parse_locator_round_trips_what_capture_prints(label):
    locator = parse_locator(f"ax(title={_literal(label)})")

    assert isinstance(locator, AXLocator)
    assert locator.queries[0].attributes == (("AXTitle", label),)


@pytest.mark.parametrize(
    "source",
    [
        'ax(identifier=__import__("os").system("true"))',
        'eval("1")',
        'ax(identifier="OK").child(role="AXButton")',
        "ax(**{'identifier': 'OK'})",
        'ax(identifier="OK", kind=os.system)',
        'ax(identifier="OK", kind=Nope)',
        'ax(identifier="OK", kind=Button) + 1',
        "ax(identifier=f'{1}')",
        'text("AC", within=text("B C"))',
        'image("mode")',
        "ax(",
        "",
    ],
)
def test_parse_locator_rejects_anything_outside_the_whitelist(source):
    with pytest.raises(ValueError):
        parse_locator(source)


def test_parse_locator_never_evaluates_a_rejected_call(monkeypatch):
    monkeypatch.delenv("MACUITEST_EVALUATED", raising=False)
    side_effect = "__import__('os').environ.__setitem__('MACUITEST_EVALUATED', '1')"

    with pytest.raises(ValueError):
        parse_locator(f"ax(identifier={side_effect})")

    assert "MACUITEST_EVALUATED" not in os.environ


def test_parse_locator_reports_a_bad_keyword_as_a_value_error():
    with pytest.raises(ValueError, match="identifer"):
        parse_locator('ax(identifer="OK")')


def test_resolve_binds_a_locator_string_to_the_app_and_window():
    target = resolve(["TextEdit", 'ax(identifier="OK", kind=Button)'], AXQuery.of(title="Fonts"))

    assert isinstance(target.element, native.Button)
    assert target.app == "TextEdit"
    assert target.label == 'ax(identifier="OK", kind=Button)'


def test_resolve_binds_text_within_to_the_same_screen():
    target = resolve(["Calculator", 'text("AC", within=ax(identifier="Keypad"))'])

    assert target.element.scope is not None


def write_screens(tmp_path):
    module = tmp_path / "screens.py"
    module.write_text(
        textwrap.dedent(
            """\
            from macuitest.lib.elements.locators import Screen, ax
            from macuitest.lib.elements.native_element import Button


            class Fonts(Screen, app="TextEdit"):
                search = ax(description="Search", kind=Button)
            """
        )
    )
    return module


def test_resolve_reads_a_module_reference(tmp_path):
    module = write_screens(tmp_path)

    target = resolve([f"{module}:Fonts.search"])

    assert isinstance(target.element, native.Button)
    assert target.app == "TextEdit"
    assert target.label == f"{module}:Fonts.search"


@pytest.mark.parametrize(
    "reference, message",
    [
        ("missing.py:Fonts.search", "No such file"),
        ("{module}:Nope.search", "no screen Nope"),
        ("{module}:Fonts.nope", "Fonts has no element nope"),
    ],
)
def test_resolve_rejects_a_bad_module_reference(tmp_path, reference, message):
    module = write_screens(tmp_path)

    with pytest.raises(ValueError, match=message):
        resolve([reference.format(module=module)])


def test_resolve_rejects_window_flags_with_a_module_reference(tmp_path):
    module = write_screens(tmp_path)

    with pytest.raises(ValueError, match="--window"):
        resolve([f"{module}:Fonts.search"], AXQuery.of(title="Fonts"))


def test_resolve_needs_an_app_and_a_locator():
    with pytest.raises(ValueError, match="<app> <locator>"):
        resolve(["TextEdit"])


def test_resolve_reads_an_element_a_screen_inherits(tmp_path):
    module = tmp_path / "screens.py"
    module.write_text(
        textwrap.dedent(
            """\
            from macuitest.lib.elements.locators import Screen, ax


            class Base(Screen, app="TextEdit"):
                search = ax(description="Search")


            class Fonts(Base):
                pass
            """
        )
    )

    assert resolve([f"{module}:Fonts.search"]).app == "TextEdit"


@pytest.mark.parametrize(
    "source",
    [
        "def broken(:\n",
        "undefined_name\n",
        "from macuitest.lib.elements.locators import Screen, ax\n\n\n"
        "class Fonts(Screen):\n    search = ax(description='Search')\n",
        "from macuitest.lib.elements.locators import Screen, image\n\n\n"
        "class Fonts(Screen, app='TextEdit'):\n    search = image()\n",
    ],
    ids=["syntax error", "error at import", "screen without app", "missing image"],
)
def test_resolve_reports_a_module_that_fails_as_a_bad_reference(tmp_path, source):
    module = tmp_path / "screens.py"
    module.write_text(source)

    with pytest.raises(ValueError, match="screens.py"):
        resolve([f"{module}:Fonts.search"])


def test_resolve_scopes_a_module_text_element_to_its_within(tmp_path):
    module = tmp_path / "screens.py"
    module.write_text(
        textwrap.dedent(
            """\
            from macuitest.lib.elements.locators import Screen, ax, text


            class Calculator(Screen, app="Calculator"):
                keypad = ax(identifier="CalculatorKeypadView")
                all_clear = text("AC", within=keypad)
            """
        )
    )

    element = resolve([f"{module}:Calculator.all_clear"]).element

    assert element.scope == vars(module_screen(module, "Calculator"))["keypad"].region


def module_screen(module, name):
    import sys

    return getattr(sys.modules[f"macuitest_checked_{module.stem}"], name)


def test_resolve_loads_a_module_image_element_from_its_folder(tmp_path):
    module = tmp_path / "screens.py"
    module.write_text(
        "from macuitest.lib.elements.locators import Screen, image\n\n\n"
        "class Fonts(Screen, app='TextEdit'):\n    search = image()\n"
    )
    png = tmp_path / "screens" / "fonts" / "search.png"
    png.parent.mkdir(parents=True)
    cv2.imwrite(str(png), numpy.zeros((8, 8), dtype=numpy.uint8))

    element = resolve([f"{module}:Fonts.search"]).element

    assert element.path == png
