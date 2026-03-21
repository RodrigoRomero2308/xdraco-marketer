"""Respuesta de GET /nft/character/summary → CharacterProfile (equipo, pets, piedras).

Solo se usan campos de datos de juego (itemType, grade, itemIdx, …), no itemPath/iconos.
"""

from __future__ import annotations

from typing import Any

from xdraco_marketer.mir4_api.constants import CLASS_ID_TO_SLUG, grade_to_rarity_label
from xdraco_marketer.models.character import CharacterProfile, EquippedItem, MagicStone, PetRef


def _is_magic_stone(item_type: str) -> bool:
    return item_type.startswith("8_")


def _is_pet_orb(item_type: str) -> bool:
    return item_type.startswith("23_") or item_type.startswith("28_")


def summary_data_to_profile(data: dict[str, Any]) -> CharacterProfile:
    """
    Usa data['character'], data['equipItem'].
    Las skills no vienen en summary en las muestras actuales: skills=[] hasta otro endpoint.
    """

    ch = data.get("character") or {}
    class_raw = ch.get("class", "0")
    try:
        cid = int(str(class_raw))
    except ValueError:
        cid = 0
    slug = CLASS_ID_TO_SLUG.get(cid, str(class_raw))

    power = int(str(ch.get("powerScore", "0")) or 0)

    items: list[EquippedItem] = []
    stones: list[MagicStone] = []
    pets: list[PetRef] = []

    equip = data.get("equipItem") or {}
    if isinstance(equip, dict):
        for slot_key, row in equip.items():
            if not isinstance(row, dict):
                continue
            itype = str(row.get("itemType") or "")
            if not itype:
                continue
            grade = str(row.get("grade") or "")
            enh = int(str(row.get("enhance") or "0"))
            tier = int(str(row.get("tier") or "0"))
            item_idx = str(row.get("itemIdx") or "")
            name = row.get("itemName")

            if _is_magic_stone(itype):
                stones.append(
                    MagicStone(
                        stone_type_id=itype,
                        tier=tier,
                    )
                )
            elif _is_pet_orb(itype):
                pets.append(PetRef(pet_id=item_idx, name=str(name) if name else None))
            else:
                items.append(
                    EquippedItem(
                        item_id=item_idx,
                        name=str(name) if name else None,
                        slot=str(slot_key),
                        item_type=itype,
                        rarity=grade_to_rarity_label(grade),
                        enhancement=enh,
                    )
                )

    return CharacterProfile(
        class_id=slug,
        power=power,
        skills=[],  # rellenar si aparece otro campo o endpoint
        items=items,
        pets=pets,
        stones=stones,
    )
