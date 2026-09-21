# data/ingest/

Scratch: local book links and mapping notes. Not for GitHub.

Git tracks only this README. Do not force-add the rest. Do not open PRs that add licensed or trademarked game text, art, or names.

When a mapping is stable, write rows into `data/packs/` (public packs only if we have the right to ship them). The engine loads packs, not this folder.

```
data/ingest/<source>/README.md
data/ingest/<source>/books/    # symlink to PDFs you own
```
