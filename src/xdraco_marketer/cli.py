"""CLI opcional: listar NFTs en venta y opcionalmente cargar detalle (summary+stats)."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from xdraco_marketer.bargains.detector import BargainDetector, BargainSettings
from xdraco_marketer.mir4_api.client import Mir4Client
from xdraco_marketer.rules.loader import load_rule_from_yaml_text


def _cmd_list(args: argparse.Namespace) -> int:
    with Mir4Client(delay_s=args.delay) as client:
        data = client.fetch_sale_list(page=args.page, class_id=args.class_id)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    with Mir4Client(delay_s=args.delay) as client:
        n = 0
        for row in client.iter_sale_rows(max_pages=args.pages, class_id=args.class_id):
            if n >= args.limit:
                break
            listing = client.fetch_listing(row)
            ch = listing.character
            print(
                f"{listing.listing_id}\t{listing.price}\t{ch.class_id}\t"
                f"{ch.power}\tstats={len(ch.stats)}"
            )
            n += 1
    return 0


def _cmd_bargains(args: argparse.Namespace) -> int:
    rule = load_rule_from_yaml_text(args.rule.read_text(encoding="utf-8"))
    settings = BargainSettings(
        median_ratio_max=Decimal(args.ratio),
        min_comparables=args.min_cohort,
    )
    det = BargainDetector(rule, settings)
    listings = []
    with Mir4Client(delay_s=args.delay) as client:
        for row in client.iter_sale_rows(max_pages=args.pages, class_id=args.class_id):
            if len(listings) >= args.limit:
                break
            listings.append(client.fetch_listing(row))
    for deal in det.find(listings):
        li = deal.listing
        print(
            f"ganga\t{li.listing_id}\tprice={li.price}\t"
            f"median_peers={deal.median_peer_price}\t"
            f"ratio={deal.ratio_to_median}"
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
    pb.add_argument("--rule", type=argparse.FileType("r", encoding="utf-8"), required=True)
    pb.add_argument("--pages", type=int, default=2)
    pb.add_argument("--class", dest="class_id", type=int, default=0)
    pb.add_argument("--limit", type=int, default=15)
    pb.add_argument("--delay", type=float, default=0.25)
    pb.add_argument("--ratio", default="0.92")
    pb.add_argument("--min-cohort", type=int, dest="min_cohort", default=3)
    pb.set_defaults(func=_cmd_bargains)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
