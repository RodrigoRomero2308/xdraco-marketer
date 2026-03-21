"""Constantes alineadas con la API de listado (class numérico)."""

# list/data-infered.txt + respuesta real de /nft/lists
CLASS_ID_TO_SLUG: dict[int, str] = {
    1: "warrior",
    2: "sorcerer",
    3: "taoist",
    4: "arbalist",
    5: "lancer",
    6: "darkist",
    7: "lionheart",
}


def grade_to_rarity_label(grade: str | int) -> str:
    """Grade API → etiqueta estable para reglas (min_rarity)."""

    g = str(grade).strip()
    return {
        "5": "legendary",
        "4": "epic",
        "3": "rare",
        "2": "unusual",
        "1": "common",
    }.get(g, g)
