"""Conditional bonuses: item categories and effect rows with "when" (using / wearing). Test data: tests/fixtures/library."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lex import combat, engine, packs
from lex.api import app
from lex.sheet import sheet

FIXTURE = Path(__file__).parent / "fixtures" / "library"
HERO = "myth-odysseus"


@pytest.fixture
def lib(conn):
    packs.import_pack(conn, FIXTURE)
    return conn


def _ch(s):
    return {c["id"]: c["value"] for c in s["channels"]}


def _wear(conn, *refs):
    with conn:
        conn.execute("DELETE FROM character_active WHERE character_id=?", (HERO,))
        for i, ref in enumerate(refs):
            conn.execute("INSERT INTO character_active VALUES (?,?,?)", (HERO, i, ref))


def test_when_rules():
    assert engine.when_met(None, set(), set())
    assert engine.when_met({"using": "knife"}, {"knife", "melee"}, set())
    assert not engine.when_met({"using": "knife"}, {"spear"}, {"knife"})
    assert engine.when_met({"using": ["spear", "knife"]}, {"knife"}, set())  # a list means any of them
    assert not engine.when_met({"using": ["spear", "knife"], "wearing": "shield"}, {"knife"}, set())  # both keys: both
    assert engine.when_met({"using": ["spear", "knife"], "wearing": "shield"}, {"knife"}, {"shield"})
    assert engine.check_when({"holding": "x"}) and engine.check_when({"using": []}) and engine.check_when({"using": [1]})
    assert engine.check_when({}) and engine.check_when("knife")
    assert engine.check_when({"using": ["a", "b"], "wearing": "c"}) is None


def test_knife_bonus_only_with_the_knife(lib):
    spear = sheet(lib, HERO, attack="bronze_spear")
    knife = sheet(lib, HERO, attack="bronze_knife")
    # Knife fighting, level 2: +1 Strike (level 1) and +1 Strike, +1 Defense (level 2), all "when using a knife";
    # the knife's own row (+1 Initiative) applies only while it is the weapon used.
    assert _ch(knife)["strike"] - _ch(spear)["strike"] == 2
    assert _ch(knife)["defense"] - _ch(spear)["defense"] == 1
    assert _ch(knife)["initiative"] - _ch(spear)["initiative"] == 1
    assert knife["using"]["name"] == "Bronze knife" and knife["bonuses"]["using"] == ["Knife", "Melee weapon"]
    texts = {(b["text"], b["met"]) for b in knife["bonuses"]["conditional"]}
    assert ("+1 Strike when using a knife", True) in texts and ("+1 Initiative when using Bronze knife", True) in texts
    assert ("+1 Strike when using a knife", False) in {(b["text"], b["met"]) for b in spear["bonuses"]["conditional"]}
    # Picking the knife on the sheet (the REST call the UI makes) gives the same numbers.
    with TestClient(app) as client:
        client.post("/users", json={"username": "gm", "password": ""})
        with lib:
            lib.execute("UPDATE users SET role='gm' WHERE username='gm'")
        client.post("/login", json={"username": "gm", "password": ""})
        assert _ch(client.patch(f"/characters/{HERO}", json={"attack": "bronze_knife"}).json()) == _ch(knife)
        assert _ch(client.patch(f"/characters/{HERO}", json={"attack": "bronze_spear"}).json()) == _ch(spear)


def test_robot_armor_bonus_only_while_worn(lib):
    out = sheet(lib, HERO)
    _wear(lib, "bronze_giant")
    inside = sheet(lib, HERO)
    assert _ch(inside)["actions"] - _ch(out)["actions"] == 1
    assert _ch(inside)["strike"] - _ch(out)["strike"] == 2
    assert inside["bonuses"]["wearing"] == ["Robot armor"]
    met = {b["text"]: b["met"] for b in inside["bonuses"]["conditional"]}
    assert met["+2 Strike while wearing robot armor"] is True
    _wear(lib)
    assert _ch(sheet(lib, HERO)) == _ch(out)


def test_worn_item_bonus_goes_when_removed(lib):
    bare = _ch(sheet(lib, HERO, attack="bronze_spear"))
    _wear(lib, "shield")
    worn = _ch(sheet(lib, HERO, attack="bronze_spear"))
    # The shield's own +1 Defense, and Shield wall's +2 Defense when using a spear or a knife and wearing a shield.
    assert worn["defense"] - bare["defense"] == 3
    assert _ch(sheet(lib, HERO, attack="bow"))["defense"] - bare["defense"] == 1  # a bow is neither: only the shield
    _wear(lib)
    assert _ch(sheet(lib, HERO, attack="bronze_spear")) == bare


def test_unconditional_effects_unchanged(lib):
    for attack, worn in (("bronze_spear", ()), ("bronze_knife", ("shield",)), ("bow", ("bronze_giant",))):
        _wear(lib, *worn)
        s = sheet(lib, HERO, attack=attack)
        always = {(b["text"], b["from"]["name"]) for b in s["bonuses"]["always"]}
        assert always == {("+1 Strike", "Hero"), ("+1 Actions", "Hero"), ("+1 Initiative", "Shield wall"),
                          ("+2 Intellect", "Cunning")}
        assert next(a["value"] for a in s["attrs"] if a["id"] == "intellect") == 19
    # Repo data with no categories or when: the sheet keeps its numbers and has no conditional bonuses.
    ilya = sheet(lib, "pc-ilya")
    assert [c["value"] for c in ilya["channels"]] == [4, 4, 2, 1]
    assert ilya["bonuses"]["conditional"] == []


def test_combat_uses_the_attack_picked(lib):
    fid = combat.start(lib, [{"name": "Crew", "characters": [HERO]}, {"name": "Raiders", "characters": ["pc-kesh"]}])
    combat.roll_initiative(lib, fid, HERO, 20)
    combat.roll_initiative(lib, fid, "pc-kesh", 1)
    assert combat.state(lib, fid)["current"] == HERO
    combat.act(lib, fid, HERO, "bronze_knife", "pc-kesh")
    knife = combat._pending(lib, fid)["bonus"]
    combat.undo(lib, fid)
    combat.act(lib, fid, HERO, "bronze_spear", "pc-kesh")
    spear = combat._pending(lib, fid)["bonus"]
    assert knife == _ch(sheet(lib, HERO, attack="bronze_knife"))["strike"]
    assert knife - spear == 2
    # Worn robot armor counts for its built-in attack too.
    combat.undo(lib, fid)
    _wear(lib, "bronze_giant")
    combat.act(lib, fid, HERO, "giant_fist", "pc-kesh")
    assert combat._pending(lib, fid)["bonus"] == spear + 2


def test_import_checks_and_round_trip(lib, tmp_path):
    cats = lib.execute("SELECT category FROM item_categories WHERE item_pack='myth-sample' AND item_id='bronze_knife'"
                       " ORDER BY position").fetchall()
    assert [r[0] for r in cats] == ["knife", "melee"]
    from tests.test_packs import _same_tree

    _same_tree(FIXTURE, packs.export_pack(lib, "myth-sample", tmp_path / "out"))

    def doc(**rows):
        d = {"id": "t", "name": "T", "adapter": None, "species": [], "occupations": [], "abilities": [], "items": [],
             "entries": [], "characters": [], "portraits": {}, "lore": []}
        d.update(rows)
        return d

    with pytest.raises(packs.PackError) as e:
        packs.import_pack(lib, doc(
            abilities=[{"id": "a", "name": "A", "effects": [{"verb": "mod.channel", "target": "strike", "value": 1,
                                                             "when": {"holding": "knife"}}]},
                       {"id": "b", "name": "B", "effects": [{"verb": "mod.channel", "target": "strike", "value": 1,
                                                             "when": {"using": []}}]}],
            items=[{"id": "i", "name": "I", "kind": "weapon", "categories": "knife"},
                   {"id": "j", "name": "J", "kind": "weapon", "categories": ["knife", "knife"]}],
            meta={"categories": [{"name": "no id"}]},
        ))
    text = str(e.value)
    for part in ("when.holding: only using and wearing", "when.using: must be a category name",
                 "items[0].categories", "items[1].categories", "pack.json.categories"):
        assert part in text


def test_library_shows_categories_and_conditions(lib):
    with TestClient(app) as client:
        menu = client.get("/library").json()
        tags = {t["id"]: t for t in menu["tags"]}
        assert tags["knife"] == {"id": "knife", "label": "Knife", "count": 1}
        assert tags["melee"]["count"] == 2 and tags["robot-armor"]["label"] == "Robot armor"
        knife = client.get("/library/items/myth-sample/bronze_knife").json()
        assert knife["categories"] == [{"id": "knife", "label": "Knife"}, {"id": "melee", "label": "Melee weapon"}]
        assert "Categories" not in {f["label"] for f in knife["facts"]}
        skill = client.get("/library/abilities/myth-sample/knife_fighting").json()
        lv2 = skill["levels"][1]["effects"]
        assert [e["text"] for e in lv2] == ["+1 Strike when using a knife", "+1 Defense when using a knife"]
        assert lv2[0]["condition"] == "when using a knife" and lv2[0]["when"] == {"using": "knife"}
        wall = client.get("/library/abilities/myth-sample/shield_wall").json()
        assert wall["effects"][0]["text"] == "+2 Defense when using a spear or a knife and while wearing a shield"
        r = client.get("/library/rows", params={"tag": "melee"}).json()
        assert {x["id"] for x in r["rows"]} == {"bronze_knife", "bronze_spear"} and r["tag_label"] == "Melee weapon"
        r = client.get("/library/rows", params={"tag": "knife"}).json()
        assert [(b["text"], b["from"]["name"], b["from"].get("note")) for b in r["bonuses"]] == [
            ("+1 Strike when using a knife", "Knife fighting", "Novice"),
            ("+1 Strike when using a knife", "Knife fighting", "Veteran"),
            ("+1 Defense when using a knife", "Knife fighting", "Veteran"),
            ("+2 Defense when using a spear or a knife and while wearing a shield", "Shield wall", None)]
        rows = client.get("/library/rows", params={"category": "abilities.skill", "q": "giant"}).json()["rows"]
        assert rows[0]["summary"].startswith("Fighting from inside")


def test_condition_words_keep_proper_names():
    from lex import library

    assert library._lower("Knife") == "knife"
    assert library._lower("Bronze Giant armor") == "Bronze Giant armor"
    assert library._article(library._lower("Bronze Giant armor")) == "Bronze Giant armor"
    assert library._article(library._lower("Spear")) == "a spear"
