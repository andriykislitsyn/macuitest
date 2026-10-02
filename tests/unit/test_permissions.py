import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.ui.monitor import Monitor
from macuitest.lib.operating_system import permissions


@pytest.fixture
def ungranted(monkeypatch):
    monkeypatch.setattr(permissions, "_granted", set())


def test_denied_screen_recording_raises_naming_the_pane(ungranted, monkeypatch):
    monkeypatch.setattr(permissions.Quartz, "CGPreflightScreenCaptureAccess", lambda: False)

    with pytest.raises(PermissionError) as denied:
        permissions.require_screen_recording()

    message = str(denied.value)
    assert "Privacy & Security > Screen & System Audio Recording" in message
    assert "Screen Recording before macOS 15" in message
    assert "restart that app" in message


def test_denied_accessibility_raises_naming_the_pane(ungranted, monkeypatch):
    monkeypatch.setattr(permissions.ApplicationServices, "AXIsProcessTrusted", lambda: False)

    with pytest.raises(PermissionError) as denied:
        permissions.require_accessibility()

    assert "Privacy & Security > Accessibility" in str(denied.value)
    assert "restart" not in str(denied.value)


def test_a_granted_permission_is_checked_once(ungranted, monkeypatch):
    checks = []
    monkeypatch.setattr(
        permissions.ApplicationServices, "AXIsProcessTrusted", lambda: checks.append(1) or True
    )

    permissions.require_accessibility()
    permissions.require_accessibility()

    assert checks == [1]


def test_a_denied_permission_is_checked_again(ungranted, monkeypatch):
    answers = iter([False, True])
    monkeypatch.setattr(permissions.Quartz, "CGPreflightScreenCaptureAccess", lambda: next(answers))

    with pytest.raises(PermissionError):
        permissions.require_screen_recording()
    permissions.require_screen_recording()


def test_capture_checks_screen_recording_before_capturing(ungranted, monkeypatch):
    monkeypatch.setattr(permissions.Quartz, "CGPreflightScreenCaptureAccess", lambda: False)

    with pytest.raises(PermissionError):
        Monitor.capture(Region(0, 0, 10, 10))
