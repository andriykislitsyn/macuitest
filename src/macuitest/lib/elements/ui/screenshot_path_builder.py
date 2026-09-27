import os
from pathlib import Path
from typing import Union

from macuitest.config.settings import settings
from macuitest.lib.operating_system.env import env


class ScreenshotPathBuilder:
    """Build screenshot paths under `root/category`.

    Args:
        category: Screenshot subdirectory, lowercased with spaces and hyphens replaced by
            underscores.
        root: Screenshot root. Defaults to `$MACUITEST_SCR`, then `settings.paths.screenshots`,
            then the home directory.
    """

    def __init__(self, category: str, root: Union[Path, str, None] = None):
        self.root = Path(
            root or os.environ.get("MACUITEST_SCR") or settings.paths.screenshots or Path.home()
        )
        self.category = category.lower().replace(" ", "_").replace("-", "_")

    def __getattr__(self, item: str):
        return getattr(self, item) if item == "category" else self.build_path(self.category, item)

    def build_path(self, section: str, scr_name: str) -> str:
        """Build absolute path to a screenshot."""
        base = self.root.joinpath(section).joinpath(f"{scr_name}.png")
        os_ver = env.version[1] if env.version < (11, 0) else env.version[0]
        os_specific = self.root.joinpath(section).joinpath(f"{scr_name}_{os_ver}.png")
        return (os_specific if os_specific.exists() else base).as_posix()
