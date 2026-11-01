import json

import pytest

from lex import combat, dice, packs
from lex.combat import CombatError


def _test_pack(conn, tmp_path):
    """Test-only rows: a cost-bearing attack, a timed ward, and a mental attack. Nothing here is shipped."""
    d = tmp_path / "combat-test"
    d.mkdir()
    (d / "pack.json").write_text(json.dumps({"id": "combat-test", "name": "Combat test", "depends": ["universal"]}))
    (d / "abilities.json").write_text(json.dumps([
        {"id": "spark", "name": "Spark", "kind": "spell", "damage": "2d6", "prefix": "unit", "cost": 5},
        {"id": "ward", "name": "Ward", "kind": "spell", "slot": "spell", "total": 10, "prefix": "unit",
         "cost": 3, "melees": 2},
        {"id": "lure", "name": "Lure", "kind": "psionic", "mental": True, "bonus_roll": 2,
         "damage": "1d6", "prefix": "unit"},
    ]))
    packs.import_pack(conn, d)
    for pos, aid in enumerate(("spark", "ward", "lure"), start=50):
        conn.execute("INSERT INTO character_abilities (character_id, position, ability_pack, ability_id) VALUES (?, ?, ?, ?)",
                     ("pc-calder", pos, "combat-test", aid))
    conn.commit()


def _st(conn, fid):
    return combat.state(conn, fid)


def _who(st, cid):
    return next(c for g in st["groups"] for c in g["combatants"] if c["id"] == cid)


def _seg(st, cid, layer):
    return next(s for s in _who(st, cid)["defense"]["segments"] if s["id"] == layer)


def _fight(conn):
    fid = combat.start(conn, [{"name": "Adepts", "characters": ["pc-calder"]},
                              {"name": "Raiders", "characters": ["pc-kesh"]}])
    combat.roll_initiative(conn, fid, "pc-calder", 15)  # 15 + Initiative 1 = 16
    combat.roll_initiative(conn, fid, "pc-kesh", 10)    # 10 + Initiative 3 = 13
    return fid


def test_dice_convert_by_probability():
    assert dice.target(0) == 11 and dice.target(5) == 6
    assert dice.target(5, "d100") == 26
    assert dice.target(5, "3d6", low=True) == 12
    assert dice.target(-1, "d100") == 56 and dice.target(-1) == 12


def test_full_fight(conn, tmp_path):
    _test_pack(conn, tmp_path)
    fid = _fight(conn)
    st = _st(conn, fid)
    assert st["status"] == "melee" and st["melee"] == 1
    assert st["order"] == ["pc-calder", "pc-kesh"] and st["current"] == "pc-calder"
    assert _who(st, "pc-calder")["actions_left"] == 3 and _who(st, "pc-kesh")["actions_left"] == 3
    assert {o["id"] for o in st["options"]} >= {"spark", "ward", "staff"}

    # Strike against Defense; the spell spends Anima.
    with pytest.raises(CombatError):
        combat.act(conn, fid, "pc-kesh", "punch", "pc-calder")  # not Kesh's action
    combat.act(conn, fid, "pc-calder", "spark", "pc-kesh")
    st = _st(conn, fid)
    assert _who(st, "pc-calder")["anima"]["current"] == 51
    assert st["pending"]["step"] == "attack" and st["pending"]["needed"] == 8  # Strike +3 on a d20
    assert combat.roll(conn, fid, 12)["landed"]
    st = _st(conn, fid)
    assert st["pending"]["step"] == "defense" and st["pending"]["roller"] == "pc-kesh"
    assert st["pending"]["choices"] == ["dodge", "pass"]  # a spell bolt cannot be parried
    assert not combat.roll(conn, fid, 5, choice="dodge")["defended"]  # Defense +3 needs 8
    assert _who(_st(conn, fid), "pc-kesh")["actions_left"] == 2  # the dodge spent an action
    combat.roll(conn, fid, values=[7])
    st = _st(conn, fid)
    assert _seg(st, "pc-kesh", "hide")["value"] == 32 - 7
    assert st["current"] == "pc-kesh"

    # A punch can be parried; the parry spends the defender's action.
    combat.act(conn, fid, "pc-kesh", "punch", "pc-calder")
    combat.roll(conn, fid, 20)
    assert _st(conn, fid)["pending"]["choices"] == ["dodge", "parry", "pass"]
    assert combat.roll(conn, fid, 18, choice="parry")["defended"]
    st = _st(conn, fid)
    assert _who(st, "pc-calder")["actions_left"] == 1 and st["current"] == "pc-calder"

    # Switching on a timed ward needs no roll; it happens when selected.
    combat.act(conn, fid, "pc-calder", "ward")
    st = _st(conn, fid)
    assert "ward" in _who(st, "pc-calder")["activated"] and st["pending"] is None
    assert _who(st, "pc-calder")["anima"]["current"] == 48
    assert [t["melees_left"] for t in st["timers"]] == [2]

    # Kesh still has an action (3, less the dodge and the punch) and comes around again; then the melee rolls over.
    assert _st(conn, fid)["current"] == "pc-kesh"
    combat.act(conn, fid, "pc-kesh", "punch", "pc-calder")
    combat.roll(conn, fid, 2)  # misses
    st = _st(conn, fid)
    assert st["melee"] == 2 and st["current"] == "pc-calder"
    assert _who(st, "pc-calder")["actions_left"] == 3 and _who(st, "pc-kesh")["actions_left"] == 3
    # Anima recovers between melees: Willpower 15% of 56 M per minute, a sixth per melee = 1 M.
    assert _who(st, "pc-calder")["anima"]["current"] == 49
    assert [t["melees_left"] for t in st["timers"]] == [1]

    # Damage goes outer layer first: the ward takes 10, the rest goes on inward.
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")  # use an action, then Kesh hits back
    combat.roll(conn, fid, 1)
    combat.act(conn, fid, "pc-kesh", "club", "pc-calder")
    combat.roll(conn, fid, 20)
    combat.roll(conn, fid, choice="pass")
    combat.roll(conn, fid, values=[22])
    st = _st(conn, fid)
    first = st["log"][0]["then"][0]["hits"]
    assert sum(h["taken"] for h in first) == 22 and first[0]["taken"] > 0
    outer = [s for s in _who(st, "pc-calder")["defense"]["segments"]]
    assert sum(s["total"] - s["value"] for s in outer) == 22

    # Undo a mistyped roll and enter it again.
    before = _st(conn, fid)
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")
    combat.roll(conn, fid, 3)
    combat.undo(conn, fid, 2)
    after = _st(conn, fid)
    assert after["current"] == before["current"] and _who(after, "pc-calder")["actions_left"] == _who(before, "pc-calder")["actions_left"]

    # Timed effects count down by melee and switch off.
    while _st(conn, fid)["melee"] == 2:
        cur = _st(conn, fid)["current"]
        other = "pc-kesh" if cur == "pc-calder" else "pc-calder"
        combat.act(conn, fid, cur, "punch", other)
        combat.roll(conn, fid, 1)
    st = _st(conn, fid)
    assert st["melee"] == 3 and st["timers"] == [] and "ward" not in _who(st, "pc-calder")["activated"]

    # The GM ends the fight; sheets stay as updated, Anima recovers fully between fights.
    combat.end(conn, fid)
    st = _st(conn, fid)
    assert st["status"] == "ended" and st["ended"] == "ended by the GM"
    assert _who(st, "pc-calder")["anima"]["current"] == 56
    assert _seg(st, "pc-kesh", "hide")["value"] == 25
    with pytest.raises(CombatError):
        combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")


def test_fight_ends_when_a_side_is_defeated(conn):
    fid = _fight(conn)
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")
    combat.roll(conn, fid, 20)
    combat.roll(conn, fid, choice="pass")
    # Kesh: hide 32 then 28 flesh hit points. The roll is checked against the dice.
    with pytest.raises(CombatError):
        combat.roll(conn, fid, values=[13])
    conn.execute("UPDATE character_gauges SET current=3 WHERE character_id='pc-kesh' AND gauge='hit_points'")
    conn.execute("UPDATE character_items SET data=json_set(data, '$.current', 0) WHERE character_id='pc-kesh' AND item_id='hide'")
    conn.commit()
    combat.roll(conn, fid, values=[5])
    st = _st(conn, fid)
    assert _who(st, "pc-kesh")["status"] == "down"
    assert st["status"] == "ended" and "Raiders" in st["ended"]
    # The GM can undo the blow that ended it; the fight is back on.
    combat.undo(conn, fid)
    assert _st(conn, fid)["status"] == "melee"


def test_fight_ends_when_a_side_has_fled(conn):
    fid = combat.start(conn, [{"name": "A", "characters": ["pc-calder"]},
                              {"name": "B", "characters": ["pc-kesh", "pc-ilya"]}])
    for cid, r in (("pc-calder", 20), ("pc-kesh", 10), ("pc-ilya", 5)):
        combat.roll_initiative(conn, fid, cid, r)
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")
    combat.roll(conn, fid, 1)
    combat.act(conn, fid, "pc-kesh", leave=True)
    assert _st(conn, fid)["status"] == "melee"  # Ilya is still fighting
    combat.act(conn, fid, "pc-ilya", leave=True)
    st = _st(conn, fid)
    assert st["status"] == "ended" and "B" in st["ended"] and st["order"] == ["pc-calder"]


def test_mental_attack_is_resisted_with_willpower(conn, tmp_path):
    _test_pack(conn, tmp_path)
    fid = _fight(conn)
    combat.act(conn, fid, "pc-calder", "lure", "pc-kesh")
    st = _st(conn, fid)
    assert st["pending"]["needed"] == 9  # the ability's own +2, not Strike
    combat.roll(conn, fid, 9)
    st = _st(conn, fid)
    assert st["pending"]["step"] == "resist" and st["pending"]["roller"] == "pc-kesh"
    assert combat.roll(conn, fid, 20)["resisted"]
    st = _st(conn, fid)
    assert _who(st, "pc-kesh")["actions_left"] == 3  # resisting never costs an action
    assert st["current"] == "pc-kesh"


def test_unperceived_attack_gets_no_defense(conn):
    fid = _fight(conn)
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh", unperceived=True)
    combat.roll(conn, fid, 20)
    assert _st(conn, fid)["pending"]["step"] == "damage"


def test_threshold_and_prefix_pass_through(conn):
    fid = combat.start(conn, [{"name": "A", "characters": ["pc-bex"]}, {"name": "B", "characters": ["npc-thorn"]}])
    # 12 plain hit points on a hecto suit is below one hecto point: nothing at all.
    assert combat._harm(conn, fid, "pc-bex", 12, "unit") == [{"layer": "siege_enforcer", "taken": 0}]
    # 9 kilo = 90 hecto: all on the suit.
    assert combat._harm(conn, fid, "pc-bex", 9, "kilo") == [{"layer": "siege_enforcer", "taken": 90, "left": 710}]
    # Thorn: 80 hecto scales, 50 hecto flesh. 10 kilo = 100 hecto: 80 on scales, 20 on flesh.
    hits = combat._harm(conn, fid, "npc-thorn", 10, "kilo")
    assert hits == [{"layer": "scales", "taken": 80, "left": 0}, {"layer": "hit_points", "taken": 20, "left": 30}]


def test_not_enough_anima(conn, tmp_path):
    _test_pack(conn, tmp_path)
    conn.execute("UPDATE character_gauges SET current=4 WHERE character_id='pc-calder' AND gauge='anima'")
    conn.commit()
    fid = _fight(conn)
    with pytest.raises(CombatError, match="Anima"):
        combat.act(conn, fid, "pc-calder", "spark", "pc-kesh")
    st = _st(conn, fid)
    assert _who(st, "pc-calder")["actions_left"] == 3 and st["pending"] is None


def test_reflex_defense_costs_no_action(conn):
    conn.execute("UPDATE character_channels SET data='{\"value\": 3, \"reflex\": true}' WHERE character_id='pc-kesh' AND channel='defense'")
    conn.commit()
    fid = _fight(conn)
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")
    combat.roll(conn, fid, 20)
    assert not _st(conn, fid)["pending"]["needs_action"]
    combat.roll(conn, fid, 20, choice="dodge")
    assert _who(_st(conn, fid), "pc-kesh")["actions_left"] == 3


def test_three_d6_low_campaign_die(conn):
    fid = combat.start(conn, [{"name": "A", "characters": ["pc-calder"]}, {"name": "B", "characters": ["pc-kesh"]}],
                       die="3d6", low=True)
    with pytest.raises(CombatError):
        combat.roll_initiative(conn, fid, "pc-calder", 2)
    combat.roll_initiative(conn, fid, "pc-calder", 3)   # a 3 is the best roll on a low 3d6
    combat.roll_initiative(conn, fid, "pc-kesh", 18)
    st = _st(conn, fid)
    assert st["current"] == "pc-calder"
    combat.act(conn, fid, "pc-calder", "staff", "pc-kesh")
    st = _st(conn, fid)
    assert st["pending"]["needed"] == dice.target(3, "3d6", True)
    assert "or lower" in st["pending"]["ask"]


@pytest.mark.parametrize("field,value", [("cost", -1), ("cost", "5"), ("melees", 1.5), ("mental", "yes"), ("area", 1)])
def test_combat_fields_are_checked_on_import(conn, tmp_path, field, value):
    d = tmp_path / "bad-combat"
    d.mkdir()
    (d / "pack.json").write_text(json.dumps({"id": "bad-combat", "name": "Bad", "depends": ["universal"]}))
    (d / "abilities.json").write_text(json.dumps([{"id": "x", "name": "X", field: value}]))
    with pytest.raises(packs.PackError, match=field):
        packs.import_pack(conn, d)
