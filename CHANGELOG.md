# Changelog

## 0.10.0 (2026-10-03)

### Breaking changes

- `python -m macuitest.locators` is now the `macuitest` command, also run as `python -m macuitest`: `macuitest tree`, `macuitest capture`, and `macuitest check`.

### Added

- `macuitest find`, `read`, `wait`, `press`, `set`, and `click` act on one element named by a locator string, such as `macuitest press TextEdit 'ax(identifier="OK")'`, or by a screen module element, such as `macuitest press screens.py:Fonts.search`. Exit code 1 means the UI said no, and 2 means bad usage.

### Fixed

- AppleScript text elements' `set_text` escapes quotes and backslashes. A value such as `He said "hi"` used to fail, and a backslash changed the text.

## 0.9.1 (2026-10-03)

### Added

- `capture --append` adds a screen to an existing module, with the imports it lacks.

### Changed

- `capture` skips the elements inside tables, outlines, and lists that have no `ax()` locator, or one that every row repeats, and notes how many in a comment. The Fonts panel in TextEdit used to produce an `image()` and a PNG for each font row. It also skips layout containers, such as groups, scroll areas, and toolbars, that would only get `image()`, and scroll bars. Pass `--role` to capture them anyway.

### Fixed

- `UIElement` reads a PNG's scale from its DPI, so a pattern captured at 2x matches on a 1x display and the reverse. macOS screenshots record 144 DPI at 2x, and `capture` now records the DPI too. A PNG without a DPI, or with one other than 72, 144, or 216, is still assumed captured on the menu bar display. To mark an older 2x PNG, run `sips -s dpiWidth 144 -s dpiHeight 144 <png>`.

## 0.9.0 (2026-10-03)

### Breaking changes

- `is_visible` checks once and never waits, on every element kind. `VisibleText` and `UIElement` used to wait up to `settings.elements.timeout`, and AppleScript elements up to 5 s. Wait with `wait_displayed()`.
- Every element kind has `click_mouse`, `double_click_mouse`, `right_click_mouse`, and `hover_mouse`, and their options after the offsets are keyword-only. This renames `double_click` and `right_click` on `VisibleText` and `UIElement`, `rightclick_mouse` on `NativeElement`, and `doubleclick_mouse` and `rightclick_mouse` on AppleScript elements. `NativeElement.click_mouse(hold_time=)` is now `hold=`. `region` is keyword-only on `VisibleText` and `UIElement`.
- AppleScript elements' `wait_displayed` and `wait_vanish`, and `NativeElement.wait_vanish`, default to the `settings.elements` timeouts instead of 5 s.
- `did_vanish` is removed: use `wait_vanish()`. AppleScript elements' `is_exists()` is now the `exists` property.
- `Application.is_frontmost` and `is_hidden`, and `Window.is_minimized` and `is_full_screen`, are properties. `if app.is_frontmost:` works now, and `app.is_frontmost()` raises `TypeError`.

### Added

- `python -m macuitest.locators tree` prints an app's accessibility tree with the `ax()` locator of each element. It only reads, unless you pass `--activate`.
- `NativeElement.wait_displayed()`.

### Fixed

- `capture` names a screen after the app instead of the window title, which is often a document name. A window screen, captured with `--window-title` or `--window-subrole`, still takes the window's title. A title or app name that would make the class `None`, `True`, or `False` falls back to the next source.
- `capture` and `tree` skip AppKit's generated `_NS:<n>` identifiers, which change between launches. An element whose role can't be read gets no `role=` locator.
- A screen declared in a package's `__init__.py` keeps its images in the package folder, not in an `__init__` folder.
- `image(within=)` on an area smaller than the image reports the image as not found instead of raising `cv2.error`.
- `text()` and `VisibleText` reject a single character written in decomposed form, such as `e` plus a combining accent.
- `python -m macuitest.locators` reports a module it can't load, and a capture it can't write, without a traceback.
- `Window.full_screen = True` sets full screen. It used to set `AXFrontmost`.

## 0.8.0 (2026-10-03)

### Breaking changes

- Python 3.13 or later is required. The package builds with uv from `pyproject.toml`, and `setup.py`, `setup.cfg`, `tox.ini`, and the requirements files are gone.
- OCR uses Apple Vision instead of Tesseract.
  - `OCRManager(language="eng")` is now `OCRManager(languages=("en-US",))`, with Vision language codes. `OCRManager()` follows `settings.ocr.languages`.
  - `recognize` drops `is_font_white`.
  - `wait_text` checks that the text appears in the region, not that the region's whole text equals it.
- `wait_displayed` on `UIElement` returns the match box as a `Region`, not its top-left `Point`.
- `UIElement` searches every display by default, not only the main one.
- `UIElementNotFoundOnScreen` carries the element's repr, such as `<UIElement "ok.png", similarity=0.925>`, instead of the bare path.
- `is_visible` returns False when the element is missing. It always returned True before.
- `Application.window` targets the first standard window instead of `window 1`, and the window position and size setters raise on failure instead of doing nothing.
- `KeyBoardController.write` types Unicode text, so it works on any keyboard layout. It no longer sends US virtual keycodes, except for tabs and line breaks.
- `wait_condition` checks before its first sleep and polls every 50 ms instead of every 5 ms.
- Mouse moves under 50 px take the full `duration` instead of a third of it.
- Color names come from CIELAB distance, so some borderline colors get different names.
- Repeated runs of the same AppleScript source share properties and top-level variables.
- `MouseConfig` is gone. Set `settings.mouse` from `macuitest.config.settings`, or the `[mouse]` table in the settings file.
- `UIElement.similarity` defaults to `settings.elements.similarity` when you don't pass one.
- `ScreenRecorder` and `SystemPreferences` are removed.
- `pytesseract`, `biplist`, and the pyobjc AVFoundation, CoreMedia, and CoreText packages are no longer dependencies.

### Added

- `VisibleText` finds elements by their visible text, with the same actions and waits as `UIElement`. Single-character text raises `ValueError`, since Vision doesn't read isolated characters reliably.
- Screen captures raise `PermissionError` naming the System Settings pane when Screen Recording isn't granted, instead of reading only the wallpaper.
- `Screen` classes declare an app's elements with `text()`, `image()`, `applescript()`, and `ax()`. App screens scope text and image lookups to the app's window, and `within=` narrows them to another element. Lookups on app screens raise `PermissionError` when Accessibility isn't granted.
- `Screen(window=window(title=..., subrole=...))` covers a dialog or secondary window, so its lookups search only that window.
- `ScreenElement.scope` sets where a lookup searches when it passes no region.
- `python -m macuitest.locators capture` writes a PNG per element of an app's window, alert, or floating panel, and a `Screen` module declaring them. `check` finds missing and undeclared images. `macuitest.lib.elements.locators` exports the locator classes and `standard_window_frame` for suites that inspect their screens.
- `Monitor.capture_window` captures one window, even while it's covered.
- A TOML settings file for mouse and keyboard timings, the search display, element defaults, OCR languages, and the screenshot root. `python -m macuitest.config init` writes a documented copy.
- `Monitor.displays` lists every display's bounds, and `Monitor.capture` returns a CGImage of a region.

### Fixed

- Screen matching, mouse moves, and the default search region work on multi-monitor and retina setups, including displays at negative coordinates.
- XML property lists no longer read as empty and get overwritten on the next write.
- `ShellExecutor.sudo` passes the password on stdin, so it no longer shows in `ps` output or logs.
- Identical copies of a pattern resolve to the topmost, then leftmost, one.
- Pattern scale follows the menu bar display, not whichever screen holds the key window.

### Performance

- A full-desktop template match takes about 200 ms instead of 900 ms.
- Color sampling of an element takes about 30 ms instead of 740 ms, and no longer re-runs the caller's script in worker processes.
- Repeated AppleScript queries run 2 to 4 times faster.
