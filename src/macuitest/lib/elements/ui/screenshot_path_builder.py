import os
from pathlib import Path
from typing import Union

from macuitest.lib.operating_system.env import env


class ScreenshotPathBuilder:
    """Screenshot path builder."""

    def __init__(
        self,
        category: str,
        root: Union[Path, str] = os.environ.get("MACUITEST_SCR", os.environ.get("HOME")),
    ):
        self.root = Path(root)
        self.category = category.lower().replace(" ", "_").replace("-", "_")

    def __getattr__(self, item: str):
        return getattr(self, item) if item == "category" else self.build_path(self.category, item)

    def build_path(self, section: str, scr_name: str) -> str:
        """Build absolute path to a screenshot."""
        base = self.root.joinpath(section).joinpath(f"{scr_name}.png")
        os_ver = env.version[1] if env.version < (11, 0) else env.version[0]
        os_specific = self.root.joinpath(section).joinpath(f"{scr_name}_{os_ver}.png")
        return (os_specific if os_specific.exists() else base).as_posix()
