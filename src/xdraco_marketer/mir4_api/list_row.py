"""Filas de GET /nft/lists → perfil parcial + stats por nombre (subconjunto)."""

from __future__ import annotations

from typing import Any

from xdraco_marketer.mir4_api.constants import CLASS_ID_TO_SLUG
from xdraco_marketer.models.character import CharacterProfile
from xdraco_marketer.stat_labels import normalize_stat_label


def list_row_to_profile_stub(row: dict[str, Any]) -> CharacterProfile:
    """
    El listado incluye class, powerScore, price, stat[] con statName/statValue numéricos.
    No incluye equipamiento ni skills; sirve para filtros por clase, power y stats básicas.
    """

    cid = int(row.get("class", 0))
    slug = CLASS_ID_TO_SLUG.get(cid, str(cid))
    power = int(row.get("powerScore", 0))
    stats: dict[str, float] = {}
    for s in row.get("stat") or []:
        name = s.get("statName")
        val = s.get("statValue")
        if name is None or val is None:
            continue
        stats[normalize_stat_label(str(name))] = float(val)

    return CharacterProfile(
        class_id=slug,
        power=power,
        stats=stats,
    )
