#!/usr/bin/env python3
"""
Compatibilidad: regenera solo la clase Maga (2).

Preferir:
  python scripts/scrape_skill_books_by_class.py --class 2 --out-dir data/glossary
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEW = ROOT / "scrape_skill_books_by_class.py"


def main() -> int:
    argv = [sys.executable, str(NEW), "--class", "2"] + sys.argv[1:]
    return subprocess.call(argv)


if __name__ == "__main__":
    raise SystemExit(main())
