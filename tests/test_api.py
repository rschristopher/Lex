from fastapi.testclient import TestClient

from lex.api import app


def _login(client, name, role=None, conn=None):
    client.post("/users", json={"username": name, "password": ""})
    if role == "gm":
        with conn:
            conn.execute("UPDATE users SET role='gm' WHERE username=?", (name,))
    r = client.post("/login", json={"username": name, "password": ""})
    assert r.status_code == 200
    return r.json()


def test_adapters_include_universal(conn):
    with TestClient(app) as client:
        ids = {a["id"] for a in client.get("/adapters").json()}
        assert ids == {"universal", "u-simplified"}


def test_roster_and_sheet(conn):
    with TestClient(app) as client:
        rows = client.get("/characters", params={"sheet": True}).json()
        assert len(rows) == 12
        ilya = next(r for r in rows if r["id"] == "pc-ilya")
        assert ilya["sheet"]["adapter"] == "universal"
        assert ilya["sheet"]["occupation"]["id"] == "soldier"
        assert ilya["sheet"]["species"]["name"] == "Human"
        sheet = client.get("/characters/pc-ilya/sheet").json()
        assert sheet["name"] == "Ilya"
        labels = [c["label"] for c in sheet["channels"]]
        assert labels == ["Actions", "Strike", "Defense", "Initiative"]
        simp = client.get("/characters/pc-ilya/sheet", params={"adapter": "u-simplified"}).json()
        assert [a["label"] for a in simp["attrs"]][1] == "Dexterity"
        assert [g["label"] for g in simp["gauges"]] == ["Hit points"]
        assert [c["id"] for c in simp["channels"]] == ["actions", "strike", "defense", "initiative"]
        skills = next(g for g in simp["groups"] if g["id"] == "abilities")
        assert skills["name"] == "Skills"
        assert client.get(sheet["portrait"]).status_code == 200


def test_patch_play_state_writes_sqlite(conn):
    with TestClient(app) as client:
        _login(client, "gm", "gm", conn)
        off = client.patch("/characters/pc-ilya", json={"activated": [], "attack": "knife"}).json()
        assert off["using"]["name"] == "Knife"
        unarmored = next(r for g in off["groups"] if g["id"] == "armor" for r in g["rows"] if r["name"] == "Unarmored")
        assert unarmored["on"]
        assert conn.execute("SELECT attack FROM characters WHERE id='pc-ilya'").fetchone()[0] == "knife"
        assert conn.execute("SELECT COUNT(*) FROM character_active WHERE character_id='pc-ilya'").fetchone()[0] == 0


def test_players_edit_only_their_own(conn):
    with TestClient(app) as gm, TestClient(app) as ana, TestClient(app) as ben:
        _login(gm, "gm", "gm", conn)
        _login(ana, "ana")
        _login(ben, "ben")
        assert gm.patch("/characters/pc-ilya", json={"owner": "ana"}).json()["owner"] == "ana"
        assert ana.patch("/characters/pc-ilya", json={"attack": "knife"}).status_code == 200
        assert ben.patch("/characters/pc-ilya", json={"attack": "knife"}).status_code == 403
        # Ben may still browse Ana's character.
        assert ben.get("/characters/pc-ilya/sheet").status_code == 200
        # Only the GM changes owners; signed-out tablets cannot edit.
        assert ana.patch("/characters/pc-ilya", json={"owner": "ben"}).status_code == 403
        assert TestClient(app).patch("/characters/pc-ilya", json={"attack": "knife"}).status_code == 401
        # The GM edits non-player characters.
        assert gm.patch("/characters/npc-thorn", json={"attack": "bite"}).json()["using"]["name"] == "Bite"
        assert ana.patch("/characters/npc-thorn", json={"attack": "bite"}).status_code == 403


def test_new_character_needs_name_and_species(conn):
    with TestClient(app) as client:
        assert client.post("/characters", json={"name": "Wren", "species": "human"}).status_code == 401
        _login(client, "ana")
        assert client.post("/characters", json={"name": "Wren"}).status_code == 422
        assert client.post("/characters", json={"species": "human"}).status_code == 422
        s = client.post("/characters", json={"name": "Wren", "species": "human"}).json()
        assert (s["id"], s["species"]["name"], s["owner"]) == ("wren", "Human", "ana")
        assert client.patch("/characters/wren", json={"attack": ""}).status_code == 200


def test_buy_ability_spends_experience(conn):
    with conn:
        conn.execute("UPDATE abilities SET price=5 WHERE pack='universal' AND id='intimidate'")
    with TestClient(app) as gm, TestClient(app) as ana:
        _login(gm, "gm", "gm", conn)
        _login(ana, "ana")
        gm.patch("/characters/pc-ilya", json={"owner": "ana"})
        assert ana.post("/characters/pc-ilya/abilities", json={"ability": "intimidate"}).status_code == 409
        assert ana.post("/characters/pc-ilya/experience", json={"add": 7}).status_code == 403
        gm.post("/characters/pc-ilya/experience", json={"add": 7})
        s = ana.post("/characters/pc-ilya/abilities", json={"ability": "intimidate"}).json()
        assert s["unspent_experience"] == 2
        assert any(r["id"] == "intimidate" for g in s["groups"] for r in g["rows"])
        assert ana.post("/characters/pc-ilya/abilities", json={"ability": "keen", "grant": True}).status_code == 403
        assert gm.post("/characters/pc-ilya/abilities", json={"ability": "keen", "grant": True}).status_code == 200


def test_player_ui_served(conn):
    with TestClient(app) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Lex" in page.text
        assert 'id="adapter"' in page.text
        assert 'id="scale"' in page.text
        assert 'id="home"' in page.text
        for el in ('id="login"', 'id="signup"', 'id="new-character"', 'id="new-species"'):
            assert el in page.text


def test_fight_permissions_and_flow(conn):
    with TestClient(app) as gm, TestClient(app) as ana, TestClient(app) as ben:
        _login(gm, "gm", "gm", conn)
        _login(ana, "ana")
        _login(ben, "ben")
        gm.patch("/characters/pc-calder", json={"owner": "ana"})
        gm.patch("/characters/pc-kesh", json={"owner": "ben"})
        groups = [{"name": "Adepts", "characters": ["pc-calder"]}, {"name": "Raiders", "characters": ["pc-kesh"]}]
        assert ana.post("/fights", json={"groups": groups}).status_code == 403
        r = gm.post("/fights", json={"groups": groups})
        assert r.status_code == 200
        fid = r.json()["id"]
        # A player rolls only for their own character; everyone can watch the fight.
        assert ana.post(f"/fights/{fid}/initiative", json={"character": "pc-kesh", "value": 5}).status_code == 403
        assert ana.post(f"/fights/{fid}/initiative", json={"character": "pc-calder", "value": 99}).status_code == 409
        assert ana.post(f"/fights/{fid}/initiative", json={"character": "pc-calder", "value": 15}).status_code == 200
        st = ben.post(f"/fights/{fid}/initiative", json={"character": "pc-kesh"}).json()  # auto-roll
        assert st["status"] == "melee" and ben.get(f"/fights/{fid}").json()["groups"][0]["combatants"][0]["id"] == "pc-calder"
        first = st["current"]
        mine, theirs = (ana, ben) if first == "pc-calder" else (ben, ana)
        other = "pc-kesh" if first == "pc-calder" else "pc-calder"
        assert theirs.post(f"/fights/{fid}/act", json={"actor": first, "use": "punch", "target": other}).status_code == 403
        st = mine.post(f"/fights/{fid}/act", json={"actor": first, "use": "punch", "target": other}).json()
        assert st["pending"]["roller"] == first
        assert theirs.post(f"/fights/{fid}/roll", json={"value": 20}).status_code == 403
        st = gm.post(f"/fights/{fid}/roll", json={"value": 20}).json()  # the GM types the paper player's roll
        assert st["result"]["landed"] and st["pending"]["roller"] == other
        st = theirs.post(f"/fights/{fid}/roll", json={"choice": "pass"}).json()
        assert st["pending"]["step"] == "damage"
        assert mine.post(f"/fights/{fid}/undo", json={"count": 1}).status_code == 403
        assert gm.post(f"/fights/{fid}/undo", json={"count": 1}).json()["pending"]["step"] == "defense"
        assert ana.post(f"/fights/{fid}/end").status_code == 403
        assert gm.post(f"/fights/{fid}/end").json()["status"] == "ended"


def test_fight_screen_served(conn):
    with TestClient(app) as client:
        page = client.get("/fight").text
        for el in ('id="groups"', 'id="modal"', 'id="auto"', 'id="undo"', 'id="end"', "/static/fight.js"):
            assert el in page
        assert client.get("/static/fight.js").status_code == 200
        assert 'href="/fight"' in client.get("/").text
