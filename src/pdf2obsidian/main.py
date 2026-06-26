from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from pdf2obsidian import __author__, __version__
from pdf2obsidian.gui.main_window import MainWindow


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PDF2Obsidian desktop converter")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version, creator, and license information.",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = _parse_args(sys.argv[1:])
    if args.version:
        print(f"PDF2Obsidian {__version__}")
        print(f"Created by {__author__}")
        print("License: MIT")
        return 0

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
