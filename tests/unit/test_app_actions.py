from unittest import mock

import pytest

from macuitest.lib import actions
from macuitest.lib import app_actions


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
