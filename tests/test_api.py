from fastapi.testclient import TestClient

from lex.api import app


def test_adapters_include_universal():
    with TestClient(app) as client:
        ids = {a["id"] for a in client.get("/adapters").json()}
        assert ids == {"universal", "u-simplified"}


def test_roster_and_sheet():
    with TestClient(app) as client:
        rows = client.get("/characters", params={"sheet": True}).json()
        assert len(rows) >= 1
        ilya = next(r for r in rows if r["id"] == "pc-ilya")
        assert ilya["sheet"]["adapter"] == "universal"
        assert ilya["sheet"]["class"]["id"] == "soldier"
        sheet = client.get("/characters/pc-ilya/sheet").json()
        assert sheet["name"] == "Ilya"
        labels = [c["label"] for c in sheet["channels"]]
        assert labels == ["Actions", "Attack", "Parry", "Dodge", "Initiative"]
        simp = client.get("/characters/pc-ilya/sheet", params={"adapter": "u-simplified"}).json()
        assert [a["label"] for a in simp["attrs"]][1] == "Dexterity"
        assert [g["label"] for g in simp["gauges"]] == ["Hit points"]
        assert [c["id"] for c in simp["channels"]] == ["actions", "attack", "parry", "dodge", "initiative"]
        assert all(c["id"] != "defense" for c in simp["channels"])
        skills = next(g for g in simp["groups"] if g["id"] == "abilities")
        assert skills["name"] == "Skills"


def test_patch_play_state():
    with TestClient(app) as client:
        before = client.get("/characters/pc-ilya/sheet").json()
        try:
            off = client.patch("/characters/pc-ilya", json={"activated": [], "attack": "knife"}).json()
            assert off["using"]["name"] == "Knife"
            assert not any(g["id"] == "armor" and g["kind"] == "hits" for g in off["gauges"])
            unarmed_row = next(r for g in off["groups"] if g["id"] == "armor" for r in g["rows"] if r["name"] == "Unarmored")
            assert unarmed_row["on"]
        finally:
            client.patch("/characters/pc-ilya", json={
                "activated": before.get("activated") or ["field_plate"],
                "attack": before.get("attack") or "service_rifle",
            })


def test_player_ui_served():
    with TestClient(app) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Lex" in page.text
        assert 'id="adapter"' in page.text
        assert 'id="scale"' in page.text
        assert 'id="home"' in page.text
