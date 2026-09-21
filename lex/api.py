from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lex import fold, store
from lex.paths import DEFAULT_ADAPTER, PKG

app = FastAPI(title="Lex")


@app.get("/adapters")
def adapters():
    return store.list_adapters()


@app.get("/characters")
def characters(adapter: str | None = Query(default=None), sheet: bool = Query(default=False)):
    rows = fold.list_sheets(adapter or DEFAULT_ADAPTER)
    if sheet:
        return rows
    return [{k: r[k] for k in ("id", "name", "npc", "level", "class", "ancestry", "portrait") if k in r} for r in rows]


@app.get("/characters/{char_id}/sheet")
def character_sheet(char_id: str, adapter: str | None = Query(default=None)):
    try:
        _pid, doc = store.load_character(char_id)
    except FileNotFoundError:
        raise HTTPException(404, "character not found")
    return fold.fold(doc, adapter or DEFAULT_ADAPTER)


@app.patch("/characters/{char_id}")
def patch_character(char_id: str, body: dict[str, Any], adapter: str | None = Query(default=None)):
    allowed = {"activated", "attack"}
    patch = {k: body[k] for k in allowed if k in body}
    try:
        doc = store.patch_character(char_id, patch)
    except FileNotFoundError:
        raise HTTPException(404, "character not found")
    return fold.fold(doc, adapter or DEFAULT_ADAPTER)


@app.get("/portraits/{pack_id}/{name}")
def portrait(pack_id: str, name: str):
    path = store.portrait_file(pack_id, name)
    if path is None:
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/")
def index():
    return FileResponse(PKG / "index.html")


if (PKG / "static").is_dir():
    app.mount("/static", StaticFiles(directory=PKG / "static"), name="static")
