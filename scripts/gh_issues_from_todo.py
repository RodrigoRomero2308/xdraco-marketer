#!/usr/bin/env python3
"""
Crea un issue de GitHub por cada línea `- [ ]` en TODO.md usando la CLI `gh`.

Requisitos:
  - GitHub CLI instalada: https://cli.github.com/
  - `gh auth login` en este repo
  - Ejecutar desde la raíz del repo (o pasar --todo)

Uso:
  python scripts/gh_issues_from_todo.py           # solo muestra qué haría
  python scripts/gh_issues_from_todo.py --apply   # crea issues de verdad

No borra ni edita TODO.md; los issues viven en GitHub aparte del archivo.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

LINE_RE = re.compile(r"^- \[ \] (.+)$")


def parse_todo(path: Path) -> list[tuple[str, str]]:
    section = "General"
    out: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        m = LINE_RE.match(line.rstrip())
        if m:
            out.append((section, m.group(1).strip()))
    return out


def title_from_body(body: str, max_len: int = 75) -> str:
    t = body.replace("**", "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="TODO.md → gh issue create")
    p.add_argument(
        "--todo",
        type=Path,
        default=root / "TODO.md",
        help="Ruta a TODO.md",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Crear issues (sin esto solo imprime plan)",
    )
    args = p.parse_args()

    if not args.todo.is_file():
        print(f"No existe {args.todo}", file=sys.stderr)
        return 1

    if args.apply and not shutil.which("gh"):
        print("No se encontró `gh` en PATH. Instalá GitHub CLI y hacé `gh auth login`.", file=sys.stderr)
        return 1

    items = parse_todo(args.todo)
    if not items:
        print("No hay líneas `- [ ]` en el archivo.")
        return 0

    prefix = "[TODO] "
    for section, body in items:
        title = prefix + title_from_body(body)
        issue_body = (
            f"**Sección:** {section}\n\n"
            f"{body}\n\n"
            "---\n"
            f"Origen: `{args.todo.name}` en el repositorio."
        )
        if not args.apply:
            print("---")
            print(f"Título: {title}")
            print(issue_body[:200] + ("..." if len(issue_body) > 200 else ""))
            continue

        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--body",
            issue_body,
        ]
        subprocess.run(cmd, check=True, cwd=root)

    if not args.apply:
        print(f"\nModo simulación: {len(items)} issues. Repetí con --apply para crearlos.")
    else:
        print(f"Creados {len(items)} issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
