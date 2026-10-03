import os

import pytest

from macuitest.lib.elements import applescript_element
from macuitest.lib.elements import native_element
from macuitest.lib.elements.locators.capture import _literal
from macuitest.lib.elements.locators.factories import AppleScriptLocator
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import TextLocator
from macuitest.lib.elements.locators.target import parse_locator


def test_parse_locator_reads_an_ax_call_with_its_kind():
    locator = parse_locator('ax(description="Search", role="AXButton", kind=Button)')

    assert isinstance(locator, AXLocator)
    assert locator.queries[0].attributes == (("AXDescription", "Search"), ("AXRole", "AXButton"))
    assert locator.kind is native_element.Button


def test_parse_locator_reads_an_applescript_kind_from_applescript_element():
    locator = parse_locator('applescript(\'button "OK" of window 1\', kind=Button)')

    assert isinstance(locator, AppleScriptLocator)
    assert locator.kind is applescript_element.Button


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
