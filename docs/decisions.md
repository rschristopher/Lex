# Decisions

Planning record for the real Lex app. The code in this repo is still the character-sheet mockup. Terms are defined in [glossary.md](glossary.md). The engine rules are in [universal-system.md](universal-system.md).

## What Lex is

Lex is one app with three jobs.

- Players and the GM manage characters, both player characters and non-player characters.
- During play, two or more groups of those characters can be in a melee. Lex handles the math and keeps the sheets current.
- The GM has tools for adventures inside a campaign.

The game is the GM talking and the players playing their characters in a shared story. Dice stay on the table. The same game can be played with paper and dice alone. Tablets assist. Lex does not play the game, and it has nothing to start or stop. Nothing in the app holds the table until a sheet is finished.

There is one Lex engine. Characters from other games are converted into that engine. One campaign has one set of rules. An adapter is a sheet language: labels, attribute names, and which dice are shown. It does not change the math. A different melee engine is later work, and it is not part of this app.

Verisimilitude stays in force. Scale and damage threshold mean a pitchfork does nothing to a tank or a god. Armor is worn hits on the harm track. It is not a to-hit number. The GM may adapt labels, within that limit.

## Species and occupation

Species is what the character is, and exactly one. A human, an elf, a mutant, a dragon. Things with the same name from different sources are different things, shown with their source, such as Elf (D&D) and Elf (Tolkien).

Occupation is what the character does. A soldier, a politician, a wizard. Do not use Class or Ancestry for these. Armor Class is a different idea and is not used.

An occupation is one ordered set of abilities, or several ordered sets side by side. A later set counts only when every set before it is met. The catalog is large, and includes catchalls such as Vagabond. The sheet shows the top two or three. The player can pin one as a reminder of what they are spending toward. The pin does not lock spending.

Abilities are the truth. An ability works as soon as it is bought. Qualifying for an occupation follows from what the character owns. Gaps block the title and do not block the ability. The same purchase can satisfy a requirement on more than one occupation, and it is paid for once. Occupation positions are not added together. A wizard and a scholar are not a single higher number.

Some species have growth that a source book writes as per-level bonuses. That growth is an occupation only that species can advance. The starting body is the first set, so a character who never spends on it stays there. Later sets are bought with experience. A metahuman can spend everything on Mage and leave the species occupation on its first set. The lock runs one way: only that species can advance that occupation, and the species can still advance any other occupation.

Two characters of the same species can have different abilities available. Each carries their own list. A custom species occupation walks that list. The list can be one ordered set, or two or more ordered sets.

An ability can be bought only when its constraints are met. A constraint can require a species, a previous set of an occupation, an ability already owned, or a list written on that character. The campaign can also forbid an ability. The set is made of the abilities you buy. Other abilities can require that set without being part of it.

This is enough to convert a GURPS character, a Rifts character, and a D&D character into the same sheet. GURPS has no character level and no occupation level. It does have levels on single traits. Those trait levels stay. A GURPS sheet shows the points and the traits. A leveled occupation shows how far its ordered sets have been met.

## Experience, prices, and loot

The character stores total experience, spent experience, and unspent experience. Any two fix the third. Unspent is what the player saves or spends.

The price of an ability is written in the data pack. The GM sets it while preparing data, not during play. Play spends that number.

The GM adds unspent experience after a scene or after play. Each character gets their own amount. The GM decides. An adventure can record a suggested amount, and the GM can ignore it.

A new character's starting unspent experience is in the pack. The GM sets that amount. The player may spend it while creating the character or during play. Creation is not a phase the app locks. Fill the sheet enough for the GM to run, the way a paper sheet is filled in.

The GM decides what loot exists, and the players receive it.

## Server and who sees what

One local web server. The GM and the players are browsers on their own devices. This is not a cloud app and it is not real security.

Login is a username and a password. The password may be blank. The player or the GM can create the login. Usernames are unique. Becoming the GM is an explicit setup or promote step; the first account created is not automatically GM. More than one login may be GM. A tablet is signed in as one login at a time. A shared tablet at the table is just the GM's login; players who use it are handled the same way as players with paper.

The server can hold dozens of campaigns and dozens of adventures. The GM opens one campaign, and one adventure in that campaign is in play. Only one campaign is in play on the server at a time, even when there is more than one GM. Several GMs can co-run the same campaign, and every GM has full control of it. A GM can also play a character in a campaign they run; that character's turn opens the same locked modal as any player's.

A login can have characters in more than one campaign. Before a campaign is open, the tablet lists every character on that login. After the GM opens a campaign, the screen is built around that campaign and one character. The player can switch to another of their characters in the open campaign, and can still open characters from closed campaigns, but those sit further back. In a fight, the modal follows whichever of their characters has the turn. Outside that turn modal they may switch characters freely, including characters not in the fight. The turn modal itself stays locked to the character whose action it is.

The player does not browse campaigns or adventures. They see their characters, and anything the GM has shared.

Players edit their own characters inside the constraints. The GM sees every player character and every non-player character, and can change a non-player character as they see fit. A GM can also directly edit any player character. Ordinary GM edits follow the same constraints and experience costs as a player's. The GM can also always add a power or ability to a character, or add a constraint to one. An owned ability that breaks a constraint stops working until the constraint is removed.

The GM can generate a random non-player character before the game or during it. It is a full character. The pack decides which rolls are used. The GM can edit the result.

## Combat

A group is a list the GM makes so they can see who is together. Keep this simple. A fight is two or more groups. During that fight a character is in only one of those groups. Outside a fight the GM groups any characters they want. Groups that follow from location are later.

The GM marks the groups as fighting. The tablets of the characters in those groups show the combat screen. Every tablet in the fight shows both groups and the initiative order the whole time. Players can see non-player hit points and armor. In v1 those numbers are always visible; hiding them for a "what they look like" view is later work.

Initiative is rolled once, at the start of the fight, on the table or with the auto-roll button. That order stays until the fight is over. Each melee gives every character their actions back, and Lex walks the same order, one action at a time. Characters with actions left keep coming around. Lex does not stop the fight to collect a new initiative. The GM ends the fight. The GM can call a fresh initiative if the situation changes, such as new characters joining. When the GM ends the fight, Lex does not prompt about leftover actions; the combat screen goes away and sheets stay as updated.

On your action you pick a weapon or a power on the combat screen and tap a target when the action needs one. A power spends Anima. Anima recovers as a character catches their breath: during a fight as each melee passes, and again after combat. How hit points heal depends on the character. Damaged armor in most cases needs repair. At zero flesh hit points a character is unconscious or dead; what happens next is the GM's call. Timed effects and constraints count down by melee during a fight. Outside a fight, timing is the GM's call; Lex gives the GM tooling to see those timed effects and constraints. Lex is not a virtual tabletop and does not run a game clock. If the action needs a roll, a modal shows that roll's dice and asks for the result, with a small button that rolls for you. If it does not need a roll, the effect happens when you select it.

The modal is on the tablet of the character who is rolling and on the GM's tablet. Either can type the result or use the auto-roll button. The same rule covers every roll. A defense modal includes a pass, so the defender can keep the action and enter no roll.

The GM can undo the last action, or several actions in a row, to fix a mistake such as a mistyped roll. Undo is GM-controlled.

A player with paper says the action, for example "laser rifle to the bandit." The GM selects it, the player rolls, and the GM enters the number.

When the GM ends the fight, the combat screen goes away. The sheets stay, already updated.

## Rolls outside a fight

Outside a fight, a player can tap a skill on their sheet to open the same roll modal. The GM can also call for a roll, which opens the modal on that character's tablet. The same roll rules apply: the rolling tablet and the GM's tablet both show it, and either can type the result or auto-roll.

## Attributes

Attribute scores are integers, and 10 is an average human. From 1 to 30 a score is linear. Strength is lift, 6 kg per point, and above 30 every 5 points is ×10. Strength adds to fists and hand-to-hand weapons, and the blow takes the prefix its strike work reaches. Strength dice, what a fist does, is one d6 per full 10 points from 1 to 30, at least 1; above 30, each 5 points runs 1, 2, 3, 5, 7 dice and then the next prefix. Low Strength costs lift and carry, not damage. The Strength bonus is Strength dice minus 1, and hand-to-hand damage is the bonus plus the weapon's dice at the Strength's prefix. A weapon's own bonus damage, such as a magic sword's +2d6 fire or a powered weapon's plasma, adds on top at its own prefix; Strength does not change it and durability does not cap it. Each hand-to-hand weapon has a durability, which is a prefix set by its material; a natural weapon's comes from the species. A blow, or a parried blow, beyond the durability destroys the weapon, at the GM's discretion, and a parried blow then lands with full force. A wielder can pull a blow to a lower Strength. The free steps are 1 plus half the Agility bonus, rounded down, and pulling that many prefix steps or fewer needs no roll. Past them, a `d20` must beat the number of extra steps, and a failure lands at full Strength. This rule is optional. Durability is optional. Speed is top speed, 0.7 m/s per point; above 30 it has its own curve, with light speed at 90 and ×5 per point from 90 to 100. Speed is how fast one moves over time, and animals and vehicles have it. Above 90 it needs a mechanism that gets around general relativity, such as warping or folding space or jumping along a trajectory. Warping, folding, or jumping is Speed only when it can land anywhere along its path in a given time. Teleporting with a range, line of sight, or limits on the target is an ability; teleporting with no limits can be 100+. A vehicle's Speed is on the vehicle. Worn gear such as power armor puts its Speed on the wearer's sheet. Speed governs movement only and gives no actions, initiative, or reaction time; any of those that come with high Speed are abilities. Agility is control and precision, not reaction time, and gives no initiative. By itself it is a bonus, max(0, floor(Agility / 5) − 2), to Strike and Defense, and it sets the free steps for pulling a blow, with no other traits. Combat has two bonuses, Strike and Defense. Strike applies to every attack. Defense is one roll, and the defender chooses to dodge or parry: a parry works only against melee and thrown attacks, needs no room, and puts the weapon's durability at stake; a dodge needs room; neither stops an area effect. Skills, occupations, and species add abilities with their own Agility-based bonuses: gymnastics for balance and safe fall (a height that doubles every 5 points of Agility above 30), a hand-to-hand fighting skill for catching thrown objects, pickpocketing, sleight of hand, surgery, riding, or Reflex Defense. Catching full-draw arrows or bullets, acting first, and dodging beams are abilities. Reflex Defense makes a dodge or parry cost no action and rolls the normal Defense bonus; in each melee the first 1 + Agility bonus have no penalty, then −2 cumulative per further reflex defense. It is the same whatever its source. Any defense, from Reflex Defense or spending an action, works only against an attack the defender perceives. What is perceived is the attacker, not the projectile. An attack from outside combat, such as a sniper's first shot, lands with no defense roll; the target is then in combat, and the sniper's later attacks that melee can be defended unless the sniper relocates or leaves combat. Advanced fencing and sword-fighting skills, acrobatic occupations, augmented soldiers, and species grant it; each skill says whether it grants it and at what level; it replaces the automatic parry from combat training. A sixth sense for danger comes only from a species or a psionic power, cannot be trained, and puts the character into combat before an unperceived attack, with an initiative roll, so they can defend even against a sniper's first shot. Endurance is how well a body holds up against what is done to it: fatigue, poison, disease, heat, cold, vacuum, staying conscious when badly hurt, and recovery. It has no physical measure and is a bonus on resistance rolls. 30 is an elite soldier or marathoner. At 100, ordinary poison, disease, and exhaustion cannot touch the character; surviving deep space or the inside of a star comes from an ability. Flesh hit points are a total stored on the sheet, from species and body mass plus abilities. The flesh prefix comes from species or an ability, never from an attribute. The mapping is in [universal-system.md](universal-system.md#attributes).

The scale ends at 100, which means immeasurable. A character at 100 gets everything 100 gives. Anything beyond that comes from a specific power or ability, such as one that deals cosmic damage, or from the GM, never from the attribute.

## Rewards

After a fight, Lex can open a reward screen. The GM puts up a stack of items and can type an experience award for each character. Experience is spent later, on the sheet.

One player holds an item at a time. They click to claim it and click again to let go. Someone else who wants it talks with them at the table. The holder can let go, or the GM can assign it. The GM can also start a fight over it. The GM controls the screen and can close it whenever they want. While an item is held, every tablet still shows the full item details.

Items nobody took stay on the ground, unclaimed. The GM can open that stack again. Nothing is discarded and nothing is given away by closing the screen.

## Adventures

An adventure holds locations, stories in prose, maps, and non-player characters, plus any suggested experience, loot, and groups. The GM can edit it during the game. It is enough to run from.

Player characters belong to the campaign and stay as the adventures change.

For any adventure material, the GM can show it or hide it, for every player or for the players they pick. Players do not open the adventure. They see a map, or anything else, only when the GM sends it.

## LLM and ingest

An LLM can work with Lex in two ways: as a skill inside an existing LLM harness, or with Lex acting as the agentic harness itself. A goal is to ingest an entire book and produce a data pack of everything in it: characters, maps, abilities, powers, species, occupations, and so on. The GM drives the LLM. They iterate together on every stat and number, the way a planning session works, and the LLM can recommend stats and numbers based on existing material.

## Packs and copyright

During play, sqlite on the server is the live record. Packs are import and export. Characters move between Lex servers through data packs. An exported character can depend on other packs; how dependencies work is later detail. The repo ships only original packs. A pack converted from a copyrighted or licensed game, such as GURPS, Rifts, or D&D, lives only on the local server and is gitignored. It is never committed or published. Ingest notes about a copyrighted game follow the same rule: they stay local and gitignored, not committed to `data/ingest/`. `.gitignore` already enforces this: everything under `data/packs/` and `data/ingest/` is ignored except the READMEs and the original `universal` and `u-simplified` packs. 

## Campaign die

The GM sets the campaign's die system (for example GURPS 3d6, d20, or d100). Every player at that table uses the same system. The GM can change it at any time, and the change applies to everyone. Systems are not mixed inside one campaign. Sheet labels may still differ per tablet; the die itself does not.
