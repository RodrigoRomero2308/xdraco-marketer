"""Normalización de nombres de stats para claves en CharacterProfile.stats y reglas."""

from __future__ import annotations

import unicodedata


def normalize_stat_label(s: str) -> str:
    """
    Etiqueta comparable: minúsculas, sin acentos, espacios colapsados.
    Así "Ataque Mágico", "ataque magico" y "  ATAQUE   MAGICO " coinciden.
    """

    t = unicodedata.normalize("NFKD", s.strip())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())
