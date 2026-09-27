# Changelog

## 0.8.0

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

- `TextElement` finds elements by their visible text, with the same actions and waits as `UIElement`.
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
