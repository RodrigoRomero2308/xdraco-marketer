from xdraco_marketer.stat_labels import normalize_stat_label


def test_normalize_stat_label_accents_and_case() -> None:
    assert normalize_stat_label("Ataque Mágico") == normalize_stat_label("ataque magico")
    assert normalize_stat_label("  Defensa   Física  ") == "defensa fisica"
    assert normalize_stat_label("Evasión") == "evasion"
