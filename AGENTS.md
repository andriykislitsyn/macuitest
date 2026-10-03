# Agent notes for macuitest

macuitest drives real macOS apps. Anything that posts input (clicks, keys, `Application.activate`, `capture`, `tree --activate`) moves the user's focus and can type into the wrong app. Run those only when the user approves that run. Reading is safe: `python -m macuitest.locators tree <app>` and `check <module>`, AX attribute reads, and System Events `get` and `exists` queries.

## Commands

```bash
uv sync
uv run pytest tests/unit
uv run ruff check && uv run ruff format --check
uv run ty check
```

Lock with a current uv, such as `uvx --from uv@latest uv lock`. An older uv rewrites `uv.lock` to an older lock revision.

Unit tests never touch the real screen or real apps: autouse guards in `tests/unit/conftest.py` fail any capture and any AppleScript run, and settings reset to `default.toml` before each test. To put text on a fake screen, use the `text_image` fixture. To fake System Events, patch `as_wrapper.tell_app_process` or the method that reads. Every permission reads as granted in unit tests.

## Exploring an app

- Start with `python -m macuitest.locators tree <app>`. It prints each element's attributes and the `ax()` locator that finds it. Calculator and floating panels such as TextEdit's Fonts panel show windows only while the app is active, which needs `--activate`.
- An element's `ax()` locator is valid only if it's the first match in depth-first order across the app's windows, front to back. `tree` and `capture` apply that rule. Hand-written locators must too.
- AppKit generates identifiers like `_NS:34`. They change between launches, so never match on them. `tree` and `capture` hide them.

## Gotchas

- AppleScript `whose` binds to the whole reference in front of it. Parenthesize: `(first window whose subrole is "AXStandardWindow")`.
- System Events reads many SwiftUI controls' `description` as "button" and can't read `AXDescription`. Match `value of attribute "AXIdentifier"` instead.
- System Events raises -1719 (invalid index) as well as -1728 for a reference that isn't there yet. Both mean "missing".
- AppKit keeps a closed sheet or panel alive, so a fixed AX reference to one stays valid. `ax()` elements search again on every use for that reason.
- `is_visible` checks once. Wait with `wait_displayed()` or `wait_vanish()`, never `wait_condition(lambda: x.is_visible)`.
- `UIElement` takes a PNG's pixels per point from its DPI (144 means 2x). `cv2.imwrite` records no DPI, so a PNG written with it falls back to the menu bar display's scale.
- numpy 2 keeps `uint8` arithmetic in `uint8`, so pixel subtraction wraps. Cast first.
- multiprocessing on macOS spawns workers that re-run the caller's `__main__`. Never use it in library code.
- Vision returns nothing, not an error, for unsupported languages, and doesn't read single characters reliably. `VisibleText` rejects them.

## API conventions

- Every element kind shares one protocol: `click_mouse`, `double_click_mouse`, `right_click_mouse`, and `hover_mouse`, with keyword-only options after the offsets; `is_visible`, which checks once; and `wait_displayed` and `wait_vanish`, which default to the `settings.elements` timeouts. New element classes and methods follow it.
- Every `is_*` name is a property.
- `click()` and `press()` perform the accessibility action. Only `*_mouse` methods move the pointer.
- Breaking changes are fine between minor versions: rename outright, with no deprecation aliases, and list each rename under "Breaking changes" in `CHANGELOG.md`.

## Conventions

- Docs follow the Google developer documentation style guide. User-facing changes get a `CHANGELOG.md` entry under "Unreleased".
- Releases: bump `version` in `pyproject.toml`, date the changelog section, then publish a GitHub release tagged `v<version>`. `release.yml` uploads to PyPI through Trusted Publishing, and the tag must match the version. PyPI's index lags a few minutes after the upload, so the examples repo picks the release up with `uv lock --refresh --upgrade-package macuitest`.
- Example suites for real apps live in https://github.com/andriykislitsyn/macuitest-examples.
