"""The library: browse and search every pack row (species, occupations, abilities, items, entries) by category.

Categories come from the data: a table, plus the row's own `kind` for abilities, items, and entries.
Nothing here names a system or a specific row; labels come from the packs and adapters.
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from lex import engine
from lex.sheet import load_adapter

# Every browsable table, in menu order: (table, owner_type for effects and requirements, section label).
TABLES: list[tuple[str, str | None, str]] = [
    ("species", "species", "People"),
    ("occupations", "occupation", "People"),
    ("abilities", "ability", "Abilities"),
    ("items", "item", "Equipment"),
    ("entries", None, "World"),
]
OWNER_TYPE = {t: o for t, o, _ in TABLES}
OWNER_TABLE = {o: t for t, o, _ in TABLES if o}
KINDED = {"abilities", "items", "entries"}
TABLE_LABEL = {"species": "Species", "occupations": "Occupations", "abilities": "Abilities",
               "items": "Items", "entries": "Entries"}
# Free-text fields shown as the row's prose, and fields shown on their own.
TEXT_KEYS = ("text", "description", "summary")
SKIP_KEYS = {"id", "name", "kind", "source", "links", "categories", "level_from", "levels_mode", *TEXT_KEYS}
# Words that are already plural (or uncountable) in a menu.
UNCOUNTED = {"armor", "armour", "gear", "equipment", "clothing", "ammunition", "magic", "lore", "treasure",
             "cybernetics", "psionics", "species", "bionics", "food", "money"}


def _rows_sql() -> str:
    return " UNION ALL ".join([
        "SELECT 'species' AS tbl, pack, id, name, NULL AS kind, data, position FROM species",
        "SELECT 'occupations', pack, id, name, NULL, data, 0 FROM occupations",
        "SELECT 'abilities', pack, id, name, kind, data, position FROM abilities",
        "SELECT 'items', pack, id, name, kind, data, position FROM items",
        "SELECT 'entries', pack, id, name, kind, data, position FROM entries",
    ])


def humanize(key: str) -> str:
    s = re.sub(r"[_\-.]+", " ", str(key)).strip()
    return s[:1].upper() + s[1:] if s else str(key)


def plural(word: str) -> str:
    w = word.strip()
    low = w.lower()
    if not w or low in UNCOUNTED or low.endswith("s"):
        return w
    if low.endswith("y") and low[-2:-1] not in "aeiou":
        return w[:-1] + "ies"
    if low.endswith(("ch", "sh", "x")):
        return w + "es"
    return w + "s"


def category_id(table: str, kind: str | None) -> str:
    return f"{table}.{kind}" if table in KINDED and kind else table


def split_category(cat: str) -> tuple[str, str | None]:
    table, _, kind = cat.partition(".")
    if table not in OWNER_TYPE:
        raise KeyError(cat)
    return table, (kind or None)


class Labels:
    """Category and target labels from the data: pack.json `labels`, then adapters, then the kind itself."""

    def __init__(self, conn: sqlite3.Connection, adapter_id: str | None = None):
        self.packs: dict[str, str] = {}
        self.pack_labels: dict[str, str] = {}
        self.tags: dict[str, str] = {}
        for r in conn.execute("SELECT packs.id, packs.name, pack_meta.data FROM packs"
                              " LEFT JOIN pack_meta ON pack_meta.pack = packs.id ORDER BY packs.id"):
            self.packs[r["id"]] = r["name"]
            meta = json.loads(r["data"] or "{}")
            for k, v in (meta.get("labels") or {}).items():
                if isinstance(v, str):
                    self.pack_labels.setdefault(k, v)
            for c in meta.get("categories") or []:
                if isinstance(c, dict) and c.get("id") and c.get("name"):
                    self.tags.setdefault(c["id"], c["name"])
        self.adapter = load_adapter(conn, adapter_id)
        # The chosen adapter's group names first, then any other adapter's.
        self.groups: dict[str, str] = {k: v for k, v in (self.adapter.get("groups") or {}).items() if isinstance(v, str)}
        for r in conn.execute("SELECT data FROM adapters ORDER BY pack"):
            for k, v in (json.loads(r["data"]).get("groups") or {}).items():
                if isinstance(v, str):
                    self.groups.setdefault(k, v)

    def category(self, table: str, kind: str | None) -> str:
        cid = category_id(table, kind)
        for key in (cid, kind):
            if key and key in self.pack_labels:
                return self.pack_labels[key]
        if not kind or table not in KINDED:
            return self.pack_labels.get(table) or self.groups.get(table) or TABLE_LABEL[table]
        for key in (kind, kind + "s", kind + "es"):
            if key in self.groups:
                return self.groups[key]
        return plural(humanize(kind))

    def target(self, verb: str, target: str) -> str:
        """The adapter's name for an effect target (attribute or channel), else the target in words."""
        for section in ("attrs", "channels", "gauges"):
            for k, v in (self.adapter.get(section) or {}).items():
                if isinstance(v, str) and k == target:
                    return v
                if isinstance(v, dict) and (v.get("from") == target or (k == target and "from" not in v)):
                    return v.get("label") or humanize(k)
        return humanize(target)

    def tag(self, category: str) -> str:
        """An item category's name, as the pack declares it in pack.json "categories", else in words."""
        return self.tags.get(category) or humanize(category)

    def prefix(self, pid: str) -> str | None:
        p = (self.adapter.get("prefixes") or {}).get(pid)
        if isinstance(p, dict) and p:
            return ", ".join(f"{humanize(k).lower()} {v}" for k, v in p.items())
        return None


def _num(v: Any) -> Any:
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _signed(v: Any) -> str:
    v = _num(v)
    if isinstance(v, (int, float)):
        return f"+{v}" if v > 0 else str(v)
    return str(v)


def value_text(v: Any) -> str:
    """Any stored value as plain words, never JSON."""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float)):
        return str(_num(v))
    if isinstance(v, list):
        return "; ".join(value_text(x) for x in v)
    if isinstance(v, dict):
        head = v.get("name")
        rest = ", ".join(f"{humanize(k).lower()} {value_text(x)}" for k, x in v.items() if k not in ("id", "name"))
        return f"{head} ({rest})" if head and rest else (head or rest)
    return str(v)


def _lower(name: str) -> str:
    """ "Knife" -> "knife" inside a sentence; a name with another capitalised word ("Bronze Giant armor") stays."""
    words = name.split()
    if not name[1:2].islower() or any(w[:1].isupper() for w in words[1:]):
        return name
    return name[:1].lower() + name[1:]


def _article(name: str) -> str:
    """ "a knife", "an axe"; none for a plural or uncountable last word ("robot armor", "throwing knives")."""
    last = name.split()[-1].lower() if name.split() else ""
    if not name[:1].islower() or last in UNCOUNTED or last.endswith("s"):
        return name
    return ("an " if name[:1] in "aeiou" else "a ") + name


def when_text(labels: Labels, when: dict[str, Any] | None) -> str:
    """ "when using a knife or a sword", "while wearing robot armor"; both parts joined with "and". """
    if not when:
        return ""
    parts = []
    for key, value in when.items():
        names = [_article(_lower(labels.tag(c))) for c in engine.when_categories(value)]
        if key == "using":
            parts.append("when using " + " or ".join(names))
        elif key == "wearing":
            parts.append("while wearing " + " or ".join(names))
    return " and ".join(parts)


def effect_text(labels: Labels, verb: str, target: str, value: Any, extra: dict[str, Any],
                when: dict[str, Any] | None = None) -> str:
    if when is None and isinstance(extra.get("when"), dict):
        extra = dict(extra)
        when = extra.pop("when")
    cond = when_text(labels, when)
    return _effect_words(labels, verb, target, value, extra) + (f" {cond}" if cond else "")


def _effect_words(labels: Labels, verb: str, target: str, value: Any, extra: dict[str, Any]) -> str:
    name = labels.target(verb, target)
    if verb.startswith("mod.") and value is not None:
        text = f"{_signed(value)} {name}"
    elif value is not None:
        text = f"{humanize(verb)}: {name} {_signed(value)}"
    else:
        text = f"{humanize(verb)}: {name}"
    if extra:
        text += " (" + ", ".join(f"{humanize(k).lower()} {value_text(x)}" for k, x in extra.items()) + ")"
    return text


def source_text(src: Any) -> str | None:
    if src is None or src == "":
        return None
    if isinstance(src, dict):
        parts = [str(src.get(k)) for k in ("book", "title", "chapter", "section") if src.get(k)]
        page = src.get("page") or src.get("pages")
        if page:
            parts.append(f"p. {page}")
        rest = [f"{humanize(k).lower()} {value_text(v)}" for k, v in src.items()
                if k not in ("book", "title", "chapter", "section", "page", "pages")]
        return ", ".join(parts + rest)
    return value_text(src)


# ---------------------------------------------------------------- menu


def menu(conn: sqlite3.Connection, pack: str | None = None, adapter: str | None = None) -> dict[str, Any]:
    labels = Labels(conn, adapter)
    where, args = ("WHERE pack=?", [pack]) if pack else ("", [])
    counts = conn.execute(
        f"SELECT tbl, kind, COUNT(*) AS n FROM ({_rows_sql()}) {where} GROUP BY tbl, kind", args
    ).fetchall()
    sections: dict[str, list[dict[str, Any]]] = {}
    order = {t: i for i, (t, _, _) in enumerate(TABLES)}
    for r in sorted(counts, key=lambda r: (order[r["tbl"]], r["kind"] is not None, labels.category(r["tbl"], r["kind"]))):
        section = next(s for t, _, s in TABLES if t == r["tbl"])
        sections.setdefault(section, []).append({
            "id": category_id(r["tbl"], r["kind"]), "label": labels.category(r["tbl"], r["kind"]),
            "table": r["tbl"], "kind": r["kind"], "count": r["n"],
        })
    out_packs = []
    for p in conn.execute("SELECT id, name FROM packs ORDER BY name"):
        n = conn.execute(f"SELECT COUNT(*) FROM ({_rows_sql()}) WHERE pack=?", (p["id"],)).fetchone()[0]
        if n:
            out_packs.append({"id": p["id"], "name": p["name"], "count": n})
    seen = list(dict.fromkeys(s for _, _, s in TABLES))
    tags = [{"id": r["category"], "label": labels.tag(r["category"]), "count": r["n"]}
            for r in conn.execute("SELECT category, COUNT(*) AS n FROM item_categories"
                                  + (" WHERE item_pack=?" if pack else "") + " GROUP BY category", [pack] if pack else [])]
    tags.sort(key=lambda t: t["label"].lower())
    return {
        "packs": out_packs,
        "sections": [{"label": s, "categories": sections[s]} for s in seen if s in sections],
        "tags": tags,
    }


# ---------------------------------------------------------------- lists and search


def _summary(conn, labels: Labels, tbl: str, pack: str, rid: str, data: dict[str, Any]) -> str:
    for k in TEXT_KEYS:
        if isinstance(data.get(k), str) and data[k].strip():
            t = " ".join(data[k].split())
            return t if len(t) <= 160 else t[:157].rsplit(" ", 1)[0] + "…"
    bits: list[str] = []
    owner = OWNER_TYPE.get(tbl)
    if owner:
        for e in conn.execute(
            "SELECT verb, target, value, data FROM effects WHERE owner_type=? AND owner_pack=? AND owner_id=?"
            " AND level IS NULL ORDER BY position LIMIT 4", (owner, pack, rid),
        ):
            when = json.loads(e["data"] or "{}").get("when")
            bits.append(effect_text(labels, e["verb"], e["target"], e["value"], {}, when))
    for k, v in data.items():
        if k in SKIP_KEYS or isinstance(v, (list, dict)) or v in ("", None) or len(bits) >= 4:
            continue
        bits.append(f"{humanize(k)} {value_text(v)}")
    if tbl == "abilities":
        n = conn.execute("SELECT COUNT(*) FROM ability_levels WHERE ability_pack=? AND ability_id=?", (pack, rid)).fetchone()[0]
        if n:
            bits.append(f"{n} levels")
    if tbl == "occupations":
        n = conn.execute("SELECT COUNT(DISTINCT set_index) FROM occupation_sets WHERE occupation_pack=? AND occupation_id=?",
                         (pack, rid)).fetchone()[0]
        if n:
            bits.append(f"{n} ability set" + ("s" if n != 1 else ""))
    return " · ".join(bits)


def _like(s: str) -> str:
    return "%" + s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def search(conn: sqlite3.Connection, q: str = "", category: str | None = None, pack: str | None = None,
           limit: int = 50, offset: int = 0, adapter: str | None = None, tag: str | None = None) -> dict[str, Any]:
    """Rows matching every word of q in the name or any text, optionally in one category and pack.
    Name matches come first. `facets` counts the matches per category before the category filter."""
    labels = Labels(conn, adapter)
    where: list[str] = []
    args: list[Any] = []
    words = [w for w in re.split(r"\s+", q.strip()) if w]
    for w in words:
        where.append("(name LIKE ? ESCAPE '\\' OR id LIKE ? ESCAPE '\\' OR data LIKE ? ESCAPE '\\')")
        args += [_like(w)] * 3
    if pack:
        where.append("pack = ?")
        args.append(pack)
    if tag:
        where.append("tbl = 'items' AND EXISTS (SELECT 1 FROM item_categories ic WHERE ic.item_pack = pack"
                     " AND ic.item_id = id AND ic.category = ?)")
        args.append(tag)
    base = f"SELECT * FROM ({_rows_sql()})" + (" WHERE " + " AND ".join(where) if where else "")
    facets = [
        {"id": category_id(r["tbl"], r["kind"]), "label": labels.category(r["tbl"], r["kind"]), "count": r["n"]}
        for r in conn.execute(f"SELECT tbl, kind, COUNT(*) AS n FROM ({base}) GROUP BY tbl, kind", args)
    ]
    facets.sort(key=lambda f: (-f["count"], f["label"]))
    cat_where, cat_args = "", []
    if category:
        table, kind = split_category(category)
        cat_where = " WHERE tbl = ? AND kind IS ?"
        cat_args = [table, kind]
    total = conn.execute(f"SELECT COUNT(*) FROM ({base}){cat_where}", args + cat_args).fetchone()[0]
    rank, rank_args = "", []
    if words:
        rank = "CASE WHEN name LIKE ? ESCAPE '\\' THEN 0 WHEN name LIKE ? ESCAPE '\\' THEN 1 ELSE 2 END, "
        rank_args = [_like(words[0])[1:], _like(words[0])]
    rows = conn.execute(
        f"SELECT * FROM ({base}){cat_where} ORDER BY {rank}name COLLATE NOCASE, pack LIMIT ? OFFSET ?",
        args + cat_args + rank_args + [max(1, min(limit, 500)), max(0, offset)],
    ).fetchall()
    out = []
    for r in rows:
        data = json.loads(r["data"] or "{}")
        out.append({
            "category": category_id(r["tbl"], r["kind"]), "category_label": labels.category(r["tbl"], r["kind"]),
            "table": r["tbl"], "pack": r["pack"], "pack_name": labels.packs.get(r["pack"], r["pack"]),
            "id": r["id"], "name": r["name"], "kind": r["kind"],
            "summary": _summary(conn, labels, r["tbl"], r["pack"], r["id"], data),
            "categories": _tag_links(labels, data.get("categories")),
        })
    label = labels.category(*split_category(category)) if category else None
    result = {"total": total, "offset": offset, "category": category, "category_label": label,
              "facets": facets, "rows": out}
    if tag:
        result.update(tag=tag, tag_label=labels.tag(tag), bonuses=tag_bonuses(conn, labels, tag))
    return result


# ---------------------------------------------------------------- one row


def _link(conn, labels: Labels, table: str, pack: str | None, rid: str | None, note: str | None = None):
    if rid is None:
        return None
    r = None
    if table in OWNER_TYPE:
        kind_col = "kind" if table in KINDED else "NULL AS kind"
        r = conn.execute(f"SELECT name, {kind_col} FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchone()
    out = {"table": table, "pack": pack, "id": rid, "name": r["name"] if r else rid,
           "category": category_id(table, r["kind"]) if r else table,
           "category_label": labels.category(table, r["kind"]) if r else TABLE_LABEL.get(table, table),
           "missing": r is None}
    if note:
        out["note"] = note
    return out


def _requirement_text(conn, labels: Labels, rq: sqlite3.Row) -> dict[str, Any]:
    kind = rq["kind"]
    if kind == "species":
        link = _link(conn, labels, "species", rq["ref_pack"], rq["ref_id"])
        return {"text": f"Species must be {link['name']}", "link": link}
    if kind == "ability":
        link = _link(conn, labels, "abilities", rq["ref_pack"], rq["ref_id"])
        return {"text": f"Needs {link['name']}", "link": link}
    if kind == "occupation_set":
        link = _link(conn, labels, "occupations", rq["ref_pack"], rq["ref_id"])
        return {"text": f"Needs set {rq['value']} of {link['name']} complete", "link": link}
    if kind == "list":
        return {"text": "Must be on the character's own list", "link": None}
    return {"text": humanize(kind), "link": None}


def _effects(conn, labels: Labels, owner: str, pack: str, rid: str, level: int | None) -> list[dict[str, Any]]:
    out = []
    for e in conn.execute(
        "SELECT * FROM effects WHERE owner_type=? AND owner_pack=? AND owner_id=? AND level IS ? ORDER BY position",
        (owner, pack, rid, level),
    ):
        extra = json.loads(e["data"] or "{}")
        when = extra.pop("when", None)
        row = {"text": effect_text(labels, e["verb"], e["target"], e["value"], extra, when),
               "verb": e["verb"], "target": e["target"], "value": _num(e["value"])}
        if when:
            row["when"] = when
            row["condition"] = when_text(labels, when)
        out.append(row)
    return out


def _tag_links(labels: Labels, cats: Any) -> list[dict[str, Any]]:
    return [{"id": c, "label": labels.tag(c)} for c in engine.when_categories(cats)]


def tag_bonuses(conn, labels: Labels, tag: str) -> list[dict[str, Any]]:
    """Every effect row whose when names this category, with the row it belongs to."""
    out = []
    for e in conn.execute("SELECT * FROM effects WHERE data LIKE ? ESCAPE '\\' ORDER BY owner_type, owner_id, level, position",
                          (_like(json.dumps(tag, ensure_ascii=False)),)):
        extra = json.loads(e["data"] or "{}")
        when = extra.pop("when", None)
        if not when or not any(tag in engine.when_categories(v) for v in when.values()):
            continue
        table = OWNER_TABLE[e["owner_type"]]
        link = _link(conn, labels, table, e["owner_pack"], e["owner_id"])
        if e["level"] is not None:
            lv = conn.execute("SELECT name FROM ability_levels WHERE ability_pack=? AND ability_id=? AND level=?",
                              (e["owner_pack"], e["owner_id"], e["level"])).fetchone()
            link["note"] = lv["name"] if lv else f"level {e['level']}"
        out.append({"text": effect_text(labels, e["verb"], e["target"], e["value"], extra, when), "from": link})
    return out


def _facts(labels: Labels, data: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for k, v in data.items():
        if k in SKIP_KEYS or v in ("", None):
            continue
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            out.append({"label": humanize(k), "rows": [value_text(x) for x in v]})
            continue
        text = value_text(v)
        if k == "prefix" and isinstance(v, str) and labels.prefix(v):
            text = f"{v} ({labels.prefix(v)})"
        out.append({"label": humanize(k), "value": text})
    return out


def detail(conn: sqlite3.Connection, table: str, pack: str, rid: str, adapter: str | None = None) -> dict[str, Any]:
    if table not in OWNER_TYPE:
        raise KeyError(table)
    kind_col = "kind" if table in KINDED else "NULL AS kind"
    r = conn.execute(f"SELECT id, pack, name, {kind_col}, data FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchone()
    if r is None:
        raise KeyError(rid)
    labels = Labels(conn, adapter)
    data = json.loads(r["data"] or "{}")
    owner = OWNER_TYPE[table]
    text = next((data[k] for k in TEXT_KEYS if isinstance(data.get(k), str) and data[k].strip()), None)
    out: dict[str, Any] = {
        "table": table, "pack": pack, "pack_name": labels.packs.get(pack, pack), "id": rid, "name": r["name"],
        "kind": r["kind"], "category": category_id(table, r["kind"]), "category_label": labels.category(table, r["kind"]),
        "text": text, "source": source_text(data.get("source")), "facts": _facts(labels, data),
        "effects": [], "requires": [], "levels": [], "related": [],
        "categories": _tag_links(labels, data.get("categories")),
    }
    if table == "items":
        attrs = conn.execute("SELECT attr, value FROM item_attrs WHERE item_pack=? AND item_id=? ORDER BY position",
                             (pack, rid)).fetchall()
        out["facts"][:0] = [{"label": labels.target("mod.attr", a["attr"]), "value": value_text(a["value"])} for a in attrs]
    if owner:
        out["effects"] = _effects(conn, labels, owner, pack, rid, None)
        out["requires"] = [_requirement_text(conn, labels, rq) for rq in conn.execute(
            "SELECT * FROM requirements WHERE owner_type=? AND owner_pack=? AND owner_id=? ORDER BY position",
            (owner, pack, rid))]
    if table == "abilities":
        for lv in conn.execute("SELECT * FROM ability_levels WHERE ability_pack=? AND ability_id=? ORDER BY level", (pack, rid)):
            out["levels"].append({
                "level": lv["level"], "name": lv["name"], "price": lv["price"],
                "effects": _effects(conn, labels, "ability", pack, rid, lv["level"]),
                "facts": _facts(labels, json.loads(lv["data"] or "{}")),
            })
        if out["levels"]:
            level_from, mode = engine.level_rules(conn, pack, rid)
            out["levels_rule"] = " ".join([
                "The level follows the character's occupation level." if level_from == "occupation"
                else "Levels are bought one at a time.",
                "Each level replaces the one before." if mode == "replace" else "Each level adds to the ones before."])
    out["related"] = _related(conn, labels, table, owner, pack, rid)
    return out


def _related(conn, labels: Labels, table: str, owner: str | None, pack: str, rid: str) -> list[dict[str, Any]]:
    rel: list[dict[str, Any]] = []

    def add(title: str, links: list[dict[str, Any] | None]) -> None:
        links = [x for x in links if x]
        if links:
            rel.append({"title": title, "rows": links})

    if table == "occupations":
        sets: dict[int, list] = {}
        for s in conn.execute("SELECT * FROM occupation_sets WHERE occupation_pack=? AND occupation_id=?"
                              " ORDER BY set_index, position", (pack, rid)):
            sets.setdefault(s["set_index"], []).append(_link(conn, labels, "abilities", s["ability_pack"], s["ability_id"]))
        for i in sorted(sets):
            add(f"Ability set {i}", sets[i])
    if table == "abilities":
        add("Part of", [_link(conn, labels, "occupations", s["occupation_pack"], s["occupation_id"], f"set {s['set_index']}")
                        for s in conn.execute("SELECT * FROM occupation_sets WHERE ability_pack=? AND ability_id=?"
                                              " ORDER BY occupation_id, set_index", (pack, rid))])
    # Rows whose requirements point at this one.
    req_kind = {"species": "species", "abilities": "ability", "occupations": "occupation_set"}.get(table)
    if req_kind:
        owners = {"species": "species", "occupation": "occupations", "ability": "abilities", "item": "items"}
        add("Required by", [
            _link(conn, labels, owners[q["owner_type"]], q["owner_pack"], q["owner_id"],
                  f"set {q['value']}" if q["kind"] == "occupation_set" else None)
            for q in conn.execute("SELECT DISTINCT owner_type, owner_pack, owner_id, kind, value FROM requirements"
                                  " WHERE kind=? AND ref_pack=? AND ref_id=? ORDER BY owner_type, owner_id",
                                  (req_kind, pack, rid))
        ])
    # Entries link to any row; show both directions.
    if table == "entries":
        add("See also", [_link(conn, labels, x["ref_table"], x["ref_pack"], x["ref_id"])
                         for x in conn.execute("SELECT * FROM entry_links WHERE entry_pack=? AND entry_id=? ORDER BY position",
                                               (pack, rid))])
    add("Mentioned in", [_link(conn, labels, "entries", x["entry_pack"], x["entry_id"])
                         for x in conn.execute("SELECT DISTINCT entry_pack, entry_id FROM entry_links"
                                               " WHERE ref_table=? AND ref_pack=? AND ref_id=? ORDER BY entry_id",
                                               (table, pack, rid))])
    # Characters who have it.
    q = {
        "species": "SELECT id, name FROM characters WHERE species_pack=? AND species_id=?",
        "occupations": "SELECT id, name FROM characters WHERE occupation_pack=? AND occupation_id=?",
        "abilities": "SELECT c.id, c.name FROM character_abilities o JOIN characters c ON c.id=o.character_id"
                     " WHERE o.ability_pack=? AND o.ability_id=?",
        "items": "SELECT c.id, c.name FROM character_items o JOIN characters c ON c.id=o.character_id"
                 " WHERE o.item_pack=? AND o.item_id=?",
    }.get(table)
    if q:
        chars = [{"table": "characters", "pack": None, "id": c["id"], "name": c["name"], "category": "characters",
                  "category_label": "Characters", "missing": False}
                 for c in conn.execute(q + " ORDER BY name", (pack, rid))]
        add("Characters", chars)
    return rel
