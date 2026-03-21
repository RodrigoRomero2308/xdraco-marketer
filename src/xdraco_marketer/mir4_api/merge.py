"""Combinar perfil de summary con stats completos del endpoint stats."""

from __future__ import annotations

from xdraco_marketer.models.character import CharacterProfile


def with_stats(base: CharacterProfile, stats: dict[str, float]) -> CharacterProfile:
    merged = dict(base.stats)
    merged.update(stats)
    return base.model_copy(update={"stats": merged})
