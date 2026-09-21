# Ingest

`data/ingest/` is scratch: local book links and mapping notes. Git tracks only `data/ingest/README.md`. Do not PR licensed or trademarked game text, art, or names.

`data/packs/` is the catalog the engine loads. After a source is understood, write adapter / class / character / lore **rows** under `data/packs/<id>/`. `universal/` is the native pack, not a catch-all. Other packs need an explicit git exception to be public.

Do not copy book text into `data/packs/`. Do not teach fold about a source’s product name.

Process: read in `data/ingest/` → GM decides reuse vs new class vs new adapter → write rows under `data/packs/<id>/`.
