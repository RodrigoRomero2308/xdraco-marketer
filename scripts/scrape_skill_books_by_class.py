#!/usr/bin/env python3
"""
Recorre listados NFT por clase y extrae nombres de habilidades desde ítems
"Libro de habilidades de …" en GET /nft/character/inven.

  python scripts/scrape_skill_books_by_class.py --class all --out-dir data/glossary
  python scripts/scrape_skill_books_by_class.py --class 5 --pages 2 --max-chars 20

Requiere red. Usa class numérico 1–7 (ver mir4_api.constants.CLASS_ID_TO_SLUG).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://webapi.mir4global.com"
HEADERS = {
    "Accept": "application/json",
    "Origin": "https://www.xdraco.com",
    "Referer": "https://www.xdraco.com/",
    "User-Agent": "xdraco-marketer/scrape-skill-books",
}

# Cargar mapa clase → slug sin depender del paquete instalado
CLASS_ID_TO_SLUG: dict[int, str] = {
    1: "warrior",
    2: "sorcerer",
    3: "taoist",
    4: "arbalist",
    5: "lancer",
    6: "darkist",
    7: "lionheart",
}


def _normalize_label(s: str) -> str:
    t = unicodedata.normalize("NFKD", s.strip())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())


def skill_id_suggested(name_es: str) -> str:
    return _normalize_label(name_es).replace(" ", "_")


def http_get(path: str, params: dict[str, str | int]) -> dict:
    q = urlencode(params)
    url = f"{BASE}{path}?{q}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


# Sufijos de rareza en español (ítems de libro)
BOOK_RE = re.compile(
    r"^Libro de habilidades de\s+(.+?)\s+"
    r"(raro|inusual|épico|epico|legendario|Legendario|Épico|Raro)\s*$",
    re.IGNORECASE | re.UNICODE,
)


def extract_skill_fragment(item_name: str) -> str | None:
    name = item_name.strip()
    if "Libro de habilidades inusual" in name and "de " not in name.replace(
        "Libro de habilidades inusual", ""
    ):
        return None
    if "Libro de habilidades quemado" in name:
        return None
    m = BOOK_RE.match(name)
    if m:
        return m.group(1).strip()
    return None


def scrape_one_class(
    class_num: int,
    *,
    pages: int,
    max_chars: int,
    delay: float,
) -> dict:
    seen_tid: set[int] = set()
    fragments: set[str] = set()
    raw_names: set[str] = set()

    for page in range(1, pages + 1):
        data = http_get(
            "/nft/lists",
            {
                "listType": "sale",
                "class": class_num,
                "levMin": 0,
                "levMax": 0,
                "powerMin": 0,
                "powerMax": 0,
                "priceMin": 0,
                "priceMax": 0,
                "sort": "latest",
                "page": page,
                "languageCode": "es",
            },
        )
        if data.get("code") != 200:
            return {"error": data, "class_numeric": class_num}
        rows = data.get("data", {}).get("lists") or []
        if not rows:
            break
        for row in rows:
            tid = int(row["transportID"])
            if tid in seen_tid:
                continue
            seen_tid.add(tid)
            if len(seen_tid) > max_chars:
                break
            time.sleep(delay)
            try:
                inv = http_get("/nft/character/inven", {"transportID": tid, "languageCode": "es"})
            except urllib.error.HTTPError as e:
                print(f"class={class_num} HTTP {e} tid={tid}", file=sys.stderr, flush=True)
                continue
            if inv.get("code") != 200:
                continue
            for it in inv.get("data") or []:
                n = (it.get("itemName") or "").strip()
                if "Libro de habilidades" not in n:
                    continue
                raw_names.add(n)
                frag = extract_skill_fragment(n)
                if frag:
                    fragments.add(frag)
        if len(seen_tid) >= max_chars:
            break

    slug = CLASS_ID_TO_SLUG[class_num]
    return {
        "class_numeric": class_num,
        "class_slug": slug,
        "transport_ids_sampled": sorted(seen_tid),
        "skill_name_fragments_from_books_es": sorted(fragments),
        "raw_book_item_names": sorted(raw_names),
    }


def to_glossary_yaml_payload(result: dict) -> dict:
    frags = result.get("skill_name_fragments_from_books_es") or []
    skills = [
        {
            "skill_id_suggested": skill_id_suggested(name),
            "name_es": name,
            "name_en": None,
            "wiki_en_ref": None,
        }
        for name in frags
    ]
    return {
        "class_slug": result["class_slug"],
        "class_numeric": result["class_numeric"],
        "locale_names_primary": "es",
        "source_note": "Nombres ES desde ítems «Libro de habilidades de …» en GET /nft/character/inven",
        "generated_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "transport_ids_sampled": result.get("transport_ids_sampled") or [],
        "skills": skills,
        "scraped_unique_fragments_es": frags,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--class",
        dest="class_arg",
        default="all",
        help='Número 1–7 o "all" (por defecto todas salvo Maga; ver --include-sorcerer)',
    )
    p.add_argument(
        "--include-sorcerer",
        action="store_true",
        help='Con --class all, incluye también la clase 2 (Maga). Por defecto all = 1,3,4,5,6,7.',
    )
    p.add_argument("--pages", type=int, default=2)
    p.add_argument("--max-chars", type=int, default=16, dest="max_chars")
    p.add_argument("--delay", type=float, default=0.35)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Si se indica, escribe <slug>_skills.yaml por clase (requiere PyYAML)",
    )
    p.add_argument("--json", action="store_true", help="Imprimir JSON al stdout en lugar de resumen")
    args = p.parse_args()

    if args.class_arg == "all":
        class_nums = list(range(1, 8))
        if not args.include_sorcerer:
            class_nums = [c for c in class_nums if c != 2]
    else:
        cn = int(args.class_arg)
        if cn not in CLASS_ID_TO_SLUG:
            print("class debe ser 1–7 o all", file=sys.stderr)
            return 1
        class_nums = [cn]

    all_results: list[dict] = []
    for cn in class_nums:
        print(f"--- clase {cn} ({CLASS_ID_TO_SLUG[cn]}) ---", file=sys.stderr, flush=True)
        res = scrape_one_class(cn, pages=args.pages, max_chars=args.max_chars, delay=args.delay)
        all_results.append(res)
        if args.out_dir:
            if yaml is None:
                print("Instalá PyYAML (dependencia del proyecto: pip install pyyaml)", file=sys.stderr)
                return 1
            out_dir = args.out_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = res.get("class_slug", CLASS_ID_TO_SLUG[cn])
            payload = to_glossary_yaml_payload(res)
            out_path = out_dir / f"{slug}_skills.yaml"
            with out_path.open("w", encoding="utf-8") as f:
                f.write(
                    "# Glosario de habilidades (ES) inferido desde libros en inventario NFT.\n"
                    "# Regenerar: python scripts/scrape_skill_books_by_class.py --class all --out-dir ...\n\n"
                )
                yaml.safe_dump(
                    payload,
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
            print(f"Escrito {out_path}", file=sys.stderr, flush=True)

    if args.json:
        print(json.dumps(all_results if len(all_results) > 1 else all_results[0], ensure_ascii=False, indent=2))
    elif not args.out_dir:
        print(json.dumps(all_results if len(all_results) > 1 else all_results[0], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
