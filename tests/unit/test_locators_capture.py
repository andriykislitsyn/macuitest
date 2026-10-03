import cv2
import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.locators import capture as capture_module
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.capture import capture
from macuitest.lib.elements.locators.capture import walk
from macuitest.lib.elements.locators.capture import window_number
from macuitest.lib.elements.native.calls import AXErrorFailure
from macuitest.lib.elements.ui_element import recorded_scale


class FakeAX:
    """An accessibility element with fixed attributes."""

    def __init__(self, *children, **attributes):
        self.attributes = {"AXChildren": list(children), **attributes}
        self.pid = 42
        self.activations = 0

    def activate(self):
        self.activations += 1

    def get_ax_attribute(self, name):
        return self.attributes.get(name)


def element(role, x, y, width, height, **attributes):
    return FakeAX(AXRole=role, AXPosition=(x, y), AXSize=(width, height), **attributes)


def calculator_window():
    """A 200x100 pt window at (10, 20) with a button, a label, chrome, and an off-window item."""
    return FakeAX(
        element("AXButton", 30, 40, 60, 24, AXIdentifier="OK"),
        element("AXStaticText", 100, 40, 50, 20, AXDescription="Total"),
        element("AXButton", 12, 22, 10, 10, AXSubrole="AXCloseButton"),
        element("AXButton", 500, 40, 60, 24, AXIdentifier="Hidden"),
        AXRole="AXWindow",
        AXTitle="Calculator",
        AXPosition=(10, 20),
        AXSize=(200, 100),
    )


def fonts_window():
    """A window with a search button and an outline of two font rows, one with a favorite box."""
    arial = FakeAX(
        element("AXStaticText", 20, 60, 80, 16, AXValue="Arial"),
        AXRole="AXRow",
        AXPosition=(20, 60),
        AXSize=(150, 20),
    )
    helvetica = FakeAX(
        element("AXCheckBox", 150, 82, 10, 10, AXIdentifier="favorite"),
        element("AXStaticText", 20, 80, 80, 16, AXValue="Helvetica"),
        AXRole="AXRow",
        AXPosition=(20, 80),
        AXSize=(150, 20),
    )
    return FakeAX(
        element("AXButton", 30, 30, 20, 20, AXDescription="Search"),
        FakeAX(arial, helvetica, AXRole="AXOutline", AXPosition=(20, 60), AXSize=(150, 40)),
        AXRole="AXWindow",
        AXTitle="Fonts",
        AXPosition=(10, 20),
        AXSize=(200, 100),
    )


@pytest.fixture
def fonts(app, monkeypatch):
    """Serve fonts_window as the app's window."""
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: fonts_window())


@pytest.fixture
def app(monkeypatch, text_image):
    """Serve calculator_window as Calculator's window, captured at 2x, and record queries."""
    queries = []

    def standard_window(name, query=None):
        queries.append(query)
        return calculator_window()

    monkeypatch.setattr(capture_module, "standard_window", standard_window)
    monkeypatch.setattr(capture_module, "windows", lambda name: [])
    monkeypatch.setattr(capture_module, "app_root", lambda name: FakeAX())
    monkeypatch.setattr(capture_module, "window_number", lambda pid, frame: 7)
    monkeypatch.setattr(
        capture_module.monitor, "capture_window", lambda number: text_image([], 200, 100)
    )
    return queries


def test_walk_flags_window_chrome():
    seen = [(found.identifier, found.chrome) for found in walk(calculator_window())]

    assert seen == [("OK", False), (None, False), (None, True), ("Hidden", False)]


def test_capture_skips_window_chrome(app, tmp_path):
    out = tmp_path / "calculator.py"

    capture("Calculator", out)

    assert "close" not in out.read_text()


def test_a_frameless_twin_earlier_in_the_window_takes_the_identifier(
    monkeypatch, tmp_path, text_image
):
    window = FakeAX(
        FakeAX(AXRole="AXButton", AXIdentifier="OK"),
        element("AXButton", 30, 40, 60, 24, AXIdentifier="OK", AXDescription="Confirm"),
        AXRole="AXWindow",
        AXTitle="Calculator",
        AXPosition=(10, 20),
        AXSize=(200, 100),
    )
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: window)
    monkeypatch.setattr(capture_module, "windows", lambda name: [window])
    monkeypatch.setattr(capture_module, "window_number", lambda pid, frame: 7)
    monkeypatch.setattr(
        capture_module.monitor, "capture_window", lambda n: text_image([], 200, 100)
    )
    out = tmp_path / "calculator.py"

    capture("Calculator", out)

    assert 'ok = ax(description="Confirm", role="AXButton", kind=Button)' in out.read_text()


def test_an_element_in_a_front_window_takes_a_shared_title(monkeypatch, tmp_path, text_image):
    palette = FakeAX(
        element("AXButton", 0, 0, 40, 20, AXTitle="Cancel"),
        AXRole="AXWindow",
        AXSubrole="AXFloatingWindow",
        AXPosition=(0, 0),
        AXSize=(50, 30),
    )
    main = FakeAX(
        element("AXButton", 30, 40, 60, 24, AXTitle="Cancel"),
        AXRole="AXWindow",
        AXTitle="Calculator",
        AXPosition=(10, 20),
        AXSize=(200, 100),
    )
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: main)
    monkeypatch.setattr(capture_module, "windows", lambda name: [palette, main])
    monkeypatch.setattr(capture_module, "window_number", lambda pid, frame: 7)
    monkeypatch.setattr(
        capture_module.monitor, "capture_window", lambda n: text_image([], 200, 100)
    )
    out = tmp_path / "calculator.py"

    capture("Calculator", out)

    assert "cancel = image()" in out.read_text()


class SwiftUIToolbarButton(FakeAX):
    """A button whose AXSubrole read fails while its other attributes read fine."""

    def get_ax_attribute(self, name):
        if name == "AXSubrole":
            raise AXErrorFailure("There is some sort of system memory failure")
        return super().get_ax_attribute(name)


def test_walk_keeps_an_element_with_an_unreadable_attribute():
    button = SwiftUIToolbarButton(
        AXRole="AXButton", AXDescription="Mode", AXPosition=(30, 40), AXSize=(20, 20)
    )

    found = walk(FakeAX(FakeAX(button, AXRole="AXToolbar")))

    assert ("AXButton", "Mode") in [(f.role, f.description) for f in found]


def test_walk_drops_identifiers_appkit_generates():
    size = element("AXComboBox", 30, 40, 60, 24, AXIdentifier="_NS:34", AXDescription="Size")

    [found] = walk(FakeAX(size))

    assert (found.identifier, found.description) == (None, "Size")


def test_walk_reads_an_unreadable_role_as_none():
    [found] = walk(FakeAX(FakeAX(AXDescription="Mode")))

    assert found.role is None


def test_capture_names_the_screen_after_the_app_not_its_window(app, tmp_path):
    out = tmp_path / "textedit.py"

    written = capture("TextEdit", out)

    assert "class TextEdit(Screen" in out.read_text()
    assert written[1].parent == tmp_path / "textedit" / "text_edit"


def test_capture_names_a_window_screen_after_its_window(app, tmp_path):
    out = tmp_path / "textedit.py"

    capture("TextEdit", out, window=AXQuery.of(title="Calculator"))

    assert "class Calculator(Screen" in out.read_text()


def test_capture_writes_a_module_and_a_png_per_element_inside_the_window(app, tmp_path):
    out = tmp_path / "calculator.py"

    written = capture("Calculator", out)

    folder = tmp_path / "calculator" / "calculator"
    assert written == [out, folder / "ok.png", folder / "total.png"]
    assert 'ok = ax(identifier="OK", kind=Button)' in out.read_text()
    png = cv2.imread(str(folder / "ok.png"))
    assert png is not None
    # 60x24 pt plus 4 pt on each side, at 2x.
    assert png.shape[:2] == (64, 136)


def test_capture_records_the_capture_scale_in_each_png(app, tmp_path):
    capture("Calculator", tmp_path / "calculator.py")

    assert recorded_scale(tmp_path / "calculator" / "calculator" / "ok.png") == 2


def test_capture_keeps_only_the_given_roles(app, tmp_path):
    out = tmp_path / "calculator.py"

    capture("Calculator", out, roles=["AXStaticText"])

    assert "ok =" not in out.read_text()
    assert "total =" in out.read_text()


def test_capture_of_a_window_screen_declares_its_window(app, tmp_path):
    out = tmp_path / "finder.py"
    dialog = AXQuery.of(subrole="AXDialog")

    capture("Finder", out, window=dialog)

    assert app == [dialog]
    assert 'app="Finder", window=window(subrole="AXDialog")' in out.read_text()


def test_capture_writes_nothing_when_a_target_exists(app, tmp_path):
    out = tmp_path / "calculator.py"
    existing = tmp_path / "calculator" / "calculator" / "ok.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"mine")

    with pytest.raises(FileExistsError, match="--force"):
        capture("Calculator", out)

    assert not out.exists()
    assert not (existing.parent / "total.png").exists()
    assert existing.read_bytes() == b"mine"


def test_capture_with_force_replaces_existing_files(app, tmp_path):
    out = tmp_path / "calculator.py"
    out.write_text("mine")

    capture("Calculator", out, force=True)

    assert out.read_text().startswith('"""Generated by')


def test_capture_needs_a_window(monkeypatch, tmp_path):
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: None)
    monkeypatch.setattr(capture_module, "app_root", lambda name: None)
    monkeypatch.setattr(capture_module, "WINDOW_TIMEOUT", 0)

    with pytest.raises(LookupError, match="Calculator has no matching window"):
        capture("Calculator", tmp_path / "calculator.py")


def test_capture_needs_an_element_of_the_given_roles(app, tmp_path):
    with pytest.raises(LookupError, match="AXSlider"):
        capture("Calculator", tmp_path / "calculator.py", roles=["AXSlider"])


def test_capture_rejects_a_negative_margin(tmp_path):
    with pytest.raises(ValueError, match="margin"):
        capture("Calculator", tmp_path / "calculator.py", margin=-1)


def test_window_number_matches_the_owner_and_bounds(monkeypatch):
    bounds = {"X": 10, "Y": 20, "Width": 200, "Height": 100}
    windows = [
        {
            "kCGWindowOwnerPID": 42,
            "kCGWindowLayer": 25,
            "kCGWindowNumber": 1,
            "kCGWindowBounds": bounds,
        },
        {
            "kCGWindowOwnerPID": 7,
            "kCGWindowLayer": 0,
            "kCGWindowNumber": 2,
            "kCGWindowBounds": bounds,
        },
        {
            "kCGWindowOwnerPID": 42,
            "kCGWindowLayer": 0,
            "kCGWindowNumber": 3,
            "kCGWindowBounds": bounds,
        },
    ]
    monkeypatch.setattr(capture_module.Quartz, "CGWindowListCopyWindowInfo", lambda *args: windows)

    assert window_number(42, Region(10, 20, 210, 120)) == 3
    assert window_number(42, Region(0, 0, 50, 50)) is None


def test_window_number_prefers_the_on_screen_twin(monkeypatch):
    bounds = {"X": 10, "Y": 20, "Width": 200, "Height": 100}
    tab = {"kCGWindowOwnerPID": 42, "kCGWindowLayer": 0, "kCGWindowBounds": bounds}
    windows = [
        {**tab, "kCGWindowNumber": 1},
        {**tab, "kCGWindowNumber": 2, "kCGWindowIsOnscreen": True},
    ]
    monkeypatch.setattr(capture_module.Quartz, "CGWindowListCopyWindowInfo", lambda *args: windows)

    assert window_number(42, Region(10, 20, 210, 120)) == 2


def test_window_number_finds_a_floating_panel_above_layer_0(monkeypatch):
    # TextEdit's Fonts panel sits at window server layer 3.
    bounds = {"X": 1213, "Y": 726, "Width": 478, "Height": 281}
    panel = {"kCGWindowOwnerPID": 42, "kCGWindowLayer": 3, "kCGWindowNumber": 9}
    windows = [{**panel, "kCGWindowBounds": bounds, "kCGWindowIsOnscreen": True}]
    monkeypatch.setattr(capture_module.Quartz, "CGWindowListCopyWindowInfo", lambda *args: windows)

    assert window_number(42, Region(1213, 726, 1691, 1007)) == 9


def test_capture_activates_the_app_and_waits_for_its_window(monkeypatch, tmp_path, text_image):
    # Floating panels, and some apps' windows, appear in AX only while the app is active.
    root = FakeAX()
    answers = iter([None, None, calculator_window()])
    monkeypatch.setattr(capture_module, "app_root", lambda name: root)
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: next(answers))
    monkeypatch.setattr(capture_module, "windows", lambda name: [])
    monkeypatch.setattr(capture_module, "window_number", lambda pid, frame: 7)
    monkeypatch.setattr(
        capture_module.monitor, "capture_window", lambda n: text_image([], 200, 100)
    )

    capture("Calculator", tmp_path / "calculator.py")

    assert root.activations == 1


def test_window_number_prefers_an_app_window_over_a_panel_with_the_same_bounds(monkeypatch):
    bounds = {"X": 10, "Y": 20, "Width": 200, "Height": 100}
    common = {"kCGWindowOwnerPID": 42, "kCGWindowBounds": bounds, "kCGWindowIsOnscreen": True}
    windows = [
        {**common, "kCGWindowLayer": 3, "kCGWindowNumber": 1},
        {**common, "kCGWindowLayer": 0, "kCGWindowNumber": 2},
    ]
    monkeypatch.setattr(capture_module.Quartz, "CGWindowListCopyWindowInfo", lambda *args: windows)

    assert window_number(42, Region(10, 20, 210, 120)) == 2


def test_walk_marks_elements_inside_a_table_or_list():
    seen = [(found.role, found.in_collection) for found in walk(fonts_window())]

    assert seen == [
        ("AXButton", False),
        ("AXOutline", False),
        ("AXRow", True),
        ("AXStaticText", True),
        ("AXRow", True),
        ("AXCheckBox", True),
        ("AXStaticText", True),
    ]


def test_capture_skips_rows_without_a_stable_locator(fonts, tmp_path):
    out = tmp_path / "fonts.py"

    written = capture("TextEdit", out)

    source = out.read_text()
    assert "row =" not in source
    assert "static_text =" not in source
    assert "    # Skipped 4 elements inside tables and lists" in source
    assert {path.stem for path in written[1:]} == {"search", "favorite"}


def test_capture_keeps_an_element_with_a_stable_locator_inside_a_table(fonts, tmp_path):
    out = tmp_path / "fonts.py"

    capture("TextEdit", out)

    assert 'favorite = ax(identifier="favorite", kind=CheckBox)' in out.read_text()


def test_capture_keeps_rows_when_roles_ask_for_them(fonts, tmp_path):
    out = tmp_path / "fonts.py"

    capture("TextEdit", out, roles=["AXRow"])

    assert "row = image()" in out.read_text()
    assert "Skipped" not in out.read_text()


TEXTEDIT_MODULE = """\
\"\"\"TextEdit's screens.\"\"\"

from macuitest.lib.elements.locators import Screen
from macuitest.lib.elements.locators import text


class TextEdit(Screen, app="TextEdit"):
    untitled = text("Untitled")


def helper():
    return 1
"""


def test_capture_appends_a_screen_to_an_existing_module(app, tmp_path):
    out = tmp_path / "textedit.py"
    out.write_text(TEXTEDIT_MODULE)

    capture("Calculator", out, append=True)

    source = out.read_text()
    assert 'class TextEdit(Screen, app="TextEdit"):\n    untitled = text("Untitled")' in source
    assert source.endswith(
        '    return 1\n\n\nclass Calculator(Screen, app="Calculator"):\n'
        + (
            '    ok = ax(identifier="OK", kind=Button)\n'
            '    total = ax(description="Total", role="AXStaticText", kind=StaticText)\n'
        )
    )


def test_capture_append_adds_only_the_missing_imports_after_the_last_one(app, tmp_path):
    out = tmp_path / "textedit.py"
    out.write_text(TEXTEDIT_MODULE)

    capture("Calculator", out, append=True)

    imports = out.read_text().split("\n\n\nclass TextEdit")[0].splitlines()[2:]
    assert imports == [
        "from macuitest.lib.elements.locators import Screen",
        "from macuitest.lib.elements.locators import text",
        "from macuitest.lib.elements.locators import ax",
        "from macuitest.lib.elements.native_element import Button",
        "from macuitest.lib.elements.native_element import StaticText",
    ]


def test_capture_append_refuses_a_screen_the_module_defines(app, tmp_path):
    out = tmp_path / "calculator.py"
    out.write_text("class Calculator:\n    pass\n")

    with pytest.raises(FileExistsError, match="already defines Calculator"):
        capture("Calculator", out, append=True)

    assert out.read_text() == "class Calculator:\n    pass\n"
    assert not (tmp_path / "calculator" / "calculator").exists()


def test_capture_append_writes_a_new_module_when_none_exists(app, tmp_path):
    out = tmp_path / "calculator.py"

    capture("Calculator", out, append=True)

    assert out.read_text().startswith('"""Generated by')


@pytest.mark.parametrize(
    "module, head",
    [
        ("", ""),
        ("TIMEOUT = 3\n", ""),
        ('"""Screens."""\n\nTIMEOUT = 3\n', '"""Screens."""\n\n'),
        ('"""Screens."""', '"""Screens."""\n\n'),
    ],
)
def test_capture_append_puts_imports_at_the_top_of_a_module_without_any(
    app, tmp_path, module, head
):
    out = tmp_path / "calculator.py"
    out.write_text(module)

    capture("Calculator", out, append=True)

    assert out.read_text().startswith(head + "from macuitest.lib.elements.locators import Screen\n")


def test_capture_append_starts_a_new_line_after_a_last_import_without_one(app, tmp_path):
    out = tmp_path / "calculator.py"
    out.write_text("from os import path")

    capture("Calculator", out, append=True)

    assert out.read_text().startswith(
        "from os import path\nfrom macuitest.lib.elements.locators import Screen\n"
    )


def test_capture_append_refuses_existing_pngs_without_force(app, tmp_path):
    out = tmp_path / "textedit.py"
    out.write_text(TEXTEDIT_MODULE)
    existing = tmp_path / "textedit" / "calculator" / "ok.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"mine")

    with pytest.raises(FileExistsError, match="--force"):
        capture("Calculator", out, append=True)

    assert out.read_text() == TEXTEDIT_MODULE
    assert existing.read_bytes() == b"mine"


def test_capture_skips_an_element_inside_a_table_that_repeats_in_every_row(
    app, monkeypatch, tmp_path
):
    rows = [
        FakeAX(
            element("AXCheckBox", 150, y + 2, 10, 10, AXDescription="favorite"),
            AXRole="AXRow",
            AXPosition=(20, y),
            AXSize=(150, 20),
        )
        for y in (60, 80)
    ]
    table = FakeAX(*rows, AXRole="AXTable", AXPosition=(20, 60), AXSize=(150, 40))
    window = FakeAX(table, AXRole="AXWindow", AXPosition=(10, 20), AXSize=(200, 100))
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: window)
    out = tmp_path / "typefaces.py"

    capture("TextEdit", out)

    assert "favorite =" not in out.read_text()
    assert "# Skipped 4 elements" in out.read_text()


def test_walk_flags_a_scroll_bar_and_its_parts_as_chrome():
    bar = FakeAX(element("AXButton", 0, 0, 10, 10), AXRole="AXScrollBar")

    assert [found.chrome for found in walk(FakeAX(bar))] == [True, True]


def layout_window():
    """A window with a toolbar holding a search button, and a group with an identifier."""
    return FakeAX(
        FakeAX(
            element("AXButton", 30, 30, 20, 20, AXDescription="Search"),
            AXRole="AXToolbar",
            AXPosition=(10, 20),
            AXSize=(200, 30),
        ),
        element("AXGroup", 20, 60, 100, 30, AXIdentifier="sidebar"),
        AXRole="AXWindow",
        AXPosition=(10, 20),
        AXSize=(200, 100),
    )


def test_capture_skips_layout_containers_without_a_stable_locator(app, monkeypatch, tmp_path):
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: layout_window())
    out = tmp_path / "layout.py"

    capture("TextEdit", out)

    assert "toolbar" not in out.read_text()
    assert 'sidebar = ax(identifier="sidebar")' in out.read_text()


def test_capture_keeps_layout_containers_when_roles_ask_for_them(app, monkeypatch, tmp_path):
    monkeypatch.setattr(capture_module, "standard_window", lambda name, query=None: layout_window())
    out = tmp_path / "layout.py"

    capture("TextEdit", out, roles=["AXToolbar"])

    assert "toolbar = image()" in out.read_text()
