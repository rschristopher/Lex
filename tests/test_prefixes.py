from lex.prefixes import bump, color_band, convert, hit_factor, hit_threshold, interacts


def test_same_prefix():
    assert convert(32, "unit", "unit") == 32


def test_hecto_is_hundred():
    assert convert(1, "hecto", "unit") == 100
    assert convert(100, "unit", "hecto") == 1


def test_too_small_truncates_to_zero():
    assert convert(3, "centi", "unit") == 0
    assert convert(32, "unit", "hecto") == 0
    assert convert(6, "hecto", "mega") == 0
    assert not interacts(6, "hecto", "mega")


def test_club_vs_hecto_armor():
    assert convert(18, "unit", "hecto") == 0


def test_hecto_vs_unit_body():
    assert convert(4, "hecto", "unit") == 400


def test_ten_hecto_is_kilo():
    assert convert(10, "hecto", "kilo") == 1
    assert bump("hecto", 1) == "kilo"


def test_kilo_vs_mega_shield():
    assert convert(18, "kilo", "mega") == 0


def test_arbitrary_ratio_forty_two():
    # 42:1 is 4.2 deka. 41 unit does not meet 1 point of 42-scale armor.
    assert convert(41, "unit", dst_scale=42) == 0
    assert convert(42, "unit", dst_scale=42) == 1
    assert color_band(1) == "unit"
    assert color_band(2) == "unit"
    assert color_band(42) == "deka"
    assert color_band(100) == "hecto"
    assert hit_factor({"prefix": "hecto"}) == 100
    assert hit_threshold({"threshold": 6}) == 6
    assert hit_threshold({}) == 1
    assert convert(1, src_scale=42, dst="unit") == 42
    from lex.prefixes import describe_scale
    assert describe_scale(42) == "4.2 deka"


def test_kitten_never_chips_starship():
    # Each bite is independent. No leftover fraction carries to the next hit.
    bite = convert(3, "deci", "mega")
    assert bite == 0
    assert convert(3, "deci", "mega", threshold=1) == 0
    # A million bites still 0 if each is 0.
    assert sum(convert(3, "deci", "mega") for _ in range(1_000_000)) == 0
