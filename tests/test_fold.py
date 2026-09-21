from lex.fold import eval_mod, fold
from lex.store import load_character, list_adapters


def test_class_adds_channels():
    _pid, doc = load_character("pc-ilya")
    sheet = fold(doc, "universal")
    ch = {c["id"]: c["value"] for c in sheet["channels"]}
    assert ch["attack"] == 4
    assert ch["actions"] == 4
    assert ch["parry"] == 2
    assert ch["dodge"] == 2
    assert "block" not in ch
    assert sheet["class"]["name"] == "Soldier"
    ids = [a["id"] for a in sheet["attrs"]]
    assert ids == [
        "strength", "agility", "endurance", "speed",
        "intellect", "will", "awareness", "presence", "appearance",
    ]


def test_hecto_weapon_marked_high():
    _pid, doc = load_character("pc-venn")
    sheet = fold(doc, "universal")
    assert sheet["using"]["prefix"] == "hecto"
    assert sheet["using"]["high"] is True
    assert {c["id"] for c in sheet["channels"]} >= {"attack", "parry", "dodge", "block", "initiative"}


def test_gear_groups():
    _pid, doc = load_character("pc-ilya")
    sheet = fold(doc, "universal")
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
    assert segs[0]["prefix_label"] == "daA"
    assert segs[0]["style"] == "deka"
    assert segs[0]["factor"] == 10
    assert segs[-1]["id"] == "hit_points"
    assert segs[-1]["value"] == 32
    assert segs[-1]["style"] == "unit"
    assert gun["unit"] == "D"


def test_hecto_units_and_lancer():
    _pid, doc = load_character("pc-bex")
    sheet = fold(doc, "universal")
    assert sheet["class"]["name"] == "Lancer"
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
    assert attrs["strength"]["value"] == 30
    assert attrs["speed"]["value"] == 88
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
    off_doc = dict(doc)
    off_doc["activated"] = []
    off = fold(off_doc, "universal")
    off_attrs = {a["id"]: a["value"] for a in off["attrs"]}
    assert off_attrs["strength"] == 16
    assert off_attrs["speed"] == 9
    off_punch = next(r for g in off["groups"] if g["id"] == "weapons" for r in g["rows"] if r["id"] == "punch")
    assert off_punch["unit"] == "D"
    ryn = fold(load_character("pc-ryn")[1], "universal")
    assert ryn["class"]["name"] == "Augmented"
    assert ryn["using"]["prefix_label"] == "hD"
    ch = {c["id"]: c["value"] for c in ryn["channels"]}
    assert ch["actions"] == 8
    assert ch["dodge"] == 6
    assert "auto_dodge" not in ch
    assert next(c["automatic"] for c in ryn["channels"] if c["id"] == "dodge") is True
    simp = fold(doc, "u-simplified")
    g = {x["id"]: x for x in simp["gauges"]}
    assert list(g) == ["hit_points"]
    assert g["hit_points"]["label"] == "Hit points"
    assert g["hit_points"]["total"] == 28
    sch = {c["id"]: c["value"] for c in simp["channels"]}
    assert "defense" not in sch
    assert set(sch) == {"actions", "attack", "parry", "dodge", "block", "initiative"}


def test_eval_mod():
    spec = {"sub": 10, "div": 2, "floor": True}
    assert eval_mod(10, spec) == 0
    assert eval_mod(13, spec) == 1
    assert eval_mod(9, spec) == -1
    assert eval_mod(18, spec) == 4


def test_simplified_view():
    _pid, doc = load_character("pc-ilya")
    sheet = fold(doc, "u-simplified")
    assert sheet["adapter"] == "u-simplified"
    attrs = {a["id"]: a for a in sheet["attrs"]}
    assert set(attrs) == {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}
    assert attrs["dexterity"]["value"] == 13
    assert attrs["dexterity"]["mod"] == 1
    assert attrs["wisdom"]["value"] == 11
    gauges = {g["id"]: g for g in sheet["gauges"]}
    assert list(gauges) == ["hit_points"]
    assert gauges["hit_points"]["label"] == "Hit points"
    assert gauges["hit_points"]["total"] == 32
    ch = {c["id"]: c["value"] for c in sheet["channels"]}
    assert set(ch) == {"actions", "attack", "parry", "dodge", "initiative"}
    assert "defense" not in ch
    assert "auto_dodge" not in ch
    assert ch["parry"] == 2
    assert ch["dodge"] == 2
    assert not any(c.get("automatic") for c in sheet["channels"])
    assert ch["initiative"] == 2
    assert ch["attack"] == 4
    assert ch["actions"] == 4


def test_armor_does_not_change_hit_or_miss():
    _pid, doc = load_character("pc-ilya")
    on = {c["id"]: c["value"] for c in fold(doc, "universal")["channels"]}
    off_doc = dict(doc)
    off_doc["activated"] = []
    off = {c["id"]: c["value"] for c in fold(off_doc, "universal")["channels"]}
    assert on == off
    simp_on = {c["id"]: c["value"] for c in fold(doc, "u-simplified")["channels"]}
    simp_off = {c["id"]: c["value"] for c in fold(off_doc, "u-simplified")["channels"]}
    assert simp_on == simp_off


def test_field_on_top_of_armor():
    _pid, doc = load_character("pc-calder")
    sheet = fold(doc, "universal")
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
    simp = fold(doc, "u-simplified")
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
    mora = fold(load_character("pc-mora")[1], "universal")
    assert [s["id"] for s in mora["defense"]["armor"]["segments"]] == ["tk_field", "hit_points"]
    assert mora["defense"]["armor"]["segments"][0]["name"] == "Telekinetic defense field"
    assert mora["defense"]["armor"]["segments"][0]["threshold"] == 6
    assert mora["defense"]["armor"]["segments"][0]["factor"] == 1
    assert mora["defense"]["armor"]["segments"][0]["style"] == "unit"
    assert mora["defense"]["armor"]["segments"][0]["value"] == 40
    assert mora["defense"]["armor"]["segments"][-1]["value"] == 24
    kesh = fold(load_character("pc-kesh")[1], "universal")
    assert all((s.get("threshold") or 1) == 1 for s in kesh["defense"]["armor"]["segments"])
    psi = next(g for g in mora["groups"] if g["id"] == "psionic")
    assert psi["name"] == "Psionics"
    assert {r["id"] for r in psi["rows"]} >= {"tk_field", "mind_lance"}
    assert "tk_field" not in {r["id"] for g in mora["groups"] if g["id"] == "armor" for r in g["rows"]}
    rows = next(g for g in mora["groups"] if g["id"] == "armor")["rows"]
    assert next(r for r in rows if r["name"] == "Unarmored")["on"]
    off = dict(load_character("pc-mora")[1])
    off["activated"] = []
    assert [s["id"] for s in fold(off, "universal")["defense"]["armor"]["segments"]] == ["hit_points"]


def test_adapters_listed():
    ids = {a["id"] for a in list_adapters()}
    assert ids == {"universal", "u-simplified"}
