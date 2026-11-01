from lex import engine, packs
from lex.sheet import sheet


def pack(pid="test", **rows):
    doc = {"id": pid, "name": pid, "adapter": None, "species": [], "occupations": [], "abilities": [],
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


def test_layer_replaces_physical_attributes_while_worn(conn):
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
