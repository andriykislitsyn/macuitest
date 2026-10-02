![CI](https://github.com/andriykislitsyn/macuitest/actions/workflows/ci.yml/badge.svg)

# macuitest

Functional and UI test automation for macOS apps. macuitest finds elements by AppleScript locator, accessibility object, screenshot, or visible text, then clicks, types, and waits on them like a person would.

## Requirements

- macOS, Python 3.13 or later.
- Grant these permissions in System Settings > Privacy & Security to the app that runs your tests, such as Terminal, iTerm2, or your IDE:
  - **Accessibility**, for mouse and keyboard input and AppleScript element control.
  - **Screen Recording**, for `UIElement`, `VisibleText`, and color checks. Without it, screen captures show only the wallpaper, so every lookup times out.
- macOS asks once for permission to control System Events. Allow it.

## Installation

```bash
uv add macuitest
# or
pip install macuitest
```

## Quick start

```python
from macuitest.lib.apps.application import Finder
from macuitest.lib.elements.applescript_element import MenuBarItem
from macuitest.lib.elements.ui_element import UIElement
from macuitest.lib.elements.visible_text import VisibleText

finder = Finder()
finder.activate()

# An AppleScript locator, resolved through System Events.
MenuBarItem('menu bar item "File" of menu bar 1', process="Finder").click_mouse()

# Visible text, found with Apple Vision. No screenshot to maintain.
VisibleText("New Finder Window").click_mouse()

# A screenshot of the element, found with template matching.
UIElement("screenshots/sidebar_toggle.png").wait_displayed()
```

## Element types

| Module in `macuitest.lib.elements` | Finds elements by | Best for |
|---|---|---|
| `applescript_element` | AppleScript locator, such as `button "OK" of window 1` | Native controls with stable accessibility names |
| `native_element` | Accessibility (AX) objects through pyobjc | Reading attributes and walking the accessibility tree |
| `visible_text` | Visible text, read with Apple Vision | Buttons, tabs, links, and banners with a text label |
| `ui_element` | A screenshot of the element | Icons and custom-drawn controls without text |

`VisibleText` and `UIElement` share one API: `click_mouse`, `double_click`, `right_click`, `hover_mouse`, `paste`, `wait_displayed`, `wait_vanish`, and the `is_visible` property. Every method takes a `region` to search, and a window-sized region is several times faster than the whole desktop.

To find AppleScript locators, use Accessibility Inspector (bundled with Xcode) or UI Browser.

## Configuration

One settings file holds the defaults for mouse and keyboard timings, the search display, element matching and timeouts, OCR languages, and the screenshot root. Create a documented copy in your project:

```bash
python -m macuitest.config init
```

That writes `macuitest.toml` with every key and a comment, and each key that has a default is set to it. Edit the keys you need and delete the rest:

```toml
[mouse]
move = 0.36          # Slower cursor moves, easier to follow in a screen recording.

[screen]
display = 1          # Search only the second display. 0 is the menu bar display.

[ocr]
languages = ["en-US", "uk-UA"]
```

macuitest reads the first of these it finds, the first time you import a macuitest element or controller:

1. The file named by `$MACUITEST_CONFIG`.
2. `macuitest.toml` in the working directory.
3. `pyproject.toml` in the working directory, with each table under `[tool.macuitest]`, such as `[tool.macuitest.mouse]`.

A missing `$MACUITEST_CONFIG` file, an unknown key, or a bad value raises `ConfigError` naming the file and the key. A `display` index is checked against the displays connected at that moment. Code can change any setting at run time:

```python
from macuitest.config.settings import settings
from macuitest.lib.elements.ui.monitor import monitor

settings.mouse.move = 0.1
settings.screen.search_region = monitor.displays[1]  # A Region, which code can set and files can't.
```

Other environment variables:

- `$MACUITEST_SCR` sets the screenshot root for `ScreenshotPathBuilder` and wins over `paths.screenshots`.
- `$MACUITEST_PASSWORD` gives `ShellExecutor.sudo` the admin password when the `com.macuitest.automation` keychain item is missing. Keep it out of config files.

## Development

```bash
uv sync
uv run pytest tests/unit
uv run ruff check && uv run ruff format --check
uv run ty check
```

Unit tests never read the real screen. Tests that need text on screen draw it into an image with the `text_image` fixture.

See [CHANGELOG.md](CHANGELOG.md) for release notes.
