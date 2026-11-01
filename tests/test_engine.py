import json

from lex import engine, packs
from lex.sheet import sheet


def pack(pid="test", **rows):
    doc = {"id": pid, "name": pid, "adapter": None, "species": [], "occupations": [], "abilities": [], "ladders": [],
           "items": [], "characters": [], "portraits": {}, "lore": []}
    doc.update(rows)
    return doc


def channels(conn, cid):
    return {c["id"]: c["value"] for c in sheet(conn, cid)["channels"]}


def test_every_effect_applies():
    effects = [
        {"verb": "mod.attr", "target": "speed", "value": 23},
        {"verb": "mod.attr", "target": "speed", "value": 2},
        {"verb": "mod.attr", "target": "strength", "value": 2},
        {"verb": "mod.channel", "target": "defense", "value": 1, "reflex": True},
    ]
    vals, flagged = engine.apply_effects({"speed": 8, "strength": 10}, effects, "mod.attr")
    assert vals == {"speed": 33, "strength": 12}
    assert flagged == set()
    assert engine.apply_effects({}, effects, "mod.channel") == ({"defense": 1}, {"defense"})


def lore_pack():
    # Every rule here is a row in a pack; the engine has no idea what any of it is.
    return pack(
        species=[{"id": "deep_one", "name": "Deep One",
                  "effects": [{"verb": "mod.channel", "target": "initiative", "value": 1}]}],
        abilities=[
            {"id": "tide_sense", "name": "Tide sense", "price": 3,
             "effects": [{"verb": "mod.channel", "target": "defense", "value": 2, "reflex": True}]},
            {"id": "deep_call", "name": "Deep call", "price": 5,
             "requires": [{"kind": "species", "id": "deep_one"}],
             "effects": [{"verb": "mod.channel", "target": "strike", "value": 1}]},
            {"id": "elder_sign", "name": "Elder sign", "price": 2,
             "requires": [{"kind": "occupation_set", "id": "keeper", "set": 1}]},
            {"id": "old_tongue", "name": "Old tongue", "price": 1, "requires": [{"kind": "list"}]},
        ],
        occupations=[{"id": "keeper", "name": "Keeper", "sets": [["tide_sense"], ["deep_call"]]}],
        characters=[
            {"id": "marsh", "name": "Marsh", "species": "deep_one", "unspent_experience": 20,
             "attrs": {"agility": 10}, "channels": {"strike": 0, "defense": 0, "initiative": 0}, "list": ["old_tongue"]},
            {"id": "olmstead", "name": "Olmstead", "species": "universal:human", "unspent_experience": 20,
             "attrs": {"agility": 10}, "channels": {"strike": 0, "defense": 0, "initiative": 0},
             "abilities": ["deep_call"]},
        ],
    )


def test_sheet_sums_owned_rows(conn):
    packs.import_pack(conn, lore_pack())
    assert channels(conn, "marsh") == {"actions": 0, "strike": 0, "defense": 0, "initiative": 1}
    engine.buy_ability(conn, "marsh", "test", "tide_sense")
    s = sheet(conn, "marsh")
    ch = {c["id"]: c for c in s["channels"]}
    assert ch["defense"]["value"] == 2 and ch["defense"]["reflex"] is True
    assert s["unspent_experience"] == 17


def test_constraints_block_purchase_and_stop_owned_abilities(conn):
    packs.import_pack(conn, lore_pack())
    try:
        engine.buy_ability(conn, "olmstead", "test", "elder_sign")
        raise AssertionError("bought without meeting the set")
    except engine.Refused as e:
        assert "needs set 1 of occupation test:keeper" in str(e)
    # Olmstead owns an ability whose species constraint he breaks: it stays on the sheet but does nothing.
    s = sheet(conn, "olmstead")
    assert s["inactive"] == [{"id": "deep_call", "name": "Deep call", "why": ["needs species test:deep_one"]}]
    assert channels(conn, "olmstead")["strike"] == 0
    # The list written on Marsh lets him buy what is on it; Olmstead has no such list.
    engine.buy_ability(conn, "marsh", "test", "old_tongue")
    try:
        engine.buy_ability(conn, "olmstead", "test", "old_tongue")
        raise AssertionError("bought off-list")
    except engine.Refused as e:
        assert "list" in str(e)


def test_occupation_sets_follow_from_abilities(conn):
    packs.import_pack(conn, lore_pack())
    assert engine.occupation_progress(conn, "marsh")[0]["sets_met"] == 0
    engine.buy_ability(conn, "marsh", "test", "deep_call")
    # A later set counts only when every set before it is met.
    assert engine.occupation_progress(conn, "marsh")[0]["sets_met"] == 0
    engine.buy_ability(conn, "marsh", "test", "tide_sense")
    top = sheet(conn, "marsh")["occupations"][0]
    assert (top["name"], top["sets_met"], top["sets"]) == ("Keeper", 2, 2)
    engine.buy_ability(conn, "marsh", "test", "elder_sign")
    assert sheet(conn, "marsh")["unspent_experience"] == 20 - 5 - 3 - 2


def test_campaign_can_forbid_an_ability(conn):
    packs.import_pack(conn, lore_pack())
    with conn:
        conn.execute("INSERT INTO campaigns (id, name) VALUES (1, 'Innsmouth')")
        conn.execute("INSERT INTO campaign_forbidden VALUES (1, 'test', 'tide_sense')")
        conn.execute("UPDATE characters SET campaign_id=1 WHERE id='marsh'")
    try:
        engine.buy_ability(conn, "marsh", "test", "tide_sense")
        raise AssertionError("bought a forbidden ability")
    except engine.Refused as e:
        assert "forbidden" in str(e)
    # The GM can still add it, and it does not work while the campaign forbids it.
    engine.buy_ability(conn, "marsh", "test", "tide_sense", grant=True)
    assert channels(conn, "marsh")["defense"] == 0


def test_no_price_means_no_purchase(conn):
    try:
        engine.buy_ability(conn, "pc-ilya", "universal", "keen")
        raise AssertionError
    except engine.Refused as e:
        assert "no price" in str(e)


def test_worn_vehicle_replaces_physical_attributes(conn):
    def attrs(cid):
        return {a["id"]: a["value"] for a in sheet(conn, cid)["attrs"]}

    bex = attrs("pc-bex")
    assert (bex["strength"], bex["speed"]) == (38, 31)
    assert (bex["agility"], bex["endurance"], bex["intellect"], bex["willpower"]) == (11, 14, 11, 12)
    with conn:
        conn.execute("DELETE FROM character_active WHERE character_id='pc-bex'")
    off = attrs("pc-bex")
    assert (off["strength"], off["speed"]) == (30, 8)

    # A different wearer gets the suit's values, not their own plus something.
    with conn:
        conn.execute("INSERT INTO character_items VALUES ('pc-calder', 99, 'universal', 'siege_enforcer', '{}')")
        conn.execute("DELETE FROM character_active WHERE character_id='pc-calder'")
        conn.execute("INSERT INTO character_active VALUES ('pc-calder', 0, 'siege_enforcer')")
    before = {a["attr"]: a["value"] for a in conn.execute(
        "SELECT attr, value FROM character_attrs WHERE character_id='pc-calder'")}
    calder = attrs("pc-calder")
    assert (calder["strength"], calder["speed"]) == (38, 31)
    assert (before["strength"], before["speed"]) != (38, 31)
    assert calder["intellect"] == before["intellect"] and calder["willpower"] == before["willpower"]


def test_vehicle_rows_have_their_own_attributes(conn):
    # A vehicle that is not worn: its own attribute rows, only those that apply, resolved on its own.
    packs.import_pack(conn, pack(
        items=[{"id": "skiff", "name": "Skiff", "kind": "vehicle", "attrs": {"speed": 40}}],
        characters=[{"id": "zadok", "name": "Zadok", "attrs": {"strength": 9, "speed": 7}, "items": ["skiff"]}],
    ))
    assert engine.vehicle_attributes(conn, "test", "skiff") == {"speed": 40}
    s = sheet(conn, "zadok")
    assert s["vehicles"] == [{"id": "skiff", "name": "Skiff", "attrs": {"speed": 40}}]
    # The pilot's own sheet is untouched by a vehicle that is not worn.
    attrs = {a["id"]: a["value"] for a in s["attrs"]}
    assert (attrs["strength"], attrs["speed"]) == (9, 7)
    assert engine.vehicle_attributes(conn, "universal", "scales") == {}


def test_wearer_effects_do_not_reach_inside_a_worn_vehicle(conn):
    # Bex owns an ability row with +5 Strength, +3 Speed and +2 Agility.
    packs.import_pack(conn, pack(abilities=[{"id": "might", "name": "Might", "effects": [
        {"verb": "mod.attr", "target": "strength", "value": 5},
        {"verb": "mod.attr", "target": "speed", "value": 3},
        {"verb": "mod.attr", "target": "agility", "value": 2},
    ]}]))
    with conn:
        conn.execute("INSERT INTO character_abilities (character_id, position, ability_pack, ability_id)"
                     " VALUES ('pc-bex', 99, 'test', 'might')")

    def attrs():
        return {a["id"]: a["value"] for a in sheet(conn, "pc-bex")["attrs"]}

    suit = attrs()
    assert (suit["strength"], suit["speed"], suit["agility"]) == (38, 31, 13)
    # An effect that belongs to the worn vehicle itself still applies to its values.
    with conn:
        conn.execute("INSERT INTO effects (owner_type, owner_pack, owner_id, position, verb, target, value)"
                     " VALUES ('item', 'universal', 'siege_enforcer', 0, 'mod.attr', 'strength', 1)")
    assert attrs()["strength"] == 39
    with conn:
        conn.execute("DELETE FROM character_active WHERE character_id='pc-bex'")
    off = attrs()
    assert (off["strength"], off["speed"], off["agility"]) == (35, 11, 13)



def leveled_pack():
    # Test-only rows: level names, count, prices, and bonuses all come from the pack.
    return pack(
        abilities=[
            {"id": "occult_lore", "name": "Occult lore", "levels": [
                {"name": "Initiate", "price": 2, "effects": [{"verb": "mod.channel", "target": "initiative", "value": 1}]},
                {"name": "Adept of the Necronomicon", "price": 4,
                 "effects": [{"verb": "mod.channel", "target": "initiative", "value": 3}]},
                {"name": "Dreamer of R'lyeh", "price": 9,
                 "effects": [{"verb": "mod.channel", "target": "initiative", "value": 6},
                             {"verb": "mod.channel", "target": "defense", "value": 1}]},
            ]},
            {"id": "swimming", "name": "Swimming", "price": 1,
             "effects": [{"verb": "mod.channel", "target": "defense", "value": 1}]},
        ],
        characters=[{"id": "armitage", "name": "Armitage", "unspent_experience": 20,
                     "channels": {"strike": 0, "defense": 0, "initiative": 0}}],
    )


def test_skill_effect_rows_apply(conn):
    packs.import_pack(conn, leveled_pack())
    assert channels(conn, "armitage")["defense"] == 0
    engine.buy_ability(conn, "armitage", "test", "swimming")
    assert channels(conn, "armitage")["defense"] == 1
    try:
        engine.buy_ability(conn, "armitage", "test", "swimming")
        raise AssertionError("bought an unleveled skill twice")
    except engine.Refused as e:
        assert "already owned" in str(e)


def test_skill_levels_bought_in_order(conn):
    packs.import_pack(conn, leveled_pack())

    def level_row():
        rows = next(g for g in sheet(conn, "armitage")["groups"] if g["id"] == "abilities")["rows"]
        return next(r for r in rows if r["id"] == "occult_lore")

    try:
        engine.buy_ability(conn, "armitage", "test", "occult_lore", level=2)
        raise AssertionError("skipped a level")
    except engine.Refused as e:
        assert "buy level 1 (Initiate) first" in str(e)
    assert engine.buy_ability(conn, "armitage", "test", "occult_lore", level=1) == 18
    assert channels(conn, "armitage")["initiative"] == 1
    assert level_row()["level"] == "Initiate"
    try:
        engine.buy_ability(conn, "armitage", "test", "occult_lore", level=3)
        raise AssertionError("skipped a level")
    except engine.Refused as e:
        assert "levels cannot be skipped" in str(e)
    assert engine.buy_ability(conn, "armitage", "test", "occult_lore") == 14
    # Level bonuses stack: level 2 is level 1's +1 plus its own +3.
    assert channels(conn, "armitage")["initiative"] == 1 + 3
    assert engine.buy_ability(conn, "armitage", "test", "occult_lore") == 5
    ch = channels(conn, "armitage")
    assert (ch["initiative"], ch["defense"]) == (1 + 3 + 6, 1)
    assert level_row()["level"] == "Dreamer of R'lyeh"
    try:
        engine.buy_ability(conn, "armitage", "test", "occult_lore")
        raise AssertionError("past the top level")
    except engine.Refused as e:
        assert "top level" in str(e)
    # The owned level round-trips through export.
    assert packs.character_doc(conn, "armitage")["abilities"] == [{"id": "occult_lore", "level": 3}]


def test_leveled_pack_round_trips(conn, tmp_path):
    packs.import_pack(conn, leveled_pack())
    engine.buy_ability(conn, "armitage", "test", "occult_lore")
    first = packs.export_pack(conn, "test", tmp_path / "a")
    packs.import_pack(conn, first)
    second = packs.export_pack(conn, "test", tmp_path / "b")
    for name in ("abilities.json", "characters/armitage.json"):
        assert (first / name).read_text() == (second / name).read_text()
    assert channels(conn, "armitage")["initiative"] == 1
    for change, message in (
        (lambda d: d["abilities"][0].update(price=3), "an ability with levels sets its price on each level"),
        (lambda d: d["characters"][0].update(abilities=[{"id": "occult_lore", "level": 4}]),
         "level: must be one of the ability's levels, 1 to 3"),
    ):
        bad = leveled_pack()
        change(bad)
        try:
            packs.import_pack(conn, bad)
            raise AssertionError(message)
        except packs.PackError as e:
            assert message in " | ".join(e.errors)


def test_casting_roll_comes_from_the_ladder_rows(conn):
    # A non-physical ability that references the shipped skill-level ladder; prices are this test's own.
    packs.import_pack(conn, pack(
        abilities=[{"id": "dread_whisper", "name": "Dread whisper", "kind": "psionic",
                    "ladder": "universal:skill_levels",
                    "levels": [{"price": 1}, {"price": 1}, {"price": 1}, {"price": 1}, {"price": 1}]}],
        characters=[{"id": "wilbur", "name": "Wilbur", "unspent_experience": 5}],
    ))
    seen = []
    for _ in range(5):
        engine.buy_ability(conn, "wilbur", "test", "dread_whisper")
        rows = next(g for g in sheet(conn, "wilbur")["groups"] if g["id"] == "psionic")["rows"]
        c = next(r for r in rows if r["id"] == "dread_whisper")["casting"]
        seen.append((c["level"], c["d20"], c["roll"]))
    # docs/universal-system.md casting table.
    assert seen == [
        ("Novice", 11, True), ("Apprentice", 7, True), ("Professional", 5, True),
        ("Expert", None, False), ("Master", None, False),
    ]


def test_ladder_ability_round_trips(conn, tmp_path):
    packs.import_pack(conn, pack(abilities=[
        {"id": "dread_whisper", "name": "Dread whisper", "ladder": "universal:skill_levels",
         "levels": [{"price": 1}, {"price": 2}, {"price": 3}, {"price": 4}, {"price": 5}]},
        {"id": "dream_sight", "name": "Dream sight", "ladder": "universal:skill_levels"},
    ]))
    first = packs.export_pack(conn, "test", tmp_path / "a")
    packs.import_pack(conn, first)
    second = packs.export_pack(conn, "test", tmp_path / "b")
    assert (first / "abilities.json").read_text() == (second / "abilities.json").read_text()
    rows = {r["id"]: r for r in json.loads((first / "abilities.json").read_text())}
    assert "levels" not in rows["dream_sight"]
    assert rows["dread_whisper"]["levels"][4] == {"price": 5}


def test_ladder_validation(conn):
    bad = pack(
        ladders=[{"id": "l", "name": "L", "levels": [{"name": "One", "d20": 21}]}],
        abilities=[{"id": "a", "name": "A", "ladder": "universal:skill_levels", "levels": [{"price": 1}]},
                   {"id": "b", "name": "B", "ladder": "nowhere"}],
    )
    try:
        packs.import_pack(conn, bad)
        raise AssertionError
    except packs.PackError as e:
        text = " | ".join(e.errors)
        assert "d20: must be 1 to 20, or null for no roll" in text
        assert "must have one entry per level of its ladder (5)" in text
        assert "unknown ladders 'nowhere'" in text
