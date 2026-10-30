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


def test_reflex_dodge_free_count_and_penalty():
    from lex.agility import reflex_free, reflex_penalty
    assert [reflex_free(a) for a in (10, 20, 30, 50, 75, 100)] == [1, 3, 5, 9, 14, 19]
    assert [reflex_penalty(20, n) for n in (1, 3, 4, 5, 6)] == [0, 0, -2, -4, -6]

    def dodge(pid):
        sheet = fold(load_character(pid)[1], "universal")
        return next(c for c in sheet["channels"] if c["id"] == "dodge")
    assert dodge("pc-ryn")["reflex_free"] == 3
    assert dodge("pc-venn")["reflex_free"] == 2
    assert "reflex_free" not in dodge("pc-ilya")
