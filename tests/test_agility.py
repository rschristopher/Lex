from lex.agility import agility_bonus
from lex.fold import fold
from lex.store import load_character


def test_agility_bonus_table():
    assert [agility_bonus(a) for a in (1, 9, 10, 14, 15, 20, 25, 30, 50, 75, 100)] == [
        0, 0, 0, 0, 1, 2, 3, 4, 8, 13, 18,
    ]


def test_agility_bonus_on_sheet():
    def ch(pid):
        sheet = fold(load_character(pid)[1], "universal")
        c = {x["id"]: x["value"] for x in sheet["channels"]}
        return c["attack"], c["parry"], c["dodge"], c["initiative"]
    assert ch("pc-iko") == (7, 5, 5, 3)
    assert ch("pc-venn") == (6, 6, 5, 2)
    assert ch("pc-ryn") == (7, 6, 8, 5)
    assert ch("pc-ilya") == (4, 2, 2, 1)
