from __future__ import annotations

from typing import Any

from lex.engine import apply_effects, apply_layers
from lex.prefixes import ORDER, color_band, convert, factor, hit_factor, hit_threshold
from lex.agility import AGILITY_CHANNELS, agility_bonus, reflex_free
from lex.strength import melee_damage


def eval_mod(value: int, spec: dict[str, Any]) -> int:
    """Generic (value - sub) / div, optional floor. Spec comes from adapter data."""
    import math
    x = float(value) - float(spec.get("sub") or 0)
    if spec.get("div"):
        x = x / float(spec["div"])
    if spec.get("floor", True):
        return int(math.floor(x))
    return int(x)


def _label_prefix(adapter: dict[str, Any], prefix: str, kind: str = "armor") -> str:
    table = adapter.get("prefixes") or {}
    raw = table.get(prefix)
    if isinstance(raw, dict):
        label = raw.get(kind)
        if label is not None:
            return label
        return raw.get("armor") or raw.get("damage") or ""
    if isinstance(raw, str):
        return raw
    if prefix == "unit":
        return "A" if kind == "armor" else "D"
    return prefix


def _channel_value(v: Any) -> int:
    if isinstance(v, dict):
        return int(v.get("value") or 0)
    return int(v or 0)


def _apply_channels(doc: dict[str, Any]) -> tuple[dict[str, int], set[str]]:
    """Trained channels written on the sheet, then every owned row's mod.channel effects."""
    channels: dict[str, int] = {}
    reflex: set[str] = set()
    for k, v in (doc.get("channels") or {}).items():
        channels[k] = _channel_value(v)
        if isinstance(v, dict) and v.get("reflex"):
            reflex.add(k)
    values, flagged = apply_effects(channels, doc.get("_effects") or [], "mod.channel")
    return {k: int(v) for k, v in values.items()}, reflex | flagged


def _raw_attr(doc: dict[str, Any], key: str) -> int:
    return int((doc.get("attrs") or {}).get(key) or 0)


def _attr_spec(meta: Any, aid: str) -> dict[str, Any]:
    if isinstance(meta, str):
        return {"label": meta, "from": aid}
    return {
        "label": meta.get("label") or aid,
        "from": meta.get("from") or aid,
        "mod": meta.get("mod"),
        "scale": meta.get("scale"),
    }


def scale_attr(value: int, spec: dict[str, Any] | None) -> int:
    """Equal up to spec["above"]; past it, x10 every spec["per"] points, rounded, uncapped."""
    import math
    if not spec or value <= spec["above"]:
        return value
    top = float(spec["above"])
    return int(math.floor(top * 10 ** ((value - top) / float(spec["per"])) + 0.5))


def worn_pieces(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Worn body armor only. Powers are not worn."""
    on = set(doc.get("activated") or [])
    return [
        p for p in (doc.get("armor") or [])
        if p.get("id") in on and (p.get("slot") or "body") == "body"
    ]


def _slot_rank(adapter: dict[str, Any], slot: str | None) -> int:
    order = adapter.get("hit_order") or ["psionic", "spell", "body"]
    key = slot or "body"
    if key in order:
        return order.index(key)
    return len(order)


def activated_layers(doc: dict[str, Any], adapter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Hit-first layers: activated powers that have hits, then worn armor."""
    adapter = adapter or {}
    on = set(doc.get("activated") or [])
    layers: list[dict[str, Any]] = []
    for a in doc.get("abilities") or []:
        if a.get("id") not in on or a.get("total") is None:
            continue
        slot = a.get("slot") or a.get("kind") or "psionic"
        f = hit_factor(a)
        layers.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "total": int(a.get("total") or 0),
            "prefix": a.get("prefix") or "unit",
            "factor": f,
            "threshold": hit_threshold(a),
            "slot": slot,
            "style": color_band(f),
        })
    for p in worn_pieces(doc):
        f = hit_factor(p)
        prefix = p.get("prefix") or "unit"
        layers.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "total": int(p.get("total") or 0),
            "prefix": prefix,
            "factor": f,
            "threshold": hit_threshold(p),
            "slot": p.get("slot") or "body",
            "style": color_band(f),
        })
    layers.sort(key=lambda x: _slot_rank(adapter, x.get("slot")))
    return layers


def worn_armor(doc: dict[str, Any]) -> dict[str, Any] | None:
    pieces = worn_pieces(doc)
    return pieces[0] if pieces else None


def _worn_attr_values(base: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any]:
    """Attributes under any worn layer, then every owned row's mod.attr effects (worn gear only while worn)."""
    layered = apply_layers(base, [p["layer"] for p in worn_pieces(doc) if p.get("layer")])
    values, _ = apply_effects(layered, doc.get("_effects") or [], "mod.attr")
    return values


def _fold_attrs(doc: dict[str, Any], adapter: dict[str, Any]) -> list[dict[str, Any]]:
    raw = doc.get("attrs") or {}
    spec = adapter.get("attrs") or {}
    worn = _worn_attr_values(raw, doc)
    out = []
    for aid, meta in spec.items():
        s = _attr_spec(meta, aid)
        src = s["from"]
        if isinstance(src, list):
            # Derived stat: the average of several attributes, rounded down.
            if not all(k in raw for k in src):
                continue
            base = int(sum(raw[k] for k in src) // len(src))
            val = int(sum(worn.get(k, raw[k]) for k in src) // len(src))
        else:
            if src not in raw and aid not in raw:
                continue
            base = raw.get(src, raw.get(aid, 0))
            val = worn.get(src, worn.get(aid, base))
        if s.get("scale"):
            base, val = scale_attr(base, s["scale"]), scale_attr(val, s["scale"])
        row = {"id": aid, "label": s["label"], "value": val}
        if val != base:
            row["boosted"] = True
        if s.get("mod"):
            row["mod"] = eval_mod(val, s["mod"])
        out.append(row)
    return out


def _bonus_rows(w: dict[str, Any], adapter: dict[str, Any]) -> list[dict[str, Any]]:
    """A weapon's own bonus damage, at its own prefix; Strength and durability do not touch it."""
    rows = []
    for b in w.get("bonus") or []:
        prefix = b.get("prefix") or "unit"
        rows.append({
            "qty": b.get("damage"),
            "unit": _label_prefix(adapter, prefix, "damage"),
            "type": b.get("type") or "",
            "prefix": prefix,
            "high": factor(prefix) >= 100,
        })
    return rows


def _with_strength(doc: dict[str, Any], weapons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hand-to-hand weapons (those with a durability) take the wielder's Strength."""
    strength = _worn_attr_values(doc.get("attrs") or {}, doc).get("strength")
    if strength is None:
        return weapons
    out = []
    for w in weapons:
        if w.get("durability") and w.get("damage"):
            w = dict(w)
            w.update(melee_damage(w["damage"], int(strength), w["durability"]))
        out.append(w)
    return out


def _effective_weapons(doc: dict[str, Any]) -> list[dict[str, Any]]:
    weapons = [dict(w) for w in (doc.get("weapons") or [])]
    index = {w.get("id"): i for i, w in enumerate(weapons)}
    for p in worn_pieces(doc):
        for a in p.get("attacks") or []:
            aid = a.get("id")
            if not aid:
                continue
            if aid in index:
                merged = dict(weapons[index[aid]])
                merged.update(a)
                weapons[index[aid]] = merged
            else:
                index[aid] = len(weapons)
                weapons.append(dict(a))
    return _with_strength(doc, weapons)


def _attack_options(doc: dict[str, Any]) -> list[dict[str, Any]]:
    opts = _effective_weapons(doc)
    seen = {w.get("id") for w in opts}
    for a in doc.get("abilities") or []:
        if a.get("damage") and a.get("id") not in seen:
            opts.append(dict(a))
            seen.add(a.get("id"))
    return opts


def selected_weapon(doc: dict[str, Any]) -> dict[str, Any] | None:
    options = _attack_options(doc)
    aid = doc.get("attack")
    if aid:
        for w in options:
            if w.get("id") == aid:
                return w
    if options:
        return options[0]
    return doc.get("using")


def _gauge_row(
    gid: str,
    label: str,
    kind: str,
    src: dict[str, Any],
    adapter: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "id": gid,
        "label": label,
        "kind": kind,
        "total": int(src.get("total") or 0),
    }
    if kind == "hits":
        prefix = src.get("prefix") or "unit"
        row["prefix"] = prefix
        row["prefix_label"] = _label_prefix(adapter, prefix, "armor")
        row["high"] = factor(prefix) >= 100
    return row


def _fold_gauges(doc: dict[str, Any], adapter: dict[str, Any], attrs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gauge_meta = adapter.get("gauges") or {}
    by_id = {g.get("id"): g for g in (doc.get("gauges") or [])}
    out = []
    for gid, meta in gauge_meta.items():
        if meta.get("from") == "worn":
            continue
        if gid == "anima" or meta.get("from") == "anima":
            continue
        kind = meta.get("kind") or "hits"
        src = by_id.get(gid)
        if not src:
            continue
        out.append(_gauge_row(gid, meta.get("label") or gid, kind, src, adapter))
    return out


def _fold_defense(doc: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]:
    """One hits bar: outer layers first (hit-first), flesh last (innermost)."""
    segs = []
    for p in activated_layers(doc, adapter):
        f = hit_factor(p)
        band = color_band(f)
        segs.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "value": int(p.get("total") or 0),
            "prefix": p.get("prefix") or band,
            "factor": f,
            "threshold": int(p.get("threshold") or hit_threshold(p)),
            "prefix_label": _label_prefix(adapter, p.get("prefix") or band, "armor"),
            "style": band,
        })
    hp = next((g for g in (doc.get("gauges") or []) if g.get("id") == "hit_points"), None)
    if hp and int(hp.get("total") or 0):
        f = hit_factor(hp)
        band = color_band(f)
        segs.append({
            "id": "hit_points",
            "name": "Hit Points",
            "value": int(hp["total"]),
            "prefix": hp.get("prefix") or band,
            "factor": f,
            "threshold": hit_threshold(hp),
            "prefix_label": _label_prefix(adapter, hp.get("prefix") or band, "armor"),
            "style": band,
        })
    armor = None
    if segs:
        armor = {
            "total": sum(s["value"] for s in segs),
            "segments": segs,
            "high": any(factor(s["prefix"]) >= 100 for s in segs),
            "prefix_label": "",
        }
    return {"armor": armor, "person": None}


def _fold_anima(doc: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any] | None:
    src = next((g for g in (doc.get("gauges") or []) if g.get("id") == "anima"), None)
    if not src:
        return None
    n = int(src.get("total") or 0)
    if not n:
        return None
    label = "Anima"
    for gid, meta in (adapter.get("gauges") or {}).items():
        if not isinstance(meta, dict):
            continue
        if gid == "anima" or meta.get("from") == "anima":
            label = meta.get("label") or label
            break
    cur = int(src["current"]) if src.get("current") is not None else n
    return {"label": label, "total": n, "current": cur}


def _sheet_prefixes(adapter: dict[str, Any]) -> list[dict[str, Any]]:
    table = adapter.get("prefixes") or {}
    out = []
    for name in ORDER:
        raw = table.get(name)
        if not isinstance(raw, dict):
            continue
        out.append({
            "id": name,
            "factor": factor(name),
            "armor": raw.get("armor") or "",
            "damage": raw.get("damage") or "",
        })
    return out


def _ch_spec(meta: Any, cid: str) -> dict[str, Any]:
    if isinstance(meta, str):
        return {"label": meta, "from": cid}
    return {
        "label": meta.get("label") or cid,
        "from": meta.get("from") or cid,
        "terms": meta.get("terms"),
        "omit_zero": bool(meta.get("omit_zero")),
    }


def _term_value(
    term: dict[str, Any],
    raw: dict[str, int],
    attrs: list[dict[str, Any]],
    worn: dict[str, Any] | None,
) -> int:
    if "const" in term:
        return int(term["const"])
    if "mod" in term:
        for a in attrs:
            if a["id"] == term["mod"]:
                return int(a.get("mod") or 0)
        return 0
    if "worn" in term:
        return int((worn or {}).get(term["worn"]) or 0)
    if "from" in term:
        return int(raw.get(term["from"]) or 0)
    return 0


def _fold_channels(
    doc: dict[str, Any],
    adapter: dict[str, Any],
    attrs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    spec_map = adapter.get("channels") or {}
    raw, reflex = _apply_channels(doc)
    worn = worn_armor(doc)
    agility = next((a["value"] for a in attrs if a["id"] == "agility"), 0)
    out = []
    for cid, meta in spec_map.items():
        s = _ch_spec(meta, cid)
        if s.get("terms"):
            val = sum(_term_value(t, raw, attrs, worn) for t in s["terms"])
        else:
            val = int(raw.get(s["from"]) or 0)
        if s["from"] in AGILITY_CHANNELS:
            val += agility_bonus(agility)
        if s.get("omit_zero") and val == 0:
            continue
        row = {"id": cid, "label": s["label"], "value": val}
        if cid in reflex:
            row["reflex"] = True
            row["reflex_free"] = reflex_free(agility)
        out.append(row)
    return out


def _fold_person(doc: dict[str, Any], adapter: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("coin") is None:
        return []
    return [{"name": adapter.get("purse") or "Coin", "value": doc.get("coin")}]


def _fold_groups(doc: dict[str, Any], adapter: dict[str, Any]) -> list[dict[str, Any]]:
    names = adapter.get("groups") or {}
    on = set(doc.get("activated") or [])
    attack = doc.get("attack")
    weapons = _effective_weapons(doc)
    if attack is None:
        opts = _attack_options(doc)
        if opts:
            attack = opts[0].get("id")

    body_on = bool(worn_pieces(doc))
    armor_rows = [{
        "id": "",
        "name": "Unarmored",
        "on": not body_on,
        "select": "activated",
        "slot": "body",
    }]
    for p in doc.get("armor") or []:
        prefix = p.get("prefix") or "unit"
        armor_rows.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "qty": p.get("total"),
            "unit": _label_prefix(adapter, prefix, "armor"),
            "on": p.get("id") in on,
            "select": "activated",
            "slot": p.get("slot") or "body",
            "prefix": prefix,
            "high": factor(prefix) >= 100,
        })

    weapon_rows = []
    for w in weapons:
        prefix = w.get("prefix") or "unit"
        weapon_rows.append({
            "id": w.get("id"),
            "name": w.get("name"),
            "qty": w.get("damage"),
            "unit": _label_prefix(adapter, prefix, "damage"),
            "on": w.get("id") == attack,
            "select": "attack",
            "prefix": prefix,
            "high": factor(prefix) >= 100,
            "destroyed": bool(w.get("destroyed")),
            "bonus": _bonus_rows(w, adapter),
        })

    by_kind: dict[str, list[dict[str, Any]]] = {}
    skill_rows: list[dict[str, Any]] = []
    for a in doc.get("abilities") or []:
        kind = a.get("kind")
        if not kind:
            skill_rows.append({"id": a.get("id"), "name": a.get("name"), "qty": a.get("qty") or ""})
            continue
        prefix = a.get("prefix") or "unit"
        if a.get("total") is not None:
            row = {
                "id": a.get("id"),
                "name": a.get("name"),
                "qty": a.get("total"),
                "unit": _label_prefix(adapter, prefix, "armor"),
                "on": a.get("id") in on,
                "select": "activated",
                "slot": a.get("slot") or kind,
                "prefix": prefix,
                "high": factor(prefix) >= 100,
            }
        else:
            row = {
                "id": a.get("id"),
                "name": a.get("name"),
                "qty": a.get("damage") or a.get("qty") or "",
                "unit": _label_prefix(adapter, prefix, "damage") if a.get("damage") else "",
                "on": a.get("id") == attack,
                "select": "attack" if a.get("damage") else "",
                "prefix": prefix,
                "high": factor(prefix) >= 100 if a.get("damage") else False,
            }
        by_kind.setdefault(kind, []).append(row)

    groups = []
    if doc.get("armor") is not None or armor_rows:
        groups.append({
            "id": "armor",
            "name": names.get("armor") or "Armor",
            "pane": "armor",
            "select": "activated",
            "rows": armor_rows,
        })
    if weapon_rows:
        groups.append({
            "id": "weapons",
            "name": names.get("weapons") or "Weapons",
            "pane": "weapon",
            "select": "attack",
            "rows": weapon_rows,
        })
    for kind, rows in by_kind.items():
        groups.append({
            "id": kind,
            "name": names.get(kind) or kind,
            "pane": "weapon",
            "select": "mixed",
            "rows": rows,
        })
    if skill_rows:
        groups.append({
            "id": "abilities",
            "name": names.get("abilities") or "Abilities",
            "pane": "weapon",
            "rows": skill_rows,
        })
    return groups


def fold(
    doc: dict[str, Any],
    adapter: dict[str, Any],
    *,
    occupation: dict[str, Any] | None = None,
    species: dict[str, Any] | None = None,
    portrait: str | None = None,
) -> dict[str, Any]:
    """Render a resolved character (owned rows merged, effects in doc["_effects"]) in one adapter's sheet language."""
    attrs = _fold_attrs(doc, adapter)
    gauges = _fold_gauges(doc, adapter, attrs)
    defense = _fold_defense(doc, adapter)
    channels = _fold_channels(doc, adapter, attrs)
    groups = _fold_groups(doc, adapter)
    person = _fold_person(doc, adapter)
    anima = _fold_anima(doc, adapter)

    using = None
    src = selected_weapon(doc)
    if src:
        prefix = src.get("prefix") or "unit"
        using = {
            "id": src.get("id"),
            "name": src.get("name") or "Punch",
            "damage": src.get("damage"),
            "prefix": prefix,
            "prefix_label": _label_prefix(adapter, prefix, "damage"),
            "high": factor(prefix) >= 100,
            "destroyed": bool(src.get("destroyed")),
            "bonus": _bonus_rows(src, adapter),
        }

    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "npc": bool(doc.get("npc")),
        "level": int(doc.get("level") or 1),
        "pack": doc.get("pack"),
        "adapter": adapter.get("id"),
        "occupation": occupation,
        "species": species,
        "attrs": attrs,
        "gauges": gauges,
        "defense": defense,
        "channels": channels,
        "using": using,
        "groups": groups,
        "person": person,
        "anima": anima,
        "prefixes": _sheet_prefixes(adapter),
        "activated": list(doc.get("activated") or []),
        "attack": doc.get("attack") or (using or {}).get("id") or "",
        "portrait": portrait,
    }


def harm_on_layer(
    amount: int,
    attack_prefix: str,
    layer_prefix: str,
    attack_scale: float | None = None,
    layer_scale: float | None = None,
    threshold: int = 1,
) -> int:
    return convert(amount, attack_prefix, layer_prefix, attack_scale, layer_scale, threshold)
