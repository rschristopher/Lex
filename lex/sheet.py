"""Sheet resolution from sqlite: the character's owned rows, merged and evaluated, rendered by an adapter."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from lex import engine
from lex.fold import fold
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


def resolved_doc(conn: sqlite3.Connection, cid: str) -> dict[str, Any]:
    """The character with every owned row merged in (definition, then this character's own values)."""
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    doc = character_doc(conn, cid)
    doc["pack"] = ch["pack"]
    armor: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    gear: list[dict[str, Any]] = []
    for o in conn.execute("SELECT * FROM character_items WHERE character_id=? ORDER BY position", (cid,)):
        cat = conn.execute("SELECT * FROM items WHERE pack=? AND id=?", (o["item_pack"], o["item_id"])).fetchone()
        row = _merged(o, cat, o["item_pack"], o["item_id"])
        kind = row.get("kind")
        (armor if kind == "armor" else weapons if kind == "weapon" else gear).append(row)
    effects, broken = engine.character_effects(conn, cid)
    abilities = []
    for o in conn.execute("SELECT * FROM character_abilities WHERE character_id=? ORDER BY position", (cid,)):
        cat = conn.execute("SELECT * FROM abilities WHERE pack=? AND id=?", (o["ability_pack"], o["ability_id"])).fetchone()
        row = _merged(o, cat, o["ability_pack"], o["ability_id"])
        problems = broken.get((o["ability_pack"], o["ability_id"]))
        if problems:
            row["inactive"] = problems
        abilities.append(row)
    doc.pop("items", None)
    doc["armor"] = armor
    doc["weapons"] = weapons
    doc["gear"] = gear
    doc["abilities"] = abilities
    doc["_effects"] = effects
    return doc


def _named(conn, table: str, pack: str | None, rid: str | None) -> dict[str, Any] | None:
    if not rid:
        return None
    r = conn.execute(f"SELECT name FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchone()
    return {"id": rid, "pack": pack, "name": r["name"] if r else rid}


def sheet(conn: sqlite3.Connection, cid: str, adapter_id: str | None = None) -> dict[str, Any]:
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise KeyError(cid)
    doc = resolved_doc(conn, cid)
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
    out["pinned"] = _named(conn, "occupations", ch["pinned_pack"], ch["pinned_id"])
    out["unspent_experience"] = ch["xp_unspent"]
    out["inactive"] = [{"id": a["id"], "name": a.get("name"), "why": a["inactive"]}
                       for a in doc["abilities"] if a.get("inactive")]
    owner = conn.execute("SELECT username FROM users WHERE id=?", (ch["owner_id"],)).fetchone() if ch["owner_id"] else None
    out["owner"] = owner["username"] if owner else None
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
