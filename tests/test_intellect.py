from lex.intellect import intellect_bonus


def test_intellect_bonus_table():
    assert [intellect_bonus(i) for i in (1, 9, 10, 20, 30, 50, 75, 100)] == [0, 0, 0, 2, 4, 8, 13, 18]
