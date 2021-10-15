![Tests](https://github.com/andriykislitsyn/macuitest/actions/workflows/tests.yaml/badge.svg)

# MacUITest

> A simple framework that helps to create functional and UI tests against almost any macOS application.

- Created to help testers to automate their routine tasks with ease and help me with structuring my experience;
- I'll be glad to receive suggestions on evolution of the project!

## Tips
- Allow Accessibility access in a Security&Privacy pane of System Preferences;
- You might be asked to allow various access rights anyway, those are new macOS restrictions you cannot easily avoid from Python, just allow them;
- When calling ObjC mouse wrapper a Python Launcher will show up in Dock. To avoid this behavior, you need to add `LSUIElement` `-string "1"` to a Python.app property list. Mine was located easily by running `brew --prefix python3`. It'll be under Frameworks -> Python.framework -> Resources;
- Get UI Browser app, it helps to locate AppleScript locators of the elements on your screen, very helpful;

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Examples](#examples)

---
## Installation

- Install a modern Python version (at least 3.6): `brew install python3`
- If OCR capabilities required, install Tesseract: `brew install tesseract`
- Update pip's setup tools: `pip3 install --upgrade pip setuptools wheel`
- Install the package: `pip3 install macuitest` and you should be ready to go

---
## Features
- Many of useful operations on macOS are introduced in a `macuitest.lib.operating_system` package. A `macos` module inside the package will allow you to manipulate files, processes, change some system settings, etc.;
- An `application` module inside `macuitest.lib.apps` may describe almost any GUI macOS app. Creating an instance of which will allow you to perform launch/quit operations, read some of its attributes, have basic control over its main window, etc.;
- `applescript_wrapper` module under `macuitest.lib.applescript_lib` allows to run some AppleScript commands;
- And last but not least, you can describe most if not every element of an application using `applescript_element`, `native_element` and `ui_element` modules inside `macuitest.lib.elements`. They allow working with AppleScript, PyObjC translated (Native) and UI (built on screenshots) elements retrospectively.

---
## Examples

```pythonstub
from macuitest.lib.apps.application import Application
from macuitest.lib.elements.applescript_element import ASElement

test_app = 'Calculator'
calculator = Application(test_app)

button_one = ASElement('button "1" of group 2 of window 1', process=test_app)
button_zero = ASElement('button "0" of group 2 of window 1', process=test_app)
input_field = ASElement('static text 1 of group 1 of window 1', process=test_app)

calculator.launch()
button_one.click_mouse()
button_zero.click_mouse()
button_one.click_mouse()
assert input_field.text == '101'  # Hopefully you get 101 there :)
```
