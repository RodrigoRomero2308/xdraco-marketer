"""Parseo de valores de stats tal como vienen en summary/stats (texto localizado)."""

from __future__ import annotations

import re

# Número al inicio: "945sec", "1.5min" (la API a veces concatena unidad al valor).
_NUM_PREFIX = re.compile(r"^(\d+(?:\.\d+)?)")


def parse_stat_value(raw: str | int | float) -> float:
    """Convierte '204,754', '1041.1 %', '945sec', etc. a float."""

    if isinstance(raw, int | float):
        return float(raw)
    s = str(raw).strip().replace(",", "").replace("\xa0", " ")
    s = s.replace(" ", "")
    if s.endswith("%"):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        m = _NUM_PREFIX.match(s)
        if m:
            return float(m.group(1))
        raise ValueError(f"valor de stat no numérico: {raw!r}") from None
