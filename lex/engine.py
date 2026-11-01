"""Generic effects/constraints engine. Reads rows; never names a specific ability, item, species, or occupation."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable

# docs/universal-system.md, Attributes: "Lex has seven core attributes".
ATTRIBUTES = ("strength", "agility", "endurance", "speed", "intellect", "willpower", "appearance")
# Same section: "Strength and Speed have a physical measure"; the other five have none.
PHYSICAL_ATTRIBUTES = ("strength", "speed")
VEHICLE = "vehicle"

OWNER_TABLES = {"species": "species", "occupation": "occupations", "ability": "abilities", "item": "items"}


def apply_effects(
    base: dict[str, float], effects: Iterable[dict[str, Any]], verb: str
) -> tuple[dict[str, float], set[str]]:
    """Apply every effect row with this verb; they all add to their target.

    Returns the new values and the targets an effect flagged as reflex.
    """
    values = dict(base)
    flagged: set[str] = set()
    for e in effects:
        if e.get("verb") != verb:
            continue
        if e.get("reflex"):
            flagged.add(e["target"])
        if e.get("value") is not None:
            values[e["target"]] = values.get(e["target"], 0) + e["value"]
    return {k: _num(v) for k, v in values.items()}, flagged


def apply_worn_vehicles(base: dict[str, float], vehicles: Iterable[dict[str, float]]) -> dict[str, float]:
    """A worn vehicle (power armor, robot armor) replaces the wearer's physical attributes with its own."""
    values = dict(base)
    for attrs in vehicles:
        for k, v in attrs.items():
            if k in PHYSICAL_ATTRIBUTES:
                values[k] = v
    return values


def worn_vehicle_attributes(
    base: dict[str, float], vehicles: list[dict[str, Any]], effects: Iterable[dict[str, Any]]
) -> dict[str, float]:
    """Attributes for a wearer inside worn vehicles (power armor, robot armor).

    The vehicles' physical attributes replace the wearer's entirely: only effects that belong to a worn
    vehicle apply to them. Every effect still applies to the other attributes.
    """
    effects = list(effects)
    replaced = {k for v in vehicles for k in (v.get("attrs") or {}) if k in PHYSICAL_ATTRIBUTES}
    if not replaced:
        values, _ = apply_effects(base, effects, "mod.attr")
        return values
    worn = {(v.get("pack"), v.get("id")) for v in vehicles}
    own = [e for e in effects
           if (e.get("source") or {}).get("type") == "item"
           and ((e.get("source") or {}).get("pack"), (e.get("source") or {}).get("id")) in worn]
    rest, _ = apply_effects(base, [e for e in effects if e.get("target") not in replaced], "mod.attr")
    inside, _ = apply_effects(apply_worn_vehicles(base, [v.get("attrs") or {} for v in vehicles]),
                              [e for e in own if e.get("target") in replaced], "mod.attr")
    return {**rest, **{k: inside[k] for k in replaced}}


def vehicle_attributes(conn: sqlite3.Connection, pack: str, item_id: str) -> dict[str, float]:
    """A vehicle's own attribute values, only those that apply to it."""
    return {
        r["attr"]: _num(r["value"])
        for r in conn.execute(
            "SELECT attr, value FROM item_attrs WHERE item_pack=? AND item_id=? ORDER BY position", (pack, item_id)
        )
    }


def _num(v: float) -> float | int:
    return int(v) if isinstance(v, float) and v.is_integer() else v


def owner_effects(
    conn: sqlite3.Connection, owner_type: str, pack: str, oid: str, level: int | None = None
) -> list[dict[str, Any]]:
    """Effect rows of an owner itself (level None) or of one of its levels."""
    out = []
    for r in conn.execute(
        "SELECT * FROM effects WHERE owner_type=? AND owner_pack=? AND owner_id=? AND level IS ? ORDER BY position",
        (owner_type, pack, oid, level),
    ):
        e = {"verb": r["verb"], "target": r["target"], "value": _num(r["value"]) if r["value"] is not None else None}
        e.update({k: v for k, v in json.loads(r["data"]).items() if not k.startswith("_")})
        e["source"] = {"type": owner_type, "pack": pack, "id": oid}
        if level is not None:
            e["source"]["level"] = level
        out.append(e)
    return out


def owned_abilities(conn: sqlite3.Connection, cid: str) -> set[tuple[str, str]]:
    return {
        (r["ability_pack"], r["ability_id"])
        for r in conn.execute("SELECT ability_pack, ability_id FROM character_abilities WHERE character_id=?", (cid,))
    }


def occupation_progress(conn: sqlite3.Connection, cid: str, owned: set[tuple[str, str]] | None = None) -> list[dict[str, Any]]:
    """For every occupation with sets: how many ordered sets are met. A later set counts only when every earlier one is met."""
    owned = owned_abilities(conn, cid) if owned is None else owned
    sets: dict[tuple[str, str], dict[int, list[tuple[str, str]]]] = {}
    for r in conn.execute("SELECT * FROM occupation_sets ORDER BY occupation_pack, occupation_id, set_index, position"):
        key = (r["occupation_pack"], r["occupation_id"])
        sets.setdefault(key, {}).setdefault(r["set_index"], []).append((r["ability_pack"], r["ability_id"]))
    out = []
    for (pack, oid), by_index in sets.items():
        met = 0
        for idx in sorted(by_index):
            if not all(a in owned for a in by_index[idx]):
                break
            met = idx
        name = conn.execute("SELECT name FROM occupations WHERE pack=? AND id=?", (pack, oid)).fetchone()
        out.append({"pack": pack, "id": oid, "name": name["name"] if name else oid,
                    "sets_met": met, "sets": len(by_index)})
    out.sort(key=lambda o: (-o["sets_met"], -o["sets_met"] / max(o["sets"], 1), o["name"]))
    return out


def unmet(
    conn: sqlite3.Connection,
    cid: str,
    owner_type: str,
    pack: str,
    oid: str,
    owned: set[tuple[str, str]] | None = None,
) -> list[str]:
    """Constraint rows on this owner that the character does not meet, plus a campaign ban. Empty means allowed."""
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    owned = owned_abilities(conn, cid) if owned is None else owned
    progress = None
    problems = []
    for r in conn.execute(
        "SELECT * FROM requirements WHERE owner_type=? AND owner_pack=? AND owner_id=? ORDER BY position",
        (owner_type, pack, oid),
    ):
        ref = (r["ref_pack"], r["ref_id"])
        kind = r["kind"]
        if kind == "species":
            if (ch["species_pack"], ch["species_id"]) != ref:
                problems.append(f"needs species {r['ref_pack']}:{r['ref_id']}")
        elif kind == "ability":
            if ref not in owned:
                problems.append(f"needs ability {r['ref_pack']}:{r['ref_id']}")
        elif kind == "occupation_set":
            if progress is None:
                progress = {(o["pack"], o["id"]): o["sets_met"] for o in occupation_progress(conn, cid, owned)}
            if progress.get(ref, 0) < (r["value"] or 0):
                problems.append(f"needs set {r['value']} of occupation {r['ref_pack']}:{r['ref_id']}")
        elif kind == "list":
            if owner_type == "ability" and not conn.execute(
                "SELECT 1 FROM character_list WHERE character_id=? AND ability_pack=? AND ability_id=?",
                (cid, pack, oid),
            ).fetchone():
                problems.append("not on this character's list")
    if owner_type == "ability" and ch["campaign_id"] is not None and conn.execute(
        "SELECT 1 FROM campaign_forbidden WHERE campaign_id=? AND ability_pack=? AND ability_id=?",
        (ch["campaign_id"], pack, oid),
    ).fetchone():
        problems.append("forbidden by the campaign")
    return problems


def character_effects(conn: sqlite3.Connection, cid: str) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[str]]]:
    """Every effect row the character's owned rows contribute.

    Species and occupation always; an owned ability unless it breaks a constraint;
    an item only while it is switched on (worn). Returns the effects and the abilities that stopped working.
    """
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    effects: list[dict[str, Any]] = []
    if ch["species_id"]:
        effects += owner_effects(conn, "species", ch["species_pack"], ch["species_id"])
    if ch["occupation_id"]:
        effects += owner_effects(conn, "occupation", ch["occupation_pack"], ch["occupation_id"])
    owned = owned_abilities(conn, cid)
    broken: dict[tuple[str, str], list[str]] = {}
    for r in conn.execute("SELECT * FROM character_abilities WHERE character_id=? ORDER BY position", (cid,)):
        key = (r["ability_pack"], r["ability_id"])
        problems = unmet(conn, cid, "ability", *key, owned=owned)
        if problems:
            broken[key] = problems
            continue
        effects += owner_effects(conn, "ability", *key)
        # Owning level n: the effect rows of levels 1..n stack.
        for lv in range(1, (r["level"] or 0) + 1):
            effects += owner_effects(conn, "ability", *key, level=lv)
    active = {r["ref"] for r in conn.execute("SELECT ref FROM character_active WHERE character_id=?", (cid,))}
    for r in conn.execute("SELECT * FROM character_items WHERE character_id=? ORDER BY position", (cid,)):
        if r["item_id"] in active:
            effects += owner_effects(conn, "item", r["item_pack"], r["item_id"])
    return effects, broken


class Refused(Exception):
    pass


def ability_levels(conn: sqlite3.Connection, pack: str, aid: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM ability_levels WHERE ability_pack=? AND ability_id=? ORDER BY level", (pack, aid)
    ).fetchall()


def buy_ability(
    conn: sqlite3.Connection, cid: str, pack: str, aid: str, *, grant: bool = False, level: int | None = None
) -> int:
    """Buy an ability, or its next level, with unspent experience inside its constraints.

    An ability with levels is bought one level at a time, starting at its first; levels cannot be skipped.
    `level`, when given, must be that next level. grant=True is the GM adding it outright.
    Returns the unspent experience left.
    """
    ab = conn.execute("SELECT * FROM abilities WHERE pack=? AND id=?", (pack, aid)).fetchone()
    if ab is None:
        raise KeyError(f"{pack}:{aid}")
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    owned = conn.execute(
        "SELECT * FROM character_abilities WHERE character_id=? AND ability_pack=? AND ability_id=?", (cid, pack, aid)
    ).fetchone()
    levels = ability_levels(conn, pack, aid)
    if levels:
        nxt = (owned["level"] or 0) + 1 if owned else 1
        if nxt > len(levels):
            raise Refused("already at the top level")
        if level is not None and level != nxt:
            raise Refused(f"buy level {nxt} ({levels[nxt - 1]['name']}) first; levels cannot be skipped")
        price = levels[nxt - 1]["price"]
    else:
        if owned:
            raise Refused("already owned")
        if level is not None:
            raise Refused("this ability has no levels")
        nxt, price = None, ab["price"]
    left = ch["xp_unspent"] or 0
    if not grant:
        problems = unmet(conn, cid, "ability", pack, aid)
        if problems:
            raise Refused("; ".join(problems))
        if price is None:
            raise Refused("the pack sets no price for this " + ("level" if levels else "ability"))
        if left < price:
            raise Refused(f"needs {price} experience, {left} unspent")
        left -= price
    with conn:
        if owned:
            conn.execute("UPDATE character_abilities SET level=? WHERE character_id=? AND ability_pack=? AND ability_id=?",
                         (nxt, cid, pack, aid))
        else:
            pos = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM character_abilities WHERE character_id=?", (cid,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO character_abilities (character_id, position, ability_pack, ability_id, data, level)"
                " VALUES (?,?,?,?,'{}',?)", (cid, pos, pack, aid, nxt))
        if not grant:
            conn.execute("UPDATE characters SET xp_unspent=? WHERE id=?", (left, cid))
    return left
