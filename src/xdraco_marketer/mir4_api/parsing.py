"""Parseo de valores de stats tal como vienen en summary/stats (texto localizado)."""


def parse_stat_value(raw: str | int | float) -> float:
    """Convierte '204,754', '1041.1 %', etc. a float."""

    if isinstance(raw, int | float):
        return float(raw)
    s = raw.strip().replace(",", "").replace("\xa0", " ")
    s = s.replace(" ", "")
    if s.endswith("%"):
        s = s[:-1]
    return float(s)
