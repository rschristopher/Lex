# Packs

Each directory is one pack of rows. `lex import` loads it into sqlite (the live record); `lex export <pack>` writes it back.

| File | Rows |
|---|---|
| `pack.json` | `id`, `name`; optional `labels` (menu names for a kind, e.g. `{"gear": "Gear and equipment"}`) and anything else about the pack, such as `source` |
| `adapter.json` | a sheet language: labels, attribute conversions, dice |
| `species.json` | species, with `effects` and `requires` |
| `occupations/<id>.json` | an occupation, with `effects` and ordered `sets` of ability ids |
| `abilities.json` | abilities, with `price`, `effects`, and `requires` |
| `items.json` | armor, weapons, and other gear (`kind`), with `effects` while worn |
| `entries.json` | anything else the book describes (locations, adventures, creatures, ...), with `kind`, `text`, optional `source`, and `links` to other rows (`id`, `pack:id`, or `table/id`) |
| `characters/<id>.json` | a character: attributes, gauges, and the ids it owns, with its own values |
| `portraits/`, `lore/*.md` | images and lore prose |

An effect is `{"verb": "mod.channel" or "mod.attr", "target", "value"}`. Every effect and constraint a character owns applies, except:
- An item's own effects apply only while it is worn (switched on) or is the weapon used for the attack.
- An effect with `"when": {"using": "knife"}` applies only when the attack picked has that category; `{"wearing": "robot-armor"}` only while a worn item or vehicle has it. A list means any of them (`{"using": ["spear", "knife"]}`); with both keys, both must hold. The sheet lists always-on and conditional bonuses separately.
- Items carry categories as data: `"categories": ["knife", "melee"]`. `pack.json` may name them: `"categories": [{"id": "knife", "name": "Knife"}]`.
A vehicle is an item with `"kind": "vehicle"` and its own `attrs`, only physical ones (Strength, Speed) and only those that apply: `{"strength": 38, "speed": 31}`. Power armor and robot armor are vehicles with a `slot`; while worn, their attributes replace the wearer's physical attributes (Strength and Speed) and the rest stay the wearer's. Normal armor and other items have no `attrs`.
Any ability or skill can have ordered `levels`, each `{"name", "price", "effects"}`; the pack names them (for example novice through master), and then the price is on each level, not the ability. A character owns one level, `{"id": "skill_id", "level": 2}`, bought in order with experience; the effects of every level up to the owned one stack.

Two keys on a row with levels change that (data only; the defaults are today's behaviour):
- `"levels_mode": "stack"` (default) or `"replace"`: with `replace`, owning level n gives only level n's effects (for example Basic, then Elite instead of Basic).
- `"level_from": "experience"` (default) or `"occupation"`: with `occupation` the row is owned once (no stored level needed) and its level is the highest level among the character's occupations whose `sets` list it, else the character's highest occupation level, capped at the last level. `pack.json` may set `"level_from"` for every row of the pack; a row's own key wins.

A character has one `"occupation"` at its top-level `"level"`, or several: `"occupations": [{"id": "warrior", "level": 7}, {"id": "scribe", "level": 3}]`. A requirement of kind `occupation_set` is met by holding that occupation.
In a fight (`lex/combat.py`) an ability or item with `damage` (dice), `prefix`, and optional `bonus` damage rows is an attack. Optional fields: `cost` (Anima spent, in M), `mental` (the target resists with Willpower instead of Defense; `bonus_roll` is the attack's own bonus), `area` (no dodge or parry), `thrown` (can be parried, like a weapon with a `durability`), `melees` (switched on, it switches off after that many melees), and `total` (hits while switched on).
A requirement is `{"kind": "species" | "ability" | "occupation_set" | "list", "id", "set"}`.
A reference to another pack is `pack:id`.
Any row can have `text` and `source` (a string or `{"book", "section", "page"}`); the library (`/browse`) shows them. Library categories are the tables plus each row's `kind`, so an imported pack shows up there with no code change.

`universal/` is the native pack; `u-simplified/` is an adapter. Any other pack needs an explicit git exception to be public. Raw books and mapping notes belong in `data/ingest/`, not here.
