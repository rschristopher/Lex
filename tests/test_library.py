"""The library: entries (migration 6), pack metadata, and the browse/search/detail endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lex import db, packs
from lex.api import app

FIXTURE = Path(__file__).parent / "fixtures" / "library"


@pytest.fixture
def lib(conn):
    packs.import_pack(conn, FIXTURE)
    return conn


def _cats(menu):
    return {c["id"]: c for s in menu["sections"] for c in s["categories"]}


def test_migration_adds_entries_links_and_pack_meta(tmp_path):
    conn = db.connect(tmp_path / "lex.db")
    assert db.version(conn) == len(db.MIGRATIONS) >= 6
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"entries", "entry_links", "pack_meta"} <= tables
    conn.execute("INSERT INTO packs VALUES ('p', 'P')")
    conn.execute("INSERT INTO entries VALUES ('p', 'x', 0, 'X', 'location', '{}')")
    with pytest.raises(Exception):
        conn.execute("INSERT INTO entry_links VALUES ('p', 'x', 0, 'weather', 'p', 'x')")
    conn.execute("DELETE FROM packs WHERE id='p'")
    assert conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 0


def test_import_entries_and_links(lib):
    n = lambda q: lib.execute(q).fetchone()[0]
    assert n("SELECT COUNT(*) FROM entries WHERE pack='myth-sample'") == 5
    links = lib.execute("SELECT ref_table, ref_pack, ref_id FROM entry_links WHERE entry_id='escape' ORDER BY position").fetchall()
    assert [tuple(r) for r in links] == [
        ("entries", "myth-sample", "cave"), ("species", "myth-sample", "cyclops"), ("items", "myth-sample", "wineskin"),
        ("abilities", "myth-sample", "cunning"), ("occupations", "myth-sample", "hero"),
    ]


def test_fixture_round_trips_byte_for_byte(lib, tmp_path):
    from tests.test_packs import _same_tree

    out = packs.export_pack(lib, "myth-sample", tmp_path / "out")
    _same_tree(FIXTURE, out)


def _doc(**rows):
    doc = {"id": "t", "name": "T", "adapter": None, "species": [], "occupations": [], "abilities": [],
           "items": [], "entries": [], "characters": [], "portraits": {}, "lore": []}
    doc.update(rows)
    return doc


def test_bad_entries_are_refused(conn):
    with pytest.raises(packs.PackError) as e:
        packs.import_pack(conn, _doc(entries=[
            {"id": "a", "name": "A", "kind": "location", "links": ["nowhere"]},
            {"id": "b", "name": "B"},
            {"id": "c", "name": "C", "kind": "location", "effects": [{"verb": "mod.attr", "target": "speed", "value": 1}]},
        ]))
    text = str(e.value)
    assert "unknown row 'nowhere'" in text and "entries[1]: missing kind" in text and "no effects" in text
    # An id in two tables must say which.
    with pytest.raises(packs.PackError, match="write it as table/id"):
        packs.import_pack(conn, _doc(species=[{"id": "x", "name": "X"}], items=[{"id": "x", "name": "X", "kind": "gear"}],
                                     entries=[{"id": "e", "name": "E", "kind": "place", "links": ["x"]}]))
    packs.import_pack(conn, _doc(species=[{"id": "x", "name": "X"}], items=[{"id": "x", "name": "X", "kind": "gear"}],
                                 entries=[{"id": "e", "name": "E", "kind": "place", "links": ["items/x"]}]))


def test_menu_comes_from_the_data(lib):
    with TestClient(app) as client:
        menu = client.get("/library").json()
        cats = _cats(menu)
        assert cats["entries.location"]["label"] == "Locations" and cats["entries.location"]["count"] == 3
        assert cats["entries.adventure"]["label"] == "Adventures"
        assert cats["items.gear"]["label"] == "Gear and equipment"  # pack.json labels
        assert cats["items.weapon"]["label"] == "Weapons"  # adapter groups
        assert cats["items.vehicle"]["label"] == "Vehicles"
        assert cats["abilities.power"]["label"] == "Powers"
        assert [s["label"] for s in menu["sections"]] == ["People", "Abilities", "Equipment", "World"]
        assert {p["id"] for p in client.get("/packs").json()} == {"universal", "myth-sample"}
        only = _cats(client.get("/library", params={"pack": "myth-sample"}).json())
        assert only["items.weapon"]["count"] == 2 and only["species"]["count"] == 3


def test_any_imported_pack_shows_up(lib):
    packs.import_pack(lib, _doc(id="bestiary", name="Bestiary", entries=[
        {"id": "hydra", "name": "Hydra", "kind": "creature", "text": "Nine heads; cut one and two grow back."}]))
    with TestClient(app) as client:
        cats = _cats(client.get("/library").json())
        assert cats["entries.creature"] == {"id": "entries.creature", "label": "Creatures", "table": "entries",
                                            "kind": "creature", "count": 1}
        rows = client.get("/library/rows", params={"q": "heads"}).json()["rows"]
        assert [(r["pack"], r["id"]) for r in rows] == [("bestiary", "hydra")]


def test_list_search_filter_and_page(lib):
    with TestClient(app) as client:
        r = client.get("/library/rows", params={"category": "items.weapon"}).json()
        assert r["category_label"] == "Weapons" and r["total"] == len(r["rows"]) == 17
        assert [x["name"] for x in r["rows"]] == sorted((x["name"] for x in r["rows"]), key=str.lower)
        # Every word must match, in the name or the text; name matches come first.
        r = client.get("/library/rows", params={"q": "stone door"}).json()
        assert {x["id"] for x in r["rows"]} == {"cave", "escape"}
        assert {f["id"]: f["count"] for f in r["facets"]} == {"entries.location": 1, "entries.adventure": 1}
        names = [x["name"] for x in client.get("/library/rows", params={"q": "spear"}).json()["rows"]]
        assert names[:2] == ["Spear fighting", "Bronze spear"]  # name starts with it, then name has it, then text
        r = client.get("/library/rows", params={"q": "spear", "category": "items.weapon"}).json()
        assert [x["id"] for x in r["rows"]] == ["bronze_spear"]
        assert any(f["id"] == "abilities.skill" for f in r["facets"])  # facets ignore the category filter
        r = client.get("/library/rows", params={"q": "spear", "pack": "universal"}).json()
        assert all(x["pack"] == "universal" for x in r["rows"])
        a = client.get("/library/rows", params={"category": "items.weapon", "limit": 5}).json()
        b = client.get("/library/rows", params={"category": "items.weapon", "limit": 5, "offset": 5}).json()
        assert len(a["rows"]) == len(b["rows"]) == 5 and not {x["id"] for x in a["rows"]} & {x["id"] for x in b["rows"]}
        assert client.get("/library/rows", params={"q": "100%_"}).json()["total"] == 0
        assert client.get("/library/rows", params={"category": "spells"}).status_code == 404
        # Summaries are words, not JSON.
        hero = client.get("/library/rows", params={"q": "hero", "category": "occupations"}).json()["rows"][0]
        assert hero["summary"].startswith("Leader of men")
        soldier = client.get("/library/rows", params={"q": "soldier", "category": "occupations"}).json()["rows"][0]
        assert soldier["summary"] == "+2 Strike · +1 Actions"


def test_detail_in_plain_words(lib):
    with TestClient(app) as client:
        spear = client.get("/library/abilities/myth-sample/spear").json()
        assert spear["category_label"] == "Skills" and spear["source"] == "Homer, Odyssey, Book XXII"
        assert [(lv["name"], lv["price"], [e["text"] for e in lv["effects"]]) for lv in spear["levels"]] == [
            ("Novice", 100, ["+1 Strike"]), ("Veteran", 300, ["+1 Strike", "+1 Defense"]), ("Master", 900, ["+2 Strike"])]
        assert spear["related"] == [{"title": "Part of", "rows": [
            {"table": "occupations", "pack": "myth-sample", "id": "hero", "name": "Hero", "category": "occupations",
             "category_label": "Occupations", "missing": False, "note": "set 1"}]}]

        hero = client.get("/library/occupations/myth-sample/hero").json()
        assert [e["text"] for e in hero["effects"]] == ["+1 Strike", "+1 Actions"]
        sets = {r["title"]: [x["name"] for x in r["rows"]] for r in hero["related"]}
        assert sets["Ability set 1"] == ["Spear fighting", "Sailing"] and sets["Ability set 2"] == ["Command", "Cunning"]
        assert sets["Required by"] == ["Command"]
        assert sets["Mentioned in"] == ["Escape from the cave"]

        command = client.get("/library/abilities/myth-sample/command").json()
        assert [r["text"] for r in command["requires"]] == ["Needs set 1 of Hero complete"]
        assert command["requires"][0]["link"]["id"] == "hero"

        human = client.get("/library/species/myth-sample/human").json()
        assert {r["title"]: [x["name"] for x in r["rows"]] for r in human["related"]}["Required by"] == ["Prophecy"]
        cyclops = client.get("/library/species/myth-sample/cyclops").json()
        assert [e["text"] for e in cyclops["effects"]] == ["+12 Strength", "-3 Intellect"]

        prophecy = client.get("/library/abilities/myth-sample/prophecy").json()
        assert {f["label"]: f["value"] for f in prophecy["facts"]} == {"Price": "600", "Cost": "5", "Mental": "yes"}

        ship = client.get("/library/items/myth-sample/ship").json()
        facts = {f["label"]: f["value"] for f in ship["facts"]}
        assert facts["Strength"] == "60" and facts["Speed"] == "14" and facts["Crew"] == "50"

        escape = client.get("/library/entries/myth-sample/escape").json()
        assert escape["category_label"] == "Adventures" and escape["text"].startswith("Trapped")
        assert {f["label"]: f["value"] for f in escape["facts"]} == {"Players": "3 to 6"}
        see = escape["related"][0]
        assert see["title"] == "See also"
        assert [(x["category_label"], x["name"]) for x in see["rows"]] == [
            ("Locations", "The Cyclops' cave"), ("Species", "Cyclops"), ("Gear and equipment", "Wineskin of strong wine"),
            ("Abilities", "Cunning"), ("Occupations", "Hero")]

        # Repo data: universal rows cross-link to the characters who have them, with the adapter's labels.
        enforcer = client.get("/library/items/universal/siege_enforcer").json()
        rel = {r["title"]: r["rows"] for r in enforcer["related"]}
        assert [c["id"] for c in rel["Characters"]] == ["pc-bex"]
        attacks = next(f for f in enforcer["facts"] if f["label"] == "Attacks")
        assert attacks["rows"][0].startswith("Punch (damage 1d6")
        prefix = next(f for f in enforcer["facts"] if f["label"] == "Prefix")
        assert prefix["value"] == "hecto (damage hD, armor hA)"
        simp = client.get("/library/species/myth-sample/centaur", params={"adapter": "u-simplified"}).json()
        assert [e["text"] for e in simp["effects"]][1] == "+2 Strength"

        assert client.get("/library/spells/myth-sample/x").status_code == 404
        assert client.get("/library/items/myth-sample/nothing").status_code == 404


def test_library_screen_is_served(lib):
    with TestClient(app) as client:
        r = client.get("/browse")
        assert r.status_code == 200 and "/static/library.js" in r.text
        for page in ("/", "/fight", "/browse"):
            html = client.get(page).text
            assert 'href="/browse"' in html and 'action="/browse"' in html and 'aria-current="page"' in html
        for path in ("/static/library.js", "/static/library.css", "/static/nav.css"):
            assert client.get(path).status_code == 200
