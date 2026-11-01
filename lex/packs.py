"""Pack import and export. A pack directory is JSON rows; sqlite is the live record."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from lex.engine import PHYSICAL_ATTRIBUTES

CHAR_KEYS = [
    "id", "name", "npc", "level", "species", "occupation", "pinned", "unspent_experience",
    "portrait", "coin", "attrs", "gauges", "channels", "items", "abilities", "list", "activated", "attack",
]
CHAR_COLUMNS = {
    "npc": "npc", "level": "level", "portrait": "portrait", "coin": "coin",
    "attack": "attack", "unspent_experience": "xp_unspent",
}
REF_COLUMNS = {"species": "species", "occupation": "occupation", "pinned": "pinned"}
ROW_SPLIT = ("effects", "requires", "sets")


class PackError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _num(v: Any) -> Any:
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_pack(src: Path) -> dict[str, Any]:
    """Read a pack directory into one document."""
    src = Path(src)
    if not src.is_dir():
        raise PackError([f"{src}: not a directory"])
    meta = _read(src / "pack.json") if (src / "pack.json").is_file() else {}
    doc: dict[str, Any] = {
        "id": meta.get("id") or src.name,
        "name": meta.get("name") or meta.get("id") or src.name,
        "adapter": _read(src / "adapter.json") if (src / "adapter.json").is_file() else None,
        "adapter_text": (src / "adapter.json").read_text(encoding="utf-8") if (src / "adapter.json").is_file() else None,
        "species": _read(src / "species.json") if (src / "species.json").is_file() else [],
        "occupations": [_read(p) for p in sorted((src / "occupations").glob("*.json"))],
        "abilities": _read(src / "abilities.json") if (src / "abilities.json").is_file() else [],
        "items": _read(src / "items.json") if (src / "items.json").is_file() else [],
        "characters": [],
        "portraits": {},
        "lore": [],
    }
    for p in sorted((src / "characters").glob("*.json")):
        c = _read(p)
        c.setdefault("id", p.stem)
        doc["characters"].append(c)
    pdir = src / "portraits"
    if pdir.is_dir():
        for p in sorted(pdir.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                doc["portraits"][p.name] = p.read_bytes()
    ldir = src / "lore"
    if ldir.is_dir():
        for p in sorted(ldir.glob("*.md")):
            doc["lore"].append({"title": p.stem, "body": p.read_text(encoding="utf-8")})
    return doc


class _Refs:
    """Resolve a reference ("id" or "pack:id") to (pack, id): this pack first, then the database."""

    def __init__(self, conn: sqlite3.Connection, pack_id: str, doc: dict[str, Any]):
        self.conn = conn
        self.pack = pack_id
        self.local = {
            "species": {r["id"] for r in doc["species"]},
            "occupations": {r["id"] for r in doc["occupations"]},
            "abilities": {r["id"] for r in doc["abilities"]},
            "items": {r["id"] for r in doc["items"]},
        }

    def resolve(self, table: str, ref: Any, where: str, errors: list[str]) -> tuple[str, str] | None:
        if not isinstance(ref, str) or not ref:
            errors.append(f"{where}: reference must be a non-empty string")
            return None
        if ":" in ref:
            pack, rid = ref.split(":", 1)
            if pack == self.pack and rid in self.local[table]:
                return pack, rid
            if self.conn.execute(f"SELECT 1 FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchone():
                return pack, rid
            errors.append(f"{where}: unknown {table} {ref!r}")
            return None
        if ref in self.local[table]:
            return self.pack, ref
        rows = self.conn.execute(
            f"SELECT pack FROM {table} WHERE id=? AND pack<>?", (ref, self.pack)
        ).fetchall()
        if len(rows) == 1:
            return rows[0]["pack"], ref
        if not rows:
            errors.append(f"{where}: unknown {table} {ref!r}")
        else:
            errors.append(f"{where}: {ref!r} is in several packs; write it as pack:id")
        return None


def _check_row(row: Any, where: str, errors: list[str], need: tuple[str, ...] = ("id", "name")) -> bool:
    if not isinstance(row, dict):
        errors.append(f"{where}: must be an object")
        return False
    ok = True
    for k in need:
        if not isinstance(row.get(k), str) or not row.get(k):
            errors.append(f"{where}: missing {k}")
            ok = False
    return ok


def _insert_effects(conn, owner_type, pack, owner_id, effects, where, errors) -> None:
    if effects is None:
        return
    if not isinstance(effects, list):
        errors.append(f"{where}.effects: must be a list")
        return
    for i, ef in enumerate(effects):
        w = f"{where}.effects[{i}]"
        if not isinstance(ef, dict) or not ef.get("verb") or not ef.get("target"):
            errors.append(f"{w}: needs verb and target")
            continue
        value = ef.get("value")
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"{w}: value must be a number")
            continue
        extra = {k: v for k, v in ef.items() if k not in ("verb", "target", "value")}
        conn.execute(
            "INSERT INTO effects (owner_type, owner_pack, owner_id, position, verb, target, value, data)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (owner_type, pack, owner_id, i, ef["verb"], ef["target"], value, _dumps(extra)),
        )


def _insert_requirements(conn, refs: _Refs, owner_type, pack, owner_id, reqs, where, errors) -> None:
    if reqs is None:
        return
    if not isinstance(reqs, list):
        errors.append(f"{where}.requires: must be a list")
        return
    tables = {"species": "species", "ability": "abilities", "occupation_set": "occupations"}
    for i, rq in enumerate(reqs):
        w = f"{where}.requires[{i}]"
        kind = rq.get("kind") if isinstance(rq, dict) else None
        if kind not in ("species", "ability", "occupation_set", "list"):
            errors.append(f"{w}: kind must be species, ability, occupation_set, or list")
            continue
        ref_pack = ref_id = None
        if kind in tables:
            r = refs.resolve(tables[kind], rq.get("id"), w, errors)
            if r is None:
                continue
            ref_pack, ref_id = r
        value = rq.get("set")
        if kind == "occupation_set" and not isinstance(value, int):
            errors.append(f"{w}: occupation_set needs an integer set")
            continue
        conn.execute(
            "INSERT INTO requirements (owner_type, owner_pack, owner_id, position, kind, ref_pack, ref_id, value)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (owner_type, pack, owner_id, i, kind, ref_pack, ref_id, value),
        )


def _catalog_data(row: dict[str, Any]) -> str:
    return _dumps({k: v for k, v in row.items() if k not in ROW_SPLIT})


def import_pack(conn: sqlite3.Connection, src: str | Path | dict[str, Any]) -> dict[str, int]:
    """Validate and load a pack into sqlite, replacing any earlier copy. All or nothing."""
    doc = src if isinstance(src, dict) else read_pack(Path(src))
    pid = doc["id"]
    errors: list[str] = []
    kept = {
        r["id"]: (r["owner_id"], r["campaign_id"])
        for r in conn.execute("SELECT id, owner_id, campaign_id FROM characters WHERE pack=?", (pid,))
    }
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM effects WHERE owner_pack=?", (pid,))
        conn.execute("DELETE FROM requirements WHERE owner_pack=?", (pid,))
        conn.execute("DELETE FROM occupation_sets WHERE occupation_pack=?", (pid,))
        conn.execute("DELETE FROM packs WHERE id=?", (pid,))
        conn.execute("INSERT INTO packs (id, name) VALUES (?, ?)", (pid, doc.get("name") or pid))
        if doc.get("adapter") is not None:
            if not isinstance(doc["adapter"], dict):
                errors.append("adapter.json: must be an object")
            else:
                text = doc.get("adapter_text") or json.dumps(doc["adapter"], indent=2, ensure_ascii=False) + "\n"
                conn.execute("INSERT INTO adapters (pack, data) VALUES (?, ?)", (pid, text))
        refs = _Refs(conn, pid, doc)

        for i, row in enumerate(doc["species"]):
            w = f"species[{i}]"
            if not _check_row(row, w, errors):
                continue
            conn.execute("INSERT INTO species (pack, id, position, name, data) VALUES (?,?,?,?,?)",
                         (pid, row["id"], i, row["name"], _catalog_data(row)))
        for i, row in enumerate(doc["abilities"]):
            w = f"abilities[{i}]"
            if not _check_row(row, w, errors):
                continue
            price = row.get("price")
            if price is not None and (not isinstance(price, int) or price < 0):
                errors.append(f"{w}: price must be a whole number of experience")
                continue
            conn.execute(
                "INSERT INTO abilities (pack, id, position, name, kind, price, data) VALUES (?,?,?,?,?,?,?)",
                (pid, row["id"], i, row["name"], row.get("kind"), price, _catalog_data(row)),
            )
        for i, row in enumerate(doc["items"]):
            w = f"items[{i}]"
            if not _check_row(row, w, errors, ("id", "name", "kind")):
                continue
            layer = row.get("layer")
            if layer is not None and (
                not isinstance(layer, dict)
                or not all(k in PHYSICAL_ATTRIBUTES and isinstance(v, (int, float)) and v >= 0 for k, v in layer.items())
            ):
                errors.append(f"{w}.layer: must map physical attributes ({', '.join(PHYSICAL_ATTRIBUTES)}) to numbers, 0 or more")
                continue
            conn.execute("INSERT INTO items (pack, id, position, name, kind, data) VALUES (?,?,?,?,?,?)",
                         (pid, row["id"], i, row["name"], row["kind"], _catalog_data(row)))
        for row in doc["occupations"]:
            w = f"occupations/{row.get('id') if isinstance(row, dict) else '?'}"
            if not _check_row(row, w, errors):
                continue
            conn.execute("INSERT INTO occupations (pack, id, name, data) VALUES (?,?,?,?)",
                         (pid, row["id"], row["name"], _catalog_data(row)))

        # Effects, requirements, and sets after every catalog row exists, so references resolve.
        for table, owner_type in (("species", "species"), ("abilities", "ability"),
                                  ("items", "item"), ("occupations", "occupation")):
            for i, row in enumerate(doc[table]):
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                w = f"{table}/{row['id']}"
                _insert_effects(conn, owner_type, pid, row["id"], row.get("effects"), w, errors)
                _insert_requirements(conn, refs, owner_type, pid, row["id"], row.get("requires"), w, errors)
        for row in doc["occupations"]:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            sets = row.get("sets")
            if sets is None:
                continue
            if not isinstance(sets, list) or not all(isinstance(s, list) for s in sets):
                errors.append(f"occupations/{row['id']}.sets: must be a list of lists")
                continue
            for si, s in enumerate(sets, start=1):
                for pos, ref in enumerate(s):
                    r = refs.resolve("abilities", ref, f"occupations/{row['id']}.sets[{si}]", errors)
                    if r:
                        conn.execute(
                            "INSERT INTO occupation_sets VALUES (?,?,?,?,?,?)",
                            (pid, row["id"], si, pos, r[0], r[1]),
                        )

        for name, data in doc["portraits"].items():
            conn.execute("INSERT INTO portraits (pack, name, data) VALUES (?,?,?)", (pid, name, data))
        for i, lo in enumerate(doc["lore"]):
            conn.execute("INSERT INTO lore (pack, title, chunk, body) VALUES (?,?,0,?)", (pid, lo["title"], lo["body"]))

        for ci, c in enumerate(doc["characters"]):
            _import_character(conn, refs, pid, ci, c, errors)
            if isinstance(c, dict) and c.get("id") in kept:
                conn.execute("UPDATE characters SET owner_id=?, campaign_id=? WHERE id=?", (*kept[c["id"]], c["id"]))

        if errors:
            raise PackError(errors)
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return {
        "species": len(doc["species"]), "occupations": len(doc["occupations"]),
        "abilities": len(doc["abilities"]), "items": len(doc["items"]),
        "characters": len(doc["characters"]),
    }


def _import_character(conn, refs: _Refs, pid: str, ci: int, c: Any, errors: list[str]) -> None:
    w = f"characters/{c.get('id') if isinstance(c, dict) else ci}"
    if not _check_row(c, w, errors):
        return
    other = conn.execute("SELECT pack FROM characters WHERE id=?", (c["id"],)).fetchone()
    if other:
        errors.append(f"{w}: id already used by pack {other['pack']}")
        return
    cols: dict[str, Any] = {"id": c["id"], "pack": pid, "position": ci, "name": c["name"]}
    for key, col in CHAR_COLUMNS.items():
        if key in c:
            v = c[key]
            if key == "npc":
                v = 1 if v else 0
            elif key in ("level", "coin", "unspent_experience") and not isinstance(v, int):
                errors.append(f"{w}.{key}: must be a whole number")
                continue
            cols[col] = v
    for key, col in REF_COLUMNS.items():
        if c.get(key) is not None:
            table = "species" if key == "species" else "occupations"
            r = refs.resolve(table, c[key], f"{w}.{key}", errors)
            if r:
                cols[f"{col}_pack"], cols[f"{col}_id"] = r
    cols["data"] = _dumps({k: v for k, v in c.items() if k not in CHAR_KEYS})
    names = ", ".join(cols)
    conn.execute(f"INSERT INTO characters ({names}) VALUES ({', '.join('?' * len(cols))})", list(cols.values()))
    cid = c["id"]

    attrs = c.get("attrs") or {}
    if not isinstance(attrs, dict):
        errors.append(f"{w}.attrs: must be an object")
        attrs = {}
    for i, (k, v) in enumerate(attrs.items()):
        if not isinstance(v, (int, float)) or v < 0:
            errors.append(f"{w}.attrs.{k}: must be a number, 0 or more")
            continue
        conn.execute("INSERT INTO character_attrs VALUES (?,?,?,?)", (cid, i, k, v))
    for i, g in enumerate(c.get("gauges") or []):
        if not isinstance(g, dict) or not g.get("id"):
            errors.append(f"{w}.gauges[{i}]: needs id")
            continue
        extra = {k: v for k, v in g.items() if k not in ("id", "prefix", "total", "current")}
        conn.execute("INSERT INTO character_gauges VALUES (?,?,?,?,?,?,?)",
                     (cid, i, g["id"], g.get("prefix"), g.get("total"), g.get("current"), _dumps(extra)))
    for i, (k, v) in enumerate((c.get("channels") or {}).items()):
        if isinstance(v, dict):
            conn.execute("INSERT INTO character_channels VALUES (?,?,?,?,?)",
                         (cid, i, k, int(v.get("value") or 0), _dumps(v)))
        elif isinstance(v, int):
            conn.execute("INSERT INTO character_channels VALUES (?,?,?,?,NULL)", (cid, i, k, v))
        else:
            errors.append(f"{w}.channels.{k}: must be a whole number")
    for table, key, col in (("abilities", "abilities", "character_abilities"), ("items", "items", "character_items")):
        for i, own in enumerate(c.get(key) or []):
            own = {"id": own} if isinstance(own, str) else own
            if not isinstance(own, dict):
                errors.append(f"{w}.{key}[{i}]: must be an id or object")
                continue
            r = refs.resolve(table, own.get("id"), f"{w}.{key}[{i}]", errors)
            if r:
                conn.execute(f"INSERT INTO {col} VALUES (?,?,?,?,?)",
                             (cid, i, r[0], r[1], _dumps({k: v for k, v in own.items() if k != "id"})))
    for ref in c.get("list") or []:
        r = refs.resolve("abilities", ref, f"{w}.list", errors)
        if r:
            conn.execute("INSERT INTO character_list VALUES (?,?,?)", (cid, *r))
    for i, ref in enumerate(c.get("activated") or []):
        conn.execute("INSERT INTO character_active VALUES (?,?,?)", (cid, i, ref))


# ---------------------------------------------------------------- export


def _ref_out(owner_pack: str, pack: str | None, rid: str | None) -> str | None:
    if rid is None:
        return None
    return rid if pack == owner_pack else f"{pack}:{rid}"


def _effects_out(conn, owner_type, pack, oid) -> list[dict[str, Any]]:
    out = []
    for r in conn.execute(
        "SELECT * FROM effects WHERE owner_type=? AND owner_pack=? AND owner_id=? ORDER BY position",
        (owner_type, pack, oid),
    ):
        extra = json.loads(r["data"])
        ef: dict[str, Any] = {"verb": r["verb"], "target": r["target"]}
        if r["value"] is not None:
            ef["value"] = _num(r["value"])
        ef.update(extra)
        out.append(ef)
    return out


def _requires_out(conn, owner_type, pack, oid) -> list[dict[str, Any]]:
    out = []
    for r in conn.execute(
        "SELECT * FROM requirements WHERE owner_type=? AND owner_pack=? AND owner_id=? ORDER BY position",
        (owner_type, pack, oid),
    ):
        rq: dict[str, Any] = {"kind": r["kind"]}
        if r["ref_id"] is not None:
            rq["id"] = _ref_out(pack, r["ref_pack"], r["ref_id"])
        if r["value"] is not None:
            rq["set"] = r["value"]
        out.append(rq)
    return out


def _row_out(conn, owner_type: str, pack: str, r: sqlite3.Row) -> dict[str, Any]:
    row = json.loads(r["data"])
    effects = _effects_out(conn, owner_type, pack, r["id"])
    reqs = _requires_out(conn, owner_type, pack, r["id"])
    if effects:
        row["effects"] = effects
    if reqs:
        row["requires"] = reqs
    return row


def character_doc(conn: sqlite3.Connection, cid: str) -> dict[str, Any]:
    """One character as pack JSON (references, not definitions)."""
    r = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if r is None:
        raise KeyError(cid)
    pack = r["pack"]
    doc: dict[str, Any] = {"id": r["id"], "name": r["name"]}
    if r["npc"] is not None:
        doc["npc"] = bool(r["npc"])
    if r["level"] is not None:
        doc["level"] = r["level"]
    for key, col in REF_COLUMNS.items():
        ref = _ref_out(pack, r[f"{col}_pack"], r[f"{col}_id"])
        if ref is not None:
            doc[key] = ref
    if r["xp_unspent"] is not None:
        doc["unspent_experience"] = r["xp_unspent"]
    for key in ("portrait", "coin"):
        if r[key] is not None:
            doc[key] = r[key]
    attrs = conn.execute("SELECT attr, value FROM character_attrs WHERE character_id=? ORDER BY position", (cid,))
    doc["attrs"] = {a["attr"]: _num(a["value"]) for a in attrs}
    gauges = []
    for g in conn.execute("SELECT * FROM character_gauges WHERE character_id=? ORDER BY position", (cid,)):
        row: dict[str, Any] = {"id": g["gauge"]}
        for k in ("prefix", "total", "current"):
            if g[k] is not None:
                row[k] = g[k]
        row.update(json.loads(g["data"]))
        gauges.append(row)
    if gauges:
        doc["gauges"] = gauges
    channels = {}
    for ch in conn.execute("SELECT * FROM character_channels WHERE character_id=? ORDER BY position", (cid,)):
        channels[ch["channel"]] = json.loads(ch["data"]) if ch["data"] is not None else ch["value"]
    if channels:
        doc["channels"] = channels
    for key, col, pcol, icol in (("items", "character_items", "item_pack", "item_id"),
                                 ("abilities", "character_abilities", "ability_pack", "ability_id")):
        rows = [
            {"id": _ref_out(pack, o[pcol], o[icol]), **json.loads(o["data"])}
            for o in conn.execute(f"SELECT * FROM {col} WHERE character_id=? ORDER BY position", (cid,))
        ]
        if rows:
            doc[key] = rows
    lst = [_ref_out(pack, o["ability_pack"], o["ability_id"]) for o in conn.execute(
        "SELECT * FROM character_list WHERE character_id=? ORDER BY ability_pack, ability_id", (cid,))]
    if lst:
        doc["list"] = lst
    act = [a["ref"] for a in conn.execute(
        "SELECT ref FROM character_active WHERE character_id=? ORDER BY position", (cid,))]
    if act or r["attack"] is not None:
        doc["activated"] = act
    if r["attack"] is not None:
        doc["attack"] = r["attack"]
    doc.update(json.loads(r["data"]))
    return doc


def export_pack(conn: sqlite3.Connection, pack_id: str, dest: str | Path) -> Path:
    if not conn.execute("SELECT 1 FROM packs WHERE id=?", (pack_id,)).fetchone():
        raise PackError([f"no pack {pack_id!r} in the database"])
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    name = conn.execute("SELECT name FROM packs WHERE id=?", (pack_id,)).fetchone()["name"]
    _write(dest / "pack.json", {"id": pack_id, "name": name})
    ad = conn.execute("SELECT data FROM adapters WHERE pack=?", (pack_id,)).fetchone()
    if ad:
        (dest / "adapter.json").write_text(ad["data"], encoding="utf-8")
    for table, owner_type, fname in (("species", "species", "species.json"),
                                     ("abilities", "ability", "abilities.json"),
                                     ("items", "item", "items.json")):
        rows = conn.execute(f"SELECT * FROM {table} WHERE pack=? ORDER BY position", (pack_id,)).fetchall()
        if rows:
            _write(dest / fname, [_row_out(conn, owner_type, pack_id, r) for r in rows])
    for r in conn.execute("SELECT * FROM occupations WHERE pack=? ORDER BY id", (pack_id,)).fetchall():
        row = _row_out(conn, "occupation", pack_id, r)
        sets: dict[int, list[str]] = {}
        for s in conn.execute(
            "SELECT * FROM occupation_sets WHERE occupation_pack=? AND occupation_id=? ORDER BY set_index, position",
            (pack_id, r["id"]),
        ):
            sets.setdefault(s["set_index"], []).append(_ref_out(pack_id, s["ability_pack"], s["ability_id"]))
        if sets:
            row["sets"] = [sets[k] for k in sorted(sets)]
        _write(dest / "occupations" / f"{r['id']}.json", row)
    for r in conn.execute("SELECT id FROM characters WHERE pack=? ORDER BY position, id", (pack_id,)).fetchall():
        _write(dest / "characters" / f"{r['id']}.json", character_doc(conn, r["id"]))
    for r in conn.execute("SELECT name, data FROM portraits WHERE pack=? ORDER BY name", (pack_id,)):
        (dest / "portraits").mkdir(parents=True, exist_ok=True)
        (dest / "portraits" / r["name"]).write_bytes(r["data"])
    for r in conn.execute("SELECT title, body FROM lore WHERE pack=? ORDER BY id", (pack_id,)):
        (dest / "lore").mkdir(parents=True, exist_ok=True)
        (dest / "lore" / f"{r['title']}.md").write_text(r["body"], encoding="utf-8")
    return dest
