"""Evaluación de reglas sobre CharacterProfile."""

from __future__ import annotations

from xdraco_marketer.models.character import CharacterProfile
from xdraco_marketer.rules import ast
from xdraco_marketer.stat_labels import normalize_stat_label


def _norm(s: str) -> str:
    return s.strip().lower()


def _rarity_ok(item_rarity: str | None, min_rarity: str | None) -> bool:
    if min_rarity is None:
        return True
    if item_rarity is None:
        return False
    return _norm(item_rarity) == _norm(min_rarity)


def matches(profile: CharacterProfile, rule: ast.RuleExpr) -> bool:
    r = rule
    if isinstance(r, ast.And):
        return all(matches(profile, x) for x in r.items)
    if isinstance(r, ast.Or):
        return any(matches(profile, x) for x in r.items)
    if isinstance(r, ast.Not):
        return not matches(profile, r.item)
    if isinstance(r, ast.ClassIs):
        return _norm(profile.class_id) == _norm(r.class_id)
    if isinstance(r, ast.PowerGte):
        return profile.power >= r.min_power
    if isinstance(r, ast.PowerLte):
        return profile.power <= r.max_power
    if isinstance(r, ast.SkillMinLevel):
        lv = profile.skill_level(r.skill_id)
        return lv is not None and lv >= r.min_level
    if isinstance(r, ast.AllSkillsMin):
        for sid, need in r.requirements.items():
            lv = profile.skill_level(sid)
            if lv is None or lv < need:
                return False
        return True
    if isinstance(r, ast.ItemAny):
        for it in profile.items:
            if r.slot is not None and it.slot is not None:
                if _norm(it.slot) != _norm(r.slot):
                    continue
            elif r.slot is not None:
                continue
            if r.item_type is not None:
                if it.item_type is None or _norm(it.item_type) != _norm(r.item_type):
                    continue
            if r.item_type_prefix is not None:
                pref = r.item_type_prefix.strip()
                if not it.item_type or not it.item_type.startswith(pref):
                    continue
            if r.min_rarity is not None and not _rarity_ok(it.rarity, r.min_rarity):
                continue
            if r.min_enhancement is not None and it.enhancement < r.min_enhancement:
                continue
            return True
        return False
    if isinstance(r, ast.ItemsAllSlotsMin):
        by_slot: dict[str, list] = {}
        for it in profile.items:
            if it.slot:
                by_slot.setdefault(_norm(it.slot), []).append(it)
        for slot in r.slots:
            key = _norm(slot)
            candidates = by_slot.get(key, [])
            ok = False
            for it in candidates:
                if r.min_rarity is not None and not _rarity_ok(it.rarity, r.min_rarity):
                    continue
                if it.enhancement >= r.min_enhancement:
                    ok = True
                    break
            if not ok:
                return False
        return True
    if isinstance(r, ast.PetsAnyOf):
        have = {_norm(p.pet_id) for p in profile.pets}
        return any(_norm(pid) in have for pid in r.pet_ids)
    if isinstance(r, ast.PetsAllOf):
        have = {_norm(p.pet_id) for p in profile.pets}
        return all(_norm(pid) in have for pid in r.pet_ids)
    if isinstance(r, ast.StoneMinTier):
        types = r.stone_type_ids
        stones = profile.stones
        if not stones:
            return False
        if types is None or len(types) == 0:
            return all(s.tier >= r.min_tier for s in stones)
        need = {_norm(t) for t in types}
        by_type: dict[str, list] = {}
        for s in stones:
            by_type.setdefault(_norm(s.stone_type_id), []).append(s)
        for tid in need:
            arr = by_type.get(tid)
            if not arr or max(x.tier for x in arr) < r.min_tier:
                return False
        return True
    if isinstance(r, ast.StonesTypesMinTier):
        by_type = {_norm(s.stone_type_id): s.tier for s in profile.stones}
        for tid, need_tier in r.requirements.items():
            t = _norm(tid)
            if t not in by_type or by_type[t] < need_tier:
                return False
        return True
    if isinstance(r, ast.StatKeyGte):
        want = normalize_stat_label(r.key)
        for pk, val in profile.stats.items():
            if normalize_stat_label(pk) == want and val >= r.min_value:
                return True
        return False
    if isinstance(r, ast.StatKeySuffixGte):
        suf = normalize_stat_label(r.key_suffix)
        if not suf:
            return False
        for pk, val in profile.stats.items():
            nk = normalize_stat_label(pk)
            if nk.endswith(suf) and val >= r.min_value:
                return True
        return False
    raise TypeError(f"Tipo de regla no soportado: {type(r)!r}")
