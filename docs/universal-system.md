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

Our highly skilled martial artist would easily defeat any one villager, but if there is 100 of them then the martial artist is going to be overwhelmed.
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

The numeric gauge for magic, psionics, and other supernatural abilities. 
Anima is measured in Magi or Magic points `M`.
Anima recuperates dynamically as a character "catches their breath" during or after an encounter.


### Scaling and Anima Threshold

Lex uses the metric system to scale supernatural Anima, using `M` (Magi points) as the base universal unit. 
And, like with Danage Thresholds, the Anima Threshold denoted by metric prefixes makes exceptionally large numbers clean, efficient, and easy to read on a character sheet, especially for powerful characters.

*   A base character with no real magic or psionic abilities might have an Anima pool of `12 M`.
*   A mortal mage or psychic character might have an Anima pool of `160 M` with an Anima Threshold of 10, and thus `16 dM`
*   A powerful demigod might possess an Anima pool of `120 hM`, which represents a whopping `12,000 M`.

### Trivial Costs and At-Will Powers

When calculating resource consumption, Lex applies a consistent floor truncation rule based on the character's active Anima Threshold:

```
points_deducted = floor(spell_cost_base / character_anima_threshold)
```

If a high-tier character casts a low-cost spell, the final cost naturally resolves to zero. This models immense power seamlessly without requiring specialized trait rules or exception lists:

*   **The God Effect:** A spell costing `30 M` cast by a demigod operating at a hecto-Magic scale (`hM`, scale 100) calculates as `floor(30 / 100) = 0`. The ability is free for that character to cast.
*   **High-Tier Drain:** If that same demigod channels a world-shaking miracle costing `5,000 M`, the math resolves to `floor(5000 / 100) = 50 hM`. The action inflicts a noticeable drain on their massive reserves, keeping major magic balanced.

This also means that as character increases their Anima Threshold, their lower-level abilities (which costs less than their threshold) becone free. 

For example, when an entry-level mage attains `dM` levels of abilities, with Anima costs of `10 M` or above, their lower-level abilities (any that require less than 10 M) become free, like muscle memory.

*Note: While an ability may cost 0 M to execute, it is still bound by the action economy and explicitly consumes an attack or action during a melee block.*




## Dice

In Lex, dice stay on the eable, while dice rolls can be automated with the push of a button, the whole point of an RPG is the players' participation in a shared story, through their decision making and dice rolls. 

Lex simply automates the boilerplate, such as conversion math, and stacked effects, allowing seamless universal gameplay.

RPGs have many different dice mechanics, from the classic `d20` roll, to `3d6` (bell curve) rolls, or `d100` probability rolls. Each major gaming system has its own dice rules, and competent GMs regularly modify these rules to fit the needs of their campaign. Lex enbraces this approach which is why dice mechanics are defined in the adapter layer (alongside labels and attribute conversion). So while one adapter uses a classic `d20` to determine if an attack is a hit or miss, another adapter could use `3d6` where a low roll determines a hit.

Under the hood, the Lex engine is tracking effects/constraints, and is doesn't particularly care which dice mechanics determined a hit or miss, Lex just track the result. 

That said, combat bonuses will be adjusted to reflect the dice mechanics, e.g., a +5 to strike on a `d20` will nean the user just needs a 5 or higher to hit, an 80% likelihood. This means a `d100` is an 80 or higher (which would show as +30% bonus). And likewise a `3d6` low to hit would be a roll of 13 or lower (a similar 80% likelihood).

The GM chooses the system, and can even opt-out of different dice mechanics, for example, skill rolls can be replaced by GM judgment, or attribute rolls can be replaced by a fixed point scale that players to their character as they wish.

The adapter can define dice mechanics (even opt out) for the following areas:

+ attributes, character creation and per-level increases 
+ hit points and per-level increases
+ anima abd per-level increases
+ combat rolls, such as initiative, and bonuses for striking and dodging
+ skill rolls, or knowledge rolls
+ saving throws

In all cases, the underlying Lex engine does not care which dice mechanics are used on the table, Lex faithfully converts from to another using a simple probability conversion, and will say things like "roll 60 or above" if using a `1d100`, or "roll 12 or above" if using a `1d20`.

Note that some rolls, like weapon damage, are fixed and universal across all ganes, alrhough where exceptions exist those be converted to standard hit point system (one of the few areas most games agree on).



## HUD 

HUD displays Hit Points and Anima and combat stats.
Combined Hit Points: flesh on the left, remaining armor next, depleted on the right. Remainder is a darker same-color fill when the Damage Threshold is greater than 1; hover on that remainder shows the Damage Threshold. Black empty only when you are on base unit hits (threshold 1) and under 100. Hit Points colors are blood red (unit) → orange (deka) → amber (hecto) → gold (kilo and up). Anima is blue. Roster and sheet use the same HUD.


## Classes and lore

Classes are mechanical packages (effects and constraints). Ancestry/species is a separate axis. Lore is prose the fold does not read. Ingest writes **rows** into `data/packs/` which is ingested into the Lex database; working notes and book links stay in `data/ingest/` (untracked except `data/ingest/README.md`).
