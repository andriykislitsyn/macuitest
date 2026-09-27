import os
import subprocess
import sys
from pathlib import Path

import pytest

from macuitest.config import __main__ as config_cli
from macuitest.config import settings as settings_module
from macuitest.config.constants import Region
from macuitest.config.settings import ConfigError
from macuitest.config.settings import Settings
from macuitest.lib.elements.ui.monitor import monitor


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MACUITEST_CONFIG", raising=False)
    return tmp_path


def write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def test_defaults():
    s = Settings()

    assert (s.mouse.move, s.mouse.hold, s.mouse.pause) == (0.18, 0.24, 0.24)
    assert s.mouse.default_position == (5, 3)
    assert s.keyboard.pause == 0.001
    assert (s.screen.display, s.screen.search_region) == (None, None)
    assert (s.elements.similarity, s.elements.timeout, s.elements.vanish_timeout) == (0.925, 5, 15)
    assert s.ocr.languages == ("en-US",)
    assert s.paths.screenshots is None


def test_the_shipped_default_file_loads_to_the_code_defaults():
    s = Settings()
    s.load(settings_module.DEFAULT_FILE)

    assert s == Settings(source=settings_module.DEFAULT_FILE)


def test_load_without_a_file_keeps_defaults(workdir):
    s = Settings()
    s.load()

    assert s == Settings()


def test_load_reads_macuitest_toml_in_the_working_directory(workdir):
    write(workdir / "macuitest.toml", "[mouse]\nmove = 0.5\n")

    s = Settings()
    s.load()

    assert (s.mouse.move, s.source) == (0.5, workdir / "macuitest.toml")


def test_env_var_wins_over_the_local_file(workdir, monkeypatch):
    write(workdir / "macuitest.toml", "[mouse]\nmove = 0.5\n")
    other = write(workdir / "other.toml", "[mouse]\nmove = 0.7\n")
    monkeypatch.setenv("MACUITEST_CONFIG", str(other))

    s = Settings()
    s.load()

    assert s.mouse.move == 0.7


def test_env_var_pointing_to_a_missing_file_raises(workdir, monkeypatch):
    monkeypatch.setenv("MACUITEST_CONFIG", str(workdir / "missing.toml"))

    with pytest.raises(ConfigError, match="missing.toml"):
        Settings().load()


def test_pyproject_tool_table_is_read_without_a_local_file(workdir):
    write(workdir / "pyproject.toml", "[tool.macuitest.mouse]\nmove = 0.4\n")

    s = Settings()
    s.load()

    assert (s.mouse.move, s.source) == (0.4, workdir / "pyproject.toml")


def test_pyproject_without_a_tool_table_is_ignored(workdir):
    write(workdir / "pyproject.toml", "[project]\nname = 'x'\n")

    s = Settings()
    s.load()

    assert s == Settings()


def test_local_file_wins_over_pyproject(workdir):
    write(workdir / "pyproject.toml", "[tool.macuitest.mouse]\nmove = 0.4\n")
    write(workdir / "macuitest.toml", "[mouse]\nmove = 0.5\n")

    s = Settings()
    s.load()

    assert s.mouse.move == 0.5


def test_every_key_is_read(tmp_path):
    path = write(
        tmp_path / "all.toml",
        """
[mouse]
move = 0.1
hold = 0.2
pause = 0.3
default_position = [10, 20]
[keyboard]
pause = 0.05
[elements]
similarity = 0.8
timeout = 3
vanish_timeout = 4.5
[ocr]
languages = ["en-US", "uk-UA"]
[paths]
screenshots = "shots"
""",
    )

    s = Settings()
    s.load(path)

    assert (s.mouse.move, s.mouse.hold, s.mouse.pause) == (0.1, 0.2, 0.3)
    assert s.mouse.default_position == (10, 20)
    assert s.keyboard.pause == 0.05
    assert (s.elements.similarity, s.elements.timeout, s.elements.vanish_timeout) == (0.8, 3, 4.5)
    assert s.ocr.languages == ("en-US", "uk-UA")
    assert s.paths.screenshots == tmp_path / "shots"  # Relative to the config file.


def test_default_position_accepts_points_on_a_display_left_of_the_main_one(tmp_path):
    s = Settings()
    s.load(write(tmp_path / "c.toml", "[mouse]\ndefault_position = [-3000, 10]\n"))

    assert s.mouse.default_position == (-3000, 10)


def test_screenshots_path_expands_the_home_directory(tmp_path):
    s = Settings()
    s.load(write(tmp_path / "c.toml", '[paths]\nscreenshots = "~/shots"\n'))

    assert s.paths.screenshots == Path.home() / "shots"


def test_display_is_checked_against_the_connected_displays(tmp_path, monkeypatch):
    monkeypatch.setattr(type(monitor), "displays", [Region(0, 0, 10, 10), Region(10, 0, 20, 10)])
    s = Settings()

    s.load(write(tmp_path / "ok.toml", "[screen]\ndisplay = 1\n"))
    assert s.screen.display == 1

    with pytest.raises(ConfigError, match="screen.display"):
        s.load(write(tmp_path / "bad.toml", "[screen]\ndisplay = 2\n"))


@pytest.mark.parametrize(
    "text, key",
    [
        ("[mouse]\nmove = 'fast'\n", "mouse.move"),
        ("[mouse]\nmove = true\n", "mouse.move"),
        ("[mouse]\nmove = -1\n", "mouse.move"),
        ("[mouse]\ndefault_position = [1]\n", "mouse.default_position"),
        ("[elements]\nsimilarity = 1.5\n", "elements.similarity"),
        ("[ocr]\nlanguages = 'en-US'\n", "ocr.languages"),
        ("[ocr]\nlanguages = []\n", "ocr.languages"),
        ("[paths]\nscreenshots = 3\n", "paths.screenshots"),
        ("[mouse]\nspeed = 1\n", "mouse.speed"),
        ("[mice]\nmove = 1\n", "mice"),
        ("mouse = 1\n", "mouse"),
        ("[screen]\nsearch_region = [0, 0, 1, 1]\n", "screen.search_region"),
    ],
)
def test_invalid_values_raise_naming_the_file_and_key(tmp_path, text, key):
    path = write(tmp_path / "bad.toml", text)

    with pytest.raises(ConfigError, match=rf"bad\.toml.*{key}"):
        Settings().load(path)


def test_malformed_toml_raises_naming_the_file(tmp_path):
    with pytest.raises(ConfigError, match="bad.toml"):
        Settings().load(write(tmp_path / "bad.toml", "[mouse\n"))


def test_load_resets_code_overrides_and_keeps_section_objects(tmp_path):
    s = Settings()
    mouse = s.mouse
    s.mouse.hold = 9
    s.screen.search_region = Region(0, 0, 1, 1)

    s.load(write(tmp_path / "c.toml", "[mouse]\nmove = 0.5\n"))

    assert s.mouse is mouse
    assert (s.mouse.move, s.mouse.hold, s.screen.search_region) == (0.5, 0.24, None)


def test_init_copies_the_default_file(tmp_path, capsys):
    target = tmp_path / "macuitest.toml"

    assert config_cli.main(["init", str(target)]) == 0
    assert target.read_text() == settings_module.DEFAULT_FILE.read_text()


def test_init_refuses_to_overwrite(tmp_path, capsys):
    target = write(tmp_path / "macuitest.toml", "mine")

    assert config_cli.main(["init", str(target)]) == 1
    assert target.read_text() == "mine"
    assert "already exists" in capsys.readouterr().err


def test_relative_screenshots_stay_with_the_config_file_after_chdir(workdir, monkeypatch):
    write(workdir / "macuitest.toml", '[paths]\nscreenshots = "shots"\n')
    s = Settings()
    s.load()

    monkeypatch.chdir("/")

    assert s.paths.screenshots is not None
    assert s.paths.screenshots.resolve() == (workdir / "shots").resolve()


def test_a_non_table_tool_section_in_pyproject_raises(workdir):
    write(workdir / "pyproject.toml", "[tool]\nmacuitest = 1\n")

    with pytest.raises(ConfigError, match="pyproject.toml"):
        Settings().load()


def test_a_config_path_that_is_a_directory_raises(tmp_path):
    with pytest.raises(ConfigError, match=str(tmp_path)):
        Settings().load(tmp_path)


def test_init_works_when_the_current_config_cannot_load(tmp_path):
    target = tmp_path / "new.toml"
    env = {**os.environ, "MACUITEST_CONFIG": str(target)}

    result = subprocess.run(
        [sys.executable, "-m", "macuitest.config", "init", str(target)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert target.read_text() == settings_module.DEFAULT_FILE.read_text()
