"""Perfil de personaje normalizado para reglas y comparaciones.

Los IDs (clase, skill, ítem, pet, piedra) son strings para que puedas mapear
lo que devuelva WEMIX / scraping / export manual sin acoplar a enums del juego.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillLevel(BaseModel):
    """Nivel de una skill en el perfil; en MIR4 el rango de juego es 1–12."""

    skill_id: str
    level: int = Field(ge=0)


class EquippedItem(BaseModel):
    """Ítem equipado relevante para filtros (ranura opcional para reglas por slot)."""

    item_id: str | None = None
    name: str | None = None
    # Ranura lógica (ej. clave API "1".."15") o nombre de slot si lo mapeás.
    slot: str | None = None
    # Tipo MIR4 (ej. "2_1", "8_5"); útil para filtros por prefijo de ítem.
    item_type: str | None = None
    # rareza libre: "legendary", "L", "4", etc. Las reglas comparan en minúsculas.
    rarity: str | None = None
    enhancement: int = Field(default=0, ge=0)


class PetRef(BaseModel):
    pet_id: str
    name: str | None = None


class MagicStone(BaseModel):
    """Piedra mágica: tipo + tier; stats opcionales para extensiones."""

    stone_type_id: str
    tier: int = Field(ge=0, default=0)
    stats: dict[str, float] = Field(default_factory=dict)


class CharacterProfile(BaseModel):
    class_id: str
    power: int = Field(ge=0)
    skills: list[SkillLevel] = Field(default_factory=list)
    items: list[EquippedItem] = Field(default_factory=list)
    pets: list[PetRef] = Field(default_factory=list)
    stones: list[MagicStone] = Field(default_factory=list)
    # Stats: claves normalizadas (ver stat_labels), ej. "ataque magico".
    stats: dict[str, float] = Field(default_factory=dict)

    def skill_level(self, skill_id: str) -> int | None:
        sid = skill_id.strip().lower()
        for s in self.skills:
            if s.skill_id.strip().lower() == sid:
                return s.level
        return None
