# Writing a suite

The reference suites are in https://github.com/andriykislitsyn/macuitest-examples: a Calculator folder and a TextEdit folder, each with `screens.py`, `conftest.py`, and tests.

## Workflow

1. Explore with `macuitest tree <app>`, then generate a module with `macuitest capture <app> --out <app>/screens.py`. To add a sheet or panel's screen to the same module, capture it with `--append`.
2. Edit the module. Delete entries the tests don't need, and replace any locator that encodes state, such as an identifier holding the current mode. Comment each edit.
3. Run `macuitest check <app>/screens.py` until it reports nothing. Then run `macuitest check --live <app>/screens.py` with the app open: it looks up each `ax()` and `applescript()` element read-only and lists the misses. An element that appears only after an action shows as not found, which is expected.
4. Write a `conftest.py` with a session fixture that launches the app, waits for its window, and quits it at the end.
5. Write tests that read elements from `screens.py`. Tests never contain locators.

## Rules for fixtures and tests

- `is_visible` checks once. Wait with `wait_displayed()` or `wait_vanish()`, such as after a hotkey opens a sheet.
- Call `Application.activate()` before every hotkey or typed input. It raises unless the app comes to the front, so keys can't land in another app, such as the user's editor.
- Never type into or save the user's documents. Create your own, leave them empty, and close them with `saving no`.
- A fixture closes whatever it opened, such as a sheet or panel, even when the test fails. Check before toggling: Command-T on an open Fonts panel closes it.
- AppKit generates identifiers like `_NS:34`. They change between launches, and `tree` and `capture` hide them.
- A suite drives the user's mouse and keyboard. Run it only when the user approves that run.
