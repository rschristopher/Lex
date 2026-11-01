"""Fights. Dice stay on the table: Lex asks for a roll, takes the number, and does the bookkeeping.

Everything here reads owned rows through the sheet; no weapon, power, or armor is named in code.
Optional row fields the fight reads: `damage`/`prefix`/`bonus` (an attack), `durability` (a melee weapon:
can be parried and pulled), `thrown` (can be parried), `area` (no dodge or parry), `mental` (resist with
Willpower instead of Defense), `bonus_roll` (a mental attack's own bonus), `cost` (Anima, in M),
`melees` (switches off after that many melees), `total` (hits while switched on).
"""

from __future__ import annotations

import json
import random
import sqlite3
from typing import Any

from lex import dice
from lex.agility import pull_fails_on, pull_free_steps, reflex_penalty
from lex.fold import _attack_options, activated_layers, worn_pieces
from lex.prefixes import ORDER, factor, hit_factor, hit_threshold
from lex.sheet import load_adapter, resolved_doc, sheet
from lex.strength import melee_damage
from lex.willpower import willpower_resist_bonus

SHEET = "universal"  # combat reads the universal sheet; each tablet still shows its own labels
FIGHTING, DOWN, LEFT = "in", "down", "left"
CHAR_TABLES = ("character_gauges", "character_abilities", "character_items", "character_active", "timers")


class CombatError(ValueError):
    pass


# ---------------------------------------------------------------- reading


def _fight(conn: sqlite3.Connection, fid: int) -> sqlite3.Row:
    f = conn.execute("SELECT * FROM fights WHERE id=?", (fid,)).fetchone()
    if f is None:
        raise KeyError(fid)
    return f


def _combatant(conn, fid: int, cid: str) -> sqlite3.Row:
    c = conn.execute("SELECT * FROM combatants WHERE fight_id=? AND character_id=?", (fid, cid)).fetchone()
    if c is None:
        raise CombatError(f"{cid} is not in this fight")
    return c


def _all(conn, fid: int) -> list[sqlite3.Row]:
    """Every combatant in initiative order (highest first; ties keep the GM's listing order)."""
    return conn.execute(
        "SELECT * FROM combatants WHERE fight_id=? "
        "ORDER BY initiative IS NULL, initiative DESC, group_no, position", (fid,)
    ).fetchall()


def _pending(conn, fid: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT data FROM fight_pending WHERE fight_id=?", (fid,)).fetchone()
    return json.loads(r["data"]) if r else None


def _set_pending(conn, fid: int, data: dict[str, Any] | None) -> None:
    conn.execute("DELETE FROM fight_pending WHERE fight_id=?", (fid,))
    if data is not None:
        conn.execute("INSERT INTO fight_pending (fight_id, data) VALUES (?, ?)", (fid, json.dumps(data)))


def _sheet(conn, cid: str) -> dict[str, Any]:
    return sheet(conn, cid, SHEET)


def _channel(sh: dict[str, Any], cid: str) -> int:
    return next((int(c["value"]) for c in sh["channels"] if c["id"] == cid), 0)


def _reflex(sh: dict[str, Any]) -> bool:
    return any(c["id"] == "defense" and c.get("reflex") for c in sh["channels"])


def _attr(sh: dict[str, Any], aid: str) -> int:
    return int(next((a["value"] for a in sh["attrs"] if a["id"] == aid), 0) or 0)


def open_fight(conn, cid: str) -> int | None:
    r = conn.execute(
        "SELECT f.id FROM fights f JOIN combatants c ON c.fight_id = f.id "
        "WHERE c.character_id=? AND f.status != 'ended' ORDER BY f.id DESC", (cid,)
    ).fetchone()
    return r["id"] if r else None


# ---------------------------------------------------------------- undo log


def _rows(conn, sql: str, args) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(sql, args)]


def _snapshot(conn, fid: int) -> dict[str, Any]:
    cids = [r["character_id"] for r in conn.execute("SELECT character_id FROM combatants WHERE fight_id=?", (fid,))]
    marks = ",".join("?" * len(cids)) or "NULL"
    return {
        "fight": dict(_fight(conn, fid)),
        "combatants": _rows(conn, "SELECT * FROM combatants WHERE fight_id=?", (fid,)),
        "pending": _pending(conn, fid),
        "characters": cids,
        "tables": {t: _rows(conn, f"SELECT * FROM {t} WHERE character_id IN ({marks})", cids) for t in CHAR_TABLES},
    }


def _restore(conn, fid: int, snap: dict[str, Any]) -> None:
    now = [r["character_id"] for r in conn.execute("SELECT character_id FROM combatants WHERE fight_id=?", (fid,))]
    cids = sorted(set(now) | set(snap["characters"]))
    marks = ",".join("?" * len(cids)) or "NULL"
    f = snap["fight"]
    cols = [k for k in f if k != "id"]
    conn.execute(f"UPDATE fights SET {', '.join(k + '=?' for k in cols)} WHERE id=?", [f[k] for k in cols] + [fid])
    for t in CHAR_TABLES:
        conn.execute(f"DELETE FROM {t} WHERE character_id IN ({marks})", cids)
        for row in snap["tables"][t]:
            conn.execute(f"INSERT INTO {t} ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})", list(row.values()))
    conn.execute("DELETE FROM combatants WHERE fight_id=?", (fid,))
    for row in snap["combatants"]:
        conn.execute(f"INSERT INTO combatants ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})", list(row.values()))
    _set_pending(conn, fid, snap["pending"])


def _log(conn, fid: int, kind: str, actor: str | None, data: dict[str, Any], snap: dict[str, Any]) -> None:
    conn.execute("INSERT INTO fight_log (fight_id, kind, actor, data, snapshot) VALUES (?, ?, ?, ?, ?)",
                 (fid, kind, actor, json.dumps(data), json.dumps(snap)))


def _note(conn, fid: int, kind: str, actor: str | None, data: dict[str, Any]) -> None:
    """Append to the newest log entry's story without a new undo point."""
    r = conn.execute("SELECT id, data FROM fight_log WHERE fight_id=? ORDER BY id DESC LIMIT 1", (fid,)).fetchone()
    d = json.loads(r["data"])
    d.setdefault("then", []).append({"kind": kind, "actor": actor, **data})
    conn.execute("UPDATE fight_log SET data=? WHERE id=?", (json.dumps(d), r["id"]))


def undo(conn, fid: int, count: int = 1) -> None:
    """Put the fight and its characters back as they were before the last `count` steps."""
    if count < 1:
        raise CombatError("undo at least one step")
    with conn:
        entries = conn.execute("SELECT id, snapshot FROM fight_log WHERE fight_id=? ORDER BY id DESC LIMIT ?",
                               (fid, count)).fetchall()
        if len(entries) < count:
            raise CombatError("not that many steps to undo")
        oldest = entries[-1]
        _restore(conn, fid, json.loads(oldest["snapshot"]))
        conn.execute("DELETE FROM fight_log WHERE fight_id=? AND id >= ?", (fid, oldest["id"]))


# ---------------------------------------------------------------- setup and the walk


def start(conn, groups: list[dict[str, Any]], *, die: str = "d20", low: bool = False,
          pull_rule: bool = False, campaign_id: int | None = None) -> int:
    """The GM marks two or more groups as fighting. A character is in one group only."""
    dice.parse(die)
    if len(groups) < 2:
        raise CombatError("a fight is two or more groups")
    seen: set[str] = set()
    for g in groups:
        members = g.get("characters") or []
        if not members:
            raise CombatError("every group needs at least one character")
        for cid in members:
            if cid in seen:
                raise CombatError(f"{cid} is in more than one group")
            seen.add(cid)
            if conn.execute("SELECT 1 FROM characters WHERE id=?", (cid,)).fetchone() is None:
                raise CombatError(f"no character {cid}")
            if open_fight(conn, cid):
                raise CombatError(f"{cid} is already in a fight")
    with conn:
        fid = conn.execute("INSERT INTO fights (campaign_id, status, die, die_low, pull_rule) VALUES (?, 'initiative', ?, ?, ?)",
                           (campaign_id, die, int(bool(low)), int(bool(pull_rule)))).lastrowid
        for no, g in enumerate(groups):
            conn.execute("INSERT INTO fight_groups VALUES (?, ?, ?)", (fid, no, g.get("name") or f"Group {no + 1}"))
            for pos, cid in enumerate(g["characters"]):
                conn.execute("INSERT INTO combatants (fight_id, character_id, group_no, position) VALUES (?, ?, ?, ?)",
                             (fid, cid, no, pos))
    return fid


def join(conn, fid: int, cid: str, group_no: int) -> None:
    """A new character joins a group mid-fight; they roll initiative before their first action."""
    f = _fight(conn, fid)
    if f["status"] == "ended":
        raise CombatError("the fight is over")
    if conn.execute("SELECT 1 FROM fight_groups WHERE fight_id=? AND group_no=?", (fid, group_no)).fetchone() is None:
        raise CombatError("no such group")
    if open_fight(conn, cid):
        raise CombatError(f"{cid} is already in a fight")
    with conn:
        _log(conn, fid, "join", cid, {"group": group_no}, _snapshot(conn, fid))
        pos = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM combatants WHERE fight_id=? AND group_no=?",
                           (fid, group_no)).fetchone()[0]
        conn.execute("INSERT INTO combatants (fight_id, character_id, group_no, position) VALUES (?, ?, ?, ?)",
                     (fid, cid, group_no, pos))


def fresh_initiative(conn, fid: int) -> None:
    """The GM calls a fresh initiative: everyone rolls again; actions left this melee are kept."""
    f = _fight(conn, fid)
    if f["status"] == "ended":
        raise CombatError("the fight is over")
    with conn:
        _log(conn, fid, "fresh_initiative", None, {}, _snapshot(conn, fid))
        conn.execute("UPDATE combatants SET initiative=NULL, init_roll=NULL WHERE fight_id=?", (fid,))
        conn.execute("UPDATE fights SET status='initiative', current=NULL WHERE id=?", (fid,))
        _set_pending(conn, fid, None)


def roll_initiative(conn, fid: int, cid: str, value: int | None = None, rng: random.Random | None = None) -> None:
    f = _fight(conn, fid)
    if f["status"] == "ended":
        raise CombatError("the fight is over")
    c = _combatant(conn, fid, cid)
    if c["initiative"] is not None:
        raise CombatError("initiative already rolled")
    if value is None:
        value = dice.roll(f["die"], rng)
    if not dice.valid(value, f["die"]):
        raise CombatError(f"{value} is not a roll of {f['die']}")
    # The roll, read as the d20 roll with the same chance, plus the Initiative bonus.
    score = dice.d20_equivalent(value, f["die"], bool(f["die_low"])) + _channel(_sheet(conn, cid), "initiative")
    with conn:
        _log(conn, fid, "initiative", cid, {"roll": value}, _snapshot(conn, fid))
        conn.execute("UPDATE combatants SET init_roll=?, initiative=? WHERE fight_id=? AND character_id=?",
                     (value, score, fid, cid))
        waiting = conn.execute("SELECT COUNT(*) FROM combatants WHERE fight_id=? AND status=? AND initiative IS NULL",
                               (fid, FIGHTING)).fetchone()[0]
        if f["status"] == "initiative" and not waiting:
            if f["melee"] == 0:
                _new_melee(conn, fid, first=True)
            else:
                conn.execute("UPDATE fights SET status='melee' WHERE id=?", (fid,))
                _advance(conn, fid, from_top=True)


def _can_act(c: sqlite3.Row) -> bool:
    return c["status"] == FIGHTING and c["actions_left"] > 0 and c["initiative"] is not None


def _new_melee(conn, fid: int, first: bool = False) -> None:
    """Every character gets their actions back. Between melees: Anima recovers and timers count down."""
    if not first:
        _between_melees(conn, fid)
    conn.execute("UPDATE fights SET melee = melee + 1, status='melee' WHERE id=?", (fid,))
    for c in conn.execute("SELECT * FROM combatants WHERE fight_id=?", (fid,)).fetchall():
        n = max(0, _channel(_sheet(conn, c["character_id"]), "actions")) if c["status"] == FIGHTING else 0
        conn.execute("UPDATE combatants SET actions_left=?, reflex_used=0 WHERE fight_id=? AND character_id=?",
                     (n, fid, c["character_id"]))
    _advance(conn, fid, from_top=True)


def _between_melees(conn, fid: int) -> None:
    for c in conn.execute("SELECT * FROM combatants WHERE fight_id=?", (fid,)).fetchall():
        cid = c["character_id"]
        g = conn.execute("SELECT * FROM character_gauges WHERE character_id=? AND gauge='anima'", (cid,)).fetchone()
        if g and g["total"] and g["current"] is not None and g["current"] < g["total"]:
            per_minute = g["total"] * _attr(_sheet(conn, cid), "willpower") / 100
            cur = min(g["total"], g["current"] + int(per_minute / 6))
            conn.execute("UPDATE character_gauges SET current=? WHERE character_id=? AND gauge='anima'",
                         (None if cur >= g["total"] else cur, cid))
        for t in conn.execute("SELECT * FROM timers WHERE character_id=?", (cid,)).fetchall():
            if t["melees_left"] <= 1:
                conn.execute("DELETE FROM timers WHERE id=?", (t["id"],))
                conn.execute("DELETE FROM character_active WHERE character_id=? AND ref=?", (cid, t["ref"]))
            else:
                conn.execute("UPDATE timers SET melees_left = melees_left - 1 WHERE id=?", (t["id"],))


def _advance(conn, fid: int, from_top: bool = False) -> None:
    """The next character in the same order with actions left; when nobody has any, the next melee."""
    if _check_end(conn, fid):
        return
    order = _all(conn, fid)
    cur = _fight(conn, fid)["current"]
    ids = [c["character_id"] for c in order]
    start_at = 0 if from_top or cur not in ids else ids.index(cur) + 1
    for i in range(len(order)):
        c = order[(start_at + i) % len(order)]
        if _can_act(c):
            conn.execute("UPDATE fights SET current=? WHERE id=?", (c["character_id"], fid))
            return
    if from_top:  # a fresh melee and still nobody can act: the GM decides
        conn.execute("UPDATE fights SET current=NULL WHERE id=?", (fid,))
        return
    _new_melee(conn, fid)


def _check_end(conn, fid: int) -> bool:
    """The fight ends on its own when no more than one group has anyone left fighting."""
    sides = conn.execute("SELECT DISTINCT group_no FROM combatants WHERE fight_id=? AND status=?",
                         (fid, FIGHTING)).fetchall()
    if len(sides) > 1:
        return False
    names = [r["name"] for r in conn.execute(
        "SELECT name FROM fight_groups WHERE fight_id=? AND group_no NOT IN "
        "(SELECT group_no FROM combatants WHERE fight_id=? AND status=?)", (fid, fid, FIGHTING))]
    _close(conn, fid, "no one left fighting in " + ", ".join(names))
    return True


def _close(conn, fid: int, reason: str) -> None:
    conn.execute("UPDATE fights SET status='ended', current=NULL, ended_reason=? WHERE id=?", (reason, fid))
    _set_pending(conn, fid, None)
    # Between fights, Anima recovers fully. Hit points and armor stay as they are.
    conn.execute("UPDATE character_gauges SET current=NULL WHERE gauge='anima' AND character_id IN "
                 "(SELECT character_id FROM combatants WHERE fight_id=?)", (fid,))


def end(conn, fid: int) -> None:
    """The GM ends the fight at any time; leftover actions are dropped."""
    if _fight(conn, fid)["status"] == "ended":
        raise CombatError("the fight is over")
    with conn:
        _log(conn, fid, "end", None, {}, _snapshot(conn, fid))
        _close(conn, fid, "ended by the GM")


# ---------------------------------------------------------------- actions


def options(conn, cid: str) -> list[dict[str, Any]]:
    """What a character can pick on their action: attacks (need a target) and things to switch on."""
    doc = resolved_doc(conn, cid)
    out = []
    for w in _attack_options(doc):
        out.append({"id": w.get("id"), "name": w.get("name") or w.get("id"), "kind": "attack",
                    "damage": w.get("damage"), "prefix": w.get("prefix") or "unit",
                    "mental": bool(w.get("mental")), "cost": int(w.get("cost") or 0)})
    on = set(doc.get("activated") or [])
    seen = {o["id"] for o in out}
    for a in doc.get("abilities") or []:
        if a["id"] in seen or a["id"] in on or a.get("inactive"):
            continue
        if any(a.get(k) is not None for k in ("total", "melees", "cost", "slot")):
            out.append({"id": a["id"], "name": a.get("name") or a["id"], "kind": "activate",
                        "cost": int(a.get("cost") or 0)})
    for p in doc.get("armor") or []:
        if p["id"] not in on:
            out.append({"id": p["id"], "name": p.get("name") or p["id"], "kind": "activate", "cost": 0})
    return out


def _find(doc: dict[str, Any], ref: str) -> dict[str, Any] | None:
    for row in (doc.get("abilities") or []) + (doc.get("armor") or []):
        if row.get("id") == ref:
            return row
    return None


def _spend_anima(conn, cid: str, cost: int) -> None:
    if cost <= 0:
        return
    g = conn.execute("SELECT * FROM character_gauges WHERE character_id=? AND gauge='anima'", (cid,)).fetchone()
    have = 0 if g is None else (g["current"] if g["current"] is not None else int(g["total"] or 0))
    if have < cost:
        raise CombatError(f"not enough Anima: {have} M, needs {cost} M")
    conn.execute("UPDATE character_gauges SET current=? WHERE character_id=? AND gauge='anima'", (have - cost, cid))


def _raw_dice(doc: dict[str, Any], ref: str) -> str | None:
    for w in doc.get("weapons") or []:
        if w.get("id") == ref:
            return w.get("damage")
    for p in worn_pieces(doc):
        for a in p.get("attacks") or []:
            if a.get("id") == ref and a.get("damage"):
                return a["damage"]
    return None


def act(conn, fid: int, actor: str, use: str | None = None, target: str | None = None, *,
        leave: bool = False, unperceived: bool = False, pull: int | None = None) -> None:
    """The current character spends an action: an attack on a target, switching something on, or leaving."""
    f = _fight(conn, fid)
    if f["status"] != "melee":
        raise CombatError("not in a melee" if f["status"] != "ended" else "the fight is over")
    if _pending(conn, fid):
        raise CombatError("a roll is still waiting")
    if f["current"] != actor:
        raise CombatError("not this character's action")
    with conn:
        snap = _snapshot(conn, fid)
        if leave:
            _log(conn, fid, "leave", actor, {}, snap)
            conn.execute("UPDATE combatants SET status=?, actions_left=0 WHERE fight_id=? AND character_id=?",
                         (LEFT, fid, actor))
            _advance(conn, fid)
            return
        doc = resolved_doc(conn, actor)
        opt = next((o for o in options(conn, actor) if o["id"] == use), None)
        if opt is None:
            raise CombatError(f"{actor} cannot use {use!r} now")
        conn.execute("UPDATE combatants SET actions_left = actions_left - 1 WHERE fight_id=? AND character_id=?",
                     (fid, actor))
        if opt["kind"] == "activate":
            row = _find(doc, use) or {}
            _log(conn, fid, "activate", actor, {"use": use, "name": opt["name"]}, snap)
            _spend_anima(conn, actor, int(row.get("cost") or 0))
            pos = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM character_active WHERE character_id=?",
                               (actor,)).fetchone()[0]
            conn.execute("INSERT OR IGNORE INTO character_active (character_id, position, ref) VALUES (?, ?, ?)",
                         (actor, pos, use))
            if row.get("melees"):
                conn.execute("INSERT INTO timers (character_id, ref, melees_left) VALUES (?, ?, ?)",
                             (actor, use, int(row["melees"])))
            _advance(conn, fid)
            return
        t = _combatant(conn, fid, target or "")
        if t["status"] != FIGHTING or target == actor:
            raise CombatError("pick another character who is still fighting")
        weapon = next(w for w in _attack_options(doc) if w.get("id") == use)
        _spend_anima(conn, actor, int(weapon.get("cost") or 0))
        sh = _sheet(conn, actor)
        mental = bool(weapon.get("mental"))
        bonus = int(weapon.get("bonus_roll") or 0) if mental else _channel(sh, "strike")
        comps = [{"dice": weapon["damage"], "prefix": weapon.get("prefix") or "unit"}]
        comps += [{"dice": b["damage"], "prefix": b.get("prefix") or "unit"}
                  for b in weapon.get("bonus") or [] if b.get("damage")]
        p: dict[str, Any] = {
            "step": "attack", "roller": actor, "actor": actor, "target": target, "use": use,
            "name": weapon.get("name") or use, "mental": mental, "bonus": bonus,
            "area": bool(weapon.get("area")), "unperceived": bool(unperceived),
            "parry": bool(weapon.get("durability") or weapon.get("thrown")), "damage": comps,
        }
        if pull is not None:
            if not f["pull_rule"] or not weapon.get("durability"):
                raise CombatError("a blow can be pulled only with a hand-to-hand weapon, when the GM uses that rule")
            strength = _attr(sh, "strength")
            raw = _raw_dice(doc, use) or weapon["damage"]
            pulled = melee_damage(raw, strength, weapon["durability"], pulled=int(pull))
            steps = max(0, ORDER.index(comps[0]["prefix"]) - ORDER.index(pulled["prefix"]))
            p["pull"] = {"score": int(pull), "steps": steps, "fails_on": pull_fails_on(_attr(sh, "agility"), steps),
                         "dice": pulled["damage"], "prefix": pulled["prefix"]}
            if steps <= pull_free_steps(_attr(sh, "agility")):
                p["damage"][0] = {"dice": pulled["damage"], "prefix": pulled["prefix"]}
                p["pull"]["roll"] = False
        _log(conn, fid, "attack", actor, {"use": use, "name": p["name"], "target": target}, snap)
        _set_pending(conn, fid, p)


def _ask(conn, fid: int, p: dict[str, Any], step: str, roller: str, **kw) -> None:
    p = {**p, "step": step, "roller": roller, **kw}
    _set_pending(conn, fid, p)


def _finish(conn, fid: int) -> None:
    _set_pending(conn, fid, None)
    _advance(conn, fid)


def _to_damage(conn, fid: int, p: dict[str, Any]) -> None:
    pull = p.get("pull")
    if pull and pull.get("roll") is not False and "rolled" not in pull:
        _ask(conn, fid, p, "pull", p["actor"])
    else:
        _ask(conn, fid, p, "damage", p["actor"])


def roll(conn, fid: int, value: int | None = None, *, choice: str | None = None,
         values: list[int] | None = None, rng: random.Random | None = None) -> dict[str, Any]:
    """The waiting roll: typed in, or rolled by Lex when no value is given."""
    f = _fight(conn, fid)
    p = _pending(conn, fid)
    if not p:
        raise CombatError("no roll is waiting")
    die, low = f["die"], bool(f["die_low"])
    with conn:
        snap = _snapshot(conn, fid)
        step = p["step"]
        if step == "damage":
            if values is None:
                values = [dice.roll(c["dice"], rng) for c in p["damage"]]
            if len(values) != len(p["damage"]) or not all(dice.valid(v, c["dice"]) for v, c in zip(values, p["damage"])):
                raise CombatError("enter one roll for each damage dice: " + ", ".join(c["dice"] for c in p["damage"]))
            _log(conn, fid, "damage", p["actor"], {"rolls": values, "target": p["target"]}, snap)
            hits = []
            for v, c in zip(values, p["damage"]):
                hits += _harm(conn, fid, p["target"], v, c["prefix"])
            _note(conn, fid, "harm", p["target"], {"hits": hits})
            _finish(conn, fid)
            return {"hits": hits}
        if step == "pull":
            if value is None:
                value = dice.roll("d20", rng)
            if not dice.valid(value, "d20"):
                raise CombatError("a pull is rolled on a d20")
            ok = value > p["pull"]["fails_on"]
            _log(conn, fid, "pull", p["actor"], {"roll": value, "held": ok}, snap)
            p["pull"]["rolled"] = value
            if ok:
                p["damage"][0] = {"dice": p["pull"]["dice"], "prefix": p["pull"]["prefix"]}
            _to_damage(conn, fid, p)
            return {"held": ok}
        if step == "defense":
            if choice not in ("dodge", "parry", "pass"):
                raise CombatError("choose dodge, parry, or pass")
            if choice == "pass":
                _log(conn, fid, "pass", p["target"], {}, snap)
                _to_damage(conn, fid, p)
                return {"landed": True}
            if choice == "parry" and not p["parry"]:
                raise CombatError("a parry works only against melee and thrown attacks")
            d = _combatant(conn, fid, p["target"])
            sh = _sheet(conn, p["target"])
            bonus = _channel(sh, "defense")
            if _reflex(sh):
                nth = d["reflex_used"] + 1
                bonus += reflex_penalty(_attr(sh, "agility"), nth)
                change = ("reflex_used = reflex_used + 1", {})
            elif d["actions_left"] > 0:
                change = ("actions_left = actions_left - 1", {})
            else:
                raise CombatError("no action left to defend with; pass")
        else:
            bonus = p["bonus"]
        if value is None:
            value = dice.roll(die, rng)
        if not dice.valid(value, die):
            raise CombatError(f"{value} is not a roll of {die}")
        needed = dice.target(bonus, die, low)
        ok = dice.meets(value, needed, low)
        if step == "attack":
            _log(conn, fid, "attack_roll", p["actor"], {"roll": value, "needed": needed, "landed": ok}, snap)
            if not ok:
                _finish(conn, fid)
            elif p["mental"]:
                r = willpower_resist_bonus(_attr(_sheet(conn, p["target"]), "willpower"))
                _ask(conn, fid, p, "resist", p["target"], bonus=r)
            elif p["area"] or p["unperceived"]:
                _to_damage(conn, fid, p)
            else:
                _ask(conn, fid, p, "defense", p["target"])
            return {"landed": ok, "needed": needed}
        if step == "defense":
            conn_sql = f"UPDATE combatants SET {change[0]} WHERE fight_id=? AND character_id=?"
            _log(conn, fid, choice, p["target"], {"roll": value, "needed": needed, "defended": ok}, snap)
            conn.execute(conn_sql, (fid, p["target"]))
            if ok:
                _finish(conn, fid)
            else:
                _to_damage(conn, fid, p)
            return {"defended": ok, "needed": needed}
        if step == "resist":
            _log(conn, fid, "resist", p["target"], {"roll": value, "needed": needed, "resisted": ok}, snap)
            if ok or not p["damage"]:
                _finish(conn, fid)
            else:
                _to_damage(conn, fid, p)
            return {"resisted": ok, "needed": needed}
    raise CombatError(f"unknown step {step}")


def _harm(conn, fid: int, cid: str, amount: int, prefix: str) -> list[dict[str, Any]]:
    """Damage at a prefix works through the switched-on layers, then flesh. Each layer counts it at its own
    prefix; below its threshold it does nothing and stops there. What a layer cannot hold goes on inward."""
    doc = resolved_doc(conn, cid)
    adapter = load_adapter(conn, SHEET)
    ability_ids = {a["id"] for a in doc.get("abilities") or []}
    layers = activated_layers(doc, adapter)
    hp = next((g for g in doc.get("gauges") or [] if g.get("id") == "hit_points"), None)
    if hp and int(hp.get("total") or 0):
        layers.append({"id": "hit_points", "name": "Hit Points", "total": int(hp["total"]), "current": hp.get("current"),
                       "prefix": hp.get("prefix") or "unit", "factor": hit_factor(hp), "threshold": hit_threshold(hp)})
    left = float(amount) * factor(prefix)  # in plain hit points
    out = []
    for L in layers:
        cur = int(L["current"] if L.get("current") is not None else L["total"])
        if cur <= 0:
            continue
        pts = int(left / L["factor"])
        if pts < max(1, int(L.get("threshold") or 1)):
            out.append({"layer": L["id"], "taken": 0})
            break
        take = min(pts, cur)
        _set_current(conn, cid, L["id"], cur - take, ability_ids)
        out.append({"layer": L["id"], "taken": take, "left": cur - take})
        if L["id"] == "hit_points" and cur - take <= 0:
            conn.execute("UPDATE combatants SET status=?, actions_left=0 WHERE fight_id=? AND character_id=?",
                         (DOWN, fid, cid))
        if pts <= cur:
            break
        left -= take * L["factor"]
    return out


def _set_current(conn, cid: str, layer: str, value: int, ability_ids: set[str]) -> None:
    if layer == "hit_points":
        conn.execute("UPDATE character_gauges SET current=? WHERE character_id=? AND gauge='hit_points'", (value, cid))
        return
    table, col = ("character_abilities", "ability_id") if layer in ability_ids else ("character_items", "item_id")
    r = conn.execute(f"SELECT rowid, data FROM {table} WHERE character_id=? AND {col}=?", (cid, layer)).fetchone()
    d = json.loads(r["data"])
    d["current"] = value
    conn.execute(f"UPDATE {table} SET data=? WHERE rowid=?", (json.dumps(d), r["rowid"]))


# ---------------------------------------------------------------- timers (GM tooling) and the screen


def add_timer(conn, cid: str, ref: str, melees: int) -> None:
    if melees < 1:
        raise CombatError("a timer runs at least one melee")
    with conn:
        conn.execute("INSERT INTO timers (character_id, ref, melees_left) VALUES (?, ?, ?)", (cid, ref, melees))


def timers(conn) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT t.*, c.name AS character FROM timers t JOIN characters c ON c.id = t.character_id ORDER BY t.id")]


def state(conn, fid: int) -> dict[str, Any]:
    f = _fight(conn, fid)
    die, low = f["die"], bool(f["die_low"])
    order = _all(conn, fid)
    groups = []
    for g in conn.execute("SELECT * FROM fight_groups WHERE fight_id=? ORDER BY group_no", (fid,)):
        members = []
        for c in conn.execute("SELECT * FROM combatants WHERE fight_id=? AND group_no=? ORDER BY position",
                              (fid, g["group_no"])):
            sh = _sheet(conn, c["character_id"])
            members.append({
                "id": c["character_id"], "name": sh["name"], "npc": sh["npc"], "owner": sh["owner"],
                "status": c["status"], "initiative": c["initiative"], "init_roll": c["init_roll"],
                "actions_left": c["actions_left"], "defense": sh["defense"]["armor"], "anima": sh["anima"],
                "activated": sh["activated"],
            })
        groups.append({"no": g["group_no"], "name": g["name"], "combatants": members})
    p = _pending(conn, fid)
    if p:
        if p["step"] == "damage":
            p["ask"] = "roll damage: " + " + ".join(f"{c['dice']} at {c['prefix']}" for c in p["damage"])
        elif p["step"] == "pull":
            p["ask"] = f"roll a d20 to pull the blow: fails on {p['pull']['fails_on']} or lower"
        else:
            bonus = p["bonus"] if p["step"] in ("attack", "resist") else None
            if p["step"] == "defense":
                sh = _sheet(conn, p["target"])
                bonus = _channel(sh, "defense")
                c = _combatant(conn, fid, p["target"])
                if _reflex(sh):
                    bonus += reflex_penalty(_attr(sh, "agility"), c["reflex_used"] + 1)
                p["choices"] = ["dodge", "parry", "pass"] if p["parry"] else ["dodge", "pass"]
                p["needs_action"] = not _reflex(sh)
            p["needed"] = dice.target(bonus, die, low)
            p["ask"] = f"{p['step']}: roll {die}, {dice.describe(p['needed'], low)}"
    log = [{"id": r["id"], "kind": r["kind"], "actor": r["actor"], **json.loads(r["data"])}
           for r in conn.execute("SELECT * FROM fight_log WHERE fight_id=? ORDER BY id DESC LIMIT 40", (fid,))]
    return {
        "id": fid, "status": f["status"], "melee": f["melee"], "die": die, "low": low,
        "pull_rule": bool(f["pull_rule"]), "current": f["current"], "ended": f["ended_reason"],
        "order": [c["character_id"] for c in order if c["status"] == FIGHTING],
        "groups": groups, "pending": p,
        "options": options(conn, f["current"]) if f["current"] and not p else [],
        "log": log,
        "timers": [t for t in timers(conn) if t["character_id"] in {c["character_id"] for c in order}],
    }
