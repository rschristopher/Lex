from lex.fold import eval_mod
from lex.sheet import list_adapters, sheet as resolve


def fold(conn, cid, adapter="universal"):
    return resolve(conn, cid, adapter)


def take_off(conn, cid):
    with conn:
        conn.execute("DELETE FROM character_active WHERE character_id=?", (cid,))


def test_class_adds_channels(conn):
    cid = "pc-ilya"
    sheet = fold(conn, cid, "universal")
    ch = {c["id"]: c["value"] for c in sheet["channels"]}
    assert ch["strike"] == 4
    assert ch["actions"] == 4
    assert ch["defense"] == 2
    assert "block" not in ch
    assert sheet["occupation"]["name"] == "Soldier"
    ids = [a["id"] for a in sheet["attrs"]]
    assert ids == [
        "strength", "agility", "endurance", "speed",
        "intellect", "willpower", "appearance",
    ]


def test_hecto_weapon_marked_high(conn):
    cid = "pc-venn"
    sheet = fold(conn, cid, "universal")
    assert (sheet["using"]["damage"], sheet["using"]["prefix"]) == ("6d6", "unit")
    plasma = sheet["using"]["bonus"][0]
    assert (plasma["qty"], plasma["unit"], plasma["type"], plasma["high"]) == ("1d6", "hD", "plasma", True)
    assert {c["id"] for c in sheet["channels"]} >= {"strike", "defense", "initiative"}
    assert "block" not in {c["id"] for c in sheet["channels"]}


def test_gear_groups(conn):
    cid = "pc-ilya"
    sheet = fold(conn, cid, "universal")
    names = {g["id"]: g for g in sheet["groups"]}
    assert names["armor"]["name"] == "Armor"
    assert names["weapons"]["name"] == "Weapons"
    assert names["abilities"]["name"] == "Abilities"
    worn = next(r for r in names["armor"]["rows"] if r["on"])
    assert worn["name"] == "Field plate"
    gun = next(r for r in names["weapons"]["rows"] if r["on"])
    assert gun["name"] == "Service rifle"
    assert sheet["using"]["name"] == "Service rifle"
    assert sheet["person"] == [{"name": "Coin", "value": 1200}]
    assert sheet["anima"]["label"] == "Anima"
    assert sheet["anima"]["total"] == 14
    segs = sheet["defense"]["armor"]["segments"]
    assert [s["id"] for s in segs] == ["field_plate", "hit_points"]
    assert segs[0]["value"] == 40
    assert segs[0]["prefix_label"] == "dA"
    assert segs[0]["style"] == "deka"
    assert segs[0]["factor"] == 10
    assert segs[-1]["id"] == "hit_points"
    assert segs[-1]["value"] == 32
    assert segs[-1]["style"] == "unit"
    assert gun["unit"] == "D"


def test_hecto_units_and_lancer(conn):
    cid = "pc-bex"
    sheet = fold(conn, cid, "universal")
    assert sheet["occupation"]["name"] == "Lancer"
    assert sheet["using"]["name"] == "Siege Cannon"
    assert sheet["using"]["damage"] == "4d6"
    assert sheet["using"]["prefix_label"] == "kD"
    armor = sheet["defense"]["armor"]
    assert [s["id"] for s in armor["segments"]] == ["siege_enforcer", "hit_points"]
    assert armor["segments"][0]["name"] == "Siege Enforcer"
    assert armor["segments"][0]["style"] == "hecto"
    assert armor["segments"][0]["value"] == 800
    assert armor["segments"][-1]["value"] == 28
    attrs = {a["id"]: a for a in sheet["attrs"]}
    assert attrs["strength"]["value"] == 38
    assert attrs["speed"]["value"] == 31
    assert attrs["strength"]["boosted"] is True
    assert attrs["speed"]["boosted"] is True
    assert "boosted" not in attrs["agility"]
    punch = next(r for g in sheet["groups"] if g["id"] == "weapons" for r in g["rows"] if r["id"] == "punch")
    assert punch["name"] == "Punch"
    assert punch["unit"] == "hD"
    assert punch["qty"] == "1d6"
    kick = next(r for g in sheet["groups"] if g["id"] == "weapons" for r in g["rows"] if r["id"] == "kick")
    assert kick["unit"] == "hD"
    assert kick["qty"] == "2d6"
    take_off(conn, cid)
    off = fold(conn, cid, "universal")
    off_attrs = {a["id"]: a["value"] for a in off["attrs"]}
    assert off_attrs["strength"] == 30
    assert off_attrs["speed"] == 8
    off_punch = next(r for g in off["groups"] if g["id"] == "weapons" for r in g["rows"] if r["id"] == "punch")
    assert off_punch["unit"] == "D"
    ryn = fold(conn, "pc-ryn", "universal")
    assert ryn["occupation"]["name"] == "Augmented"
    assert (ryn["using"]["damage"], ryn["using"]["prefix_label"]) == ("7d6", "D")
    assert [(b["qty"], b["unit"], b["type"]) for b in ryn["using"]["bonus"]] == [("2d6", "hD", "resonance")]
    ch = {c["id"]: c["value"] for c in ryn["channels"]}
    assert ch["actions"] == 8
    assert ch["defense"] == 8  # 6 trained + Agility 20 bonus
    assert next(c["reflex"] for c in ryn["channels"] if c["id"] == "defense") is True
    simp = fold(conn, cid, "u-simplified")
    g = {x["id"]: x for x in simp["gauges"]}
    assert list(g) == ["hit_points"]
    assert g["hit_points"]["label"] == "Hit points"
    assert g["hit_points"]["total"] == 28
    sch = {c["id"]: c["value"] for c in simp["channels"]}
    assert set(sch) == {"actions", "strike", "defense", "initiative"}


def test_eval_mod():
    spec = {"sub": 10, "div": 2, "floor": True}
    assert eval_mod(10, spec) == 0
    assert eval_mod(13, spec) == 1
    assert eval_mod(9, spec) == -1
    assert eval_mod(18, spec) == 4


def test_simplified_view(conn):
    cid = "pc-ilya"
    sheet = fold(conn, cid, "u-simplified")
    assert sheet["adapter"] == "u-simplified"
    attrs = {a["id"]: a for a in sheet["attrs"]}
    assert set(attrs) == {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}
    assert attrs["dexterity"]["value"] == 13
    assert attrs["dexterity"]["mod"] == 1
    assert attrs["wisdom"]["value"] == 11
    # Charisma is derived: average of Appearance 10, Willpower 11, Intellect 11, rounded down.
    assert attrs["charisma"]["value"] == 10
    assert attrs["charisma"]["mod"] == 0
    gauges = {g["id"]: g for g in sheet["gauges"]}
    assert list(gauges) == ["hit_points"]
    assert gauges["hit_points"]["label"] == "Hit points"
    assert gauges["hit_points"]["total"] == 32
    ch = {c["id"]: c["value"] for c in sheet["channels"]}
    assert set(ch) == {"actions", "strike", "defense", "initiative"}
    assert ch["defense"] == 2
    assert not any(c.get("reflex") for c in sheet["channels"])
    assert ch["initiative"] == 2
    assert ch["strike"] == 4
    assert ch["actions"] == 4


def test_armor_does_not_change_hit_or_miss(conn):
    cid = "pc-ilya"
    on = {c["id"]: c["value"] for c in fold(conn, cid, "universal")["channels"]}
    simp_on = {c["id"]: c["value"] for c in fold(conn, cid, "u-simplified")["channels"]}
    take_off(conn, cid)
    off = {c["id"]: c["value"] for c in fold(conn, cid, "universal")["channels"]}
    assert on == off
    simp_off = {c["id"]: c["value"] for c in fold(conn, cid, "u-simplified")["channels"]}
    assert simp_on == simp_off


def test_field_on_top_of_armor(conn):
    cid = "pc-calder"
    sheet = fold(conn, cid, "universal")
    segs = sheet["defense"]["armor"]["segments"]
    assert [s["id"] for s in segs] == ["magic_shield", "robes", "hit_points"]
    assert segs[0]["name"] == "Magic shield"
    assert segs[0]["value"] == 30
    assert segs[0]["style"] == "unit"
    assert segs[1]["value"] == 18
    assert segs[-1]["id"] == "hit_points"
    assert segs[-1]["value"] == 22
    assert sheet["anima"]["label"] == "Anima"
    assert sheet["anima"]["total"] == 56
    assert all(p["name"] != "Anima" for p in sheet["person"])
    simp = fold(conn, cid, "u-simplified")
    assert simp["anima"]["label"] == "Stamina"
    assert all(p["name"] != "Stamina" for p in simp["person"])
    assert all(p["name"] != "Anima" for p in simp["person"])
    magic = next(g for g in sheet["groups"] if g["id"] == "spell")
    assert magic["name"] == "Magic"
    assert {r["id"] for r in magic["rows"]} >= {"magic_shield", "flame_bolt"}
    assert next(r for r in magic["rows"] if r["id"] == "magic_shield")["select"] == "activated"
    assert next(r for r in magic["rows"] if r["id"] == "flame_bolt")["select"] == "attack"
    armor_ids = {r["id"] for r in next(g for g in sheet["groups"] if g["id"] == "armor")["rows"]}
    assert "magic_shield" not in armor_ids
    mora = fold(conn, "pc-mora", "universal")
    assert [s["id"] for s in mora["defense"]["armor"]["segments"]] == ["tk_field", "hit_points"]
    assert mora["defense"]["armor"]["segments"][0]["name"] == "Telekinetic defense field"
    assert mora["defense"]["armor"]["segments"][0]["threshold"] == 6
    assert mora["defense"]["armor"]["segments"][0]["factor"] == 1
    assert mora["defense"]["armor"]["segments"][0]["style"] == "unit"
    assert mora["defense"]["armor"]["segments"][0]["value"] == 40
    assert mora["defense"]["armor"]["segments"][-1]["value"] == 24
    kesh = fold(conn, "pc-kesh", "universal")
    assert all((s.get("threshold") or 1) == 1 for s in kesh["defense"]["armor"]["segments"])
    psi = next(g for g in mora["groups"] if g["id"] == "psionic")
    assert psi["name"] == "Psionics"
    assert {r["id"] for r in psi["rows"]} >= {"tk_field", "mind_lance"}
    assert "tk_field" not in {r["id"] for g in mora["groups"] if g["id"] == "armor" for r in g["rows"]}
    rows = next(g for g in mora["groups"] if g["id"] == "armor")["rows"]
    assert next(r for r in rows if r["name"] == "Unarmored")["on"]
    take_off(conn, "pc-mora")
    assert [s["id"] for s in fold(conn, "pc-mora", "universal")["defense"]["armor"]["segments"]] == ["hit_points"]


def test_adapters_listed(conn):
    ids = {a["id"] for a in list_adapters(conn)}
    assert ids == {"universal", "u-simplified"}


def test_simplified_strength_scale(conn):
    cid = "npc-syrn"
    for lex, score, mod in [(10, 10, 0), (30, 30, 10), (35, 300, 145), (43, 11943, 5966)]:
        with conn:
            conn.execute("UPDATE character_attrs SET value=? WHERE character_id=? AND attr='strength'", (lex, cid))
        row = next(a for a in fold(conn, cid, "u-simplified")["attrs"] if a["id"] == "strength")
        assert (row["value"], row["mod"]) == (score, mod)
