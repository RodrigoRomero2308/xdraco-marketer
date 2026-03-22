"""
Tests unitarios del evaluador de reglas (`matches`).

Sirven como red de seguridad al refactorizar `evaluate.py` o ampliar `ast.py`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from decimal import Decimal

from xdraco_marketer.models.character import (
    CharacterProfile,
    EquippedItem,
    MagicStone,
    PetRef,
    SkillLevel,
)
from xdraco_marketer.models.listing import Currency, Listing
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


def test_price_gte_lte_requires_listing() -> None:
    li = Listing(
        listing_id="1",
        character=CharacterProfile(class_id="sorcerer", power=1),
        price=Decimal("150"),
        currency=Currency.WEMIX,
    )
    assert matches(li, ast.PriceGte(min_price=Decimal("100")))
    assert not matches(li, ast.PriceGte(min_price=Decimal("200")))
    assert matches(li, ast.PriceLte(max_price=Decimal("150")))
    assert not matches(li, ast.PriceLte(max_price=Decimal("149")))
    p = _base()
    assert not matches(p, ast.PriceGte(min_price=Decimal("1")))
    assert not matches(p, ast.PriceLte(max_price=Decimal("999999999")))


def test_skill_min_and_all_skills() -> None:
    p = _base()
    assert matches(p, ast.SkillMinLevel(skill_id="s1", min_level=10))
    assert not matches(p, ast.SkillMinLevel(skill_id="s1", min_level=11))
    assert not matches(p, ast.SkillMinLevel(skill_id="missing", min_level=1))
    assert matches(p, ast.AllSkillsMin(requirements={"s1": 10, "s2": 5}))
    assert not matches(p, ast.AllSkillsMin(requirements={"s1": 10, "s2": 6}))


def test_skill_or_two_alternative_builds() -> None:
    """OR: skill principal alta O (dos skills + stat)."""
    rule = ast.And(
        items=[
            ast.ClassIs(class_id="sorcerer"),
            ast.PowerGte(min_power=350_000),
            ast.Or(
                items=[
                    ast.SkillMinLevel(skill_id="skill_meteor_storm", min_level=12),
                    ast.And(
                        items=[
                            ast.AllSkillsMin(
                                requirements={"skill_ice_wall": 9, "skill_fire_nova": 9}
                            ),
                            ast.StatKeyGte(key="Ataque Mágico", min_value=12_000),
                        ]
                    ),
                ]
            ),
        ]
    )
    meteor_only = CharacterProfile(
        class_id="sorcerer",
        power=400_000,
        skills=[SkillLevel(skill_id="skill_meteor_storm", level=12)],
        stats={"ataque magico": 5_000},
    )
    assert matches(meteor_only, rule)

    combo = CharacterProfile(
        class_id="sorcerer",
        power=400_000,
        skills=[
            SkillLevel(skill_id="skill_ice_wall", level=9),
            SkillLevel(skill_id="skill_fire_nova", level=9),
        ],
        stats={"ataque magico": 12_000},
    )
    assert matches(combo, rule)

    low_meteor = meteor_only.model_copy(
        update={"skills": [SkillLevel(skill_id="skill_meteor_storm", level=11)]}
    )
    assert not matches(low_meteor, rule)


def test_skill_not_blocks_overlevel_secondary() -> None:
    """NOT(skill_min) excluye quien tenga la skill secundaria al tope (12)."""
    rule = ast.And(
        items=[
            ast.ClassIs(class_id="lancer"),
            ast.AllSkillsMin(requirements={"main": 10}),
            ast.Not(item=ast.SkillMinLevel(skill_id="secondary", min_level=12)),
        ]
    )
    ok = CharacterProfile(
        class_id="lancer",
        power=100,
        skills=[
            SkillLevel(skill_id="main", level=10),
            SkillLevel(skill_id="secondary", level=11),
        ],
    )
    assert matches(ok, rule)

    bad = ok.model_copy(
        update={"skills": [SkillLevel(skill_id="main", level=10), SkillLevel(skill_id="secondary", level=12)]}
    )
    assert not matches(bad, rule)


def test_skill_or_with_item_and_branch() -> None:
    """OR entre skill alta sola y AND(ítem legendario + skill media)."""
    rule = ast.Or(
        items=[
            ast.SkillMinLevel(skill_id="burst", min_level=11),
            ast.And(
                items=[
                    ast.ItemAny(min_rarity="legendary", min_enhancement=10),
                    ast.SkillMinLevel(skill_id="burst", min_level=8),
                ]
            ),
        ]
    )
    high_burst = CharacterProfile(
        class_id="warrior",
        power=1,
        skills=[SkillLevel(skill_id="burst", level=11)],
        items=[],
    )
    assert matches(high_burst, rule)

    low_burst_gear = CharacterProfile(
        class_id="warrior",
        power=1,
        skills=[SkillLevel(skill_id="burst", level=8)],
        items=[
            EquippedItem(slot="1", item_type="2_1", rarity="legendary", enhancement=10),
        ],
    )
    assert matches(low_burst_gear, rule)

    weak = CharacterProfile(
        class_id="warrior",
        power=1,
        skills=[SkillLevel(skill_id="burst", level=8)],
        items=[
            EquippedItem(slot="1", item_type="2_1", rarity="epic", enhancement=10),
        ],
    )
    assert not matches(weak, rule)


def test_skill_or_power_and_stat_from_yaml() -> None:
    text = """
type: or
items:
  - type: skill_min
    skill_id: skill_signature_move
    min_level: 10
  - type: and
    items:
      - type: power_gte
        min_power: 500000
      - type: stat_key_gte
        key: "Defensa Física"
        min_value: 8000
"""
    rule = load_rule_from_yaml_text(text)
    by_skill = CharacterProfile(
        class_id="taoist",
        power=100_000,
        skills=[SkillLevel(skill_id="skill_signature_move", level=10)],
        stats={},
    )
    assert matches(by_skill, rule)

    by_power_stat = CharacterProfile(
        class_id="taoist",
        power=600_000,
        skills=[],
        stats={"defensa fisica": 9000},
    )
    assert matches(by_power_stat, rule)

    neither = CharacterProfile(
        class_id="taoist",
        power=400_000,
        skills=[SkillLevel(skill_id="skill_signature_move", level=9)],
        stats={"defensa fisica": 1000},
    )
    assert not matches(neither, rule)


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


def test_price_rule_loads_from_yaml() -> None:
    rule = load_rule_from_yaml_text(
        """
type: and
items:
  - type: price_gte
    min_price: 50
  - type: price_lte
    max_price: 500
"""
    )
    li = Listing(
        listing_id="1",
        character=CharacterProfile(class_id="sorcerer", power=1),
        price=Decimal("100"),
        currency=Currency.WEMIX,
    )
    assert matches(li, rule)


def test_yaml_rejects_skill_min_level_out_of_mir4_range() -> None:
    with pytest.raises(ValidationError):
        load_rule_from_yaml_text(
            """
type: skill_min
skill_id: x
min_level: 15
"""
        )


def test_unsupported_rule_type_raises() -> None:
    class FakeRule:
        type = "fake"

    with pytest.raises(TypeError, match="no soportado"):
        matches(_base(), FakeRule())  # type: ignore[arg-type]
