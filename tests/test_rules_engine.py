"""
Tests unitarios del evaluador de reglas (`matches`).

Sirven como red de seguridad al refactorizar `evaluate.py` o ampliar `ast.py`.
"""

from __future__ import annotations

import pytest

from xdraco_marketer.models.character import (
    CharacterProfile,
    EquippedItem,
    MagicStone,
    PetRef,
    SkillLevel,
)
from xdraco_marketer.rules import ast
from xdraco_marketer.rules.evaluate import matches
from xdraco_marketer.rules.loader import load_rule_from_yaml_text


def _base() -> CharacterProfile:
    return CharacterProfile(
        class_id="sorcerer",
        power=400_000,
        skills=[
            SkillLevel(skill_id="s1", level=10),
            SkillLevel(skill_id="s2", level=5),
        ],
        items=[
            EquippedItem(
                slot="1",
                item_type="2_1",
                rarity="legendary",
                enhancement=10,
            ),
            EquippedItem(
                slot="weapon",
                item_type="4_1",
                rarity="epic",
                enhancement=7,
            ),
        ],
        pets=[
            PetRef(pet_id="pet_a"),
            PetRef(pet_id="pet_b"),
        ],
        stones=[
            MagicStone(stone_type_id="8_1", tier=3),
            MagicStone(stone_type_id="8_2", tier=2),
        ],
        stats={
            "ataque magico": 100.0,
            "evasion": 50.0,
        },
    )


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        (ast.ClassIs(class_id="sorcerer"), True),
        (ast.ClassIs(class_id="warrior"), False),
        (ast.PowerGte(min_power=400_000), True),
        (ast.PowerGte(min_power=400_001), False),
        (ast.PowerLte(max_power=400_000), True),
        (ast.PowerLte(max_power=399_999), False),
    ],
)
def test_class_and_power(rule: ast.RuleExpr, expected: bool) -> None:
    assert matches(_base(), rule) is expected


def test_skill_min_and_all_skills() -> None:
    p = _base()
    assert matches(p, ast.SkillMinLevel(skill_id="s1", min_level=10))
    assert not matches(p, ast.SkillMinLevel(skill_id="s1", min_level=11))
    assert not matches(p, ast.SkillMinLevel(skill_id="missing", min_level=1))
    assert matches(p, ast.AllSkillsMin(requirements={"s1": 10, "s2": 5}))
    assert not matches(p, ast.AllSkillsMin(requirements={"s1": 10, "s2": 6}))


def test_item_any() -> None:
    p = _base()
    assert matches(p, ast.ItemAny(min_rarity="legendary", min_enhancement=10))
    assert matches(p, ast.ItemAny(slot="1", min_enhancement=10))
    assert matches(p, ast.ItemAny(item_type="2_1"))
    assert matches(p, ast.ItemAny(item_type_prefix="4_"))
    assert not matches(p, ast.ItemAny(item_type="99_9"))
    assert not matches(
        p,
        ast.ItemAny(min_rarity="legendary", min_enhancement=99),
    )


def test_items_all_slots_min() -> None:
    p = _base()
    assert matches(
        p,
        ast.ItemsAllSlotsMin(slots=["1", "weapon"], min_enhancement=7),
    )
    assert not matches(
        p,
        ast.ItemsAllSlotsMin(slots=["1", "missing_slot"], min_enhancement=0),
    )


def test_or_not() -> None:
    p = _base()
    assert matches(
        p,
        ast.Or(items=[ast.ClassIs(class_id="warrior"), ast.ClassIs(class_id="sorcerer")]),
    )
    neither = ast.Or(
        items=[ast.ClassIs(class_id="warrior"), ast.ClassIs(class_id="lancer")],
    )
    assert not matches(p, neither)
    assert matches(p, ast.Not(item=ast.ClassIs(class_id="warrior")))
    assert not matches(p, ast.Not(item=ast.ClassIs(class_id="sorcerer")))


def test_pets() -> None:
    p = _base()
    assert matches(p, ast.PetsAnyOf(pet_ids=["pet_x", "pet_a"]))
    assert matches(p, ast.PetsAllOf(pet_ids=["pet_a", "pet_b"]))
    assert not matches(p, ast.PetsAllOf(pet_ids=["pet_a", "pet_c"]))


def test_stones() -> None:
    p = _base()
    assert matches(p, ast.StoneMinTier(min_tier=2, stone_type_ids=None))
    assert matches(p, ast.StonesTypesMinTier(requirements={"8_1": 3, "8_2": 2}))
    assert not matches(p, ast.StonesTypesMinTier(requirements={"8_1": 99}))
    empty_stones = _base().model_copy(update={"stones": []})
    assert not matches(empty_stones, ast.StoneMinTier(min_tier=1, stone_type_ids=None))


def test_stat_keys() -> None:
    p = _base()
    assert matches(p, ast.StatKeyGte(key="Evasión", min_value=50.0))
    assert not matches(p, ast.StatKeyGte(key="Evasión", min_value=51.0))
    assert matches(p, ast.StatKeyGte(key="ataque magico", min_value=100.0))
    assert matches(p, ast.StatKeySuffixGte(key_suffix="magico", min_value=100.0))
    assert not matches(p, ast.StatKeySuffixGte(key_suffix="magico", min_value=200.0))


def test_loader_yaml_branches() -> None:
    yaml_text = """
type: or
items:
  - type: not
    item:
      type: class_is
      class_id: warrior
  - type: power_lte
    max_power: 100
"""
    rule = load_rule_from_yaml_text(yaml_text)
    assert matches(_base(), rule)


def test_unsupported_rule_type_raises() -> None:
    class FakeRule:
        type = "fake"

    with pytest.raises(TypeError, match="no soportado"):
        matches(_base(), FakeRule())  # type: ignore[arg-type]
