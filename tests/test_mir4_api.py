from xdraco_marketer.mir4_api import (
    list_row_to_profile_stub,
    parse_stat_value,
    stats_response_to_stat_map,
    summary_data_to_profile,
    with_stats,
)
from xdraco_marketer.models.character import CharacterProfile
from xdraco_marketer.rules.ast import StatKeyGte, StatKeySuffixGte
from xdraco_marketer.rules.evaluate import matches


def test_parse_stat_value() -> None:
    assert parse_stat_value("204,754") == 204754.0
    assert parse_stat_value("1041.1%") == 1041.1
    assert parse_stat_value(123) == 123.0


def test_stats_response_uses_normalized_stat_names() -> None:
    rows = [
        {
            "statName": "Ataque Mágico",
            "statValue": "1,000",
            "iconPath": "https://host/path/Ico_Status_ADDMagicDamage.png",  # la API lo manda; el código lo ignora
        }
    ]
    m = stats_response_to_stat_map(rows)
    assert m["ataque magico"] == 1000.0


def test_list_row_stub() -> None:
    row = {
        "class": 2,
        "powerScore": 340158,
        "stat": [{"statName": "Ataque Mágico", "statValue": 10611}],
    }
    p = list_row_to_profile_stub(row)
    assert p.class_id == "sorcerer"
    assert p.power == 340158
    assert p.stats["ataque magico"] == 10611.0


def test_stat_rules() -> None:
    p = CharacterProfile(
        class_id="sorcerer",
        power=300_000,
        stats={
            "ataque magico": 10000.0,
        },
    )
    assert matches(p, StatKeyGte(key="Ataque Mágico", min_value=9000.0))
    assert matches(p, StatKeySuffixGte(key_suffix="magico", min_value=9000.0))


def test_summary_equip_split() -> None:
    sample = {
        "character": {
            "class": "1",
            "powerScore": "534935",
        },
        "equipItem": {
            "1": {
                "itemIdx": "200201029",
                "enhance": "15",
                "grade": "5",
                "tier": "4",
                "itemType": "2_1",
                "itemName": "Weapon",
            },
            "40": {
                "itemIdx": "801200005",
                "enhance": "0",
                "grade": "5",
                "tier": "1",
                "itemType": "8_1",
                "itemName": "Piedra",
            },
        },
    }
    p = summary_data_to_profile(sample)
    assert p.class_id == "warrior"
    assert len([x for x in p.items if x.item_type == "2_1"]) >= 1
    assert any(s.stone_type_id.startswith("8_") for s in p.stones)
    full = with_stats(p, {"ataque magico": 1.0})
    assert "ataque magico" in full.stats

