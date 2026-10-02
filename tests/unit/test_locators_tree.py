import textwrap

import pytest

from macuitest.lib.elements.locators import tree as tree_module
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.tree import tree


class FakeAX:
    """An accessibility element with fixed attributes."""

    def __init__(self, *children, **attributes):
        self.attributes = {"AXChildren": list(children), **attributes}
        self.activations = 0

    def activate(self):
        self.activations += 1

    def get_ax_attribute(self, name):
        return self.attributes.get(name)


def calculator_window():
    return FakeAX(
        FakeAX(
            FakeAX(AXRole="AXButton", AXIdentifier="Seven", AXDescription="7"),
            AXRole="AXGroup",
            AXIdentifier="Keypad",
        ),
        FakeAX(AXRole="AXStaticText", AXValue="‎0"),
        FakeAX(AXRole="AXButton", AXSubrole="AXCloseButton"),
        AXRole="AXWindow",
        AXTitle="Calculator",
        AXSubrole="AXStandardWindow",
    )


class Windows(list):
    """The app's windows, plus the app root that counts activations."""

    root: FakeAX


@pytest.fixture
def served(monkeypatch):
    windows = Windows()
    windows.root = FakeAX()
    monkeypatch.setattr(tree_module, "windows", lambda app: windows)
    monkeypatch.setattr(tree_module, "app_root", lambda app: windows.root)
    return windows


def test_tree_indents_each_element_under_its_window_with_its_locator(served):
    served.append(calculator_window())

    assert tree("Calculator") == textwrap.dedent(
        """\
        AXWindow title="Calculator" subrole="AXStandardWindow"
          AXGroup identifier="Keypad"  ax(identifier="Keypad")
            AXButton identifier="Seven" description="7"  ax(identifier="Seven", kind=Button)
          AXStaticText value="‎0"
          AXButton [chrome]
        """
    )


def test_tree_shows_a_locator_only_for_the_first_of_identical_elements(served):
    served.append(
        FakeAX(
            FakeAX(AXRole="AXButton", AXDescription="favorite"),
            FakeAX(AXRole="AXButton", AXDescription="favorite"),
            AXRole="AXWindow",
        )
    )

    lines = tree("TextEdit").splitlines()

    assert lines[1].endswith('ax(description="favorite", role="AXButton", kind=Button)')
    assert lines[2] == '  AXButton description="favorite"'


def test_tree_trims_long_values(served):
    served.append(FakeAX(FakeAX(AXRole="AXTextArea", AXValue="x" * 100), AXRole="AXWindow"))

    assert tree("TextEdit").splitlines()[1] == f'  AXTextArea value="{"x" * 40}…"'


def test_tree_keeps_only_the_given_roles(served):
    served.append(calculator_window())

    lines = tree("Calculator", roles=["AXStaticText"]).splitlines()

    assert lines == [
        'AXWindow title="Calculator" subrole="AXStandardWindow"',
        '  AXStaticText value="‎0"',
    ]


def test_tree_with_a_window_query_shows_only_that_window(served, monkeypatch):
    fonts = FakeAX(
        FakeAX(AXRole="AXButton", AXDescription="Search"), AXRole="AXWindow", AXTitle="Fonts"
    )
    served.extend([FakeAX(AXRole="AXWindow", AXTitle="Untitled"), fonts])
    monkeypatch.setattr(
        tree_module, "standard_window", lambda app, query=None: fonts if query else served[0]
    )

    lines = tree("TextEdit", window=AXQuery.of(title="Fonts")).splitlines()

    assert lines[0] == 'AXWindow title="Fonts"'
    assert len(lines) == 2


def test_tree_without_windows_suggests_activating(served):
    with pytest.raises(LookupError, match="Calculator .* pass --activate"):
        tree("Calculator")


def test_tree_without_the_queried_window_names_the_query(served, monkeypatch):
    monkeypatch.setattr(tree_module, "standard_window", lambda app, query=None: None)

    with pytest.raises(LookupError, match="AXTitle='Fonts'"):
        tree("TextEdit", window=AXQuery.of(title="Fonts"))


def test_tree_leaves_the_app_in_the_background_by_default(served):
    served.append(calculator_window())

    tree("Calculator")

    assert served.root.activations == 0


def test_tree_activates_the_app_when_asked(served):
    served.append(calculator_window())

    tree("Calculator", activate=True)

    assert served.root.activations == 1
