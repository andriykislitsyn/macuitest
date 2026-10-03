![CI](https://github.com/andriykislitsyn/macuitest/actions/workflows/ci.yml/badge.svg)

# macuitest

macuitest is a Python library for end-to-end tests of macOS apps. It finds elements by accessibility attributes, AppleScript locator, screenshot, or visible text, then clicks, types, and waits on them the way a person would. It also includes helpers for the system around the app, such as preferences, property lists, processes, and files, so a test can set up state and check results outside the app's window.

To see complete suites for real apps, go to [macuitest examples](https://github.com/andriykislitsyn/macuitest-examples).

## Before you begin

To use macuitest, you need the following:

- macOS and Python 3.13 or later.
- Two permissions for the app you run your tests from, such as Terminal, iTerm2, or your IDE. Grant them in **System Settings > Privacy & Security**:
  - **Accessibility**, for mouse and keyboard input, AppleScript elements, and every lookup on a `Screen` with an `app`.
  - **Screen & System Audio Recording**, called **Screen Recording** before macOS 15, for screenshots, visible text, and color checks.

After you grant Screen Recording, quit and reopen the app you run your tests from, since macOS applies that grant only to a newly started app. Accessibility takes effect right away.

When a permission is missing, `Screen` lookups and screen captures raise `PermissionError` naming the System Settings pane. Other calls fail without that hint: an AppleScript element raises `AppleScriptError`, and mouse and keyboard input does nothing.

The first time your tests control System Events, macOS asks for permission. Allow it.

## Install macuitest

To install macuitest from PyPI, run one of these commands:

```bash
uv add macuitest
# or
pip install macuitest
```

## Quick start

The following script drives Finder with three kinds of elements. The screenshot step needs a PNG of your own:

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

Each module in `macuitest.lib.elements` finds elements a different way:

| Module | Finds elements by | Best for |
|---|---|---|
| `applescript_element` | AppleScript locator, such as `button "OK" of window 1` | Apps you already script through System Events |
| `native_element` | Accessibility (AX) objects through pyobjc | Reading attributes and walking the accessibility tree |
| `visible_text` | Visible text, read with Apple Vision | Buttons, tabs, links, and banners with a text label of two or more characters |
| `ui_element` | A screenshot of the element | Icons and custom-drawn controls without text |
| `locators` | `Screen` classes that declare an app's elements with the kinds above | Any app you test more than once |

Every element kind shares one API: `click_mouse`, `double_click_mouse`, `right_click_mouse`, `hover_mouse`, `wait_displayed`, `wait_vanish`, and the `is_visible` property. `is_visible` checks once, so wait with `wait_displayed` or `wait_vanish`. The mouse methods move the real pointer, while `click()` and `press()` on accessibility and AppleScript elements perform the accessibility action without it. `VisibleText` and `UIElement` also have `paste`, and their methods take a `region` to search. A window-sized region is faster to search than the whole desktop.

To browse an app's accessibility attributes, use Accessibility Inspector, which comes with Xcode, or see [Inspect an app](#inspect-an-app). To turn them into locators, see [Capture elements](#capture-elements).

## Declare an app's elements with screens

A `Screen` class declares an app's elements in one place, so your tests don't need to contain locators:

```python
from macuitest.lib.elements.applescript_element import Button as ScriptButton
from macuitest.lib.elements.locators import Screen, applescript, ax, image, text
from macuitest.lib.elements.native_element import Button

KEYPAD = "group 1 of group 1 of splitter group 1 of group 1 of window 1"


class Calculator(Screen, app="Calculator"):
    keypad = ax(identifier="CalculatorKeypadView")
    seven = ax(identifier="Seven", kind=Button)
    display = ax(identifier="StandardInputView").child(role="AXStaticText")
    all_clear = text("AC", within=keypad)
    mode = image()
    seven_as = applescript(
        f'(first button whose value of attribute "AXIdentifier" is "Seven") of {KEYPAD}',
        kind=ScriptButton,
    )


Calculator.seven.press()
```

Screens work as follows:

- `ax()` matches accessibility attributes and searches again every time you use the element, so `is_visible` and `wait_vanish` see a closed sheet or panel. A missing element reads as not visible, and acting on it raises `LookupError`. Pass `kind=` for actions such as `press`.
- `text()` and `image()` search the app's first standard window, or the frame of `within=`. When the window is missing, minimized, or hidden, they find nothing, and waits keep polling.
- `image()` loads `<name>.png` next to the module. For example, `Calculator` in `apps/calculator.py` reads `apps/calculator/calculator/mode.png`.
- Screens are never instantiated. Read elements from the class.

### Alerts, panels, and sheets

For an alert or a secondary window, name the window once with `window=`. The screen's text, image, and `ax()` lookups then search only that window:

```python
from macuitest.lib.elements.locators import Screen, ax, window
from macuitest.lib.elements.native_element import Button


class EmptyTrash(Screen, app="Finder", window=window(subrole="AXDialog")):
    cancel = ax(title="Cancel", role="AXButton", kind=Button)


class Fonts(Screen, app="TextEdit", window=window(title="Fonts")):
    search = ax(description="Search", role="AXButton", kind=Button)
```

Keep these window rules in mind:

- Alerts have no title, so match them by subrole.
- Floating panels, such as TextEdit's Fonts panel, disappear from the accessibility tree while their app isn't active. Activate the app before your tests look up their elements. `capture` activates the app for you.
- Sheets, such as a Save panel, sit inside their window and need no `window=`.
- `app` is the process that owns the window. System prompts belong to system processes, such as `SecurityAgent` for password prompts, not to the app that triggered them.

### Inspect an app

To see what `ax()` can find in a running app, print its accessibility tree:

```bash
python -m macuitest.locators tree TextEdit --window-title Fonts
```

Each line shows an element's role, identifier, description, title, and value, indented under its parent, then the `ax()` locator that finds it, when one does. Narrow the output with `--role`, `--window-title`, or `--window-subrole`. `tree` only reads, and leaves the app in the background. Some apps, such as Calculator, and floating panels show their windows only while the app is active, so pass `--activate` to bring the app to the front first.

### Capture elements

Instead of writing a screen by hand, capture it from the running app:

```bash
python -m macuitest.locators capture Calculator --out apps/calculator.py --role AXButton
python -m macuitest.locators check apps/calculator.py
```

`capture` walks the app's first standard window and writes the following:

- `apps/calculator.py`, with an `ax()` entry for each element it can identify, else an `image()` entry.
- A PNG of each element in `apps/calculator/calculator/`, cropped with a 4 pt margin. Change the margin with `--margin`.

`capture` brings the app to the front first and crops each element from a capture of that one window. To capture an alert, panel, or secondary window, pass `--window-subrole AXDialog` or `--window-title`. The screen class is named after the app, or after the window when you pass one of those options. `capture` doesn't overwrite existing files unless you pass `--force`.

To add another window's screen to a module you already have, pass `--append`. `capture` adds the class and any imports the module lacks, and refuses when the module already defines a class with that name.

Rows of tables, outlines, and lists show data that changes, such as the font list in TextEdit's Fonts panel. `capture` skips the elements inside them that have no `ax()` locator, and notes how many in a comment. Find a row by what it shows instead, such as `text("Helvetica")`. To capture rows anyway, name their role with `--role AXRow`.

`capture` and `tree` skip identifiers that AppKit generates, such as `_NS:34`, because they change between launches.

Then edit the generated module: delete the entries you don't need, and switch an entry to `image()` where its accessibility attributes don't identify it. Identifiers that encode state, such as Calculator's `Mode: basic; unitConversion: false`, need a stable replacement, such as a match on the description.

`check` lists declared images that are missing on disk and PNGs that no element declares. It exits with status 1 when it finds either.

## Configure macuitest

One settings file holds the defaults for mouse and keyboard timings, the search display, element matching and timeouts, OCR languages, and the screenshot root. To create a documented copy in your project, run the following command:

```bash
python -m macuitest.config init
```

The command writes `macuitest.toml` with every key and a comment, and sets each key that has a default to that default. Edit the keys you need and delete the rest:

```toml
[mouse]
move = 0.36          # Slower cursor moves, easier to follow in a screen recording.

[screen]
display = 1          # Search only the second display. 0 is the menu bar display.

[ocr]
languages = ["en-US", "uk-UA"]
```

The first time you import a macuitest element or controller, macuitest reads the first of these files that it finds:

1. The file named by `$MACUITEST_CONFIG`.
2. `macuitest.toml` in the working directory.
3. `pyproject.toml` in the working directory, with each table under `[tool.macuitest]`, such as `[tool.macuitest.mouse]`.

A missing `$MACUITEST_CONFIG` file, an unknown key, or a bad value raises `ConfigError` naming the file and the key. macuitest checks a `display` index against the displays connected at that moment. Your code can change any setting at run time:

```python
from macuitest.config.settings import settings
from macuitest.lib.elements.ui.monitor import monitor

settings.mouse.move = 0.1
settings.screen.search_region = monitor.displays[1]  # A Region, which code can set and files can't.
```

macuitest also reads these environment variables:

- `$MACUITEST_SCR` sets the screenshot root for `ScreenshotPathBuilder`, and wins over `paths.screenshots`.
- `$MACUITEST_PASSWORD` gives `ShellExecutor.sudo` the admin password when the `com.macuitest.automation` keychain item is missing. Keep it out of config files.

## Develop macuitest

To set up the project and run the checks that CI runs, use these commands:

```bash
uv sync
uv run pytest tests/unit
uv run ruff check && uv run ruff format --check
uv run ty check
```

Unit tests never read the real screen. A test that needs text on screen draws it into an image with the `text_image` fixture.

For release notes, see [CHANGELOG.md](https://github.com/andriykislitsyn/macuitest/blob/main/CHANGELOG.md).
