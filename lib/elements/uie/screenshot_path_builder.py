from pathlib import Path

from lib.operating_system.env import env


class ScreenshotPathBuilder:
    """Screenshot path builder."""

    def __init__(self, category, root=None):
        self._screenshots_dir = root or Path(__file__).parents[2].joinpath('media')
        self.category = category.lower().replace(' & ', '_and_').replace(' ', '_').replace('-', '_')

    def __getattr__(self, item):
        return object.__getattribute__(self, item) if item == 'category' else self.path(self.category, item)

    def path(self, section: str, scr_name: str) -> str:
        """Build absolute path to a screenshot."""
        _base = f'{self._screenshots_dir}/{section}/{scr_name}.png'
        _macos_specific = f'{self._screenshots_dir}/{section}/{scr_name}_{env.version[1]}.png'
        if Path(_macos_specific).exists():
            return _macos_specific
        return _base
