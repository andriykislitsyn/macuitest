"""Write the default config file: `python -m macuitest.config init [path]`."""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from macuitest.config import DEFAULT_FILE


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command line and return its exit code."""
    parser = argparse.ArgumentParser(prog="python -m macuitest.config")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="copy the default config file, every key documented")
    init.add_argument("path", nargs="?", default=Path("macuitest.toml"), type=Path)
    args = parser.parse_args(argv)
    if args.path.exists():
        print(f"{args.path} already exists", file=sys.stderr)
        return 1
    shutil.copyfile(DEFAULT_FILE, args.path)
    print(f"Wrote {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
