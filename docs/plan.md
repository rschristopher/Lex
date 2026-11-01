# Plan

This is the implementation plan for Lex. The rules and app design are in [universal-system.md](universal-system.md); terms are in [glossary.md](glossary.md).

The existing code is a mockup built on hardcoded JSON files. Lex is built from the ground up in this order. Each layer is documented and tested with competing systems and data packs.

1. **Data layer.** A sqlite schema for the effects and constraints engine, the combat layer, and lore. During play, sqlite on the server is the live record ([Lore, ingest, and packs](universal-system.md#lore-ingest-and-packs)).
2. **Ingest.** Load the JSON packs in `data/packs/` into sqlite, and export characters back to packs.
3. **Engine.** The fold that resolves a character sheet from its effects and constraints, and the combat layer ([Combat Rules](universal-system.md#combat-rules), [Fights in the app](universal-system.md#fights-in-the-app)).
4. **API.** REST HTTP endpoints for character sheets, combat, and lore.
5. **UI.** The roster and character sheet, with leveling and rule enforcement; the combat screen; and lore, browsing maps and concepts. Every device is a browser on the one local server ([Server and logins](universal-system.md#server-and-logins)).
6. **Packs.** Ingest other systems locally to prove the universal system. Only original and public domain packs are published.
7. **Later.** Research and a proof of concept for an adapter that plays by another system's rules, not only converting to and from Lex.
