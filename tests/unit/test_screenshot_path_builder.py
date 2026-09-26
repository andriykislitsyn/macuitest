from pathlib import Path

from macuitest.lib.elements.ui.screenshot_path_builder import ScreenshotPathBuilder


def test_root_defaults_to_env_var_read_at_construction(monkeypatch, tmp_path):
    monkeypatch.setenv("MACUITEST_SCR", str(tmp_path))

    assert ScreenshotPathBuilder("Main Window").ok_button == str(
        tmp_path / "main_window/ok_button.png"
    )


def test_root_falls_back_to_home(monkeypatch):
    monkeypatch.delenv("MACUITEST_SCR", raising=False)

    assert ScreenshotPathBuilder("dialogs").root == Path.home()


def test_explicit_root_wins_over_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("MACUITEST_SCR", "/ignored")

    assert ScreenshotPathBuilder("dialogs", root=tmp_path).root == tmp_path
