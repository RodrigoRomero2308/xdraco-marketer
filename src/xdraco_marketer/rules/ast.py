"""Expresiones de regla: composición lógica + condiciones atómicas sobre CharacterProfile."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class ClassIs(BaseModel):
    """Personaje de una clase (id libre, ej. mage, warrior)."""

    type: Literal["class_is"] = "class_is"
    class_id: str


class PowerGte(BaseModel):
    type: Literal["power_gte"] = "power_gte"
    min_power: int = Field(ge=0)


class PowerLte(BaseModel):
    type: Literal["power_lte"] = "power_lte"
    max_power: int = Field(ge=0)


class SkillMinLevel(BaseModel):
    """Una skill con nivel mínimo (inclusive). En MIR4 los niveles van de 1 a 12."""

    type: Literal["skill_min"] = "skill_min"
    skill_id: str
    min_level: int = Field(ge=1, le=12)


class AllSkillsMin(BaseModel):
    """Varias skills deben cumplir nivel mínimo (AND). Cada nivel debe estar entre 1 y 12 (MIR4)."""

    type: Literal["all_skills_min"] = "all_skills_min"
    requirements: dict[str, int]

    @field_validator("requirements")
    @classmethod
    def _levels_mir4(cls, v: dict[str, int]) -> dict[str, int]:
        for sid, lvl in v.items():
            if not 1 <= lvl <= 12:
                raise ValueError(
                    f"Nivel de skill para {sid!r} debe estar entre 1 y 12 (MIR4), recibido {lvl}"
                )
        return v


class ItemAny(BaseModel):
    """Existe al menos un ítem que cumple rareza y/o mejora."""

    type: Literal["item_any"] = "item_any"
    slot: str | None = None
    item_type: str | None = None
    item_type_prefix: str | None = None
    min_rarity: str | None = None
    min_enhancement: int | None = Field(default=None, ge=0)


class ItemsAllSlotsMin(BaseModel):
    """Cada slot listado tiene un ítem con al menos X de mejora (y opcional rareza mínima)."""

    type: Literal["items_all_slots_min"] = "items_all_slots_min"
    slots: list[str]
    min_enhancement: int = Field(ge=0)
    min_rarity: str | None = None


class PetsAnyOf(BaseModel):
    type: Literal["pets_any_of"] = "pets_any_of"
    pet_ids: list[str]


class PetsAllOf(BaseModel):
    type: Literal["pets_all_of"] = "pets_all_of"
    pet_ids: list[str]


class StoneMinTier(BaseModel):
    """Piedras: tipos listados con tier mínimo; si no hay tipos, todas las piedras >= tier."""

    type: Literal["stone_min_tier"] = "stone_min_tier"
    min_tier: int = Field(ge=0)
    stone_type_ids: list[str] | None = None


class StonesTypesMinTier(BaseModel):
    """Por tipo de piedra, tier mínimo."""

    type: Literal["stones_types_min_tier"] = "stones_types_min_tier"
    requirements: dict[str, int]


class StatKeyGte(BaseModel):
    """stat[key] >= min_value; key = nombre legible (ej. Ataque Mágico, Evasión)."""

    type: Literal["stat_key_gte"] = "stat_key_gte"
    key: str
    min_value: float


class StatKeySuffixGte(BaseModel):
    """Algún stat cuya etiqueta normalizada termine en key_suffix (ej. sufijo del nombre)."""

    type: Literal["stat_key_suffix_gte"] = "stat_key_suffix_gte"
    key_suffix: str
    min_value: float


class And(BaseModel):
    type: Literal["and"] = "and"
    items: list[RuleExpr]


class Or(BaseModel):
    type: Literal["or"] = "or"
    items: list[RuleExpr]


class Not(BaseModel):
    type: Literal["not"] = "not"
    item: RuleExpr


_RuleLeaf = (
    ClassIs
    | PowerGte
    | PowerLte
    | SkillMinLevel
    | AllSkillsMin
    | ItemAny
    | ItemsAllSlotsMin
    | PetsAnyOf
    | PetsAllOf
    | StoneMinTier
    | StonesTypesMinTier
    | StatKeyGte
    | StatKeySuffixGte
)

_RuleBranch = And | Or | Not

RuleExpr = Annotated[
    _RuleBranch | _RuleLeaf,
    Field(discriminator="type"),
]

And.model_rebuild()
Or.model_rebuild()
Not.model_rebuild()
