"""Console entry: `lex serve`, `lex import`, `lex export`, `lex user`, `lex test`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def serve(host: str, port: int) -> None:
    import uvicorn

    from lex import db
    from lex.paths import ROOT

    conn = db.connect()
    if not conn.execute("SELECT 1 FROM characters LIMIT 1").fetchone():
        print(f"{db.db_path()} has no characters yet; run `lex import` first.", file=sys.stderr)
    conn.close()
    uvicorn.run(
        "lex.api:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(ROOT / "lex")],
        reload_includes=["*.py", "*.html", "*.css", "*.js"],
    )


def do_import(paths: list[str]) -> int:
    from lex import db, packs
    from lex.paths import PACK_DIR

    targets = [Path(p) for p in paths]
    if not targets:
        # Adapter-only packs first is not required; references resolve inside each pack, then the database.
        targets = [p for p in sorted(PACK_DIR.iterdir()) if p.is_dir()]
    conn = db.connect()
    code = 0
    for t in targets:
        if not t.is_dir() and (PACK_DIR / str(t)).is_dir():
            t = PACK_DIR / str(t)
        try:
            counts = packs.import_pack(conn, t)
        except packs.PackError as e:
            code = 1
            print(f"{t}: not imported", file=sys.stderr)
            for err in e.errors:
                print(f"  {err}", file=sys.stderr)
            continue
        print(f"{t.name}: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    print(f"database: {db.db_path()}")
    return code


def do_export(pack_id: str, dest: str | None) -> int:
    from lex import db, packs

    conn = db.connect()
    try:
        out = packs.export_pack(conn, pack_id, dest or pack_id)
    except packs.PackError as e:
        print(e, file=sys.stderr)
        return 1
    print(out)
    return 0


def do_user(args: argparse.Namespace) -> int:
    import sqlite3

    from lex import db

    conn = db.connect()
    with conn:
        if args.action == "add":
            try:
                conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                             (args.username, args.password or "", "gm" if args.gm else "player"))
            except sqlite3.IntegrityError:
                print("username taken", file=sys.stderr)
                return 1
        elif args.action == "gm":
            if not conn.execute("UPDATE users SET role='gm' WHERE username=?", (args.username,)).rowcount:
                print("no such user", file=sys.stderr)
                return 1
        elif args.action == "own":
            u = conn.execute("SELECT id FROM users WHERE username=?", (args.username,)).fetchone()
            if u is None or not conn.execute("UPDATE characters SET owner_id=? WHERE id=?", (u["id"], args.character)).rowcount:
                print("no such user or character", file=sys.stderr)
                return 1
    for r in conn.execute("SELECT username, role FROM users ORDER BY username"):
        print(f"{r['username']}\t{r['role']}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="lex")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="local web server (default)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    i = sub.add_parser("import", help="load pack directories into sqlite (default: every pack in data/packs)")
    i.add_argument("packs", nargs="*")
    e = sub.add_parser("export", help="write one pack from sqlite back to a directory")
    e.add_argument("pack")
    e.add_argument("dest", nargs="?")
    u = sub.add_parser("user", help="logins: add NAME [--gm], gm NAME, own NAME CHARACTER")
    u.add_argument("action", choices=["add", "gm", "own"])
    u.add_argument("username")
    u.add_argument("character", nargs="?")
    u.add_argument("--password", default="")
    u.add_argument("--gm", action="store_true")
    sub.add_parser("test", help="pytest")
    args = p.parse_args()
    if args.cmd == "test":
        import pytest

        sys.exit(pytest.main(["tests"]))
    elif args.cmd == "import":
        sys.exit(do_import(args.packs))
    elif args.cmd == "export":
        sys.exit(do_export(args.pack, args.dest))
    elif args.cmd == "user":
        sys.exit(do_user(args))
    else:
        serve(getattr(args, "host", "127.0.0.1"), getattr(args, "port", 8000))
