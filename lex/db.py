"""sqlite schema: the live record. Everything from a pack is a row; code never names a specific ability."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from lex.paths import ROOT

DEFAULT_DB = ROOT / "lex.db"

# Each entry is one migration; the index + 1 is the schema version (PRAGMA user_version).
MIGRATIONS: list[str] = [
    """
    CREATE TABLE packs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    -- An adapter is a sheet language: labels, attribute conversions, dice. Stored as the pack's document.
    CREATE TABLE adapters (
        pack TEXT PRIMARY KEY REFERENCES packs(id) ON DELETE CASCADE,
        data TEXT NOT NULL
    );

    CREATE TABLE species (
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        id TEXT NOT NULL,
        position INTEGER NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (pack, id)
    );

    CREATE TABLE occupations (
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        id TEXT NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (pack, id)
    );

    -- An occupation is one or more ordered sets of abilities. set_index starts at 1.
    CREATE TABLE occupation_sets (
        occupation_pack TEXT NOT NULL,
        occupation_id TEXT NOT NULL,
        set_index INTEGER NOT NULL,
        position INTEGER NOT NULL,
        ability_pack TEXT NOT NULL,
        ability_id TEXT NOT NULL,
        FOREIGN KEY (occupation_pack, occupation_id) REFERENCES occupations(pack, id) ON DELETE CASCADE
    );

    CREATE TABLE abilities (
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        id TEXT NOT NULL,
        position INTEGER NOT NULL,
        name TEXT NOT NULL,
        kind TEXT,
        price INTEGER,            -- experience; NULL means the pack sets no price
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (pack, id)
    );

    -- Armor, weapons, and any other gear.
    CREATE TABLE items (
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        id TEXT NOT NULL,
        position INTEGER NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (pack, id)
    );

    -- Generic effect rows: owner (species, occupation, ability, item) changes a target by an operation.
    CREATE TABLE effects (
        rowid INTEGER PRIMARY KEY,
        owner_type TEXT NOT NULL CHECK (owner_type IN ('species', 'occupation', 'ability', 'item')),
        owner_pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        owner_id TEXT NOT NULL,
        position INTEGER NOT NULL,
        verb TEXT NOT NULL,       -- e.g. mod.channel, mod.attr
        target TEXT NOT NULL,     -- e.g. strike, strength
        op TEXT NOT NULL CHECK (op IN ('add', 'replace')),
        value REAL,
        data TEXT NOT NULL DEFAULT '{}'
    );
    CREATE INDEX effects_owner ON effects(owner_type, owner_pack, owner_id);

    -- Constraint rows: what must hold before an owner (usually an ability) can be bought or keeps working.
    CREATE TABLE requirements (
        rowid INTEGER PRIMARY KEY,
        owner_type TEXT NOT NULL CHECK (owner_type IN ('species', 'occupation', 'ability', 'item')),
        owner_pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        owner_id TEXT NOT NULL,
        position INTEGER NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('species', 'ability', 'occupation_set', 'list')),
        ref_pack TEXT,
        ref_id TEXT,
        value INTEGER              -- occupation_set: the set index that must be met
    );
    CREATE INDEX requirements_owner ON requirements(owner_type, owner_pack, owner_id);

    CREATE TABLE portraits (
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        data BLOB NOT NULL,
        PRIMARY KEY (pack, name)
    );

    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL DEFAULT '',
        role TEXT NOT NULL DEFAULT 'player' CHECK (role IN ('gm', 'player'))
    );

    CREATE TABLE sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE campaigns (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        die TEXT NOT NULL DEFAULT 'd20',
        is_open INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE campaign_packs (
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        PRIMARY KEY (campaign_id, pack)
    );

    -- The campaign can forbid an ability.
    CREATE TABLE campaign_forbidden (
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        ability_pack TEXT NOT NULL,
        ability_id TEXT NOT NULL,
        PRIMARY KEY (campaign_id, ability_pack, ability_id)
    );

    CREATE TABLE characters (
        id TEXT PRIMARY KEY,
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        position INTEGER NOT NULL DEFAULT 0,
        name TEXT NOT NULL,
        npc INTEGER,
        level INTEGER,
        species_pack TEXT,
        species_id TEXT,
        occupation_pack TEXT,
        occupation_id TEXT,
        pinned_pack TEXT,         -- the occupation the player pinned as a reminder
        pinned_id TEXT,
        portrait TEXT,
        coin INTEGER,
        attack TEXT,
        xp_unspent INTEGER,
        owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
        data TEXT NOT NULL DEFAULT '{}'
    );

    CREATE TABLE character_attrs (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        attr TEXT NOT NULL,
        value REAL NOT NULL,      -- fractions allowed below 1 for tiny creatures
        PRIMARY KEY (character_id, attr)
    );

    CREATE TABLE character_gauges (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        gauge TEXT NOT NULL,
        prefix TEXT,
        total INTEGER,
        current INTEGER,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (character_id, gauge)
    );

    -- Trained combat bonuses written on the sheet (actions, strike, defense, initiative, ...).
    CREATE TABLE character_channels (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        channel TEXT NOT NULL,
        value INTEGER NOT NULL,
        data TEXT,                -- NULL when the pack wrote a bare number
        PRIMARY KEY (character_id, channel)
    );

    -- Ownership. data holds this character's own values for the row (skill %, level, overrides).
    CREATE TABLE character_abilities (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        ability_pack TEXT NOT NULL,
        ability_id TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (character_id, ability_pack, ability_id)
    );

    CREATE TABLE character_items (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        item_pack TEXT NOT NULL,
        item_id TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (character_id, item_pack, item_id)
    );

    -- What is switched on: worn armor, raised fields.
    CREATE TABLE character_active (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        ref TEXT NOT NULL,
        PRIMARY KEY (character_id, ref)
    );

    -- The list of abilities written on this character (a requirement of kind 'list' checks it).
    CREATE TABLE character_list (
        character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
        ability_pack TEXT NOT NULL,
        ability_id TEXT NOT NULL,
        PRIMARY KEY (character_id, ability_pack, ability_id)
    );

    -- Lore prose in chunks. The engine never reads it; embedding is filled by a later milestone.
    CREATE TABLE lore (
        id INTEGER PRIMARY KEY,
        pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        chunk INTEGER NOT NULL DEFAULT 0,
        body TEXT NOT NULL,
        embedding BLOB
    );
    """,
    # 2: effects have no operation; every effect row a character owns applies.
    """
    CREATE TABLE effects_new (
        rowid INTEGER PRIMARY KEY,
        owner_type TEXT NOT NULL CHECK (owner_type IN ('species', 'occupation', 'ability', 'item')),
        owner_pack TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
        owner_id TEXT NOT NULL,
        position INTEGER NOT NULL,
        verb TEXT NOT NULL,       -- e.g. mod.channel, mod.attr
        target TEXT NOT NULL,     -- e.g. strike, strength
        value REAL,
        data TEXT NOT NULL DEFAULT '{}'
    );
    INSERT INTO effects_new (rowid, owner_type, owner_pack, owner_id, position, verb, target, value, data)
        SELECT rowid, owner_type, owner_pack, owner_id, position, verb, target, value, data FROM effects;
    DROP TABLE effects;
    ALTER TABLE effects_new RENAME TO effects;
    CREATE INDEX effects_owner ON effects(owner_type, owner_pack, owner_id);
    """,
    # 3: a vehicle (items.kind = 'vehicle', including power armor and robot armor) has its own
    # attribute values, only for the attributes that apply to it. Other items have none.
    """
    CREATE TABLE item_attrs (
        item_pack TEXT NOT NULL,
        item_id TEXT NOT NULL,
        position INTEGER NOT NULL,
        attr TEXT NOT NULL,
        value REAL NOT NULL,
        PRIMARY KEY (item_pack, item_id, attr),
        FOREIGN KEY (item_pack, item_id) REFERENCES items(pack, id) ON DELETE CASCADE
    );
    """,
    # 4: any skill or ability can have ordered levels (names come from the pack), each with its own
    # experience price and effect rows. A character owns one level of it.
    """
    CREATE TABLE ability_levels (
        ability_pack TEXT NOT NULL,
        ability_id TEXT NOT NULL,
        level INTEGER NOT NULL,   -- 1, 2, ... in the pack's order
        name TEXT NOT NULL,
        price INTEGER,            -- experience; NULL means the pack sets no price
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (ability_pack, ability_id, level),
        FOREIGN KEY (ability_pack, ability_id) REFERENCES abilities(pack, id) ON DELETE CASCADE
    );
    ALTER TABLE effects ADD COLUMN level INTEGER;              -- NULL: the owner itself; n: its level n
    ALTER TABLE character_abilities ADD COLUMN level INTEGER;  -- the level owned, for abilities with levels
    """,
]


def db_path() -> Path:
    return Path(os.environ.get("LEX_DB") or DEFAULT_DB)


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def migrate(conn: sqlite3.Connection) -> int:
    cur = version(conn)
    for i in range(cur, len(MIGRATIONS)):
        with conn:
            conn.executescript(MIGRATIONS[i])
            conn.execute(f"PRAGMA user_version = {i + 1}")
    return version(conn)
