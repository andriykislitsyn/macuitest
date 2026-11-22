# Operating an app

## Verbs

| Verb | Does | Takes focus |
|---|---|---|
| `find` | Prints the element's role, title, frame, and value, or exits 1. Doesn't wait. | No |
| `read` | Prints the element's text or value. | No |
| `wait` | Waits for the element to appear, or to vanish with `--vanish`. | No |
| `press` | Performs the accessibility press action. Exits 1 when the element offers none. | No |
| `set` | Writes the element's value, such as a text field's text. | No |
| `click` | Brings the app forward, then clicks with the mouse. `--double` and `--right` change the click. | Yes |
| `launch` | Opens the app, or brings it forward, and waits for its window. | Yes |
| `quit` | Asks the app to quit, like Command-Q. Exits 1 while it's still running. | No |
| `menu` | Presses a menu item, such as `macuitest menu TextEdit "File > Save…"`. | No |
| `keys` | Posts one shortcut, such as `cmd+shift+s`. | Yes |
| `type` | Types text into the focused element, checking focus before each character. | Yes |
| `screenshot` | Writes a PNG of the app's window, with any sheet over it, and prints the path. | No |

`click`, `keys`, and `type` refuse input when the app doesn't come to the front. They can't tell when a launcher panel such as Spotlight holds keyboard focus, or when another app's floating window covers the element.

## Locator strings

A target is `<app> '<locator>'` or `<module.py>:<Screen>.<element>`. A string is parsed, never run as Python.

- `ax(identifier=..., description=..., title=..., role=..., kind=Button)` finds an element by accessibility attributes. `kind` is an element class such as `Button` or `StaticText`.
- `.child(...)` after `ax()` finds a descendant of an element that has no label of its own, such as `ax(identifier="StandardInputView").child(role="AXStaticText", kind=StaticText)`.
- `text("Label")` finds visible text with Apple Vision.
- `applescript()` and `image()` work only in a module.
- `--window-title` and `--window-subrole` scope a string to one window.

`tree` and `capture` print locators that are valid by construction: a locator is the first match in depth-first order across the app's windows, front to back. Hand-written locators must follow that rule.

## When the tree isn't enough

- Apps that draw everything themselves, such as games, canvas editors, and Electron apps, expose little or nothing. Use `screenshot` to look, and `text()` or `image()` locators in a module to act.
- `capture` writes a screen module with locators and, for elements the tree can't name, PNGs to match.
- Test whether an element exists with `find`, not by retrying `click`.
