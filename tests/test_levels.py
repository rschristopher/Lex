"""More than one occupation, levels that follow occupation level, and stacked or replacement levels.
Test data: tests/fixtures/levels (pack.json sets "level_from": "occupation"; two rows override it)."""

import json
from pathlib import Path

import pytest

from lex import engine, packs
from lex.sheet import sheet

FIXTURE = Path(__file__).parent / "fixtures" / "levels"
P = "levels-sample"


@pytest.fixture
def lv(conn):
    packs.import_pack(conn, FIXTURE)
    return conn


def _ch(s):
    return {c["id"]: c["value"] for c in s["channels"]}


def _eff(conn, cid, target):
    return sum(e["value"] or 0 for e in engine.character_effects(conn, cid)[0] if e["target"] == target and not e.get("when"))


def test_old_single_occupation_doc_keeps_its_level(lv):
    # "occupation" + "level": 4 -> that occupation at level 4; sword drill follows it (the stored level 1 is not used)
    assert [(o["id"], o["level"]) for o in engine.character_occupations(lv, "levels-old")] == [("warrior", 4)]
    assert engine.effective_level(lv, "levels-old", P, "sword_drill", 1) == 4
    assert _eff(lv, "levels-old", "strike") == 4  # levels stack: 1..4


def test_level_is_the_highest_listing_occupation_else_the_highest(lv):
    occ = engine.character_occupations(lv, "levels-two")
    assert [(o["id"], o["level"]) for o in occ] == [("warrior", 7), ("scribe", 3)]
    assert engine.effective_level(lv, "levels-two", P, "sword_drill", None) == 5   # warrior 7, capped at the last level
    assert engine.effective_level(lv, "levels-two", P, "letters", None) == 3       # only the scribe lists it
    assert engine.effective_level(lv, "levels-two", P, "swimming", None) == 5      # nobody lists it: highest (7), capped
    assert engine.effective_level(lv, "levels-two", P, "tally", 2) == 2            # row says experience: stored level
    assert _eff(lv, "levels-two", "lore") == 3
    s = sheet(lv, "levels-two")
    assert [(o["id"], o["level"]) for o in s["occupation_levels"]] == [("warrior", 7), ("scribe", 3)]
    assert s["level"] == 7


def test_replacement_levels(lv):
    # giant piloting: Basic (+1 actions, +1 strike) then Elite (+2, +3), each replacing the one before, while in the giant
    base = _ch(sheet(lv, "levels-two"))
    with lv:
        lv.execute("UPDATE character_abilities SET level=2 WHERE character_id='levels-two' AND ability_id='giant_piloting'")
    elite = _ch(sheet(lv, "levels-two"))
    assert elite["actions"] - base["actions"] == 1   # 2 replaces 1, not 1 + 2
    assert elite["strike"] - base["strike"] == 2     # 3 replaces 1
    with lv:
        lv.execute("DELETE FROM character_active WHERE character_id='levels-two'")
    assert _ch(sheet(lv, "levels-two"))["actions"] == base["actions"] - 1   # out of the giant: none of it


def test_stacked_levels_stay_the_default(conn):
    packs.import_pack(conn, Path(__file__).parent / "fixtures" / "library")
    assert engine.level_rules(conn, "myth-sample", "knife_fighting") == ("experience", "stack")


def test_occupation_requirement_refuses_until_the_occupation_is_added(lv):
    _, broken = engine.character_effects(lv, "levels-scribe")
    assert broken[(P, "oath_of_the_order")] == [f"needs set 1 of occupation {P}:warrior"]
    _, broken = engine.character_effects(lv, "levels-two")   # holds the warrior occupation
    assert (P, "oath_of_the_order") not in broken
    with lv:
        lv.execute("DELETE FROM character_abilities WHERE character_id='levels-scribe' AND ability_id='oath_of_the_order'")
    with pytest.raises(engine.Refused):
        engine.buy_ability(lv, "levels-scribe", P, "oath_of_the_order")
    with lv:
        lv.execute("INSERT INTO character_occupations VALUES ('levels-scribe', 1, ?, 'warrior', 1)", (P,))
    assert engine.buy_ability(lv, "levels-scribe", P, "oath_of_the_order") == 4


def test_occupation_driven_skill_is_owned_once(lv):
    with pytest.raises(engine.Refused, match="follows the occupation level"):
        engine.buy_ability(lv, "levels-scribe", P, "letters")
    left = engine.buy_ability(lv, "levels-scribe", P, "swimming")
    assert left == 4 and engine.effective_level(lv, "levels-scribe", P, "swimming", None) == 3


def test_round_trip_both_forms(lv, tmp_path):
    out = packs.export_pack(lv, P, tmp_path / "out")
    for name in ("levels-old", "levels-two", "levels-scribe"):
        a = json.loads((FIXTURE / "characters" / f"{name}.json").read_text())
        b = json.loads((out / "characters" / f"{name}.json").read_text())
        assert a == b, name
    for name in ("pack.json", "abilities.json"):
        assert json.loads((FIXTURE / name).read_text()) == json.loads((out / name).read_text())


def test_import_checks(conn):
    doc = packs.read_pack(FIXTURE)
    doc["meta"]["level_from"] = "age"
    doc["abilities"][0]["levels_mode"] = "max"
    doc["characters"][1]["occupation"] = "warrior"
    doc["characters"][2]["occupations"] = [{"id": "scribe"}]
    with pytest.raises(packs.PackError) as e:
        packs.import_pack(conn, doc)
    text = str(e.value)
    assert "pack.json.level_from" in text and "levels_mode: must be stack or replace" in text
    assert "occupation or occupations, not both" in text and "needs id and a level" in text
