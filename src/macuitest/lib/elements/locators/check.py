"""Find declared images missing on disk, PNGs no element declares, and elements not on screen."""

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Optional

from macuitest.lib import app_actions
from macuitest.lib.elements.locators.factories import AppleScriptLocator
from macuitest.lib.elements.locators.factories import AXLocator
from macuitest.lib.elements.locators.factories import ImageLocator
from macuitest.lib.elements.locators.screen import Locator
from macuitest.lib.elements.locators.screen import Screen
from macuitest.lib.elements.locators.screen import image_folder
from macuitest.lib.elements.locators.screen import images_root


@dataclass(frozen=True)
class Report:
    """Images a module declares but lacks, and PNGs in its image folders nothing declares."""

    missing: list[Path]
    undeclared: list[Path]

    @property
    def clean(self) -> bool:
        return not self.missing and not self.undeclared


def load_module(path: Path) -> ModuleType:
    """Import the Python file at `path`.

    Raises:
        ImportError: `path` isn't a Python file.
    """
    name = f"macuitest_checked_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"{path} isn't a Python module")
    module = importlib.util.module_from_spec(spec)
    # Screens find their image folder through sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class LiveReport:
    """What a module's elements look like in the running apps.

    Elements are named `Screen.element`. `skipped` holds the ones a live check can't resolve:
    text and image elements, which match pixels, and elements of a screen with no app.
    """

    found: list[str]
    missing: list[str]
    skipped: list[str]
    not_running: list[str]

    @property
    def clean(self) -> bool:
        return not self.missing and not self.not_running


def check(module: ModuleType) -> Report:
    """Compare `module`'s screens with the PNGs in its image folders.

    A PNG counts as declared when its screen has an attribute of that name, of any kind, or an
    `image()` naming that file. A `@<variant>` suffix is ignored.
    """
    module_file = Path(module.__file__ or "")
    missing: list[Path] = []
    declared_in: dict[Path, set[str]] = {}
    for screen in _screens(module):
        locators = {
            name: value for name, value in vars(screen).items() if isinstance(value, Locator)
        }
        images = [value for value in locators.values() if isinstance(value, ImageLocator)]
        missing += [image.path for image in images if not image.path.exists()]
        declared = set(locators) | {image.file_name for image in images}
        declared_in[image_folder(module_file, screen.__name__)] = declared
    undeclared = [
        png
        for png in sorted(images_root(module_file).glob("*/*.png"))
        if png.stem.split("@")[0] not in declared_in.get(png.parent, set())
    ]
    return Report(missing=sorted(missing), undeclared=undeclared)


def check_live(module: ModuleType) -> LiveReport:
    """Resolve the `ax()` and `applescript()` elements of `module`'s screens in the running apps.

    Reads only: nothing is pressed and no app comes forward. An app that isn't running lands in
    `not_running` once, and its elements are neither found nor missing.

    Raises:
        AppleScriptError: System Events failed for a reason other than a missing element.
    """
    found: list[str] = []
    missing: list[str] = []
    skipped: list[str] = []
    not_running: list[str] = []
    for screen in _screens(module):
        for name, locator in vars(screen).items():
            if not isinstance(locator, Locator):
                continue
            label = f"{screen.__name__}.{name}"
            app = _app_of(locator, screen)
            if app is None:
                skipped.append(label)
            elif not app_actions.running(app):
                if app not in not_running:
                    not_running.append(app)
            elif _resolves(locator):
                found.append(label)
            else:
                missing.append(label)
    return LiveReport(found, missing, skipped, not_running)


def _app_of(locator: Locator, screen: type[Screen]) -> Optional[str]:
    """Return the app `locator` is read from, or None when a live check can't read it."""
    if isinstance(locator, AXLocator):
        return screen.app
    if isinstance(locator, AppleScriptLocator):
        return locator.process or screen.app
    return None


def _resolves(locator: Locator) -> bool:
    if isinstance(locator, AXLocator):
        return locator.find() is not None
    return bool(locator.resolve().exists)


def _screens(module: ModuleType) -> list[type[Screen]]:
    return [
        value
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, Screen)
        and value.__module__ == module.__name__
    ]
