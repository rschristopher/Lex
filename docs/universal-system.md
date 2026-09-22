# Lex

Lex is a complete and playable RPG system which can convert characters, classes and lore to/from any other RPG. Lex is designed to be LLM-friendly in order to incorporate any material, from other RPGs to fantasy novels (including graphic novels) into a fully imtegrated multiverse.

There are three primary components of Lex:

1. character app -- manage a roster of characters (playable and non-playable characters), powered by the underlying universal effects/constraints engine, and generate character sheets compatible with any existing RPG.
2. combat and gaming layer -- manage player combat and gaming where dice rolls stay on the table and Lex handles the math and rules enforcement; utilizes the same universal effects/constraints engine such that character sheets dynamically update during combat and gameplay.
3. GM-assistant -- helps manage adventures (serial or episodic) within a larger campaign. LLM-friendly such that custom characters, character classes, locations, and lore can be ingested and integrated into a campaign. 

For example, ingest Homer's Iliad and Odyssey alongside wild west novelas for a Greek mythological take on the wild west. 
Or if you want to integrate Japanese demons (oni or yokai) alognside the Greek gods, point your favorite LLM at the relevant text (in any language) and ingest that into Lex.
Use the GM-assistant with an LLM to create maps and towns in custom adventures for your campaign. Lex is the ideal RPG harness for a LLM.


See [glossary.md](glossary.md) for definitions of terms.

The Lex app is NOT a virtual-table-top, and doesn't try to be. Lex manages characters (PCs and NPCs), assists with combat, and includes a GM-assistant to manage adventures and larger campaigns.
The goal is that dice stay on the table, and Lex manages the math (using an effects/constraints engine) of leveling characters, combat, armor, and damage. 

Other games are not separate engines. They are **adapters** which converts characters to/from other systems, acting as a kind of Rosetta stone for tabletop RPGs.
Lex presupposes a multiversal RPG, where one can easily integrate disparate lore, for example, ingest Homer's Odyssey alongside wild-west novels for a Greek Mythological cowboy western campaign.

**Packs are not exclusive.** Load as many as you want. Characters, classes, and lore from every pack sit in one campaign. 
Every adapter with `"view": true` is a sheet language for that same campaign (presentation only, it does not change the underlying engine math).





## Verisimilitude

> The quality or state of being verisimilar; the appearance of truth; probability; likelihood

Table-top RPGs are often incompatible, with many conflicting and contradictory rules; which ultimately means that a truly "universal" RPG system like Lex would be impossible.
However, the overlap is usually immense, and the conflicts rare, which is why the concept of a universal system has always been so appealing, why conversion books exists, and why competent GMs have already been doing this for decades.

The design of Lex is based on that exact pattern of what competent players and GMs have been doing naturally, a simple concept of *Verisimilitude", where we favor rules that adhere to consistency and truth, strictly avoiding (and even discarding) rules that lead to absurd conclusions that break the immersion of the game.

For example, many popular systems include an "Armor Class" where an attacker rolls a `d20` and it must be greater than the "Armor Class" to determine if it is a hit.
Good armor has a high "Armor Class" and is thus difficult to hit.
This however creates many conflated and confusing situations where a literal tank would appear very difficult to hit, with the same mechanics of landing a blow on an experienced marital artist. And relatedly, this produces a rather confounding situation where 100 villagers with pitchforks would technically be able to defeat a tank as easily as they could defeat an experienced martial artist (100 villargers with pitchforks can wear down tank armor, using the same mechanics as they could to overwhelm and defeat the martial artist).

*Verisimilitude* is the recognition that the system itself shouldn't require GM intervention to avoid villagers with pitchforks defeating a tank.
Other systems have a more accurate and believable "Damage Resistance" concept (or "Damage Threshold"), where a tank is trivially easy to hit, but the damage from pitchforks is simply never able to hurt the tank, and the tank easily wins against 100 villagers, but the martial artist does not.



## Combat Rules

Whether rolling `d20` or `3d6` or `d100` to determine a hit, almost all systems use a similar and very compatible system for combat.
Within a given system, a competent GM will modify the rules to what works for the players.
Lex is customizable to any system (within reason, see *verisimilitude*)

1. [optional] initiative roll, determine who goes first, and the order of combat
2. attack, roll and determine if the attack succeeds
3. [optional] defense, roll to determine if a successful attack lands (or was parried or dodged); characters without automatic parry (from combat training), or automatic dodge (from character class or ability) must choose this as it consumes an action.
4. damage, roll to determine the exact amount of damage from a successful attack.
5. [optional] damage reduction, if applicable (specific to character ability, e.g., reduce fire damage)

Whether a 1-second round, or a multi-second melee where each player has a set number of actions within the melee, combat always iterates through that same pattern of attack, defense, and damage.

What adds verisimilitude is that a martial artist must explicitly defend, whereas a tank simply doesn't need to actively defend, but is protected by armor (which cannot be hurt by pitchforks).
And similarly, a martial artist can realistically perform more actions than a tank during a given block of time; but those extra actions will not be sufficient to fend off 100 villagers with pitchforks.



### Actions

Not all players are equal, and the number of actions performed in a block of time is required for verisimilitude.
Whether it's 6-second melees or 15-second melees, it doesn't matter, what matters is that the system represents a believable number of actions for all characters (PCs and NPCs) during a block of time.

Lex defaults to 10-second melees for simplicity sake.

In Lex a highly trained martial artist might have 8-10 actions per melee, and each of the villagers has only 3, and the tank might only have 2 (assuming a WWII-era tank).

Our highly martial artist would easily defeat any one villager, but if there is 100 of them then the martial artist is going to be overwhelmed.
The tank on the other hand is still impervious to pitch forks (and even punches from the martial artist).



### Damage Threshold

A martial artist cannot damage a tank, nor can a mob of villagers with pitchforks.

Similarly, a mob of villagers should not be able to defeat a dragon or any kind of mythological creature.
This is a common failure of verisimilitude for many popular games.

Additionally, games that integrate high-concept sci-fi often result in such failures.
A futuristic suit of power armor should easily defeat 100 medieval villagers, but not necessarily a futuristic tank or even a mythological creature (depends on the game).

The actual physics of modern weaponry demonstrates this exact problem, and where most gaming systems tend to fail.

| Weapon | Joules | Dice Formula | Average Rolled Damage | Steel Plate (300) | Ceramic Plate (2,000) | Tank Armor (300,000) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Punch** | ~100 J | **1d6** | 3.5 | n/a | n/a | n/a |
| **9mm Pistol** | ~500 J | **5d6** | 17.5 | n/a | n/a | n/a |
| **Assault Rifle** | ~1,000 J | **1d6 × 10** | 35 | n/a | n/a | n/a |
| **Heavy Machine Gun** | ~10,000 J | **1d6 × 100** | 350 | damaged | n/a | n/a |
| **Light AT Cannon** | ~100,000 J | **1d6 × 1,000** | 3,500 | damaged | damaged | n/a |
| **Heavy AT Cannon** | ~1,000,000 J | **1d6 × 10,000** | 35,000 | damaged | damaged | damaged |

Lex uses a simple "Damage Threshold" to solve this problem.
Damage less than the threshold is simply "not applicable", because punching a tank (or even shooting a tank with a 9mm pistol) will do no damage to the tank's armor.
But an anti-tank weapon will penetrate the tank's armor and destroy everything inside (including the humans).



### Scaling Damage and Armor

Most RPGs unfortunately do not deal with with large numbers (such as those in the above table).
However, this is an easily solved problem, and while some games stumble (badly) towards this solution, it is a solved problem that need not be re-invented.
We should know that a kilometer is 1000 meters, and we should never get confused that a 9mm pistol does no damage to a heavily armored tank.
The metrics system solves this exact problem of scaling very large (and very small) numbers.

Lex uses the metrics system for **A** (armor) and **D** (damage).
A human punch may do `1d6 D`, while the heavy anti-tank cannon inflicts `1d6 mD` (mega-damage) which is identical to `1d6 × 10,000 D`

And while Lex supports any Damage Threshold (2, 42, or even 10,000 like the tank), a metrics prefix on armor can also imply a metrics-based Damage Threshold.
For example, a tank with `300,000 A` and a Damage Threshold of 10,000 can be expressed simply as `30 mA`.
Or maybe a futuristic power armor with `250,000 A` and a Damage Threshold of 1,000 would be `250 kA`.

A GM can chose whatever scale or range they desire, keeping it small without prefixes and thresholds (such as a medieval fantasy adventure),
or they can run a high-concept sci-fi campaign that integrates Greek gods and superheroes and enjoy!

The base unit in Lex, as in all games, is a Hit Point (HP), with no prefix.

A medieval villager may have 15 HP, and a `2d6 D` pitchfork can be quite deadly.
But a knight with `300 A` of steel plate and chain-mail armor might feel immune to that villagers pitchfork, and we can represent this as `30 dA`.
And a futuristic power armor with `250 kA` will appear god-like to both the villager and the medieval knight.

Prefixes exist so a sheet can say `770 hA` instead of "77,000 HP with 100 Damage Threshold".
And similarly, one never need to write `×10` or `×100` on dice rolls for damage, in gameplay the dice is on the table and Lex does the unit conversion math.


| Prefix | Scale  | Damage | Armor  | Example |
|--------|--------|--------|--------|---------|
| centi  | 10⁻²   | cD     | cA     | guppy |
| deci   | 10⁻¹   | deD    | deA    | kitten |
| (base) | 1      | D      | A      | human |
| deka   | 10     | dD     | dA     | Kevlar |
| hecto  | 100    | hD     | hA     | power-armor
| kilo   | 1 000  | kD     | kA     | tank |
| mega   | 10⁶    | mD     | mA     | Godzilla |
| giga   | 10⁹    | gD     | gA     | mountain |
| tera   | 10¹²   | tD     | tA     | planet |


Lex can scale to the very large, as well as to the very small, where a human's base Damage Threshold of 1 will be invincible to the centi-damage bite of school of guppies.



### Per-hit conversion

```
points = floor(amount × damage_scale / armor_scale)
```

The metrics prefix denotes a base-10 exponent as the Damage Threshold, but the Lex universal engine can technically function with any arbitrary Damage Threshold. 
A base-10 damage threshold is easy to reason about and convenient to use, but the math is the same for any arbitrary number.
For example, maybe a custom body armor has a damage threshold of 42, this means damage less than 42 will not be applied.

Also, any fractional remainder will not be applied (e.g., 192 base damage against `5 hA` will not do `1.9 hD`, but only `1 hD` leaving `4 hA`).

A club at `2d6 D` against armor at Damage Threshold of 100 is 0, every time. 
An `hD` weapon against unit flesh is ×100 into hit points. 




## Anima

The numeric gauge for magic, psionics, and other abilities. Recuperates as one "catches their breath". 


## HUD 

HUD displays Hit Points and Anima and combat stats.
Combined Hit Points: flesh on the left, remaining armor next, depleted on the right. Remainder is a darker same-color fill when the Damage Threshold is greater than 1; hover on that remainder shows the Damage Threshold. Black empty only when you are on base unit hits (threshold 1) and under 100. Hit Points colors are blood red (unit) → orange (deka) → amber (hecto) → gold (kilo and up). Anima is blue. Roster and sheet use the same HUD.


## Classes and lore

Classes are mechanical packages (effects and constraints). Ancestry/species is a separate axis. Lore is prose the fold does not read. Ingest writes **rows** into `data/packs/` which is ingested into the Lex database; working notes and book links stay in `data/ingest/` (untracked except `data/ingest/README.md`).
