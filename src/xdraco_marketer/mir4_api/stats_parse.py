"""Respuesta de GET /nft/character/stats → CharacterProfile.stats (por nombre de stat)."""

from __future__ import annotations

from typing import Any

from xdraco_marketer.mir4_api.parsing import parse_stat_value
from xdraco_marketer.stat_labels import normalize_stat_label


def stats_response_to_stat_map(data_lists: list[dict[str, Any]]) -> dict[str, float]:
    """
    Cada elemento tiene statName, statValue (y opcionalmente iconPath, ignorado aquí).

    Clave: ``normalize_stat_label(statName)`` para poder reglar por "Ataque Mágico",
    "Evasión", etc., sin depender de archivos PNG.
    """

    out: dict[str, float] = {}
    for row in data_lists:
        name = row.get("statName")
        if name is None or str(name).strip() == "":
            continue
        key = normalize_stat_label(str(name))
        raw = row.get("statValue")
        if raw is None:
            continue
        try:
            out[key] = parse_stat_value(raw)
        except ValueError:
            # "---", texto puro, formatos no previstos: no romper el listado completo.
            continue
    return out
