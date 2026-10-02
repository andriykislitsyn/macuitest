![CI](https://github.com/andriykislitsyn/macuitest/actions/workflows/ci.yml/badge.svg)

# macuitest

Functional and UI test automation for macOS apps. macuitest finds elements by AppleScript locator, accessibility object, screenshot, or visible text, then clicks, types, and waits on them like a person would.

## Requirements

- macOS, Python 3.13 or later.
- Grant these permissions in System Settings > Privacy & Security to the app that runs your tests, such as Terminal, iTerm2, or your IDE:
  - **Accessibility**, for mouse and keyboard input, AppleScript element control, and every lookup on a `Screen` with an `app`. Without it, those lookups raise `PermissionError`.
  - **Screen & System Audio Recording** (Screen Recording before macOS 15), for `UIElement`, `VisibleText`, and color checks. Without it, the first screen capture raises `PermissionError` naming the System Settings pane.
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
| `locators` | `Screen` classes declaring an app's elements with the kinds above | Any app you test more than once |

`VisibleText` and `UIElement` share one API: `click_mouse`, `double_click`, `right_click`, `hover_mouse`, `paste`, `wait_displayed`, `wait_vanish`, and the `is_visible` property. Every method takes a `region` to search, and a window-sized region is several times faster than the whole desktop.

To find AppleScript locators, use Accessibility Inspector (bundled with Xcode) or UI Browser.

## Screens

Declare an app's elements in one class instead of scattering locators through tests.

```python
from macuitest.lib.elements.locators import Screen, applescript, ax, image, text
from macuitest.lib.elements.native_element import Button


class Calculator(Screen, app="Calculator"):
    keypad = ax(identifier="CalculatorKeypadView")
    seven = ax(identifier="Seven", kind=Button)
    display = ax(identifier="StandardInputView").child(role="AXStaticText")
    all_clear = text("AC", within=keypad)
    mode = image()
    seven_as = applescript('(first button whose description is "7") of group 1 of window 1')


Calculator.seven.press()
```

- `ax()` matches accessibility attributes and finds the element again on every read. Pass `kind=` for actions such as `press`.
- `text()` and `image()` search the app's first standard window, or the frame of `within=`. When the window is missing or minimized, they find nothing and waits keep polling.
- `image()` loads `<name>.png` next to the module: `Calculator` in `apps/calculator.py` reads `apps/calculator/calculator/mode.png`.
- For an alert or a secondary window, name the window once: `class EmptyTrash(Screen, app="Finder", window=window(subrole="AXDialog"))`. Its text, image, and `ax()` lookups then search only that window. Alerts have no title, so match them by subrole. Sheets, such as a Save panel, sit inside their window and need no `window=`.
- `app` is the process that owns the window. System prompts belong to system processes, such as `SecurityAgent` for password prompts, not to the app that triggered them.
- Screens are never instantiated. Read elements from the class.

### Capture elements

```bash
python -m macuitest.locators capture Calculator --out apps/calculator.py --role AXButton
python -m macuitest.locators check apps/calculator.py
```

`capture` walks the app's first standard window and writes `apps/calculator.py` with an `ax()` entry per element it can identify, else `image()`, plus a PNG per element in `apps/calculator/calculator/`, cropped with a 4 pt margin (`--margin`). It works while other windows cover the app. Pass `--window-subrole AXDialog` or `--window-title` to capture an alert or a secondary window instead. Switch an entry to `image()` where the accessibility attributes don't identify the element, and delete the ones you don't need. Identifiers that encode state, such as Calculator's `Mode: basic; unitConversion: false`, need editing. `capture` refuses to overwrite files without `--force`.

`check` lists declared images missing on disk and PNGs no element declares, and exits 1 when it finds either.

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
