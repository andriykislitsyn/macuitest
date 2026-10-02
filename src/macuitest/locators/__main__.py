"""Inspect apps and manage screen locators: `python -m macuitest.locators tree|capture|check`."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.capture import capture
from macuitest.lib.elements.locators.check import check
from macuitest.lib.elements.locators.check import load_module
from macuitest.lib.elements.locators.tree import tree


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command line and return its exit code."""
    parser = argparse.ArgumentParser(prog="python -m macuitest.locators")
    commands = parser.add_subparsers(dest="command", required=True)
    capturing = commands.add_parser(
        "capture", help="write a PNG per element of an app's window and a Screen module"
    )
    capturing.add_argument("app", help="the name of the process owning the window")
    capturing.add_argument("--out", type=Path, required=True, help="the module to write")
    capturing.add_argument("--role", action="append", default=[], help="keep only this AX role")
    capturing.add_argument("--margin", type=_margin, default=4.0, help="points around each crop")
    capturing.add_argument("--force", action="store_true", help="replace existing files")
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
    args = parser.parse_args(argv)
    if args.command == "check":
        return _check(args.module)
    window = None
    if args.window_title or args.window_subrole:
        window = AXQuery.of(title=args.window_title, subrole=args.window_subrole)
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
        )
    except (LookupError, FileExistsError, PermissionError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Wrote {written[0]} and {len(written) - 1} images")
    return 0


def _tree(app: str, window: Optional[AXQuery], roles: list[str], activate: bool) -> int:
    try:
        print(tree(app, window=window, roles=roles, activate=activate), end="")
    except (LookupError, PermissionError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def _check(module: Path) -> int:
    report = check(load_module(module))
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


if __name__ == "__main__":
    sys.exit(main())
