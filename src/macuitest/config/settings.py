"""macuitest settings, loaded from a TOML file and changeable from code.

The file is the first of `$MACUITEST_CONFIG`, `./macuitest.toml`, and the `[tool.macuitest]`
table of `./pyproject.toml`. `default.toml` next to this module documents every key. Assigning
a setting, such as `settings.mouse.move = 0.36`, overrides the file until the next `load`.
"""

import dataclasses
import os
import tomllib
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union

from macuitest.config.constants import Region

DEFAULT_FILE = Path(__file__).with_name("default.toml")


class ConfigError(ValueError):
    """Raised when a config file can't be found, parsed, or validated."""


@dataclass
class MouseSettings:
    move: float = 0.18
    hold: float = 0.24
    pause: float = 0.24
    default_position: tuple[float, float] = (5, 3)


@dataclass
class KeyboardSettings:
    pause: float = 0.001


@dataclass
class ScreenSettings:
    display: Optional[int] = None
    search_region: Optional[Region] = None  # Code only. Wins over `display`.


@dataclass
class ElementSettings:
    similarity: float = 0.925
    timeout: float = 5
    vanish_timeout: float = 15


@dataclass
class OCRSettings:
    languages: tuple[str, ...] = ("en-US",)


@dataclass
class PathSettings:
    screenshots: Optional[Path] = None


@dataclass
class Settings:
    """Every setting, one attribute per TOML section, and the file they came from."""

    mouse: MouseSettings = field(default_factory=MouseSettings)
    keyboard: KeyboardSettings = field(default_factory=KeyboardSettings)
    screen: ScreenSettings = field(default_factory=ScreenSettings)
    elements: ElementSettings = field(default_factory=ElementSettings)
    ocr: OCRSettings = field(default_factory=OCRSettings)
    paths: PathSettings = field(default_factory=PathSettings)
    source: Optional[Path] = None

    def load(self, path: Union[Path, str, None] = None) -> None:
        """Reset every setting to its default, then apply `path` or the first config file found.

        Section objects are updated in place, so references to them stay valid.

        Raises:
            ConfigError: The file is missing, malformed, or has an unknown key or a bad value.
        """
        source, table = _read(Path(path)) if path is not None else _find()
        values = _validate(table, source) if source is not None else {}
        for name in _SCHEMA:
            section = getattr(self, name)
            for key in dataclasses.fields(section):
                setattr(section, key.name, values.get((name, key.name), key.default))
        self.source = source


def _find() -> tuple[Optional[Path], dict]:
    if configured := os.environ.get("MACUITEST_CONFIG"):
        return _read(Path(configured).expanduser())
    if (local := Path("macuitest.toml")).is_file():
        return _read(local)
    if (pyproject := Path("pyproject.toml")).is_file():
        tool = _read(pyproject)[1].get("tool", {}).get("macuitest")
        if tool is not None:
            return pyproject, tool
    return None, {}


def _read(path: Path) -> tuple[Path, dict]:
    try:
        with path.open("rb") as file:
            return path, tomllib.load(file)
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e


def _validate(table: dict, source: Path) -> dict[tuple[str, str], Any]:
    values = {}
    for name, keys in table.items():
        if name not in _SCHEMA:
            raise ConfigError(f"{source}: unknown section {name}")
        if not isinstance(keys, dict):
            raise ConfigError(f"{source}: {name} must be a table")
        for key, value in keys.items():
            convert = _SCHEMA[name].get(key)
            if convert is None:
                raise ConfigError(f"{source}: unknown key {name}.{key}")
            try:
                values[name, key] = convert(value, source)
            except ValueError as e:
                raise ConfigError(f"{source}: {name}.{key} {e}") from None
    return values


def _seconds(value, source) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"must be a number of seconds, got {value!r}")
    return value


def _point(value, source) -> tuple[float, float]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value)
    ):
        raise ValueError(f"must be [x, y] in points, got {value!r}")
    return value[0], value[1]


def _similarity(value, source) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"must be a number from 0 to 1, got {value!r}")
    return value


def _display(value, source) -> int:
    # Imported here so settings without a display key never load Quartz.
    from macuitest.lib.elements.ui.monitor import monitor

    count = len(monitor.displays)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < count:
        raise ValueError(f"must be a display index from 0 to {count - 1}, got {value!r}")
    return value


def _languages(value, source) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
        raise ValueError(f"must be a list of language codes, got {value!r}")
    return tuple(value)


def _path(value, source) -> Path:
    if not isinstance(value, str):
        raise ValueError(f"must be a path, got {value!r}")
    return source.parent / Path(value).expanduser()


_SCHEMA: dict[str, dict[str, Callable[[Any, Path], Any]]] = {
    "mouse": {"move": _seconds, "hold": _seconds, "pause": _seconds, "default_position": _point},
    "keyboard": {"pause": _seconds},
    "screen": {"display": _display},
    "elements": {"similarity": _similarity, "timeout": _seconds, "vanish_timeout": _seconds},
    "ocr": {"languages": _languages},
    "paths": {"screenshots": _path},
}

settings = Settings()
settings.load()
