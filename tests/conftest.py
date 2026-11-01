import pytest

from lex import db, packs
from lex.paths import PACK_DIR


@pytest.fixture
def conn(tmp_path, monkeypatch):
    """A fresh sqlite database with the shipped packs imported. The API reads the same file via LEX_DB."""
    path = tmp_path / "lex.db"
    monkeypatch.setenv("LEX_DB", str(path))
    c = db.connect(path)
    packs.import_pack(c, PACK_DIR / "universal")
    packs.import_pack(c, PACK_DIR / "u-simplified")
    yield c
    c.close()
