from decimal import Decimal
from pathlib import Path

from xdraco_marketer.models.character import (
    CharacterProfile,
    EquippedItem,
    MagicStone,
    PetRef,
    SkillLevel,
)
from xdraco_marketer.models.listing import Currency, Listing
from xdraco_marketer.rules.ast import And, ClassIs, PowerGte, SkillMinLevel
from xdraco_marketer.rules.evaluate import matches
from xdraco_marketer.rules.loader import load_rule_from_yaml_text


def sample_mage() -> CharacterProfile:
    return CharacterProfile(
        class_id="mage",
        power=320_000,
        skills=[
            SkillLevel(skill_id="skill_fireball", level=10),
            SkillLevel(skill_id="skill_meteor", level=10),
        ],
        items=[EquippedItem(slot="weapon", rarity="legendary", enhancement=8)],
        pets=[PetRef(pet_id="pet_dragon_a")],
        stones=[
            MagicStone(stone_type_id="stone_attack", tier=5),
            MagicStone(stone_type_id="stone_crit", tier=4),
        ],
    )


def test_yaml_rule_matches_mage() -> None:
    yaml_text = """
type: and
items:
  - type: class_is
    class_id: mage
  - type: power_gte
    min_power: 300000
  - type: all_skills_min
    requirements:
      skill_fireball: 10
      skill_meteor: 10
  - type: item_any
    min_rarity: legendary
    min_enhancement: 7
  - type: pets_any_of
    pet_ids:
      - pet_dragon_a
      - pet_phoenix_b
  - type: stones_types_min_tier
    requirements:
      stone_attack: 5
      stone_crit: 4
"""
    rule = load_rule_from_yaml_text(yaml_text)
    assert matches(sample_mage(), rule)


def test_example_yaml_skill_rules_or_two_paths() -> None:
    """Carga examples/skill_rules_or_two_paths.yaml y valida ambos caminos del OR."""
    root = Path(__file__).resolve().parents[1]
    text = (root / "examples" / "skill_rules_or_two_paths.yaml").read_text(encoding="utf-8")
    rule = load_rule_from_yaml_text(text)

    meteor = CharacterProfile(
        class_id="sorcerer",
        power=400_000,
        skills=[SkillLevel(skill_id="skill_meteor_storm", level=12)],
        stats={"ataque magico": 1},
    )
    assert matches(meteor, rule)

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

    fail_wrong_class = meteor.model_copy(update={"class_id": "warrior"})
    assert not matches(fail_wrong_class, rule)


def test_example_yaml_skill_rules_and_not_nested() -> None:
    """Carga examples/skill_rules_and_not_nested.yaml: AND + NOT + OR con ítem."""
    root = Path(__file__).resolve().parents[1]
    text = (root / "examples" / "skill_rules_and_not_nested.yaml").read_text(encoding="utf-8")
    rule = load_rule_from_yaml_text(text)

    ok = CharacterProfile(
        class_id="lancer",
        power=450_000,
        skills=[
            SkillLevel(skill_id="skill_main_thrust", level=10),
            SkillLevel(skill_id="skill_dragon_sweep", level=8),
            SkillLevel(skill_id="skill_cosmetic_trap", level=10),
            SkillLevel(skill_id="skill_burst_strike", level=11),
        ],
        items=[],
    )
    assert matches(ok, rule)

    bad_not = ok.model_copy(
        update={
            "skills": [
                SkillLevel(skill_id="skill_main_thrust", level=10),
                SkillLevel(skill_id="skill_dragon_sweep", level=8),
                SkillLevel(skill_id="skill_cosmetic_trap", level=12),
                SkillLevel(skill_id="skill_burst_strike", level=11),
            ]
        }
    )
    assert not matches(bad_not, rule)

    ok_via_gear = CharacterProfile(
        class_id="lancer",
        power=450_000,
        skills=[
            SkillLevel(skill_id="skill_main_thrust", level=10),
            SkillLevel(skill_id="skill_dragon_sweep", level=8),
            SkillLevel(skill_id="skill_cosmetic_trap", level=10),
            SkillLevel(skill_id="skill_burst_strike", level=8),
        ],
        items=[EquippedItem(slot="weapon", rarity="legendary", enhancement=10)],
    )
    assert matches(ok_via_gear, rule)


def test_example_yaml_skill_rules_or_power_stat() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "examples" / "skill_rules_or_and_power_stat.yaml").read_text(encoding="utf-8")
    rule = load_rule_from_yaml_text(text)
    p = CharacterProfile(
        class_id="darkist",
        power=600_000,
        skills=[],
        stats={"defensa fisica": 9000},
    )
    assert matches(p, rule)


def test_and_or_not() -> None:
    p = sample_mage()
    rule = And(
        items=[
            ClassIs(class_id="mage"),
            PowerGte(min_power=300_000),
            SkillMinLevel(skill_id="skill_fireball", min_level=10),
        ]
    )
    assert matches(p, rule)

    bad = p.model_copy(update={"power": 1000})
    assert not matches(bad, rule)


def test_listing_currency_split() -> None:
    from xdraco_marketer.bargains.detector import BargainDetector, BargainSettings
    from xdraco_marketer.rules.loader import load_rule_from_yaml_text

    yaml_text = """
type: and
items:
  - type: class_is
    class_id: mage
  - type: power_gte
    min_power: 300000
"""
    rule = load_rule_from_yaml_text(yaml_text)
    ch = sample_mage()
    listings = [
        Listing(listing_id="1", character=ch, price=Decimal("100"), currency=Currency.WEMIX),
        Listing(listing_id="2", character=ch, price=Decimal("110"), currency=Currency.WEMIX),
        Listing(listing_id="3", character=ch, price=Decimal("105"), currency=Currency.WEMIX),
        Listing(
            listing_id="4",
            character=ch,
            price=Decimal("1"),
            currency=Currency.DRACO,
        ),
    ]
    settings = BargainSettings(
        min_comparables=3,
        median_ratio_max=Decimal("0.95"),
    )
    det = BargainDetector(rule, settings)
    deals = det.find(listings)
    assert len(deals) >= 1
    assert any(d.listing.listing_id == "1" for d in deals)
