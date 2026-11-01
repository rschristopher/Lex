# Packs

Each directory is one pack of rows. `lex import` loads it into sqlite (the live record); `lex export <pack>` writes it back.

| File | Rows |
|---|---|
| `pack.json` | `id`, `name` |
| `adapter.json` | a sheet language: labels, attribute conversions, dice |
| `species.json` | species, with `effects` and `requires` |
| `occupations/<id>.json` | an occupation, with `effects` and ordered `sets` of ability ids |
| `abilities.json` | abilities, with `price`, `effects`, and `requires` |
| `items.json` | armor, weapons, and other gear (`kind`), with `effects` while worn |
| `characters/<id>.json` | a character: attributes, gauges, and the ids it owns, with its own values |
| `portraits/`, `lore/*.md` | images and lore prose |

An effect is `{"verb": "mod.channel" or "mod.attr", "target", "value"}`. Every effect and constraint a character owns applies.
A vehicle is an item with `"kind": "vehicle"` and its own `attrs`, only those that apply: `{"strength": 38, "speed": 31}`. Power armor and robot armor are vehicles with a `slot`; while worn, their attributes replace the wearer's physical attributes (Strength and Speed) and the rest stay the wearer's. Normal armor and other items have no `attrs`.
A requirement is `{"kind": "species" | "ability" | "occupation_set" | "list", "id", "set"}`.
A reference to another pack is `pack:id`.

`universal/` is the native pack; `u-simplified/` is an adapter. Any other pack needs an explicit git exception to be public. Raw books and mapping notes belong in `data/ingest/`, not here.
