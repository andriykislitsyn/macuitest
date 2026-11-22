---
name: macuitest
description: "Use when operating, automating, or testing a macOS app through its accessibility tree with the macuitest CLI or Python library: reading an app's UI with macuitest tree, pressing buttons, typing, driving menus, taking screenshots, or writing a UI test suite for a Mac app. Covers press versus click, why a lookup fails, and the approval rules. Not for web pages (Selenium, Playwright) or iOS apps (XCUITest)."
license: MIT
compatibility: "Requires macOS, Python 3.13+, macuitest 0.11.0+, and macOS Accessibility permission (plus Screen Recording for screenshots and visible-text matching)."
metadata:
  author: Andrii Kislitsyn
  repository: https://github.com/andriykislitsyn/macuitest
---

# macuitest

macuitest drives macOS apps through the accessibility tree, the tree VoiceOver reads. Prefer it to screenshots plus vision: a lookup takes milliseconds, names the exact element, and survives window moves and theme changes.

It needs [macuitest](https://github.com/andriykislitsyn/macuitest) 0.11.0 or later (`uv add macuitest` or `pip install macuitest`) and Accessibility permission for the terminal. Screenshots and visible-text matching also need Screen Recording.

## The loop

1. Read the UI: `macuitest tree <app>` prints every element with the `ax()` locator that finds it. Read it before guessing a locator.
2. Act on that locator with a verb: `macuitest press Calculator 'ax(identifier="Seven", kind=Button)'`.
3. Confirm with `read` or `wait`. Don't assume the action worked.
4. To reuse locators, write them to a module with `macuitest capture <app> --out screens.py`. Every verb also takes `screens.py:Screen.element`.

Verbs and locator syntax: `references/operating.md`. Writing a test suite: `references/writing-suites.md`.

## Rules

- Reads are safe at any time: `tree` without `--activate`, `find`, `read`, `wait`, `screenshot`.
- Everything else changes the app or takes focus: ask the user before each run. `click`, `launch`, `keys`, `type`, `capture`, and `tree --activate` can type into the wrong app. A module reference and `check` import the module, which runs its code.
- Prefer `press` and `set`. They work with the app in the background. Use `click` when an element offers no press action.
- Exit 0 means done, 1 means the UI said no (missing, timed out, focus refused), 2 means bad usage.

## Gotchas

- `press` on an element without an accessibility press action exits 1. macOS would accept it silently and do nothing, as on System Settings sidebar labels. Use `click`.
- Calculator and floating panels such as TextEdit's Fonts panel show windows only while the app is active. Use `launch`, or `tree --activate` with approval.
- AppKit identifiers like `_NS:34` change between launches. Never match on them.
- Electron apps such as VS Code expose almost no tree. Fall back to `screenshot`, visible text, or image locators, and tell the user why.
- `quit` is polite only. An app asking to save stays open: find the dialog with `tree`, answer it with `press`, then `quit` again.
- `type` writes escapes as written. Pass a real line break, or send `keys <app> return`.
