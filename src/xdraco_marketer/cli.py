"""CLI opcional: listar NFTs en venta y opcionalmente cargar detalle (summary+stats)."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from decimal import Decimal
from pathlib import Path
from typing import Any

from xdraco_marketer.bargains.detector import BargainDetector, BargainSettings
from xdraco_marketer.mir4_api.client import Mir4Client
from xdraco_marketer.models.listing import Listing
from xdraco_marketer.rules.loader import load_rule_from_yaml_text


def _cmd_list(args: argparse.Namespace) -> int:
    with Mir4Client(delay_s=args.delay) as client:
        data = client.fetch_sale_list(page=args.page, class_id=args.class_id)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    rows_seen = 0
    loaded = 0
    errors: list[tuple[str, str]] = []
    with Mir4Client(delay_s=args.delay) as client:
        for row in client.iter_sale_rows(max_pages=args.pages, class_id=args.class_id):
            if loaded >= args.limit:
                break
            rows_seen += 1
            lid = _row_short_id(row)
            try:
                listing = client.fetch_listing(row)
            except Exception as e:
                errors.append((lid, _fmt_err(e)))
                continue
            ch = listing.character
            print(
                f"{listing.listing_id}\t{listing.price}\t{ch.class_id}\t"
                f"{ch.power}\tstats={len(ch.stats)}"
            )
            loaded += 1
    _print_scan_report(args, rows_seen=rows_seen, loaded=loaded, errors=errors)
    return 1 if errors else 0


def _row_short_id(row: dict[str, Any]) -> str:
    s = row.get("seq")
    t = row.get("transportID")
    if s is not None and t is not None:
        return f"seq={s} tid={t}"
    return str(row.get("seq", row.get("transportID", "?")))


def _fmt_err(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"


def _print_scan_report(
    args: argparse.Namespace,
    *,
    rows_seen: int,
    loaded: int,
    errors: list[tuple[str, str]],
) -> None:
    print("\n--- reporte scan ---", file=sys.stderr)
    print(f"  páginas máx.: {args.pages}  clase: {args.class_id}  delay: {args.delay}s", file=sys.stderr)
    print(f"  filas recorridas (listado): {rows_seen}", file=sys.stderr)
    print(f"  perfiles cargados OK: {loaded} (límite {args.limit})", file=sys.stderr)
    print(f"  errores al cargar detalle: {len(errors)}", file=sys.stderr)
    for lid, msg in errors[:8]:
        print(f"    - {lid}: {msg}", file=sys.stderr)
    if len(errors) > 8:
        print(f"    … y {len(errors) - 8} más", file=sys.stderr)
    print("--------------------\n", file=sys.stderr)


def _print_bargains_report(
    args: argparse.Namespace,
    *,
    rows_seen: int,
    listings_loaded: int,
    errors: list[tuple[str, str]],
    cohort_size: int,
    deals_count: int,
) -> None:
    need = args.min_cohort
    print("\n--- reporte bargains ---", file=sys.stderr)
    print(f"  regla: {args.rule}", file=sys.stderr)
    print(
        f"  páginas máx.: {args.pages}  clase: {args.class_id}  "
        f"delay: {args.delay}s  límite listados: {args.limit}",
        file=sys.stderr,
    )
    print(
        f"  ratio ganga: {args.ratio}  cohorte mín.: {need} comparables",
        file=sys.stderr,
    )
    print(f"  filas recorridas (listado API): {rows_seen}", file=sys.stderr)
    print(f"  listados cargados OK (summary+stats): {listings_loaded}", file=sys.stderr)
    print(f"  errores al cargar detalle: {len(errors)}", file=sys.stderr)
    for lid, msg in errors[:8]:
        print(f"    - {lid}: {msg}", file=sys.stderr)
    if len(errors) > 8:
        print(f"    … y {len(errors) - 8} más", file=sys.stderr)
    print(f"  cumplen la regla (cohorte): {cohort_size}", file=sys.stderr)
    print(f"  gangas mostradas: {deals_count}", file=sys.stderr)
    if deals_count == 0:
        if listings_loaded == 0:
            print(
                "  nota: no hay listados cargados; revisá errores o la API.",
                file=sys.stderr,
            )
        elif cohort_size == 0:
            print(
                "  nota: nadie cumple la regla YAML (clase, stats, skills, etc.).",
                file=sys.stderr,
            )
        elif cohort_size < need:
            print(
                f"  nota: el cohorte que cumple la regla es {cohort_size}; "
                f"hacen falta al menos {need} para calcular mediana y gangas.",
                file=sys.stderr,
            )
        else:
            print(
                "  nota: hay cohorte suficiente pero ningún precio quedó bajo la mediana "
                f"(ratio ≤ {args.ratio}).",
                file=sys.stderr,
            )
    print("------------------------\n", file=sys.stderr)


def _cmd_bargains(args: argparse.Namespace) -> int:
    rule = load_rule_from_yaml_text(args.rule.read_text(encoding="utf-8"))
    settings = BargainSettings(
        median_ratio_max=Decimal(args.ratio),
        min_comparables=args.min_cohort,
    )
    det = BargainDetector(rule, settings)
    listings: list[Listing] = []
    errors: list[tuple[str, str]] = []
    rows_seen = 0
    with Mir4Client(delay_s=args.delay) as client:
        for row in client.iter_sale_rows(max_pages=args.pages, class_id=args.class_id):
            if len(listings) >= args.limit:
                break
            rows_seen += 1
            lid = _row_short_id(row)
            try:
                listings.append(client.fetch_listing(row))
            except Exception as e:
                errors.append((lid, _fmt_err(e)))
                if args.verbose_errors:
                    traceback.print_exc(file=sys.stderr)
                continue
    cohort = det.cohort(listings)
    deals = det.find(listings)
    for deal in deals:
        li = deal.listing
        print(
            f"ganga\t{li.listing_id}\tprice={li.price}\t"
            f"median_peers={deal.median_peer_price}\t"
            f"ratio={deal.ratio_to_median}"
        )
    _print_bargains_report(
        args,
        rows_seen=rows_seen,
        listings_loaded=len(listings),
        errors=errors,
        cohort_size=len(cohort),
        deals_count=len(deals),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="xdraco-marketer", description="MIR4 / XDraco helpers")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="Una página de /nft/lists (JSON crudo)")
    pl.add_argument("--page", type=int, default=1)
    pl.add_argument("--class", dest="class_id", type=int, default=0)
    pl.add_argument("--delay", type=float, default=0.0)
    pl.set_defaults(func=_cmd_list)

    ps = sub.add_parser("scan", help="Listado + summary + stats por NFT (resumen texto)")
    ps.add_argument("--pages", type=int, default=1)
    ps.add_argument("--class", dest="class_id", type=int, default=0)
    ps.add_argument("--limit", type=int, default=5)
    ps.add_argument("--delay", type=float, default=0.25, help="Pausa entre requests")
    ps.set_defaults(func=_cmd_scan)

    pb = sub.add_parser("bargains", help="Cargar N listados y evaluar regla YAML")
    pb.add_argument("--rule", type=Path, required=True, help="Archivo YAML de regla")
    pb.add_argument("--pages", type=int, default=2)
    pb.add_argument("--class", dest="class_id", type=int, default=0)
    pb.add_argument("--limit", type=int, default=15)
    pb.add_argument("--delay", type=float, default=0.25)
    pb.add_argument("--ratio", default="0.92")
    pb.add_argument("--min-cohort", type=int, dest="min_cohort", default=3)
    pb.add_argument(
        "--verbose-errors",
        action="store_true",
        help="En errores al cargar un NFT, imprimir traceback completo en stderr",
    )
    pb.set_defaults(func=_cmd_bargains)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
