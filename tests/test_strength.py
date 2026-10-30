from lex.fold import fold
from lex.store import load_character
from lex.strength import melee_damage, strength_dice

TABLE = {
    1: (1, "unit"), 9: (1, "unit"), 10: (1, "unit"), 19: (1, "unit"), 20: (2, "unit"),
    29: (2, "unit"), 30: (3, "unit"), 31: (5, "unit"), 32: (7, "unit"),
    33: (1, "deka"), 34: (2, "deka"), 35: (3, "deka"), 36: (5, "deka"), 37: (7, "deka"),
    38: (1, "hecto"), 43: (1, "kilo"), 48: (10, "kilo"), 53: (100, "kilo"), 57: (700, "kilo"),
    58: (1, "mega"), 73: (1, "giga"), 88: (1, "tera"), 99: (200, "tera"), 100: (300, "tera"),
}


def test_strength_dice_table():
    for score, want in TABLE.items():
        assert strength_dice(score) == want, score


def test_kilo_sword():
    def sword(s):
        r = melee_damage("3d6", s, "kilo")
        return r["damage"], r["prefix"], r["destroyed"]
    assert sword(10) == ("3d6", "unit", False)
    assert sword(20) == ("4d6", "unit", False)
    assert sword(32) == ("9d6", "unit", False)
    assert sword(33) == ("3d6", "deka", False)
    assert sword(43) == ("3d6", "kilo", False)
    assert sword(48) == ("12d6", "kilo", False)
    assert sword(58)[2] is True


def test_sheet_weapons_take_strength():
    def row(pid, wid):
        sheet = fold(load_character(pid)[1], "universal")
        return next(r for g in sheet["groups"] if g["id"] == "weapons" for r in g["rows"] if r["id"] == wid)
    assert (row("pc-ryn", "punch")["qty"], row("pc-ryn", "punch")["unit"]) == ("7d6", "D")
    assert row("pc-kesh", "club")["qty"] == "4d6"
    assert row("pc-calder", "punch")["qty"] == "1d6"
    assert row("pc-ryn", "resonant_blade")["unit"] == "hD"
    assert (row("npc-syrn", "bite")["qty"], row("npc-syrn", "bite")["unit"]) == ("4d6", "kD")


def test_bonus_damage_keeps_its_own_prefix():
    _pid, doc = load_character("pc-kesh")
    doc = dict(doc)
    doc["attrs"] = dict(doc["attrs"], strength=38)
    doc["weapons"] = [{
        "id": "flame_knife", "name": "Flame knife", "damage": "1d6",
        "material": "steel", "durability": "deka",
        "bonus": [{"damage": "2d6", "prefix": "unit", "type": "fire"}],
    }]
    doc["attack"] = "flame_knife"
    using = fold(doc, "universal")["using"]
    assert (using["damage"], using["prefix"], using["destroyed"]) == ("1d6", "hecto", True)
    assert using["bonus"] == [{"qty": "2d6", "unit": "D", "type": "fire", "prefix": "unit", "high": False}]


def test_pulled_blow_spares_the_weapon():
    full = melee_damage("3d6", 58, "kilo")
    pulled = melee_damage("3d6", 58, "kilo", pulled=43)
    assert full["destroyed"] is True
    assert (pulled["damage"], pulled["prefix"], pulled["destroyed"]) == ("3d6", "kilo", False)
    assert melee_damage("3d6", 20, "kilo", pulled=43)["damage"] == "4d6"
