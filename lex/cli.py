"""Console entry: `uv run lex` (serve) or `uv run lex test`."""

from __future__ import annotations

import argparse
import sys


def serve() -> None:
    import uvicorn

    from lex.paths import ROOT

    uvicorn.run(
        "lex.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT / "lex"), str(ROOT / "data")],
        reload_includes=["*.py", "*.json", "*.html", "*.css", "*.js"],
    )


def test() -> None:
    import pytest

    sys.exit(pytest.main(["tests"]))


def main() -> None:
    p = argparse.ArgumentParser(prog="lex")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="local app (default)")
    sub.add_parser("test", help="pytest")
    args = p.parse_args()
    if args.cmd == "test":
        test()
    else:
        serve()
