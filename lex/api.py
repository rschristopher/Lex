from __future__ import annotations

import re
import secrets
import sqlite3
from typing import Any, Iterator

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lex import db, engine
from lex.paths import PKG
from lex.sheet import list_adapters, list_sheets, sheet

app = FastAPI(title="Lex")
LOCAL_PACK = "local"  # characters made on this server; export with `lex export local`
COOKIE = "lex_session"


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def current_user(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> sqlite3.Row | None:
    token = request.cookies.get(COOKIE)
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        return None
    return conn.execute(
        "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id WHERE token=?", (token,)
    ).fetchone()


def need_user(user: sqlite3.Row | None = Depends(current_user)) -> sqlite3.Row:
    if user is None:
        raise HTTPException(401, "sign in first")
    return user


def need_gm(user: sqlite3.Row = Depends(need_user)) -> sqlite3.Row:
    if user["role"] != "gm":
        raise HTTPException(403, "GM only")
    return user


def _character(conn: sqlite3.Connection, cid: str) -> sqlite3.Row:
    ch = conn.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
    if ch is None:
        raise HTTPException(404, "character not found")
    return ch


def can_edit(user: sqlite3.Row, ch: sqlite3.Row) -> bool:
    """Players edit only their own characters; a GM edits any character."""
    return user["role"] == "gm" or (ch["owner_id"] is not None and ch["owner_id"] == user["id"])


def _editable(conn, cid: str, user: sqlite3.Row) -> sqlite3.Row:
    ch = _character(conn, cid)
    if not can_edit(user, ch):
        raise HTTPException(403, "not your character")
    return ch


def _ref(conn, table: str, ref: Any) -> tuple[str, str]:
    if not isinstance(ref, str) or not ref:
        raise HTTPException(422, f"{table} is required")
    if ":" in ref:
        pack, rid = ref.split(":", 1)
        rows = conn.execute(f"SELECT pack, id FROM {table} WHERE pack=? AND id=?", (pack, rid)).fetchall()
    else:
        rows = conn.execute(f"SELECT pack, id FROM {table} WHERE id=?", (ref,)).fetchall()
    if len(rows) != 1:
        raise HTTPException(422, f"unknown or ambiguous {table} {ref!r}; write it as pack:id")
    return rows[0]["pack"], rows[0]["id"]


# ------------------------------------------------------------ logins


def _user_out(u: sqlite3.Row) -> dict[str, Any]:
    return {"id": u["id"], "username": u["username"], "role": u["role"]}


@app.post("/users")
def create_user(body: dict[str, Any], conn: sqlite3.Connection = Depends(get_conn)):
    """Anyone can create a player login. Becoming GM is a separate promote step."""
    name = str(body.get("username") or "").strip()
    if not name:
        raise HTTPException(422, "username is required")
    try:
        with conn:
            cur = conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                               (name, str(body.get("password") or "")))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "username taken")
    return _user_out(conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone())


@app.post("/users/{username}/gm")
def promote(username: str, conn: sqlite3.Connection = Depends(get_conn), _gm=Depends(need_gm)):
    with conn:
        n = conn.execute("UPDATE users SET role='gm' WHERE username=?", (username,)).rowcount
    if not n:
        raise HTTPException(404, "no such user")
    return {"username": username, "role": "gm"}


@app.post("/login")
def login(body: dict[str, Any], response: Response, conn: sqlite3.Connection = Depends(get_conn)):
    u = conn.execute("SELECT * FROM users WHERE username=?", (str(body.get("username") or ""),)).fetchone()
    if u is None or u["password"] != str(body.get("password") or ""):
        raise HTTPException(401, "wrong username or password")
    token = secrets.token_urlsafe(24)
    with conn:
        conn.execute("INSERT INTO sessions VALUES (?, ?)", (token, u["id"]))
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax")
    return {**_user_out(u), "token": token}


@app.post("/logout")
def logout(request: Request, response: Response, conn: sqlite3.Connection = Depends(get_conn)):
    token = request.cookies.get(COOKIE)
    if token:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
    response.delete_cookie(COOKIE)
    return {}


@app.get("/me")
def me(user=Depends(current_user)):
    return _user_out(user) if user else None


# ------------------------------------------------------------ catalog


@app.get("/adapters")
def adapters(conn: sqlite3.Connection = Depends(get_conn)):
    return list_adapters(conn)


@app.get("/species")
def species(conn: sqlite3.Connection = Depends(get_conn)):
    return [{"id": r["id"], "pack": r["pack"], "name": r["name"]}
            for r in conn.execute("SELECT * FROM species ORDER BY name, pack")]


@app.get("/abilities")
def abilities(conn: sqlite3.Connection = Depends(get_conn)):
    return [{"id": r["id"], "pack": r["pack"], "name": r["name"], "kind": r["kind"], "price": r["price"]}
            for r in conn.execute("SELECT * FROM abilities ORDER BY name, pack")]


# ------------------------------------------------------------ characters


@app.get("/characters")
def characters(adapter: str | None = Query(default=None), sheet: bool = Query(default=False),
               conn: sqlite3.Connection = Depends(get_conn)):
    rows = list_sheets(conn, adapter)
    if sheet:
        return rows
    return [{k: v for k, v in r.items() if k != "sheet"} for r in rows]


@app.get("/characters/{cid}/sheet")
def character_sheet(cid: str, adapter: str | None = Query(default=None),
                    conn: sqlite3.Connection = Depends(get_conn)):
    _character(conn, cid)
    return sheet(conn, cid, adapter)


@app.post("/characters")
def create_character(body: dict[str, Any], adapter: str | None = Query(default=None),
                     conn: sqlite3.Connection = Depends(get_conn), user=Depends(need_user)):
    """A blank sheet owned by the caller. Name and species are required."""
    name = str(body.get("name") or "").strip()
    if not name:
        raise HTTPException(422, "name is required")
    sp_pack, sp_id = _ref(conn, "species", body.get("species"))
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "character"
    cid, n = base, 1
    while conn.execute("SELECT 1 FROM characters WHERE id=?", (cid,)).fetchone():
        n += 1
        cid = f"{base}-{n}"
    with conn:
        conn.execute("INSERT OR IGNORE INTO packs (id, name) VALUES (?, 'Local')", (LOCAL_PACK,))
        pos = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM characters WHERE pack=?", (LOCAL_PACK,)).fetchone()[0]
        conn.execute(
            "INSERT INTO characters (id, pack, position, name, npc, species_pack, species_id, owner_id)"
            " VALUES (?,?,?,?,0,?,?,?)",
            (cid, LOCAL_PACK, pos, name, sp_pack, sp_id, user["id"]),
        )
    return sheet(conn, cid, adapter)


@app.patch("/characters/{cid}")
def patch_character(cid: str, body: dict[str, Any], adapter: str | None = Query(default=None),
                    conn: sqlite3.Connection = Depends(get_conn), user=Depends(need_user)):
    _editable(conn, cid, user)
    with conn:
        if "activated" in body:
            refs = body["activated"] or []
            if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
                raise HTTPException(422, "activated must be a list of ids")
            conn.execute("DELETE FROM character_active WHERE character_id=?", (cid,))
            for i, ref in enumerate(dict.fromkeys(refs)):
                conn.execute("INSERT INTO character_active VALUES (?,?,?)", (cid, i, ref))
        if "attack" in body:
            conn.execute("UPDATE characters SET attack=? WHERE id=?", (body["attack"] or None, cid))
        if "pinned" in body:
            pin = _ref(conn, "occupations", body["pinned"]) if body["pinned"] else (None, None)
            conn.execute("UPDATE characters SET pinned_pack=?, pinned_id=? WHERE id=?", (*pin, cid))
        if "owner" in body:
            if user["role"] != "gm":
                raise HTTPException(403, "GM only")
            owner = None
            if body["owner"]:
                u = conn.execute("SELECT id FROM users WHERE username=?", (body["owner"],)).fetchone()
                if u is None:
                    raise HTTPException(422, "no such user")
                owner = u["id"]
            conn.execute("UPDATE characters SET owner_id=? WHERE id=?", (owner, cid))
    return sheet(conn, cid, adapter)


@app.post("/characters/{cid}/experience")
def add_experience(cid: str, body: dict[str, Any], adapter: str | None = Query(default=None),
                   conn: sqlite3.Connection = Depends(get_conn), _gm=Depends(need_gm)):
    """The GM adds unspent experience to one character."""
    ch = _character(conn, cid)
    amount = body.get("add")
    if not isinstance(amount, int) or amount < 0:
        raise HTTPException(422, "add must be a whole number, 0 or more")
    with conn:
        conn.execute("UPDATE characters SET xp_unspent=? WHERE id=?", ((ch["xp_unspent"] or 0) + amount, cid))
    return sheet(conn, cid, adapter)


@app.post("/characters/{cid}/abilities")
def buy(cid: str, body: dict[str, Any], adapter: str | None = Query(default=None),
        conn: sqlite3.Connection = Depends(get_conn), user=Depends(need_user)):
    """Buy an ability within its constraints and price. A GM may send grant=true to add it outright."""
    _editable(conn, cid, user)
    grant = bool(body.get("grant"))
    if grant and user["role"] != "gm":
        raise HTTPException(403, "only the GM can grant an ability")
    pack, aid = _ref(conn, "abilities", body.get("ability"))
    try:
        engine.buy_ability(conn, cid, pack, aid, grant=grant)
    except engine.Refused as e:
        raise HTTPException(409, str(e))
    return sheet(conn, cid, adapter)


@app.get("/portraits/{pack_id}/{name}")
def portrait(pack_id: str, name: str, conn: sqlite3.Connection = Depends(get_conn)):
    r = conn.execute("SELECT data FROM portraits WHERE pack=? AND name=?", (pack_id, name)).fetchone()
    if r is None:
        raise HTTPException(404)
    kind = "image/png" if name.lower().endswith(".png") else "image/jpeg"
    return Response(content=r["data"], media_type=kind)


@app.get("/")
def index():
    return FileResponse(PKG / "index.html")


if (PKG / "static").is_dir():
    app.mount("/static", StaticFiles(directory=PKG / "static"), name="static")
