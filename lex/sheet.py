"""Sheet resolution from sqlite: the character's owned rows, merged and evaluated, rendered by an adapter."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from lex import engine
from lex.fold import _attack_options, fold, selected_weapon
from lex.packs import character_doc

DEFAULT_ADAPTER = "universal"


def list_adapters(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = []
    for r in conn.execute("SELECT pack, data FROM adapters ORDER BY pack"):
        a = json.loads(r["data"])
        if a.get("view"):
            rows.append({"id": a.get("id") or r["pack"], "name": a.get("name") or r["pack"]})
    return rows


def load_adapter(conn: sqlite3.Connection, adapter_id: str | None) -> dict[str, Any]:
    for aid in (adapter_id, DEFAULT_ADAPTER):
        r = conn.execute("SELECT data FROM adapters WHERE pack=?", (aid or "",)).fetchone()
        if r:
            a = json.loads(r["data"])
            a.setdefault("id", aid)
            return a
    return {"id": DEFAULT_ADAPTER}


def _merged(owned: sqlite3.Row, catalog: sqlite3.Row | None, ref_pack: str, ref_id: str) -> dict[str, Any]:
    row = json.loads(catalog["data"]) if catalog else {"id": ref_id, "name": ref_id}
    row.update(json.loads(owned["data"]))
    row["id"] = ref_id
    row["pack"] = ref_pack
    return row


def resolved_doc(conn: sqlite3.Connection, cid: str, attack: str | None = None) -> dict[str, Any]:
    """The character with every owned row merged in (definition, then this character's own values).

    `attack` picks the attack to use (default: the one chosen on the sheet). The effects in doc["_effects"] are
    those that apply with that attack: an item's own rows only while it is worn or used, and a conditional row
    ("when") only when the used attack (using) or a worn item (wearing) has one of its categories.
    """
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    doc = character_doc(conn, cid)
    doc["pack"] = ch["pack"]
    armor: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    gear: list[dict[str, Any]] = []
    vehicles: list[dict[str, Any]] = []
    for o in conn.execute("SELECT * FROM character_items WHERE character_id=? ORDER BY position", (cid,)):
        cat = conn.execute("SELECT * FROM items WHERE pack=? AND id=?", (o["item_pack"], o["item_id"])).fetchone()
        row = _merged(o, cat, o["item_pack"], o["item_id"])
        kind = row.get("kind")
        if kind == engine.VEHICLE:
            row["attrs"] = engine.vehicle_attributes(conn, o["item_pack"], o["item_id"])
            # Worn vehicles (power armor, robot armor) take a slot like armor; others are not worn.
            (armor if row.get("slot") else vehicles).append(row)
        else:
            (armor if kind == "armor" else weapons if kind == "weapon" else gear).append(row)
    effects, broken = engine.character_effects(conn, cid)
    abilities = []
    for o in conn.execute("SELECT * FROM character_abilities WHERE character_id=? ORDER BY position", (cid,)):
        cat = conn.execute("SELECT * FROM abilities WHERE pack=? AND id=?", (o["ability_pack"], o["ability_id"])).fetchone()
        row = _merged(o, cat, o["ability_pack"], o["ability_id"])
        if o["level"] is not None:
            lv = conn.execute("SELECT name FROM ability_levels WHERE ability_pack=? AND ability_id=? AND level=?",
                              (o["ability_pack"], o["ability_id"], o["level"])).fetchone()
            row["level"] = o["level"]
            row["level_name"] = lv["name"] if lv else str(o["level"])
        problems = broken.get((o["ability_pack"], o["ability_id"]))
        if problems:
            row["inactive"] = problems
        abilities.append(row)
    doc.pop("items", None)
    doc["armor"] = armor
    doc["weapons"] = weapons
    doc["gear"] = gear
    doc["vehicles"] = vehicles
    doc["abilities"] = abilities
    if attack:
        doc["attack"] = attack
    situate(conn, doc, effects)
    return doc


def situate(conn: sqlite3.Connection, doc: dict[str, Any], effects: list[dict[str, Any]]) -> None:
    """Apply the one generic rule for conditional effects to a resolved character.

    using: the categories of the attack picked (its item row, or its own row for an attack built into armor
    or an ability). wearing: the categories of every switched-on item and vehicle. The picked item's own
    effect rows join while it is used.
    """
    doc["_effects"] = [e for e in effects if not e.get("when")]
    weapon = selected_weapon(doc) or {}
    on = set(doc.get("activated") or [])
    rows = (doc.get("armor") or []) + (doc.get("weapons") or []) + (doc.get("gear") or []) + (doc.get("vehicles") or [])
    worn = [r for r in rows if r.get("id") in on]
    used = next(((r["pack"], r["id"]) for r in doc.get("weapons") or []
                 if r.get("id") == weapon.get("id") and r.get("pack") == weapon.get("pack")), None)
    if used and used[1] not in on:
        effects = effects + engine.owner_effects(conn, "item", *used)
    using = engine.row_categories(weapon)
    wearing: set[str] = set()
    for r in worn:
        wearing |= engine.row_categories(r)
    applied, conditional = engine.situational_effects(effects, using, wearing)
    doc["_effects"] = applied
    doc["_conditional"] = conditional
    doc["_using"] = sorted(using)
    doc["_wearing"] = sorted(wearing)
    doc["_used_item"] = used
    doc["_worn_items"] = sorted({(r.get("pack"), r["id"]) for r in worn if r.get("pack")})


def _named(conn, table: str, pack: str | None, rid: str | None) -> dict[str, Any] | None:
    if not rid:
        return None
    r = conn.execute(f"SELECT name FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchone()
    return {"id": rid, "pack": pack, "name": r["name"] if r else rid}


def bonuses(conn: sqlite3.Connection, doc: dict[str, Any], adapter: dict[str, Any]) -> dict[str, Any]:
    """Always-on bonuses and conditional ones, in plain words, each with where it comes from."""
    from lex import library  # the library's wording; imported here because it imports this module

    labels = library.Labels(conn, adapter.get("id"))

    def row(e: dict[str, Any], held: str = "") -> dict[str, Any]:
        src = e.get("source") or {}
        table = library.OWNER_TABLE.get(src.get("type"), "")
        name = conn.execute(f"SELECT name FROM {table} WHERE pack=? AND id=?", (src.get("pack"), src.get("id"))
                            ).fetchone() if table else None
        extra = {k: v for k, v in e.items() if k not in ("verb", "target", "value", "source", "when", "met")}
        text = library.effect_text(labels, e["verb"], e["target"], e.get("value"), extra, e.get("when"))
        out = {"text": f"{text} {held}" if held else text,
               "verb": e["verb"], "target": e["target"], "value": e.get("value"),
               "from": {"table": table, "pack": src.get("pack"), "id": src.get("id"),
                        "name": name["name"] if name else src.get("id")}}
        if e.get("when") or held:
            if e.get("when"):
                out["when"] = e["when"]
            out["met"] = bool(e.get("met"))
        return out

    def from_item(e: dict[str, Any]) -> bool:
        return (e.get("source") or {}).get("type") == "item"

    # An item's own rows apply only while it is used (the attack picked) or worn; list every owned item's rows.
    attack_ids = {w.get("id") for w in _attack_options(doc)}
    used, worn = doc.get("_used_item"), set(doc.get("_worn_items") or [])
    held_rows = []
    for r in (doc.get("weapons") or []) + (doc.get("armor") or []) + (doc.get("gear") or []) + (doc.get("vehicles") or []):
        key = (r.get("pack"), r.get("id"))
        on = key == used or key in worn
        held = (f"when using {r.get('name')}" if r.get("id") in attack_ids and key not in worn
                else f"while wearing {r.get('name')}")
        for e in engine.owner_effects(conn, "item", *key):
            met = on and engine.when_met(e.get("when"), set(doc.get("_using") or []), set(doc.get("_wearing") or []))
            held_rows.append(row({**e, "met": met}, held))
    return {
        "using": [labels.tag(c) for c in doc.get("_using") or []],
        "wearing": [labels.tag(c) for c in doc.get("_wearing") or []],
        "always": [row(e) for e in doc.get("_effects") or [] if not e.get("when") and not from_item(e)],
        "conditional": [row(e) for e in doc.get("_conditional") or [] if not from_item(e)] + held_rows,
    }


def sheet(conn: sqlite3.Connection, cid: str, adapter_id: str | None = None, attack: str | None = None) -> dict[str, Any]:
    """The character's sheet; `attack` picks the attack whose conditional bonuses apply (default: the sheet's)."""
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    doc = resolved_doc(conn, cid, attack)
    adapter = load_adapter(conn, adapter_id)
    portrait = f"/portraits/{ch['pack']}/{ch['portrait']}" if ch["portrait"] else None
    out = fold(
        doc,
        adapter,
        occupation=_named(conn, "occupations", ch["occupation_pack"], ch["occupation_id"]),
        species=_named(conn, "species", ch["species_pack"], ch["species_id"]),
        portrait=portrait,
    )
    out["occupations"] = engine.occupation_progress(conn, cid)[:3]
    out["vehicles"] = [{"id": v["id"], "name": v.get("name"), "attrs": v["attrs"]} for v in doc["vehicles"]]
    out["pinned"] = _named(conn, "occupations", ch["pinned_pack"], ch["pinned_id"])
    out["unspent_experience"] = ch["xp_unspent"]
    out["inactive"] = [{"id": a["id"], "name": a.get("name"), "why": a["inactive"]}
                       for a in doc["abilities"] if a.get("inactive")]
    owner = conn.execute("SELECT username FROM users WHERE id=?", (ch["owner_id"],)).fetchone() if ch["owner_id"] else None
    out["owner"] = owner["username"] if owner else None
    out["bonuses"] = bonuses(conn, doc, adapter)
    return out


def list_sheets(conn: sqlite3.Connection, adapter_id: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for r in conn.execute("SELECT id FROM characters").fetchall():
        s = sheet(conn, r["id"], adapter_id)
        rows.append({
            "id": s["id"], "name": s["name"], "npc": s["npc"], "level": s["level"],
            "occupation": s["occupation"], "species": s["species"], "portrait": s["portrait"],
            "owner": s["owner"], "sheet": s,
        })
    rows.sort(key=lambda r: (r["npc"], r["name"] or r["id"]))
    return rows
