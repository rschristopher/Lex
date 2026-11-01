import filecmp

import pytest

from lex import packs
from lex.paths import PACK_DIR


def pack(pid="test", **rows):
    doc = {"id": pid, "name": pid, "adapter": None, "species": [], "occupations": [], "abilities": [],
           "items": [], "characters": [], "portraits": {}, "lore": []}
    doc.update(rows)
    return doc


def _same_tree(a, b):
    cmp = filecmp.dircmp(a, b)
    assert not cmp.left_only and not cmp.right_only and not cmp.diff_files, (cmp.left_only, cmp.right_only, cmp.diff_files)
    for sub in cmp.common_dirs:
        _same_tree(a / sub, b / sub)


@pytest.mark.parametrize("pid", ["universal", "u-simplified"])
def test_export_round_trips_byte_for_byte(conn, tmp_path, pid):
    out = packs.export_pack(conn, pid, tmp_path / pid)
    _same_tree(PACK_DIR / pid, out)
    # And the export imports back to the same rows.
    packs.import_pack(conn, out)
    again = packs.export_pack(conn, pid, tmp_path / "again")
    _same_tree(out, again)


def test_import_rows(conn):
    n = lambda q: conn.execute(q).fetchone()[0]
    assert n("SELECT COUNT(*) FROM characters") == 12
    assert n("SELECT COUNT(*) FROM occupations") == 10
    assert n("SELECT COUNT(*) FROM effects WHERE owner_type='occupation' AND verb='mod.channel'") >= 10
    # Worn gear that sets an attribute is effect rows too.
    rows = conn.execute("SELECT target, op, value FROM effects WHERE owner_type='item' AND owner_id='siege_enforcer'").fetchall()
    assert [tuple(r) for r in rows] == [("strength", "replace", 38), ("speed", "replace", 31)]
    own = conn.execute("SELECT item_id FROM character_items WHERE character_id='pc-bex' ORDER BY position").fetchall()
    assert [r[0] for r in own][:1] == ["siege_enforcer"]


def test_reimport_keeps_owner(conn):
    with conn:
        conn.execute("INSERT INTO users (username) VALUES ('ana')")
        conn.execute("UPDATE characters SET owner_id=1 WHERE id='pc-ilya'")
    packs.import_pack(conn, PACK_DIR / "universal")
    assert conn.execute("SELECT owner_id FROM characters WHERE id='pc-ilya'").fetchone()[0] == 1


def test_validation_is_all_or_nothing(conn):
    bad = pack(
        abilities=[{"id": "x", "name": "X", "effects": [{"verb": "mod.channel", "target": "strike", "op": "multiply", "value": 2}]}],
        characters=[
            {"id": "c1", "name": "C1", "species": "nope", "attrs": {"strength": -1}},
            {"id": "pc-ilya", "name": "Again"},
            {"id": "c2"},
        ],
    )
    with pytest.raises(packs.PackError) as e:
        packs.import_pack(conn, bad)
    text = " | ".join(e.value.errors)
    assert "op must be add or replace" in text
    assert "unknown species 'nope'" in text
    assert "strength: must be a number, 0 or more" in text
    assert "id already used by pack universal" in text
    assert "characters/c2: missing name" in text
    assert conn.execute("SELECT COUNT(*) FROM packs WHERE id='test'").fetchone()[0] == 0


def test_cross_pack_references(conn, tmp_path):
    packs.import_pack(conn, pack(
        "extra",
        species=[{"id": "deep_one", "name": "Deep One"}],
        characters=[{"id": "obed", "name": "Obed", "species": "deep_one", "occupation": "universal:soldier",
                     "attrs": {"strength": 0.5}, "abilities": [{"id": "universal:keen", "qty": "40%"}]}],
    ))
    doc = packs.character_doc(conn, "obed")
    assert doc["occupation"] == "universal:soldier"
    assert doc["attrs"] == {"strength": 0.5}
    assert doc["abilities"] == [{"id": "universal:keen", "qty": "40%"}]
    packs.export_pack(conn, "extra", tmp_path / "extra")
    assert (tmp_path / "extra" / "characters" / "obed.json").is_file()
