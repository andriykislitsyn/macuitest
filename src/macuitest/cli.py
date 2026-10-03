"""The macuitest command: inspect apps, manage screen locators, and act on elements."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from macuitest.lib import actions
from macuitest.lib import app_actions
from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.capture import capture
from macuitest.lib.elements.locators.check import check
from macuitest.lib.elements.locators.check import load_module
from macuitest.lib.elements.locators.target import REFERENCE
from macuitest.lib.elements.locators.target import Target
from macuitest.lib.elements.locators.target import resolve
from macuitest.lib.elements.locators.tree import tree
from macuitest.lib.elements.native.calls import AXError
from macuitest.lib.elements.screen_element import UIElementNotFoundOnScreen

# Commands that act on one element, with their help.
VERBS = {
    "find": "report whether an element is there now",
    "read": "print an element's value",
    "wait": "wait for an element to appear, or to vanish",
    "press": "perform an element's accessibility press action",
    "set": "write an element's value",
    "click": "bring the app to the front and click an element with the mouse",
}
# Commands that act on a whole app.
APP_VERBS = frozenset({"launch", "quit", "menu", "keys", "type", "screenshot"})


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command line and return its exit code."""
    parser = argparse.ArgumentParser(prog="macuitest")
    commands = parser.add_subparsers(dest="command", required=True)
    capturing = commands.add_parser(
        "capture", help="write a PNG per element of an app's window and a Screen module"
    )
    capturing.add_argument("app", help="the name of the process owning the window")
    capturing.add_argument("--out", type=Path, required=True, help="the module to write")
    capturing.add_argument("--role", action="append", default=[], help="keep only this AX role")
    capturing.add_argument("--margin", type=_margin, default=4.0, help="points around each crop")
    capturing.add_argument("--force", action="store_true", help="replace existing files")
    capturing.add_argument(
        "--append", action="store_true", help="add the screen to an existing module"
    )
    capturing.add_argument("--window-title", help="capture the window with this title")
    capturing.add_argument("--window-subrole", help="capture the window with this AX subrole")
    checking = commands.add_parser(
        "check", help="list declared images missing on disk and PNGs no element declares"
    )
    checking.add_argument("module", type=Path)
    showing = commands.add_parser(
        "tree", help="print an app's accessibility tree with each element's ax() locator"
    )
    showing.add_argument("app", help="the name of the process owning the windows")
    showing.add_argument("--role", action="append", default=[], help="show only this AX role")
    showing.add_argument("--window-title", help="show only the window with this title")
    showing.add_argument("--window-subrole", help="show only the window with this AX subrole")
    showing.add_argument("--activate", action="store_true", help="bring the app to the front first")
    for verb, help_ in VERBS.items():
        acting = commands.add_parser(verb, help=help_)
        acting.add_argument(
            "target", nargs="+", help="<app> <locator>, or <module.py>:<Screen>.<element>"
        )
        acting.add_argument("--window-title", help="search the window with this title")
        acting.add_argument("--window-subrole", help="search the window with this AX subrole")
    waiting, pressing, clicking = (commands.choices[verb] for verb in ("wait", "press", "click"))
    waiting.add_argument("--vanish", action="store_true", help="wait until it's gone")
    waiting.add_argument("--timeout", type=float, help="seconds to wait")
    pressing.add_argument("--pause", type=float, help="seconds to wait first")
    clicking.add_argument("--double", action="store_true", help="double-click")
    clicking.add_argument("--right", action="store_true", help="right-click")
    launching = commands.add_parser("launch", help="open an app and wait for its window")
    launching.add_argument("app")
    launching.add_argument(
        "--timeout", type=float, default=app_actions.LAUNCH_TIMEOUT, help="seconds to wait"
    )
    quitting = commands.add_parser("quit", help="ask an app to quit, like Command-Q")
    quitting.add_argument("app")
    quitting.add_argument(
        "--timeout", type=float, default=app_actions.QUIT_TIMEOUT, help="seconds to wait"
    )
    pressing_menu = commands.add_parser("menu", help='press a menu item, such as "File > Save…"')
    pressing_menu.add_argument("app")
    pressing_menu.add_argument("path")
    shortcut = commands.add_parser("keys", help="post a shortcut, such as cmd+s")
    shortcut.add_argument("app")
    shortcut.add_argument("combo")
    typing = commands.add_parser("type", help="type text into the app's focused element")
    typing.add_argument("app")
    typing.add_argument("text")
    shooting = commands.add_parser("screenshot", help="write a PNG of an app's window")
    shooting.add_argument("app")
    shooting.add_argument("--out", type=Path, help="the PNG to write, by default a temp file")
    shooting.add_argument("--window-title", help="capture the window with this title")
    shooting.add_argument("--window-subrole", help="capture the window with this AX subrole")
    args = parser.parse_args(argv)
    if args.command == "check":
        return _check(args.module)
    window = None
    title, subrole = getattr(args, "window_title", None), getattr(args, "window_subrole", None)
    if title or subrole:
        window = AXQuery.of(title=title, subrole=subrole)
    if args.command in APP_VERBS:
        return _act_on_app(args, window)
    if args.command in VERBS:
        parts, rest = _split_target(args.target)
        if args.command == "set" and not rest:
            parser.error("set needs a value after the element")
        if len(rest) > (1 if args.command == "set" else 0):
            parser.error(f"{args.command}: unexpected arguments {' '.join(rest)}")
        return _act(args, parts, rest, window)
    if args.command == "tree":
        return _tree(args.app, window, args.role, args.activate)
    try:
        written = capture(
            args.app,
            args.out,
            roles=args.role,
            margin=args.margin,
            force=args.force,
            window=window,
            append=args.append,
        )
    except (LookupError, PermissionError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Wrote {written[0]} and {len(written) - 1} images")
    return 0


def _act_on_app(args: argparse.Namespace, window: Optional[AXQuery]) -> int:
    try:
        if args.command == "launch":
            app_actions.launch(args.app, timeout=args.timeout)
        elif args.command == "quit":
            if not app_actions.quit(args.app, timeout=args.timeout):
                print(f"{args.app} isn't running")
        elif args.command == "menu":
            app_actions.menu(args.app, args.path)
        elif args.command == "keys":
            app_actions.keys(args.app, args.combo)
        elif args.command == "type":
            app_actions.type_text(args.app, args.text)
        else:
            print(app_actions.screenshot(args.app, args.out, window=window))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    except (
        LookupError,
        app_actions.LaunchError,
        app_actions.QuitError,
        actions.ActionError,
        actions.FocusError,
        AXError,
        PermissionError,
    ) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def _split_target(parts: list[str]) -> tuple[list[str], list[str]]:
    """Split `parts` into the target and what follows it, such as `set`'s value."""
    if REFERENCE.match(parts[0]):
        return parts[:1], parts[1:]
    return parts[:2], parts[2:]


def _act(
    args: argparse.Namespace, parts: list[str], rest: list[str], window: Optional[AXQuery]
) -> int:
    target: Optional[Target] = None
    try:
        target = resolve(parts, window)
        return _run(args, target, rest)
    except actions.NoWindowError as error:
        print(f"{error}. Launch it first.", file=sys.stderr)
        return 1
    except (LookupError, UIElementNotFoundOnScreen):
        label = target.label if target else " ".join(parts)
        app = target.app if target and target.app else "<app>"
        print(f"Not found: {label}. List elements with: macuitest tree {app}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    except (
        actions.ActionError,
        actions.FocusError,
        AXError,
        AppleScriptError,
        PermissionError,
    ) as error:
        print(error, file=sys.stderr)
        return 1


def _run(args: argparse.Namespace, target: Target, rest: list[str]) -> int:
    element = target.element
    if args.command == "find":
        snapshot = actions.find(element)
        if snapshot is None:
            raise LookupError(target.label)
        print(_describe(snapshot))
    elif args.command == "read":
        value = actions.read(element)
        print("" if value is None else value)
    elif args.command == "wait":
        if not actions.wait(element, vanish=args.vanish, timeout=args.timeout):
            state = "vanish" if args.vanish else "appear"
            print(f"Timed out waiting for {target.label} to {state}", file=sys.stderr)
            return 1
    elif args.command == "press":
        actions.press(element, pause=args.pause)
    elif args.command == "set":
        actions.set_value(element, rest[0])
    else:
        actions.click(element, target.app, double=args.double, right=args.right)
    return 0


def _describe(snapshot: actions.Snapshot) -> str:
    """Return a snapshot as one line, such as `AXButton "Search" at 412,88 24x24 value=None`."""
    words = []
    if snapshot.role:
        words.append(snapshot.role)
    if snapshot.title:
        words.append(json.dumps(snapshot.title, ensure_ascii=False))
    if snapshot.box is not None:
        box = snapshot.box
        words.append(f"at {box.x1:g},{box.y1:g} {box.x2 - box.x1:g}x{box.y2 - box.y1:g}")
    # A screen element's snapshot is only its box.
    if snapshot.role or snapshot.box is None:
        words.append(f"value={snapshot.value!r}")
    return " ".join(words)


def _tree(app: str, window: Optional[AXQuery], roles: list[str], activate: bool) -> int:
    try:
        print(tree(app, window=window, roles=roles, activate=activate), end="")
    except (LookupError, PermissionError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def _check(module: Path) -> int:
    try:
        report = check(load_module(module))
    except (ImportError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    for path in report.missing:
        print(f"Missing: {path}")
    for path in report.undeclared:
        print(f"Not declared: {path}")
    return 0 if report.clean else 1


def _margin(value: str) -> float:
    margin = float(value)
    if margin < 0:
        raise argparse.ArgumentTypeError(f"must be 0 or more, not {value}")
    return margin
