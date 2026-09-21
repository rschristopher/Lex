from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lex.paths import DEFAULT_ADAPTER, PACK_DIR


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pack_ids() -> list[str]:
    if not PACK_DIR.is_dir():
        return []
    return [p.name for p in sorted(PACK_DIR.iterdir()) if p.is_dir()]


def pack_dir(pack_id: str) -> Path:
    return PACK_DIR / pack_id


def load_adapter(adapter_id: str) -> dict[str, Any]:
    path = pack_dir(adapter_id) / "adapter.json"
    if not path.is_file():
        raise FileNotFoundError(adapter_id)
    data = _read_json(path)
    data.setdefault("id", adapter_id)
    return data


def list_adapters() -> list[dict[str, Any]]:
    rows = []
    for pid in pack_ids():
        path = pack_dir(pid) / "adapter.json"
        if not path.is_file():
            continue
        a = _read_json(path)
        if not a.get("view"):
            continue
        rows.append({"id": a.get("id") or pid, "name": a.get("name") or pid})
    return rows


def load_class(pack_id: str, class_id: str) -> dict[str, Any] | None:
    path = pack_dir(pack_id) / "classes" / f"{class_id}.json"
    if path.is_file():
        return _read_json(path)
    if pack_id != DEFAULT_ADAPTER:
        return load_class(DEFAULT_ADAPTER, class_id)
    return None


def load_ancestry(pack_id: str, ancestry_id: str) -> dict[str, Any] | None:
    path = pack_dir(pack_id) / "ancestries.json"
    if not path.is_file():
        if pack_id != DEFAULT_ADAPTER:
            return load_ancestry(DEFAULT_ADAPTER, ancestry_id)
        return None
    rows = _read_json(path)
    for row in rows:
        if row.get("id") == ancestry_id:
            return row
    return None


def iter_characters() -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for pid in pack_ids():
        cdir = pack_dir(pid) / "characters"
        if not cdir.is_dir():
            continue
        for path in sorted(cdir.glob("*.json")):
            doc = _read_json(path)
            doc.setdefault("id", path.stem)
            doc.setdefault("pack", pid)
            found.append((pid, doc))
    return found


def load_character(char_id: str) -> tuple[str, dict[str, Any]]:
    for pid, doc in iter_characters():
        if doc.get("id") == char_id:
            return pid, doc
    raise FileNotFoundError(char_id)


def character_path(char_id: str) -> Path:
    for pid in pack_ids():
        path = pack_dir(pid) / "characters" / f"{char_id}.json"
        if path.is_file():
            return path
    raise FileNotFoundError(char_id)


def patch_character(char_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    path = character_path(char_id)
    doc = _read_json(path)
    for key, val in patch.items():
        if val is None:
            doc.pop(key, None)
        else:
            doc[key] = val
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    doc.setdefault("id", char_id)
    doc.setdefault("pack", path.parent.parent.name)
    return doc


def portrait_file(pack_id: str, name: str) -> Path | None:
    safe = Path(str(name)).name
    if not safe or safe.startswith("."):
        return None
    path = pack_dir(pack_id) / "portraits" / safe
    return path if path.is_file() else None
