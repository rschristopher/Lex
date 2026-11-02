import copy
import json
import shutil
from pathlib import Path

import pytest

from lex import bakeoff
from lex.paths import PACK_DIR
from lex.speed import top_speed_ms
from lex.strength import lift_kg

FIX = Path(__file__).parent / "fixtures" / "bakeoff"
STORY = "odyssey-cyclops"


def candidates():
    return bakeoff.load_candidates([str(PACK_DIR / "universal"), str(FIX / "packs" / "toy-epic")],
                                   [f"K={FIX / 'keys' / 'toy-key'}"])


@pytest.fixture
def bk():
    return bakeoff.Bakeoff(FIX / "run", candidates())


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "run"
    shutil.copytree(FIX / "run", d)
    return d


def test_lift_and_speed_follow_the_docs_tables():
    assert lift_kg(10) == 60
    assert round(lift_kg(43) / 1000) == 72  # kilo, 72 t
    assert round(top_speed_ms(40)) == 327  # speed of sound
    assert round(top_speed_ms(52) / 1000, 1) == 8.8


def test_key_rows_are_category_and_name():
    k = bakeoff.load_key_candidate("K", FIX / "keys" / "toy-key")
    assert k.rows["kinds/giant"] == "Giant" and k.private and not k.is_pack


def test_keys_from_the_environment(monkeypatch):
    monkeypatch.setenv(bakeoff.KEYS_ENV, f"K={FIX / 'keys' / 'toy-key'}")
    assert bakeoff.parse_keys(None) == [("K", str(FIX / "keys" / "toy-key"))]
    with pytest.raises(bakeoff.BakeoffError):
        bakeoff.parse_keys(["no-label"])


def test_fixtures_are_valid(bk):
    bk.check()
    assert bk.quotes_checked[STORY]
    assert len(bk.mappings[("toy-epic", STORY)]) == 2


def test_a_quote_not_in_the_story_is_refused(bk):
    story = copy.deepcopy(bk.stories[STORY])
    story["beats"][0]["quote"] = "He lifted the whole island with one hand."
    text = (FIX / "run" / "stories" / "odyssey-cyclops.txt").read_text()
    assert any("quote is not in the source text" in e for e in bakeoff.validate_story(story, text))


def test_every_need_and_attribute_cites_a_beat(bk):
    story = copy.deepcopy(bk.stories[STORY])
    story["needs"][0]["beats"] = []
    story["characters"][0]["attrs"]["agility"]["beats"] = ["b-nowhere"]
    errs = bakeoff.validate_story(story)
    assert any("needs/human: must cite" in e for e in errs)
    assert any("unknown beat 'b-nowhere'" in e for e in errs)


def test_a_mapping_must_use_real_rows_of_the_right_kind(bk):
    story = bk.stories[STORY]
    m = copy.deepcopy(bk.mappings[("toy-epic", STORY)][0])
    m["map"]["human"]["rows"] = ["ability/hide"]
    m["map"]["hide"]["rows"] = ["ability/teleport"]
    del m["map"]["deceive"]
    errs = bakeoff.validate_mapping(m, story, bk.candidates["toy-epic"])
    assert any("species need maps to species rows" in e for e in errs)
    assert any("no row 'ability/teleport'" in e for e in errs)
    assert any("'deceive' is not mapped" in e for e in errs)


def test_a_bad_artifact_stops_the_run(run_dir):
    p = run_dir / "crosswalks" / "toy-epic__K.r1.json"
    doc = json.loads(p.read_text())
    doc["map"]["ability/hide"] = ["talents/flying"]
    p.write_text(json.dumps(doc))
    with pytest.raises(bakeoff.BakeoffError, match="no row 'talents/flying'"):
        bakeoff.run(bakeoff.Bakeoff(run_dir, candidates()))


def test_beats_run_through_the_engine(bk):
    story = bk.stories[STORY]
    out = bakeoff.simulate(bk.candidates["toy-epic"], story, bk.mappings[("toy-epic", STORY)][0])
    # Strength is the least that lifts the mountain top (1,000 t): 49.
    assert out["characters"]["bk-polyphemus"]["attrs"]["strength"] == 49
    by = {c["beat"]: c for c in out["checks"]}
    assert by["b-mountain"]["p"] == 1.0
    assert by["b-rams"]["bonus"] == 4 and by["b-rams"]["p"] == 0.7  # the hide row's stealth effect
    assert by["b-bore"]["bonus"] == 2  # the warrior row's strike, Agility 14 adds nothing
    assert by["b-drunk"]["stub"] == "attr_bonus:endurance"
    assert by["b-noman"]["p"] == 1.0
    uni = bakeoff.simulate(bk.candidates["universal"], story, bk.mappings[("universal", STORY)][0])
    assert {c["beat"]: c for c in uni["checks"]}["b-noman"]["p"] == 0.0


def test_a_temporary_grant_applies_only_on_its_beat(bk):
    story = copy.deepcopy(bk.stories[STORY])
    story["beats"].append({"id": "b-after", "quote": "x", "checks": [
        {"character": "crewman", "kind": "roll", "terms": [{"attr_bonus": "willpower"}], "outcome": "success"}]})
    out = bakeoff.simulate(bk.candidates["toy-epic"], story, bk.mappings[("toy-epic", STORY)][0])
    by = {c["beat"]: c for c in out["checks"]}
    assert by["b-courage"]["granted"] and by["b-courage"]["bonus"] == 8  # Willpower 10 + 40 is 50
    assert by["b-after"]["bonus"] == 0 and by["b-after"]["p"] == 0.5


def test_leave_one_out_scores(bk):
    rep = bakeoff.run(bk)
    assert [r["key"] for r in rep["rounds"]] == ["K", "toy-epic", "universal"]
    k_round = {f["foundation"]: f for f in rep["rounds"][0]["foundations"]}
    assert set(k_round) == {"toy-epic", "universal"}
    # Run 1 lands all 7 needs the key covers; run 2 leaves hide unmapped: 6 of 7.
    assert k_round["toy-epic"]["match_rate"] == pytest.approx((1 + 6 / 7) / 2)
    assert k_round["universal"]["match_rate"] == pytest.approx(2 / 7)
    assert k_round["universal"]["new_rows"] == 6
    assert rep["foundations"]["toy-epic"]["mapping_consistency"] == pytest.approx(7 / 8)
    assert rep["foundations"]["K"]["believability"] is None
    assert rep["summary"][0]["candidate"] == "toy-epic"
    assert rep["stubs"] == ["attr_bonus:endurance"]


def test_a_missing_crosswalk_is_reported(run_dir):
    (run_dir / "crosswalks" / "universal__K.r1.json").unlink()
    rep = bakeoff.run(bakeoff.Bakeoff(run_dir, candidates()))
    uni = next(f for f in rep["rounds"][0]["foundations"] if f["foundation"] == "universal")
    assert uni["match_rate"] is None and "crosswalk universal__K" in uni["missing"]


def test_the_report_is_reproducible(bk, tmp_path):
    a = bakeoff.write_report(bakeoff.run(bk), tmp_path / "a")
    b = bakeoff.write_report(bakeoff.run(bakeoff.Bakeoff(FIX / "run", candidates())), tmp_path / "b")
    assert (a / "report.json").read_bytes() == (b / "report.json").read_bytes()
    assert "Round: answer key K held out" in (a / "report.txt").read_text()


def test_cli(capsys, tmp_path, monkeypatch):
    import sys

    from lex import cli

    args = ["lex", "bakeoff", "run", str(FIX / "run"), "--pack", str(PACK_DIR / "universal"),
            "--pack", str(FIX / "packs" / "toy-epic"), "--key", f"K={FIX / 'keys' / 'toy-key'}",
            "--out", str(tmp_path)]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 0
    assert "Summary" in capsys.readouterr().out
    assert (tmp_path / "report.json").is_file()
