from lex.willpower import willpower_resist_bonus


def test_willpower_resist_bonus_breakpoints():
    cases = {1: 0, 10: 0, 14: 0, 15: 1, 60: 10, 63: 10, 64: 11, 99: 19, 100: 20, 120: 20}
    assert {s: willpower_resist_bonus(s) for s in cases} == cases
