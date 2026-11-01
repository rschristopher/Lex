# Plan

This is the implementation plan for Lex: the use cases Lex supports, which drive the technical design. The rules and app design are in [universal-system.md](universal-system.md); terms are in [glossary.md](glossary.md).

## Use cases

### Setting up
- The GM runs one local server; the GM and players sign in from browsers on their own devices ([Server and logins](universal-system.md#server-and-logins)).
- The GM loads packs into a campaign, from many sources at once ([Lore, ingest, and packs](universal-system.md#lore-ingest-and-packs)).
- The GM sets the campaign's die system and can change it at any time ([Dice](universal-system.md#dice)).
- With Lex as the harness, the LLM reads a source material and iterates with the user on building a data pack from it: characters, locations, powers, and everything else. Anyone can ingest; usually it is the GM.

### Characters
- A player creates a character and fills the sheet as far as the GM needs to run, spending starting experience then or in play ([Experience, prices, and loot](universal-system.md#experience-prices-and-loot)).
- A player spends experience on abilities within their constraints, and pins an occupation they are spending toward ([Species and occupations](universal-system.md#species-and-occupations)).
- A player sees their sheet in any adapter's sheet language.
- A player sees every character on their login across campaigns and switches between them.
- The GM sees and edits every character, adds abilities or constraints, and generates random non-player characters.
- A character converts to and from another game's sheet, and moves between Lex servers as a pack.

### Adventures
- The GM prepares an adventure with locations, stories, maps, non-player characters, suggested experience, loot, and groups, and edits it during play ([Adventures](universal-system.md#adventures)).
- The GM shows or hides any adventure material for every player or chosen players.
- The GM uses the GM-assistant with an LLM to create maps, towns, and adventure material, including at the table during play. The LLM is not involved in deterministic parts such as combat.

### Play and fights
- The GM groups characters and starts a fight; every tablet in it shows both groups and the initiative order ([Fights in the app](universal-system.md#fights-in-the-app)).
- On their action a player picks a weapon or power and a target, and enters the roll or uses auto-roll; a defender rolls or passes.
- A player with paper says the action, and the GM enters it.
- The GM undoes mistakes, calls a fresh initiative, and ends the fight.
- Outside a fight, a player taps a skill to roll, or the GM calls for a roll.

### Rewards
- After a fight the GM puts up loot and experience; players claim and release items, and unclaimed items stay on the ground ([Rewards](universal-system.md#rewards)).
