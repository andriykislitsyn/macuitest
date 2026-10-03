from unittest import mock

import pytest

from macuitest.lib import actions
from macuitest.lib import app_actions
from macuitest.lib.elements.controllers.keyboard_controller import KeyBoardController
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.ui_element import recorded_scale


class FakeRunning:
    """An NSRunningApplication with a name and a process ID."""

    def __init__(self, name, pid):
        self.name, self.pid, self.terminated = name, pid, False

    def localizedName(self):
        return self.name

    def processIdentifier(self):
        return self.pid

    def terminate(self):
        self.terminated = True
        return True


@pytest.fixture
def workspace(monkeypatch):
    """Serve a mutable list as the running applications."""
    apps = []
    appkit = mock.Mock()
    appkit.NSWorkspace.sharedWorkspace.return_value.runningApplications.return_value = apps
    monkeypatch.setattr(app_actions, "AppKit", appkit)
    return apps


@pytest.fixture
def opened(monkeypatch):
    """Record `open` calls, which succeed, and serve an app root that activates."""
    calls = []
    monkeypatch.setattr(
        app_actions.subprocess,
        "run",
        lambda args, **kwargs: calls.append(args) or mock.Mock(returncode=0, stderr=""),
    )
    monkeypatch.setattr(app_actions, "app_root", lambda app: mock.Mock())
    return calls


def test_launch_opens_the_app_without_a_shell(opened):
    app_actions.launch("Text Edit; rm -rf ~")

    assert opened == [["open", "-a", "Text Edit; rm -rf ~"]]


def test_launch_reports_what_open_says_about_an_unknown_app(monkeypatch):
    failure = mock.Mock(returncode=1, stderr="Unable to find application named 'Nope'\n")
    monkeypatch.setattr(app_actions.subprocess, "run", lambda args, **kwargs: failure)

    with pytest.raises(app_actions.LaunchError, match="Unable to find application named 'Nope'"):
        app_actions.launch("Nope")


def test_launch_raises_when_no_window_appears(opened, monkeypatch):
    monkeypatch.setattr(app_actions, "app_root", lambda app: None)

    with pytest.raises(actions.NoWindowError, match="TextEdit is running but has no window"):
        app_actions.launch("TextEdit", timeout=0)


def test_launch_activates_the_app_so_its_windows_show(opened, monkeypatch):
    root = mock.Mock()
    monkeypatch.setattr(app_actions, "app_root", lambda app: root)

    app_actions.launch("Calculator")

    root.activate.assert_called_once_with()


def test_quit_asks_the_app_to_quit_and_waits(workspace, monkeypatch):
    textedit = FakeRunning("TextEdit", 41)
    workspace.extend([FakeRunning("Finder", 7), textedit])
    monkeypatch.setattr(app_actions, "alive", lambda pid: not textedit.terminated)

    assert app_actions.quit("TextEdit") is True
    assert textedit.terminated


def test_quit_returns_false_when_the_app_isnt_running(workspace):
    assert app_actions.quit("TextEdit") is False


def test_quit_raises_when_the_app_is_still_running(workspace, monkeypatch):
    workspace.append(FakeRunning("TextEdit", 41))
    monkeypatch.setattr(app_actions, "alive", lambda pid: True)

    with pytest.raises(app_actions.QuitError, match="may be asking to save"):
        app_actions.quit("TextEdit", timeout=0)


class FakeAX:
    """An accessibility element with fixed attributes that records presses."""

    def __init__(self, *children, **attributes):
        self.attributes = {"AXChildren": list(children), "AXEnabled": True, **attributes}
        self.presses = 0
        self.pid = 41

    def get_ax_attribute(self, name):
        return self.attributes.get(name)

    def press(self):
        self.presses += 1


def item(title, *children, enabled=True):
    return FakeAX(*children, AXRole="AXMenuItem", AXTitle=title, AXEnabled=enabled)


def submenu(*items):
    return FakeAX(*items, AXRole="AXMenu")


@pytest.fixture
def menu_bar(monkeypatch):
    """Serve TextEdit with File > New, Save…, Export > PDF, and a disabled Revert."""
    pdf = item("PDF")
    parts = {
        "new": item("New"),
        "save": item("Save…"),
        "pdf": pdf,
        "revert": item("Revert", enabled=False),
    }
    file_menu = submenu(
        parts["new"], item(""), parts["save"], item("Export", submenu(pdf)), parts["revert"]
    )
    bar = FakeAX(
        FakeAX(file_menu, AXRole="AXMenuBarItem", AXTitle="File"),
        AXRole="AXMenuBar",
    )
    monkeypatch.setattr(app_actions, "app_element", lambda app: FakeAX(bar))
    return parts


def test_menu_presses_an_item(menu_bar):
    app_actions.menu("TextEdit", "File > New")

    assert menu_bar["new"].presses == 1


def test_menu_matches_three_dots_to_an_ellipsis(menu_bar):
    app_actions.menu("TextEdit", "File > Save...")

    assert menu_bar["save"].presses == 1


def test_menu_walks_into_a_submenu(menu_bar):
    app_actions.menu("TextEdit", "File>Export>PDF")

    assert menu_bar["pdf"].presses == 1


def test_menu_lists_the_titles_where_a_step_is_missing(menu_bar):
    with pytest.raises(actions.ActionError, match='No "Sav" in File. It has: New, Save…, Export'):
        app_actions.menu("TextEdit", "File > Sav")


def test_menu_refuses_a_disabled_item(menu_bar):
    with pytest.raises(actions.ActionError, match="Revert is disabled"):
        app_actions.menu("TextEdit", "File > Revert")

    assert menu_bar["revert"].presses == 0


def test_menu_needs_a_menu_and_an_item(menu_bar):
    with pytest.raises(actions.UsageError, match="File > Save"):
        app_actions.menu("TextEdit", "File")


def test_menu_raises_no_window_error_when_the_app_isnt_running(monkeypatch):
    monkeypatch.setattr(app_actions, "app_element", lambda app: None)

    with pytest.raises(actions.NoWindowError, match="TextEdit isn't running"):
        app_actions.menu("TextEdit", "File > New")


@pytest.mark.parametrize(
    "combo, expected",
    [
        ("cmd+s", ["command", "s"]),
        ("command+shift+s", ["command", "shift", "s"]),
        ("ctrl+alt+delete", ["ctrl", "option", "delete"]),
        ("control+option+f5", ["ctrl", "option", "f5"]),
        ("return", ["return"]),
        (" Cmd + , ", ["command", ","]),
    ],
)
def test_parse_keys_reads_modifiers_and_a_key(combo, expected):
    assert app_actions.parse_keys(combo) == expected


def test_parse_keys_reads_an_uppercase_key_as_the_key():
    assert app_actions.parse_keys("cmd+S") == ["command", "s"]


@pytest.mark.parametrize("combo", ["", "cmd+", "cmd+nope", "hyper+s", "s+cmd"])
def test_parse_keys_rejects_an_unknown_or_missing_name(combo):
    with pytest.raises(actions.UsageError):
        app_actions.parse_keys(combo)


@pytest.fixture
def keyboard(monkeypatch):
    fake = mock.create_autospec(KeyBoardController, instance=True)
    monkeypatch.setattr(app_actions, "keyboard", fake)
    return fake


def in_front_for(checks):
    """Return a bring_to_front that answers `checks`, one per focus check."""
    answers = iter(checks)
    return lambda app: lambda: next(answers)


def test_keys_posts_the_shortcut_once_the_app_is_in_front(keyboard, monkeypatch):
    monkeypatch.setattr(app_actions, "bring_to_front", in_front_for([True]))

    app_actions.keys("TextEdit", "cmd+shift+s")

    keyboard.hotkey.assert_called_once_with("command", "shift", "s")


def test_keys_parses_before_taking_focus(keyboard, monkeypatch):
    bring = mock.Mock()
    monkeypatch.setattr(app_actions, "bring_to_front", bring)

    with pytest.raises(actions.UsageError):
        app_actions.keys("TextEdit", "cmd+nope")

    bring.assert_not_called()


def test_keys_refuses_when_the_app_leaves_the_front(keyboard, monkeypatch):
    monkeypatch.setattr(app_actions, "bring_to_front", in_front_for([False]))

    with pytest.raises(actions.FocusError):
        app_actions.keys("TextEdit", "cmd+s")

    keyboard.hotkey.assert_not_called()


def test_type_text_checks_focus_before_every_character(keyboard, monkeypatch):
    monkeypatch.setattr(app_actions, "bring_to_front", in_front_for([True, True, True]))

    app_actions.type_text("TextEdit", "a\nb")

    assert [c.args for c in keyboard.write.call_args_list] == [("a",), ("\n",), ("b",)]


def test_type_text_stops_when_the_app_leaves_the_front(keyboard, monkeypatch):
    monkeypatch.setattr(app_actions, "bring_to_front", in_front_for([True, True, False]))

    with pytest.raises(actions.FocusError, match="Stopped after 2 of 4 characters"):
        app_actions.type_text("TextEdit", "abcd")

    assert keyboard.write.call_count == 2


def test_type_text_needs_text(keyboard):
    with pytest.raises(actions.UsageError):
        app_actions.type_text("TextEdit", "")


@pytest.fixture
def textedit_window(monkeypatch, text_image):
    """Serve a 200x100 pt TextEdit window, captured at 2x."""
    window = FakeAX(AXPosition=(10, 20), AXSize=(200, 100))
    queries = []
    monkeypatch.setattr(
        app_actions, "standard_window", lambda app, query=None: queries.append(query) or window
    )
    monkeypatch.setattr(app_actions, "window_number", lambda pid, frame: 7)
    monkeypatch.setattr(
        app_actions.monitor, "capture_window", lambda number: text_image([], 200, 100)
    )
    return queries


def test_screenshot_writes_the_window_at_its_scale(textedit_window, tmp_path):
    out = tmp_path / "shot.png"

    assert app_actions.screenshot("TextEdit", out) == out
    assert recorded_scale(out) == 2


def test_screenshot_defaults_to_a_temp_file_named_after_the_app(textedit_window):
    path = app_actions.screenshot("TextEdit")

    try:
        assert path.name.startswith("macuitest-text_edit-")
        assert path.suffix == ".png"
        assert path.stat().st_size > 0
    finally:
        path.unlink()


def test_screenshot_passes_the_window_query(textedit_window, tmp_path):
    query = AXQuery.of(title="Fonts")

    app_actions.screenshot("TextEdit", tmp_path / "shot.png", window=query)

    assert textedit_window == [query]


def test_screenshot_needs_a_window(monkeypatch, tmp_path):
    monkeypatch.setattr(app_actions, "standard_window", lambda app, query=None: None)

    with pytest.raises(actions.NoWindowError, match="TextEdit has no matching window"):
        app_actions.screenshot("TextEdit", tmp_path / "shot.png")


def test_screenshot_needs_screen_recording(textedit_window, monkeypatch, tmp_path):
    def denied(number):
        raise PermissionError("Grant Screen Recording")

    monkeypatch.setattr(app_actions.monitor, "capture_window", denied)

    with pytest.raises(PermissionError):
        app_actions.screenshot("TextEdit", tmp_path / "shot.png")
