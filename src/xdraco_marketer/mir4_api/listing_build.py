"""Armar `Listing` a partir de respuestas JSON de list + summary + stats."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from xdraco_marketer.mir4_api.errors import Mir4ApiError
from xdraco_marketer.mir4_api.merge import with_stats
from xdraco_marketer.mir4_api.stats_parse import stats_response_to_stat_map
from xdraco_marketer.mir4_api.summary_profile import summary_data_to_profile
from xdraco_marketer.models.character import CharacterProfile
from xdraco_marketer.models.listing import Currency, Listing


def _currency_from_blockchain(blockchain: str | None) -> Currency:
    if not blockchain:
        return Currency.UNKNOWN
    b = blockchain.strip().upper()
    if "WEMIX" in b:
        return Currency.WEMIX
    if "DRACO" in b:
        return Currency.DRACO
    if "USDT" in b:
        return Currency.USDT
    return Currency.UNKNOWN


def character_from_summary_and_stats(
    summary_data: dict[str, Any],
    stats_lists: list[dict[str, Any]],
) -> CharacterProfile:
    base = summary_data_to_profile(summary_data)
    smap = stats_response_to_stat_map(stats_lists)
    return with_stats(base, smap)


def listing_from_row_and_details(
    row: dict[str, Any],
    summary_data: dict[str, Any],
    stats_lists: list[dict[str, Any]],
) -> Listing:
    """Precio del listado (row); moneda desde summary.blockChain si existe."""

    profile = character_from_summary_and_stats(summary_data, stats_lists)
    price = Decimal(str(row.get("price", 0)))
    seq = row.get("seq")
    listing_id = str(seq) if seq is not None else str(row.get("rowID", ""))
    cc = _currency_from_blockchain(summary_data.get("blockChain"))
    extra = {
        "nftID": str(row.get("nftID", "")),
        "transportID": str(row.get("transportID", "")),
        "seq": listing_id,
    }
    return Listing(
        listing_id=listing_id,
        character=profile,
        price=price,
        currency=cc,
        extra=extra,
    )


def assert_api_ok(payload: dict[str, Any], *, context: str) -> dict[str, Any]:
    if payload.get("code") != 200:
        raise Mir4ApiError(f"{context}: code={payload.get('code')!r}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise Mir4ApiError(f"{context}: falta data")
    return data
