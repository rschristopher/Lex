import sqlite3

import pytest

from lex import db


def test_schema_created_and_versioned(tmp_path):
    conn = db.connect(tmp_path / "lex.db")
    assert db.version(conn) == len(db.MIGRATIONS)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"packs", "species", "occupations", "abilities", "items", "effects", "requirements",
            "characters", "character_abilities", "character_items", "users", "campaigns", "lore"} <= tables
    # Reopening does not re-run migrations.
    assert db.version(db.connect(tmp_path / "lex.db")) == len(db.MIGRATIONS)


def test_effect_rows_are_checked(tmp_path):
    conn = db.connect(tmp_path / "lex.db")
    conn.execute("INSERT INTO packs VALUES ('p', 'P')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO effects (owner_type, owner_pack, owner_id, position, verb, target, value)"
            " VALUES ('weather', 'p', 'x', 0, 'mod.channel', 'strike', 2)"
        )
    assert "op" not in {r[1] for r in conn.execute("PRAGMA table_info(effects)")}
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO users (username, role) VALUES ('a', 'admin')")
