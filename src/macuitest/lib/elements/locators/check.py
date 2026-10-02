"""Find declared images missing on disk and PNGs no element declares."""

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from macuitest.lib.elements.locators.factories import ImageLocator
from macuitest.lib.elements.locators.screen import Locator
from macuitest.lib.elements.locators.screen import Screen
from macuitest.lib.elements.locators.screen import image_folder


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
        for png in sorted((module_file.parent / module_file.stem).glob("*/*.png"))
        if png.stem.split("@")[0] not in declared_in.get(png.parent, set())
    ]
    return Report(missing=sorted(missing), undeclared=undeclared)


def _screens(module: ModuleType) -> list[type[Screen]]:
    return [
        value
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, Screen)
        and value.__module__ == module.__name__
    ]
