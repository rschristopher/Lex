"""Foundation bake-off: the deterministic half.

Candidates are foundations: a Lex pack directory, or an answer-key directory (JSON lists of rows with a
`name`, loaded from a path given at run time and never stored in the repo). Each round holds one candidate
out as the answer key and scores every other candidate on how well it predicts that key from the stories.

Only three steps need an LLM, and each one saves a JSON artifact that `validate_*` checks:

stories/<story>.json  reading a story into needs, characters, and beats
  {"id", "title", "source": {"work", "text"?: file next to it, for quote checks},
   "needs": [{"id", "kind": "species"|"occupation"|"ability", "text", "beats": [beat ids]}],
   "characters": [{"id", "name", "species"?: need, "occupation"?: need, "abilities": [needs],
                   "attrs": {attr: {"value": n, "beats": [...]} | {"derive": "lift"|"move", "beats": [...]}}}],
   "beats": [{"id", "quote", "summary"?,
              "grants": [{"character", "need", "from"?}],          temporary, this beat only
              "checks": [{"character", "outcome": "success"|"failure", "kind": ...}]}]}
  check kinds: "roll" with "terms": [{"channel": c} | {"attr_bonus": a} | {"const": n}];
               "lift" with "mass_kg"; "move" with "distance_m" and "seconds"; "has" with "need".
mappings/<candidate>/<story>.<run>.json  a story's needs onto one candidate's rows
  {"story", "candidate", "run", "map": {need: {"fit": "exact"|"partial"|"none", "rows": [row ids],
                                             "new_row"?: {"kind", "name"}}}}
crosswalks/<from>__<to>.<run>.json  one candidate's rows onto another's
  {"from", "to", "run", "map": {row id: [row ids]}}

A row id is "<category>/<id>": species/..., occupation/..., ability/... for a pack; for an answer key the
category is the file name and the id is the row name made lowercase with dashes.

Everything else is here and deterministic: loading, leave-one-out rotation, building characters through the
engine, beat odds from the dice math (no random rolls), the metrics, and the report.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from lex import db, dice, engine, packs
from lex.agility import AGILITY_CHANNELS, agility_bonus
from lex.endurance import endurance_resist_bonus
from lex.fold import _apply_channels, _worn_attr_values
from lex.intellect import intellect_bonus
from lex.sheet import resolved_doc
from lex.speed import top_speed_ms
from lex.strength import lift_kg
from lex.willpower import willpower_resist_bonus

KEYS_ENV = "LEX_BAKEOFF_KEYS"
NEED_KINDS = ("species", "occupation", "ability")
PACK_CATEGORIES = {"species": "species", "occupation": "occupations", "ability": "abilities"}
FITS = ("exact", "partial", "none")
OUTCOMES = ("success", "failure")
CHECK_KINDS = ("roll", "lift", "move", "has")
# d20-scale bonuses from an attribute that the docs define. Anything else is a stub (see STUBS).
ATTR_BONUS = {"agility": agility_bonus, "intellect": intellect_bonus, "willpower": willpower_resist_bonus,
              "endurance": endurance_resist_bonus}
STUBS = {
    "attr_bonus:strength": "Strength has no d20 bonus in the docs; use a lift check",
    "attr_bonus:speed": "Speed gives no roll bonus in the docs; use a move check",
    "attr_bonus:appearance": "Appearance affects no game mechanics",
}


class BakeoffError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- candidates


class Candidate:
    """A foundation: its id, its rows, and (for a Lex pack) the directory the engine imports."""

    def __init__(self, cid: str, rows: dict[str, str], pack_dir: Path | None = None, private: bool = False):
        self.id = cid
        self.rows = rows  # row id -> name
        self.pack_dir = pack_dir
        self.private = private

    @property
    def is_pack(self) -> bool:
        return self.pack_dir is not None


def load_pack_candidate(path: str | Path) -> Candidate:
    doc = packs.read_pack(Path(path))
    rows: dict[str, str] = {}
    for cat, key in PACK_CATEGORIES.items():
        for r in doc[key]:
            if isinstance(r, dict) and r.get("id"):
                rows[f"{cat}/{r['id']}"] = r.get("name") or r["id"]
    return Candidate(doc["id"], rows, pack_dir=Path(path))


def load_key_candidate(label: str, path: str | Path) -> Candidate:
    """Every top-level *.json list of objects with a `name` is a category of rows."""
    path = Path(path)
    if not path.is_dir():
        raise BakeoffError([f"answer key {label}: {path} is not a directory"])
    rows: dict[str, str] = {}
    for f in sorted(path.glob("*.json")):
        try:
            data = _read(f)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, list):
            continue
        for r in data:
            if isinstance(r, dict) and isinstance(r.get("name"), str) and slug(r["name"]):
                rows.setdefault(f"{f.stem}/{slug(r['name'])}", r["name"])
    if not rows:
        raise BakeoffError([f"answer key {label}: no rows in {path}"])
    return Candidate(label, rows, private=True)


def parse_keys(specs: list[str] | None) -> list[tuple[str, str]]:
    """LABEL=PATH pairs from flags, else from LEX_BAKEOFF_KEYS (separated by the path separator)."""
    if not specs:
        env = os.environ.get(KEYS_ENV, "")
        specs = [s for s in env.split(os.pathsep) if s]
    out = []
    for s in specs:
        label, sep, p = s.partition("=")
        if not sep or not label or not p:
            raise BakeoffError([f"answer key must be LABEL=PATH: {s!r}"])
        out.append((label, p))
    return out


def load_candidates(pack_dirs: list[str], key_specs: list[str] | None) -> list[Candidate]:
    cands = [load_pack_candidate(p) for p in pack_dirs] + [load_key_candidate(l, p) for l, p in parse_keys(key_specs)]
    seen: set[str] = set()
    for c in cands:
        if c.id in seen:
            raise BakeoffError([f"two candidates are both called {c.id!r}"])
        seen.add(c.id)
    return cands


# ---------------------------------------------------------------- artifact validation


def _ids(rows: Any, where: str, errors: list[str]) -> list[str]:
    if not isinstance(rows, list):
        errors.append(f"{where}: must be a list")
        return []
    out = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not isinstance(r.get("id"), str) or not r["id"]:
            errors.append(f"{where}[{i}]: needs an id")
            continue
        if r["id"] in out:
            errors.append(f"{where}[{i}]: duplicate id {r['id']!r}")
        out.append(r["id"])
    return out


def _norm(text: str) -> str:
    return " ".join(text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').split())


def validate_story(doc: Any, source_text: str | None = None) -> list[str]:
    """Every need, attribute, and check traces to a beat, and every quote is in the source text when given."""
    e: list[str] = []
    if not isinstance(doc, dict) or not isinstance(doc.get("id"), str):
        return ["story: needs an id"]
    beats = _ids(doc.get("beats"), "beats", e)
    needs = _ids(doc.get("needs"), "needs", e)
    chars = _ids(doc.get("characters"), "characters", e)
    need_kind = {n["id"]: n.get("kind") for n in doc.get("needs") or [] if isinstance(n, dict)}
    src = _norm(source_text) if source_text is not None else None

    def cited(where: str, refs: Any) -> None:
        if not isinstance(refs, list) or not refs:
            e.append(f"{where}: must cite at least one beat")
            return
        for b in refs:
            if b not in beats:
                e.append(f"{where}: unknown beat {b!r}")

    for n in doc.get("needs") or []:
        if not isinstance(n, dict):
            continue
        w = f"needs/{n.get('id')}"
        if n.get("kind") not in NEED_KINDS:
            e.append(f"{w}: kind must be one of {', '.join(NEED_KINDS)}")
        if not isinstance(n.get("text"), str) or not n["text"]:
            e.append(f"{w}: needs text")
        cited(w, n.get("beats"))

    def need_ref(where: str, ref: Any, kind: str | None = None) -> None:
        if ref not in needs:
            e.append(f"{where}: unknown need {ref!r}")
        elif kind and need_kind.get(ref) != kind:
            e.append(f"{where}: need {ref!r} is not a {kind}")

    for c in doc.get("characters") or []:
        if not isinstance(c, dict):
            continue
        w = f"characters/{c.get('id')}"
        if not isinstance(c.get("name"), str) or not c["name"]:
            e.append(f"{w}: needs a name")
        for k in ("species", "occupation"):
            if c.get(k) is not None:
                need_ref(f"{w}.{k}", c[k], k)
        for i, a in enumerate(c.get("abilities") or []):
            need_ref(f"{w}.abilities[{i}]", a, "ability")
        attrs = c.get("attrs") or {}
        if not isinstance(attrs, dict):
            e.append(f"{w}.attrs: must be an object")
            attrs = {}
        for k, v in attrs.items():
            aw = f"{w}.attrs.{k}"
            if k not in engine.ATTRIBUTES:
                e.append(f"{aw}: not a Lex attribute")
                continue
            if not isinstance(v, dict):
                e.append(f"{aw}: must be an object with beats")
                continue
            if "derive" in v:
                if v["derive"] not in ("lift", "move") or (v["derive"], k) not in (("lift", "strength"), ("move", "speed")):
                    e.append(f"{aw}: only strength derives from lift and speed from move")
            elif not isinstance(v.get("value"), (int, float)) or isinstance(v.get("value"), bool) or v["value"] < 0:
                e.append(f"{aw}: needs a value (a number, 0 or more) or derive")
            cited(aw, v.get("beats"))

    for b in doc.get("beats") or []:
        if not isinstance(b, dict):
            continue
        w = f"beats/{b.get('id')}"
        q = b.get("quote")
        if not isinstance(q, str) or not q.strip():
            e.append(f"{w}: needs a quote from the story")
        elif src is not None and _norm(q) not in src:
            e.append(f"{w}: quote is not in the source text")
        for i, g in enumerate(b.get("grants") or []):
            gw = f"{w}.grants[{i}]"
            if not isinstance(g, dict) or g.get("character") not in chars:
                e.append(f"{gw}: unknown character")
                continue
            need_ref(gw, g.get("need"), "ability")
        for i, ch in enumerate(b.get("checks") or []):
            cw = f"{w}.checks[{i}]"
            if not isinstance(ch, dict):
                e.append(f"{cw}: must be an object")
                continue
            if ch.get("character") not in chars:
                e.append(f"{cw}: unknown character {ch.get('character')!r}")
            if ch.get("outcome") not in OUTCOMES:
                e.append(f"{cw}: outcome must be success or failure")
            kind = ch.get("kind")
            if kind not in CHECK_KINDS:
                e.append(f"{cw}: kind must be one of {', '.join(CHECK_KINDS)}")
            elif kind == "roll":
                terms = ch.get("terms")
                if not isinstance(terms, list) or not terms:
                    e.append(f"{cw}: a roll needs terms")
                for t in terms or []:
                    if not (isinstance(t, dict) and len(t) == 1 and (
                            isinstance(t.get("channel"), str) or t.get("attr_bonus") in engine.ATTRIBUTES
                            or (isinstance(t.get("const"), int) and not isinstance(t.get("const"), bool)))):
                        e.append(f"{cw}: a term is {{channel}}, {{attr_bonus: attribute}}, or {{const: whole number}}")
            elif kind == "lift" and not _positive(ch.get("mass_kg")):
                e.append(f"{cw}: lift needs mass_kg")
            elif kind == "move" and not (_positive(ch.get("distance_m")) and _positive(ch.get("seconds"))):
                e.append(f"{cw}: move needs distance_m and seconds")
            elif kind == "has":
                need_ref(cw, ch.get("need"), "ability")
    used = {r for n in doc.get("needs") or [] if isinstance(n, dict) for r in (n.get("beats") or [])}
    for b in beats:
        bd = next(x for x in doc["beats"] if isinstance(x, dict) and x.get("id") == b)
        if b not in used and not bd.get("checks") and not bd.get("grants"):
            e.append(f"beats/{b}: no need, check, or grant uses it")
    return e


def _positive(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def validate_mapping(doc: Any, story: dict[str, Any], cand: Candidate) -> list[str]:
    e: list[str] = []
    if not isinstance(doc, dict):
        return ["mapping: must be an object"]
    if doc.get("story") != story["id"]:
        e.append(f"mapping: story is {doc.get('story')!r}, expected {story['id']!r}")
    if doc.get("candidate") != cand.id:
        e.append(f"mapping: candidate is {doc.get('candidate')!r}, expected {cand.id!r}")
    m = doc.get("map")
    if not isinstance(m, dict):
        return e + ["mapping: map must be an object"]
    needs = {n["id"]: n["kind"] for n in story["needs"]}
    for n in needs:
        if n not in m:
            e.append(f"mapping: need {n!r} is not mapped (use fit none)")
    for n, v in m.items():
        w = f"mapping.{n}"
        if n not in needs:
            e.append(f"{w}: not a need of the story")
            continue
        if not isinstance(v, dict) or v.get("fit") not in FITS:
            e.append(f"{w}: fit must be exact, partial, or none")
            continue
        rows = v.get("rows") or []
        if not isinstance(rows, list):
            e.append(f"{w}.rows: must be a list")
            continue
        if v["fit"] == "none" and rows:
            e.append(f"{w}: fit none has no rows")
        if v["fit"] != "none" and not rows:
            e.append(f"{w}: fit {v['fit']} needs rows")
        for r in rows:
            if r not in cand.rows:
                e.append(f"{w}: {cand.id} has no row {r!r}")
            elif cand.is_pack and r.split("/", 1)[0] != needs[n]:
                e.append(f"{w}: a {needs[n]} need maps to {needs[n]} rows, not {r!r}")
        nr = v.get("new_row")
        if nr is not None and not (isinstance(nr, dict) and isinstance(nr.get("name"), str) and nr["name"]):
            e.append(f"{w}.new_row: needs a name")
    return e


def validate_crosswalk(doc: Any, src: Candidate, dst: Candidate) -> list[str]:
    e: list[str] = []
    if not isinstance(doc, dict) or doc.get("from") != src.id or doc.get("to") != dst.id:
        return [f"crosswalk: from/to must be {src.id!r}/{dst.id!r}"]
    m = doc.get("map")
    if not isinstance(m, dict):
        return ["crosswalk: map must be an object"]
    for r, targets in m.items():
        if r not in src.rows:
            e.append(f"crosswalk.{r}: {src.id} has no such row")
        if not isinstance(targets, list):
            e.append(f"crosswalk.{r}: must be a list")
            continue
        for t in targets:
            if t not in dst.rows:
                e.append(f"crosswalk.{r}: {dst.id} has no row {t!r}")
    return e


# ---------------------------------------------------------------- loading a bake-off directory


class Bakeoff:
    def __init__(self, root: str | Path, candidates: list[Candidate]):
        self.root = Path(root)
        self.candidates = {c.id: c for c in candidates}
        self.stories: dict[str, dict[str, Any]] = {}
        self.quotes_checked: dict[str, bool] = {}
        self.mappings: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.crosswalks: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.digests: dict[str, str] = {}
        self.errors: list[str] = []
        self._load()

    def _json(self, path: Path) -> Any:
        raw = path.read_bytes()
        self.digests[str(path.relative_to(self.root))] = hashlib.sha256(raw).hexdigest()[:16]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as ex:
            self.errors.append(f"{path.relative_to(self.root)}: not JSON ({ex})")
            return None

    def _load(self) -> None:
        for p in sorted((self.root / "stories").glob("*.json")):
            doc = self._json(p)
            if doc is None:
                continue
            text = None
            ref = (doc.get("source") or {}).get("text") if isinstance(doc, dict) else None
            if ref:
                tp = p.parent / ref
                if tp.is_file():
                    text = tp.read_text(encoding="utf-8")
                    self.digests[str(tp.relative_to(self.root))] = hashlib.sha256(tp.read_bytes()).hexdigest()[:16]
                else:
                    self.errors.append(f"{p.name}: source text {ref} is missing")
            errs = validate_story(doc, text)
            self.errors += [f"stories/{p.name}: {x}" for x in errs]
            if not errs:
                self.stories[doc["id"]] = doc
                self.quotes_checked[doc["id"]] = text is not None
        for cid, cand in self.candidates.items():
            for p in sorted((self.root / "mappings" / cid).glob("*.json")):
                story_id = p.name.split(".")[0]
                doc = self._json(p)
                if doc is None:
                    continue
                if story_id not in self.stories:
                    self.errors.append(f"mappings/{cid}/{p.name}: no valid story {story_id!r}")
                    continue
                errs = validate_mapping(doc, self.stories[story_id], cand)
                self.errors += [f"mappings/{cid}/{p.name}: {x}" for x in errs]
                if not errs:
                    self.mappings.setdefault((cid, story_id), []).append(doc)
        for p in sorted((self.root / "crosswalks").glob("*.json")):
            pair = p.name.split(".")[0].split("__")
            if len(pair) != 2 or not all(x in self.candidates for x in pair):
                continue  # a crosswalk for a candidate not in this run
            doc = self._json(p)
            if doc is None:
                continue
            errs = validate_crosswalk(doc, self.candidates[pair[0]], self.candidates[pair[1]])
            self.errors += [f"crosswalks/{p.name}: {x}" for x in errs]
            if not errs:
                self.crosswalks.setdefault((pair[0], pair[1]), []).append(doc)

    def check(self) -> None:
        if self.errors:
            raise BakeoffError(self.errors)
        if not self.stories:
            raise BakeoffError([f"{self.root}/stories: no story beat files"])


# ---------------------------------------------------------------- beats through the engine


def _mapped(mapping: dict[str, Any], need: str | None, category: str) -> list[str]:
    if need is None:
        return []
    return [r.split("/", 1)[1] for r in mapping["map"][need].get("rows") or [] if r.startswith(category + "/")]


def derive_attrs(story: dict[str, Any], char: dict[str, Any]) -> dict[str, float]:
    """Attribute values from the story: given ones, and the least Strength or Speed its successful beats need."""
    out: dict[str, float] = {}
    for k, v in (char.get("attrs") or {}).items():
        if "value" in v:
            out[k] = v["value"]
            continue
        need = 0
        for b in story["beats"]:
            if b["id"] not in v["beats"]:
                continue
            for ch in b.get("checks") or []:
                if ch["character"] != char["id"] or ch["outcome"] != "success" or ch["kind"] != v["derive"]:
                    continue
                for s in range(1, 101):
                    ok = lift_kg(s) >= ch["mass_kg"] if v["derive"] == "lift" else \
                        top_speed_ms(s) * ch["seconds"] >= ch["distance_m"]
                    if ok or s == 100:
                        need = max(need, s)
                        break
        out[k] = need or 1
    return out


def _check_odds(conn: sqlite3.Connection, cid: str, ch: dict[str, Any], mapping: dict[str, Any],
                pack_id: str, die: str) -> dict[str, Any]:
    doc = resolved_doc(conn, cid)
    attrs = _worn_attr_values(doc.get("attrs") or {}, doc)
    kind = ch["kind"]
    if kind == "roll":
        raw, _ = _apply_channels(doc)
        bonus = 0
        for t in ch["terms"]:
            if "const" in t:
                bonus += t["const"]
            elif "channel" in t:
                bonus += int(raw.get(t["channel"]) or 0)
                if t["channel"] in AGILITY_CHANNELS:
                    bonus += agility_bonus(attrs.get("agility") or 0)
            else:
                a = t["attr_bonus"]
                if a not in ATTR_BONUS:
                    return {"stub": f"attr_bonus:{a}", "why": STUBS.get(f"attr_bonus:{a}", "no formula")}
                bonus += ATTR_BONUS[a](attrs.get(a) or 0)
        needed = dice.target(bonus, die)
        p = round(sum(q for t, q in dice.distribution(die).items() if t >= needed), 6)
        return {"p": p, "bonus": bonus, "needed": dice.describe(needed), "die": die}
    if kind == "lift":
        cap = lift_kg(attrs.get("strength") or 0)
        return {"p": 1.0 if cap >= ch["mass_kg"] else 0.0, "lift_kg": round(cap, 1)}
    if kind == "move":
        reach = top_speed_ms(attrs.get("speed") or 0) * ch["seconds"]
        return {"p": 1.0 if reach >= ch["distance_m"] else 0.0, "reach_m": round(reach, 1)}
    # has: a working (not constraint-broken) owned row mapped from the need.
    rows = set(_mapped(mapping, ch["need"], "ability"))
    working = {a["id"] for a in doc["abilities"] if a.get("pack") == pack_id and not a.get("inactive")}
    return {"p": 1.0 if rows & working else 0.0}


def simulate(cand: Candidate, story: dict[str, Any], mapping: dict[str, Any], die: str = "d20") -> dict[str, Any]:
    """Build the story's characters from one pack's rows and score every check against its beat's outcome."""
    conn = db.connect(":memory:")
    try:
        packs.import_pack(conn, cand.pack_dir)
        pid = conn.execute("SELECT id FROM packs").fetchone()["id"]
        chars = []
        for c in story["characters"]:
            sp = _mapped(mapping, c.get("species"), "species")
            oc = _mapped(mapping, c.get("occupation"), "occupation")
            ab = sorted({a for n in c.get("abilities") or [] for a in _mapped(mapping, n, "ability")})
            chars.append({
                "id": f"bk-{c['id']}", "name": c["name"], "npc": True,
                "species": f"{pid}:{sp[0]}" if sp else None, "occupation": f"{pid}:{oc[0]}" if oc else None,
                "attrs": derive_attrs(story, c), "abilities": [f"{pid}:{a}" for a in ab],
            })
        sdoc = {"id": "bakeoff-story", "name": story["id"], "adapter": None, "species": [], "occupations": [],
                "abilities": [], "items": [], "characters": chars, "portraits": {}, "lore": []}
        packs.import_pack(conn, sdoc)
        checks = []
        for b in story["beats"]:
            granted: list[tuple[str, str]] = []
            for g in b.get("grants") or []:
                cid = f"bk-{g['character']}"
                for a in _mapped(mapping, g["need"], "ability"):
                    if (pid, a) not in engine.owned_abilities(conn, cid):
                        engine.buy_ability(conn, cid, pid, a, grant=True)
                        granted.append((cid, a))
            for i, ch in enumerate(b.get("checks") or []):
                r = _check_odds(conn, f"bk-{ch['character']}", ch, mapping, pid, die)
                row = {"beat": b["id"], "check": i, "character": ch["character"], "kind": ch["kind"],
                       "outcome": ch["outcome"], "granted": bool(granted), **r}
                if "p" in r:
                    row["likelihood"] = r["p"] if ch["outcome"] == "success" else round(1.0 - r["p"], 6)
                checks.append(row)
            with conn:
                for cid, a in granted:
                    conn.execute("DELETE FROM character_abilities WHERE character_id=? AND ability_pack=? AND ability_id=?",
                                 (cid, pid, a))
        return {"checks": checks, "characters": {c["id"]: c for c in chars}}
    finally:
        conn.close()


# ---------------------------------------------------------------- metrics


def _jaccard(a: set[str], b: set[str]) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def agreement(maps: list[dict[str, list[str]]], keys: list[str]) -> float | None:
    """Mean pairwise Jaccard of row sets per key across runs; None with fewer than two runs."""
    if len(maps) < 2 or not keys:
        return None
    scores = [_jaccard(set(a.get(k) or []), set(b.get(k) or [])) for a, b in itertools.combinations(maps, 2) for k in keys]
    return sum(scores) / len(scores)


def _need_rows(m: dict[str, Any]) -> dict[str, list[str]]:
    return {n: v.get("rows") or [] for n, v in m["map"].items()}


def match(f_map: dict[str, Any], walk: dict[str, Any], k_map: dict[str, Any]) -> dict[str, int]:
    """Needs the key covers, and how many of them the foundation's rows, walked across, land on."""
    scored = hit = 0
    for n, kv in k_map["map"].items():
        truth = set(kv.get("rows") or [])
        if not truth:
            continue
        scored += 1
        pred = {t for r in f_map["map"][n].get("rows") or [] for t in walk["map"].get(r) or []}
        hit += bool(pred & truth)
    return {"scored": scored, "hit": hit}


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def foundation_stats(bk: Bakeoff, cid: str, die: str) -> dict[str, Any]:
    """Everything about one candidate that does not depend on the held-out key."""
    cand = bk.candidates[cid]
    fits = {f: 0 for f in FITS}
    new_rows: set[str] = set()
    likes: list[float] = []
    impossible: list[dict[str, Any]] = []
    stubbed: list[dict[str, Any]] = []
    consistency: list[float] = []
    missing = []
    for sid, story in sorted(bk.stories.items()):
        runs = bk.mappings.get((cid, sid))
        if not runs:
            missing.append(sid)
            continue
        first = runs[0]
        for n, v in sorted(first["map"].items()):
            fits[v["fit"]] += 1
            if v["fit"] == "none":
                new_rows.add(slug((v.get("new_row") or {}).get("name") or n))
        c = agreement([_need_rows(m) for m in runs], sorted(first["map"]))
        if c is not None:
            consistency.append(c)
        if cand.is_pack:
            for run in runs:
                for ch in simulate(cand, story, run, die)["checks"]:
                    tag = {"story": sid, "run": run.get("run"), "beat": ch["beat"], "character": ch["character"]}
                    if "stub" in ch:
                        stubbed.append({**tag, "stub": ch["stub"]})
                        continue
                    likes.append(ch["likelihood"])
                    if ch["likelihood"] == 0:
                        impossible.append({**tag, "kind": ch["kind"]})
    total = sum(fits.values())
    return {
        "candidate": cid, "engine": cand.is_pack, "missing_mappings": missing,
        "fits": fits, "coverage": (fits["exact"] + fits["partial"]) / total if total else None,
        "new_rows": len(new_rows), "new_row_names": sorted(new_rows),
        "believability": _mean(likes) if cand.is_pack else None,
        "checks": len(likes), "impossible": impossible, "stubbed": stubbed,
        "mapping_consistency": _mean(consistency),
    }


def score_round(bk: Bakeoff, key: str, stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for fid in sorted(bk.candidates):
        if fid == key:
            continue
        walks = bk.crosswalks.get((fid, key)) or []
        scored = hit = 0
        rates: list[float] = []
        missing = []
        if not walks:
            missing.append(f"crosswalk {fid}__{key}")
        for sid in sorted(bk.stories):
            fr, kr = bk.mappings.get((fid, sid)), bk.mappings.get((key, sid))
            if not fr:
                missing.append(f"mapping {fid}/{sid}")
            if not kr:
                missing.append(f"mapping {key}/{sid}")
            if not (fr and kr and walks):
                continue
            for f_map, walk, k_map in itertools.product(fr, walks, kr):
                m = match(f_map, walk, k_map)
                if m["scored"]:
                    rates.append(m["hit"] / m["scored"])
            m0 = match(fr[0], walks[0], kr[0])
            scored += m0["scored"]
            hit += m0["hit"]
        used = sorted({r for sid in bk.stories for m in bk.mappings.get((fid, sid)) or [] for v in m["map"].values()
                       for r in v.get("rows") or []})
        s = stats[fid]
        rows.append({
            "foundation": fid, "match_rate": _mean(rates), "needs_scored": scored, "needs_hit": hit,
            "coverage": s["coverage"], "new_rows": s["new_rows"], "believability": s["believability"],
            "impossible": len(s["impossible"]), "stubbed": len(s["stubbed"]),
            "mapping_consistency": s["mapping_consistency"],
            "crosswalk_consistency": agreement([w["map"] for w in walks], used),
            "unwalked_rows": len([r for r in used if walks and r not in walks[0]["map"]]),
            "missing": missing,
        })
    return {"key": key, "foundations": rows}


def run(bk: Bakeoff, die: str = "d20") -> dict[str, Any]:
    """Leave-one-out: every candidate is the answer key once."""
    bk.check()
    dice.parse(die)
    stats = {cid: foundation_stats(bk, cid, die) for cid in sorted(bk.candidates)}
    rounds = [score_round(bk, key, stats) for key in sorted(bk.candidates)]
    summary = []
    for cid in sorted(bk.candidates):
        rates = [f["match_rate"] for r in rounds for f in r["foundations"]
                 if f["foundation"] == cid and f["match_rate"] is not None]
        s = stats[cid]
        summary.append({"candidate": cid, "mean_match_rate": _mean(rates), "rounds_scored": len(rates),
                        "coverage": s["coverage"], "new_rows": s["new_rows"], "believability": s["believability"],
                        "mapping_consistency": s["mapping_consistency"]})
    summary.sort(key=lambda r: (-(r["mean_match_rate"] if r["mean_match_rate"] is not None else -1),
                                -(r["coverage"] or 0), r["new_rows"], r["candidate"]))
    return {
        "die": die,
        "stories": {sid: {"title": s.get("title"), "needs": len(s["needs"]), "beats": len(s["beats"]),
                          "quotes_checked": bk.quotes_checked[sid]} for sid, s in sorted(bk.stories.items())},
        "candidates": {cid: {"engine": c.is_pack, "rows": len(c.rows)} for cid, c in sorted(bk.candidates.items())},
        "inputs": dict(sorted(bk.digests.items())),
        "foundations": stats,
        "rounds": rounds,
        "summary": summary,
        "stubs": sorted({s["stub"] for st in stats.values() for s in st["stubbed"]}),
    }


# ---------------------------------------------------------------- report text


def _pct(v: float | None) -> str:
    return "-" if v is None else f"{100 * v:.0f}%"


def _table(head: list[str], rows: list[list[str]]) -> str:
    w = [max(len(str(x)) for x in col) for col in zip(head, *rows)]
    line = lambda r: "  ".join(str(x).ljust(n) for x, n in zip(r, w)).rstrip()
    return "\n".join([line(head), line(["-" * n for n in w])] + [line(r) for r in rows])


def text_report(rep: dict[str, Any]) -> str:
    out = [f"Bake-off: {len(rep['candidates'])} candidates, {len(rep['stories'])} stories, die {rep['die']}"]
    for sid, s in rep["stories"].items():
        out.append(f"  {sid}: {s['needs']} needs, {s['beats']} beats, quotes {'checked' if s['quotes_checked'] else 'NOT checked'}")
    head = ["foundation", "match", "scored", "coverage", "new rows", "believable", "impossible", "stubbed",
            "map runs agree", "walk runs agree"]
    for r in rep["rounds"]:
        out += ["", f"Round: answer key {r['key']} held out"]
        out.append(_table(head, [[f["foundation"], _pct(f["match_rate"]), f"{f['needs_hit']}/{f['needs_scored']}",
                                  _pct(f["coverage"]), f["new_rows"], _pct(f["believability"]), f["impossible"],
                                  f["stubbed"], _pct(f["mapping_consistency"]), _pct(f["crosswalk_consistency"])]
                                 for f in r["foundations"]]))
        for f in r["foundations"]:
            if f["missing"]:
                out.append(f"  {f['foundation']} missing: {', '.join(f['missing'])}")
    out += ["", "Summary (mean over rounds)"]
    out.append(_table(["candidate", "match", "rounds", "coverage", "new rows", "believable", "map runs agree"],
                      [[s["candidate"], _pct(s["mean_match_rate"]), s["rounds_scored"], _pct(s["coverage"]),
                        s["new_rows"], _pct(s["believability"]), _pct(s["mapping_consistency"])]
                       for s in rep["summary"]]))
    if rep["stubs"]:
        out += ["", "Stubbed checks (no rule in the docs yet): " + ", ".join(rep["stubs"])]
    return "\n".join(out) + "\n"


def write_report(rep: dict[str, Any], dest: str | Path) -> Path:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "report.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (dest / "report.txt").write_text(text_report(rep), encoding="utf-8")
    return dest
