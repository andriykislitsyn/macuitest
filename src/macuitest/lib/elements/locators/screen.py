"""`Screen` classes and the descriptors their elements are declared with."""

import re
import sys
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import ClassVar
from typing import Generic
from typing import Optional
from typing import TypeVar

T = TypeVar("T")


class Screen:
    """Elements of one app screen, declared as class attributes. Never instantiated.

    Pass `app`, the app's name as the Dock shows it, to scope text and image lookups to its
    first standard window, give AppleScript elements their process, and enable `ax()`.
    """

    app: ClassVar[Optional[str]] = None

    def __init_subclass__(cls, app: Optional[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if app is not None:
            cls.app = app

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a Screen. Read its elements from the class.")


def snake_case(name: str) -> str:
    """Return `name` in snake_case, keeping only ASCII letters and digits."""
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    words = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", words)
    return re.sub(r"[^0-9A-Za-z]+", "_", words).strip("_").lower()


def image_folder(module_file: Path, screen_name: str) -> Path:
    """Return the folder holding the images of screen `screen_name` declared in `module_file`."""
    return module_file.parent / module_file.stem / snake_case(screen_name)


class Locator(ABC, Generic[T]):
    """A `Screen` attribute that reads as an element."""

    screen: type[Screen]
    name: str

    def __set_name__(self, owner: type, name: str) -> None:
        if not issubclass(owner, Screen):
            raise TypeError(f"Declare {name} on a Screen subclass, not on {owner.__name__}")
        self.screen, self.name = owner, name

    def __get__(self, instance: object, owner: Optional[type] = None) -> T:
        return self.resolve()

    @property
    def qualified_name(self) -> str:
        return f"{self.screen.__name__}.{self.name}"

    def module_file(self) -> Path:
        """Return the file of the module that declares this element's screen.

        Raises:
            TypeError: The screen isn't declared in a module file.
        """
        file = getattr(sys.modules.get(self.screen.__module__), "__file__", None)
        if file is None:
            raise TypeError(f"{self.qualified_name}: declare screens with images in a module file")
        return Path(file)

    @abstractmethod
    def resolve(self) -> T:
        """Return the element."""


class CachedLocator(Locator[T]):
    """A locator that builds its element on first read and returns that one afterwards."""

    _element: Optional[T] = None

    def resolve(self) -> T:
        if self._element is None:
            self._element = self.build()
        return self._element

    @abstractmethod
    def build(self) -> T:
        """Create the element."""
