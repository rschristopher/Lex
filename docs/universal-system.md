# Lex

Lex is a complete and playable RPG system which can convert characters, occupations, and lore to/from any other RPG. Lex is designed to be LLM-friendly in order to incorporate any material, from other RPGs to fantasy novels (including graphic novels) into a fully imtegrated multiverse.

There are three primary components of Lex:

1. character app -- manage a roster of characters (playable and non-playable characters), powered by the underlying universal effects/constraints engine, and generate character sheets compatible with any existing RPG.
2. combat and gaming layer -- manage player combat and gaming where dice rolls stay on the table and Lex handles the math and rules enforcement; utilizes the same universal effects/constraints engine such that character sheets dynamically update during combat and gameplay.
3. GM-assistant -- helps manage adventures (serial or episodic) within a larger campaign. LLM-friendly such that custom characters, occupations, locations, and lore can be ingested and integrated into a campaign. 

The game is the GM talking and the players playing their characters in a shared story. The same game can be played with paper and dice alone; tablets assist. Lex does not play the game, and it has nothing to start or stop. Nothing in the app holds the table until a sheet is finished.

For example, ingest Homer's Iliad and Odyssey alongside wild west novelas for a Greek mythological take on the wild west. 
Or if you want to integrate Japanese demons (oni or yokai) alognside the Greek gods, point your favorite LLM at the relevant text (in any language) and ingest that into Lex.
Use the GM-assistant with an LLM to create maps and towns in custom adventures for your campaign. Lex is the ideal RPG harness for a LLM.


See [glossary.md](glossary.md) for definitions of terms.

The Lex app is NOT a virtual-table-top, and doesn't try to be. Lex manages characters (PCs and NPCs), assists with combat, and includes a GM-assistant to manage adventures and larger campaigns.
The goal is that dice stay on the table, and Lex manages the math (using an effects/constraints engine) of leveling characters, combat, armor, and damage. 

Other games are not separate engines. They are **adapters** which converts characters to/from other systems, acting as a kind of Rosetta stone for tabletop RPGs.
There is one Lex engine, and one campaign has one set of rules. An adapter is a sheet language: labels, attribute names, and which dice are shown. It does not change the math. A different melee engine is later work, and it is not part of this app.
Lex presupposes a multiversal RPG, where one can easily integrate disparate lore, for example, ingest Homer's Odyssey alongside wild-west novels for a Greek Mythological cowboy western campaign.

**Packs are not exclusive.** Load as many as you want. Characters, species, occupations, and lore from every pack sit in one campaign. 
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

Armor is worn hits on the harm track, not a to-hit number. The GM may adapt labels, within the limits of verisimilitude.



## Combat Rules

Whether rolling `d20` or `3d6` or `d100` to determine a hit, almost all systems use a similar and very compatible system for combat.
Within a given system, a competent GM will modify the rules to what works for the players.
Lex is customizable to any system (within reason, see *verisimilitude*)

1. [optional] initiative roll, determine who goes first, and the order of combat
2. attack, roll and determine if the attack succeeds
3. [optional] defense, one roll to determine if a successful attack lands; the defender chooses to dodge or parry. A defense consumes an action unless the character has Reflex Defense (an ability).
4. damage, roll to determine the exact amount of damage from a successful attack.
5. [optional] damage reduction, if applicable (specific to character ability, e.g., reduce fire damage)

Combat has two bonuses, Strike and Defense. Strike applies to every attack. A parry works only against melee and thrown attacks, needs no room, and puts the parrying weapon's durability at stake. A dodge needs room. Neither stops an area effect.

Every attack is physical or mental. A physical attack hits the body, such as a punch, a fireball, lightning, or conjured chains, vines, or tentacles, and is Strike against Defense. A mental attack acts on the target's mind or will, such as mind control, a trance, fear, or an illusion, including an illusion of chains. The attacker rolls the ability's own bonus, and the target makes a resist roll with their Willpower bonus. Resisting, like Defense, is reflexive and never costs the target an action.

Rolls are never compared. The attacker rolls against their own target to land the attack. If it lands, the defender rolls against their own target to dodge, parry, or resist. A lucky attack only lands, and can still be dodged or resisted.

A defense, whether it spends an action or comes from Reflex Defense, works only against an attack the defender perceives. What is perceived is the attacker, not the projectile: a dodge gets out of the line of fire before the shot.

An attack from outside combat, such as a sniper's first shot, is not perceived and lands with no defense roll. The target is then in combat and knows where the sniper is, so the sniper's later attacks that melee can be defended. The sniper can instead spend that action to relocate or leave combat and set up another opening shot. A sixth sense puts the character into combat before the unperceived attack; they roll initiative and can defend even against the first shot.

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



### Fights in the app

A group is a list the GM makes to see who is together. A fight is two or more groups, and during it a character is in only one of them. Outside a fight the GM groups any characters they want. Groups that follow from location are later work.

The GM marks the groups as fighting, and the tablets of the characters in those groups show the combat screen. Every tablet in the fight shows both groups and the initiative order the whole time. Players can see non-player hit points and armor; in the first version they are always visible, and hiding them for a "what they look like" view is later work.

Initiative is rolled once, at the start of the fight, on the table or with the auto-roll button. That order stays until the fight is over. Each melee gives every character their actions back, and Lex walks the same order, one action at a time; characters with actions left keep coming around. Lex does not stop the fight to collect a new initiative. The GM can call a fresh initiative if the situation changes, such as new characters joining. The GM ends the fight: the combat screen goes away, the sheets stay as updated, and Lex does not prompt about leftover actions.

On your action you pick a weapon or a power on the combat screen and tap a target when the action needs one. A power spends Anima. How hit points heal depends on the character. Damaged armor in most cases needs repair. At zero flesh hit points a character is unconscious or dead; what happens next is the GM's call. Timed effects and constraints count down by melee during a fight. Outside a fight, timing is the GM's call, and Lex gives the GM tooling to see those timed effects and constraints; Lex does not run a game clock. If the action needs a roll, a modal shows that roll's dice and asks for the result, with a small button that rolls for you. If it does not need a roll, the effect happens when you select it.

The roll modal is on the tablet of the character who is rolling and on the GM's tablet. Either can type the result or use the auto-roll button. The same rule covers every roll. A defense modal includes a pass, so the defender can keep the action and enter no roll.

The GM can undo the last action, or several actions in a row, to fix a mistake such as a mistyped roll.

A player with paper says the action, for example "laser rifle to the bandit." The GM selects it, the player rolls, and the GM enters the number.

Outside a fight, a player can tap a skill on their sheet to open the same roll modal, and the GM can call for a roll, which opens the modal on that character's tablet. The same roll rules apply.



### Damage Threshold

A martial artist cannot damage a tank, nor can a mob of villagers with pitchforks.

Similarly, a mob of villagers should not be able to defeat a dragon or any kind of mythological creature.
This is a common failure of verisimilitude for many popular games.

Additionally, games that integrate high-concept sci-fi often result in such failures.
A futuristic suit of power armor should easily defeat 100 medieval villagers, but not necessarily a futuristic tank or even a mythological creature (depends on the game).

The actual physics of modern weaponry demonstrates this exact problem, and where most gaming systems tend to fail.

| Weapon | Joules | Dice Formula | Average Rolled Damage | Steel Plate (`3 hA`) | Ceramic Plate (`2 kA`) | Tank Armor (`300 kA`, threshold `10 kA`) |
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
A human punch may do `1d6 D`, while the heavy anti-tank cannon inflicts `10d6 kD`, which averages the same as `1d6 × 10,000 D`. There is no prefix for 10,000; mega is 1,000,000.

And while Lex supports any Damage Threshold (2, 42, or even 10,000 like the tank), a metrics prefix on armor can also imply a metrics-based Damage Threshold.
For example, a tank with `300,000 A` and a Damage Threshold of 10,000 is `300 kA` with a threshold of `10 kA`.
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

### Flesh

A character's flesh hit points are a total stored on the sheet. The total comes from species and body mass, plus abilities. The flesh prefix comes from species or from an ability, never from an attribute.

| Flesh prefix | Ignores | Example |
|---|---|---|
| hecto | a `5d6 D` pistol and a `1d6 dD` rifle | a dragon |
| kilo | a `1d6 hD` heavy machine gun | a larger dragon |
| mega | a `10d6 kD` heavy anti-tank cannon | |


## Anima

The numeric gauge for magic, psionics, and other supernatural abilities. 
Anima is measured in Magi or Magic points `M`.
Anima recuperates dynamically as a character "catches their breath" during or after an encounter.

Anima is Intellect + [Willpower](#willpower) + Endurance + Strength in `M`, plus a species bonus. The human species bonus is 10, so an average human has `50 M`. Willpower sets how fast Anima recovers. An occupation never grants Anima from nothing: a mage or psychic needs enough Anima to pay for their first abilities.

Every mage or psychic occupation has the same Anima ladder, bought with experience. Each level replaces the formula, and each adds the species bonus:

| Level | Anima | Example |
|---|---|---|
| Novice | Intellect + Willpower + Endurance + Strength | all 10s: `50 M` |
| Apprentice | 10 × Intellect + 100 × Willpower + 60 × Endurance + 30 × Strength | all 10s: `2,010 M` |
| Professional | 50 × Intellect + 400 × Willpower + 300 × Endurance + 150 × Strength | all 15s: `13,510 M` |
| Expert | 200 × Intellect + 1,600 × Willpower + 1,200 × Endurance + 600 × Strength | all 20s: `72,010 M` |
| Master | 800 × Intellect + 6,400 × Willpower + 4,800 × Endurance + 2,400 × Strength | all 30s: `432,010 M` |

Most characters in a typical setting are Professional, and Expert is rare. A Master is a human trained to compete with superheroes and metahumans without cybernetics or metahuman abilities.

Anima uses the standard prefixes: deka, hecto, kilo, then mega, giga, tera, and on; above kilo each prefix is 1,000 times the last. An average human starts at deka, which is enough to begin a mage or psychic occupation. Humans and metahumans have 1 to 30 in the attributes that feed Anima, so even a Master stays below mega. Mega and above is a separate, cosmic category that takes more than an occupation.

A pool is written in the prefix that matches the setting's power band. In a mega-damage setting, a mage's or psychic's power points are hecto, 1 point to `1 hM`, so a new ley-line mage with 137 points has `137 hM` (`13,700 M`).


### Prefixes and free use

Anima uses `M` as its unit. Prefixes are notation only: `120 hM` is `12,000 M`.

*   An average human with no magic or psionic abilities has `50 M`.
*   An apprentice mage or psychic with all 10s has `2,010 M`.
*   A professional mage or psychic might have `120 hM`.

An ability can offer a free-use option, bought with experience at a price the ability sets; with it, the ability costs no Anima. An ability without that option always costs Anima. A free ability still takes an action.

An ability's Anima cost is the only limit on using it. There is no Willpower or prefix requirement, and anyone can attempt any ability. Whether it works on a target is decided by the target's resistance, such as Willpower against mind control.

Each spell, power, or ability has its own skill level, so a character can be an expert in one and a novice in another, and can mix psionics, spells, and other powers. Experience improves whichever abilities the player chooses. The levels are Novice, Apprentice, Professional, Expert, and Master. A novice fails often, an expert sometimes, and a master never; a target can still resist. Each ability says whether it uses the Intellect bonus, the Willpower bonus, or neither. An ability that is a physical attack, such as a fireball or conjured chains, has no separate roll to work: it always works, and uses the normal Strike roll against Defense.




## Attributes

Lex has eight core attributes: Strength, Agility, Endurance, Speed, Intellect, Willpower, Awareness, and Appearance. Persuading, leading, intimidating, and performing are abilities. Adapters can derive stats such as Charisma from Appearance, Willpower, and Intellect.

Attribute scores are integers, and 10 is an average human. From 1 to 30 a score is linear. The scale ends at 100.

Strength and Speed have a physical measure:

```
Strength 1 to 30:    lift = 6 kg × Strength
Strength 31 to 100:  lift = 180 kg × 10^((Strength − 30) / 5)

Speed 1 to 30:       top speed = 0.7 m/s × Speed
Speed 31 to 90:      top speed = 21 m/s × 10^((Speed − 30) / 8.39)
Speed 91 to 100:     top speed = c × 5^(Speed − 90)
```

A point is worth +10% at 10 and +3% at 29. Above 30 a Strength point is ×1.58, so 5 points is one metric prefix. A Speed point is ×1.32 from 30 to 90, where 90 is the speed of light, and ×5 above 90. A score is rounded to the nearest integer.

100 means immeasurable. A score of 100 gets everything 100 gives. Anything beyond that comes from a specific power or ability, such as one that deals cosmic damage, or from the GM. It never comes from the attribute.

Agility, Endurance, Intellect, Willpower, Awareness, and Appearance have no physical measure. They use the same integers. For these, 30 is the best humans on record and above 30 is beyond any human.

### Attribute table

Strength, Speed, Endurance, Agility, Intellect, and Willpower are decided. The other two are proposals.

| Attribute | Measures | Rolled for | 1 | 10 | 30 | 50 | 100 | Status |
|---|---|---|---|---|---|---|---|---|
| Strength | lift, 6 kg per point | lifting, breaking, grappling; strike work | 6 kg | 60 kg, untrained adult | 180 kg; the deadlift record is 32 | 1,800 t | 18 trillion t | decided |
| Speed | top speed, 0.7 m/s per point up to 30 | distance per melee, chases | 0.7 m/s | 7 m/s, untrained sprint | 21 m/s; the 100 m record peak is 18 | 5.1 km/s, under orbital speed | about 10 million times light; crosses the Milky Way in about 4 days | decided |
| Endurance | how well a body holds up against what is done to it; unitless | resisting fatigue, poison, disease, heat, cold, and vacuum; staying conscious when badly hurt; recovery | bedridden | average adult | elite soldier or marathoner | beyond any human | ordinary poison, disease, and exhaustion cannot touch it | decided |
| Agility | control and precision, not reaction time; unitless | strike, defense, free steps to pull a blow | cannot balance unaided | average adult | elite gymnast | beyond any human | full control of its body at any speed it can reach | decided |
| Intellect | reasoning, memory, and learning; unitless | knowledge and technical skills | cannot follow simple instructions | average adult | supernatural human genius; 20 is a human genius | learns a language in hours, a field in a day | knows any subject completely by thinking about it | decided |
| Willpower | resolve; unitless | pushing through pain and the body's limits; resisting fear, persuasion, mind control, and mental powers; holding concentration | yields to any pressure | average adult | the most disciplined humans on record | beyond any human | ordinary fear, pain, and persuasion cannot move it | decided |
| Awareness | perception and intuition; unitless | noticing, searching, sensing danger, reading a situation | barely registers its surroundings | average adult | elite sniper or scout | beyond any human | nothing within reach of its senses goes unnoticed | proposal |
| Appearance | how others react on sight; unitless | first impressions, standing out, blending in | repels on sight | average adult | top fashion model | beyond any human | captivates any ordinary observer | proposal |

At 100 or above, a character gets the 100 column. Anything past it, such as surviving deep space or the inside of a star, reading minds, or crossing the galaxy in a step, comes from a specific ability, a power, or the GM.

### Prefix scores

Strike work reaches each prefix at these Strength scores:

| Prefix | Strength | Lift | Strike work |
|---|---|---|---|
| deka | 33 | 717 kg | 1.2 kJ |
| hecto | 38 | 7.2 t | 12 kJ |
| kilo | 43 | 72 t | 120 kJ |
| mega | 58 | 72,000 t | 120 MJ |
| giga | 73 | 72 million t | 120 GJ |
| tera | 88 | 72 billion t | 120 TJ |

### Strength

Strike work is force times stroke. At the same stroke, it grows with lift. Strength 10 strikes about 100 J, the `1d6 D` punch in the weapon table above, so 1 D is about 30 J. The prefix a Strength reaches is the prefix of its strike work.

| Strength | Lift | Strike work, human stroke | Average damage | Example |
|---|---|---|---|---|
| 1 | 6 kg | 10 J | 0.33 D | |
| 10 | 60 kg | 100 J | 3.3 D | untrained adult, 34 to 70 kg |
| 30 | 180 kg | 300 J | 10 D | |
| 32 | 450 kg | 750 J | 25 D | deadlift world record, 510 kg |
| 33 | 720 kg | 1.2 kJ | 4 dD | deka |
| 35 | 1.8 t | 3 kJ | 1 hD | car, 1.8 t |
| 38 | 7.2 t | 12 kJ | 4 hD | hecto, power armor |
| 43 | 72 t | 120 kJ | 4 kD | kilo; main battle tank, 63 t |
| 58 | 72,000 t | 120 MJ | 4 mD | mega |
| 99 | 11 trillion t | 19 PJ | 630 tD | |

A longer limb adds stroke: ×10 limb length is ×10 strike work at the same Strength.

Strength adds its strike work to fists and hand-to-hand weapons, at the prefix that strike work reaches, with no exceptions. A Strength that reaches kilo strikes at kilo.

**Strength dice** is what a bare fist does. From 1 to 30 it is one d6 per full 10 points, at least 1, so a low Strength still punches `1d6 D`. Its cost is lift and carry. Above 30, every 5 points runs 1, 2, 3, 5, 7 dice, and then the next prefix starts again at 1. Where there is no next prefix, as between kilo and mega, the count goes ×10 every 5 points. Ten dice of one prefix average the same as one die of the next.

| Strength | Strength dice | Kilo-rated `3d6` sword |
|---|---|---|
| 1 to 19 | `1d6 D` | `3d6 D` |
| 20 to 29 | `2d6 D` | `4d6 D` |
| 30, 31, 32 | `3d6`, `5d6`, `7d6 D` | `5d6`, `7d6`, `9d6 D` |
| 33, 34, 35, 36, 37 | `1d6`, `2d6`, `3d6`, `5d6`, `7d6 dD` | `3d6`, `4d6`, `5d6`, `7d6`, `9d6 dD` |
| 38 | `1d6 hD` | `3d6 hD` |
| 43, 48, 53 | `1d6`, `10d6`, `100d6 kD` | `3d6`, `12d6`, `102d6 kD` |
| 58 | `1d6 mD` | destroyed |
| 73 | `1d6 gD` | destroyed |
| 88, 93, 99, 100 | `1d6`, `10d6`, `200d6`, `300d6 tD` | destroyed |

The Strength bonus is Strength dice minus 1. A weapon replaces the fist's die with its own dice:

```
hand-to-hand damage = (Strength dice − 1) + weapon dice, at the Strength's prefix
```

A weapon can also carry its own bonus damage, such as a magic sword's `+2d6` fire or a powered weapon's plasma or resonance. It adds on top of the Strength bonus and the weapon's dice, at its own prefix. Strength does not change it, and durability does not cap it.

Each hand-to-hand weapon has a durability, which is a prefix set by its material. A wooden knife is unit; a quality steel or titanium staff is about hecto. A natural weapon's durability comes from the species. A blow whose prefix is above the durability destroys the weapon, as does parrying a blow above it; the GM decides. A blow that destroys a parrying weapon lands with full force, as a katana does through a balsa-wood parry. Durability is an optional rule.

A wielder can pull a blow, striking as a lower Strength to spare a weapon or an ordinary foe. The free steps are 1 plus half the Agility bonus, rounded down: 1 at Agility 10, 3 at 30, 5 at 50. Pulling down that many prefix steps or fewer needs no roll. Past them, roll a `d20` and beat the number of extra steps: one extra fails on a 1, two extra on a 1 or 2. On a failure the blow lands at full Strength. This rule is optional.

### Speed

Distance in a 10-second melee is 10 seconds of top speed: 7 m × Speed up to 30. Above 30, Lex shows it from the table.

| Speed | Top speed | Per 10-second melee | Example |
|---|---|---|---|
| 2 | 1.4 m/s | 14 m | walking pace, 1.4 m/s |
| 10 | 7 m/s | 70 m | untrained adult sprint, 6 to 8 m/s |
| 15 | 10.5 m/s | 105 m | 100 m world record, average speed 10.44 m/s |
| 18 | 12.6 m/s | 126 m | 100 m world record, peak speed 12.3 m/s |
| 31 | 27.6 m/s | 276 m | hunting cheetah, measured top 25.9 m/s |
| 40 | 327 m/s | 3.3 km | speed of sound, 343 m/s |
| 52 | 8.8 km/s | 88 km | orbital speed 7.8 km/s; escape velocity 11.2 km/s is 53 |
| 63 | 181 km/s | 1,800 km | fastest spacecraft, Parker Solar Probe, 192 km/s |
| 78 | 0.037 c | 110,000 km | fusion-drive ship |
| 90 | c | 3 million km | light, 299,792 km/s |
| 91 | 5 c | 15 million km | |
| 93 | 125 c | 0.35 light-hours | slow interstellar starship, about a parsec a week |
| 94 to 95 | 625 c to 3,100 c | | typical interstellar starship, 2 to 10 light-years a day |
| 97 to 98 | 9 to 45 light-years an hour | | fast interstellar starship |
| 99 | 223 light-years an hour | | galaxy-crossing starship |
| 100 | 1,100 light-years an hour | | crosses the Milky Way in about 4 days |

Speed is how fast a character, animal, or vehicle moves over time. Above 90 it needs a mechanism that gets around the light-speed limit of general relativity, such as warping or folding space or jumping along a trajectory; without one, Speed stays below 90. Warping, folding, or jumping counts as Speed only when it can land anywhere along its path in a given time. Teleporting with a range, line of sight, or limits on the target is an ability, not Speed. Teleporting with no limits can be 100+, and anything faster than 100 comes from abilities.

A vehicle's Speed is on the vehicle, not the pilot's sheet. Worn gear such as power armor sets the wearer's Speed while it is worn.

Speed governs movement only. It gives no actions, initiative, or reaction time. Power armor that flies faster than light leaves an ordinary wearer with human reactions and human actions per melee. A species or occupation with high Speed can come with abilities that add actions or reactions, and those are abilities.

The sheet shows top speed in the unit that reads best for its band:

| Speed | Display | Example |
|---|---|---|
| up to 40 | km/h | 18 is 45 km/h |
| 40 to 45, in air | Mach | 40 is about Mach 1 |
| 45 to 74 | km/s | 52 is 8.8 km/s |
| 74 to 90 | fraction of c | 78 is 0.037 c |
| 90 to 94 | multiples of c | 91 is 5 c |
| 94 to 96 | light-years a day | 95 is 8.6 light-years a day |
| 96 to 100 | light-years an hour | 99 is 223 light-years an hour |

From 93 up, the sheet also shows the time to cross the Milky Way, 100,000 light-years: 800 years at 93, 160 years at 94, 32 years at 95, 6.4 years at 96, 94 days at 98, 19 days at 99, and 4 days at 100.

### Agility

Agility is control and precision, not reaction time. It gives no initiative. By itself it is a bonus to Strike and Defense, and it sets the free steps for pulling a blow:

```
Agility bonus = max(0, floor(Agility / 5) − 2)
```

There is no penalty below 10. The bonus is +0 at 10, +2 at 20, +4 at 30, +8 at 50, +13 at 75, and +18 at 100.

Skills, occupations, and species add abilities, each with its own Agility-based bonuses. Any character who learns the skill gains the ability. Gymnastics covers balance and tumbling. A hand-to-hand fighting skill can include catching thrown objects. Pickpocketing, sleight of hand, surgery, and riding a bicycle or a horse are skills too. Reflex Defense is an ability; each skill says whether it grants it and at what level. A sixth sense for danger, which adds to initiative and Defense, comes only from a species or a psionic power and cannot be trained. Catching full-draw arrows or bullets, acting first, and dodging beams are abilities.

#### Safe fall

Safe fall is an ability from a skill such as gymnastics. The character lands from the safe height without damage, and the height grows with Agility:

```
safe fall (m) = 6 × 2^((Agility − 30) / 5)    above 30
```

| Agility | Safe fall |
|---|---|
| 10 | 2 m |
| 20 | 3 m |
| 30 | 6 m |
| 50 | about 96 m |
| 75 | any fall on Earth; impacts to about 250 m/s |
| 100 | impacts to about 1.4 km/s |

A falling human reaches terminal velocity, about 55 m/s, near Agility 54, so from 55 any fall on Earth is safe. Proposed: above the safe height, a successful roll halves fall damage.

#### Reflex Defense

Reflex Defense makes a dodge or parry cost no action, so the character keeps their attacks. It rolls the normal Defense bonus: the Agility bonus plus training. In each melee, the first 1 + Agility bonus reflex defenses have no penalty, and each one after that is −2 cumulative (−2, −4, …).

| Agility | 10 | 20 | 30 | 50 | 75 | 100 |
|---|---|---|---|---|---|---|
| Reflex defenses with no penalty | 1 | 3 | 5 | 9 | 14 | 19 |

Reflex Defense is the same whatever its source. Like any defense, it works only against attacks the character perceives.

Advanced fencing and sword-fighting skills, acrobatic occupations, augmented soldiers, and species grant Reflex Defense.

### Intellect

Intellect is reasoning, memory, and learning. From 1 to 30 it is the human range: 10 is average, 20 a human genius, and 30 a supernatural human genius. Its bonus uses the Agility formula and adds to knowledge and technical skill rolls:

```
Intellect bonus = max(0, floor(Intellect / 5) − 2)
```

The bonus is +0 at 10, +2 at 20, +4 at 30, +8 at 50, and +18 at 100. Some abilities, such as a spell or psionic power, use the Intellect bonus. Intellect does not add to willpower, perception, or initiative.

Above 30, Intellect sets how fast and how deeply a mind learns:

| Intellect | Learning |
|---|---|
| about 40 | perfect recall; masters a field in weeks |
| about 50 | learns a language in hours, a field in a day |
| about 75 | learns a field in minutes by reading or watching |
| 100 | perfect knowledge: thinking about a subject is enough to know it completely, with no study; thinking about French gives fluency and its full history |

### Endurance

Endurance is how well a body holds up against what is done to it: fatigue, poison, disease, exposure to heat, cold, and vacuum, staying conscious when badly hurt, and recovery. It is a bonus on resistance rolls. It does not set flesh hit points or the flesh prefix. Recovery from Endurance is the default, and a character's abilities can replace it.

### Willpower

Willpower is resolve, the mental mirror of Endurance. Endurance covers the body's limits; Willpower covers pushing through them, and resisting what is done to the mind: fear, persuasion, mind control and other mental powers, and losing concentration. Pushing through pain is Willpower; the body's tolerance for it is Endurance.

Willpower is one of the sources of a character's [Anima](#anima), and it sets how fast Anima recovers.

As with Strength, up to 30 is human and 30 to 100 is superhuman. Occupations and species can raise Willpower, and experience can buy more.

Willpower's bonus is the resist roll against a [mental attack](#combat-rules), on the `d20` scale. It is +0 up to 10, then +1 every 5 points up to +10 at 60, then +1 every 4 points up to +20 at 100:

* +1 to +10 at 15, 20, 25, 30, 35, 40, 45, 50, 55, 60
* +11 to +20 at 64, 68, 72, 76, 80, 84, 88, 92, 96, 100

+20 at 100 is immunity to all mental attacks; physical attacks still apply. Powers can add their own resist bonuses, some only against one kind of attack: an immunity to hypnotic suggestion lets a low-Willpower character resist that attack as if at Willpower 100. Shielding other people's minds is an ability, not part of Willpower.

Adapters map willpower stats from point-buy and level-based games to Willpower: willpower, ego, mental endurance, power, psyche, and wisdom-based saves.

Open questions are in [plan.md](plan.md#open-questions).

### Anchors

* Untrained adult deadlift, about 61 to 70 kg for men and 34 to 41 kg for women: [exercisemenu.com](https://exercisemenu.com/is-your-deadlift-good-average-weights-by-level-age/), from [Strength Level](https://strengthlevel.com/strength-standards/deadlift/kg) data
* Deadlift world record, 510 kg (2025): [Guinness World Records](https://www.guinnessworldrecords.com/world-records/heaviest-deadlift)
* Untrained adult top speed, 6 to 8 m/s: [trackandfieldapp.com](https://www.trackandfieldapp.com/how-fast-is-the-average-person-in-the-100m/)
* Hunting cheetah top speed, 25.9 m/s: [Wilson et al., Nature 2013](https://www.nature.com/articles/nature12295)
* 100 m world record, average 10.44 m/s and peak 12.3 m/s: [Usain Bolt's 100 m world-record analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC10669785/)
* Average new US vehicle, 1,839 kg (2024): [EPA data summary](https://sellmycarhub.com/guides/average-car-weight/)
* M1A2 tank, about 63 t: [General Dynamics](https://international.gdls.com/english/products/ABRAMS/M1A2.pdf)



## Dice

In Lex, dice stay on the eable, while dice rolls can be automated with the push of a button, the whole point of an RPG is the players' participation in a shared story, through their decision making and dice rolls. 

Lex simply automates the boilerplate, such as conversion math, and stacked effects, allowing seamless universal gameplay.

RPGs have many different dice mechanics, from the classic `d20` roll, to `3d6` (bell curve) rolls, or `d100` probability rolls. Each major gaming system has its own dice rules, and competent GMs regularly modify these rules to fit the needs of their campaign. Lex enbraces this approach which is why dice mechanics are defined in the adapter layer (alongside labels and attribute conversion). So while one adapter uses a classic `d20` to determine if an attack is a hit or miss, another adapter could use `3d6` where a low roll determines a hit.

Under the hood, the Lex engine is tracking effects/constraints, and is doesn't particularly care which dice mechanics determined a hit or miss, Lex just track the result. 

That said, combat bonuses will be adjusted to reflect the dice mechanics, e.g., a +5 to strike on a `d20` will nean the user just needs a 5 or higher to hit, an 80% likelihood. This means a `d100` is a 21 or higher. And likewise a `3d6` low to hit would be a roll of 13 or lower (a similar 80% likelihood).

Every bonus in Lex is stored once on a `d20` scale, where +1 is 5%, and the campaign die converts it.

The GM chooses the system, and can even opt-out of different dice mechanics, for example, skill rolls can be replaced by GM judgment, or attribute rolls can be replaced by a fixed point scale that players to their character as they wish.

The GM sets the campaign's die system, for example `3d6`, `d20`, or `d100`. Every player at that table uses it, and the GM can change it at any time for everyone. A campaign uses one die system for every roll; systems are not mixed by area. Sheet labels may still differ per tablet; the die itself does not. For each of the following areas, the adapter sets how that die is read, or opts the area out:

+ attributes, character creation and per-level increases 
+ hit points and per-level increases
+ anima abd per-level increases
+ combat rolls, such as initiative, and bonuses for striking and dodging
+ skill rolls, or knowledge rolls
+ saving throws

In all cases, the underlying Lex engine does not care which dice mechanics are used on the table, Lex faithfully converts from one to another using a simple probability conversion, and will display rolls like "roll 60 or above" if using a `1d100`, or "roll 12 or above" if using a `1d20`.

Note that some rolls, like weapon damage, are fixed and universal across all games, although where exceptions exist those should be converted to the standard hit point system (one of the few areas most games agree on).



## HUD 

HUD, Heads Up Display, displays Hit Points and Anima and combat stats.
Combined Hit Points: flesh on the left, remaining armor next, depleted on the right. Remainder is a darker same-color fill when the Damage Threshold is greater than 1; hover on that remainder shows the Damage Threshold. Black empty only when you are on base unit hits (threshold 1) and under 100. Hit Points colors are blood red (unit) → orange (deka) → amber (hecto) → gold (kilo and up). Anima is blue. Roster and sheet use the same HUD.


## Species and occupations

Species is what a character is, and exactly one. A human, an elf, a mutant, a dragon. Things with the same name from different sources are different things, shown with their source, such as an elf from one book and an elf from another.

Occupation is what a character does. A soldier, a politician, a wizard.

An occupation is one ordered set of abilities, or several ordered sets side by side. A later set counts only when every set before it is met. The catalog is large, and includes catchalls such as Vagabond. The sheet shows the top two or three. The player can pin one as a reminder of what they are spending toward. The pin does not lock spending.

Abilities are the truth. An ability works as soon as it is bought. Qualifying for an occupation follows from what the character owns. Gaps block the title and do not block the ability. The same purchase can satisfy a requirement on more than one occupation, and it is paid for once. Occupation positions are not added together. A wizard and a scholar are not a single higher number.

Some species have growth that a source book writes as per-level bonuses. That growth is an occupation only that species can advance. The starting body is the first set, so a character who never spends on it stays there. Later sets are bought with experience. A metahuman can spend everything on Mage and leave the species occupation on its first set. The lock runs one way: only that species can advance that occupation, and the species can still advance any other occupation.

Two characters of the same species can have different abilities available. Each carries their own list. A custom species occupation walks that list. The list can be one ordered set, or two or more ordered sets.

An ability can be bought only when its constraints are met. A constraint can require a species, a previous set of an occupation, an ability already owned, or a list written on that character. The campaign can also forbid an ability. The set is made of the abilities you buy. Other abilities can require that set without being part of it.

This is enough to convert characters from point-buy games and from level-based games into the same sheet. A point-buy system with no character level and no occupation level keeps its levels on single traits, and its sheet shows the points and the traits. A leveled occupation shows how far its ordered sets have been met.


## Experience, prices, and loot

The price of an ability is written in the data pack. The GM sets it while preparing data, not during play. Play spends that number.

The GM adds unspent experience after a scene or after play. Each character gets their own amount. The GM decides. An adventure can record a suggested amount, and the GM can ignore it.

A new character's starting unspent experience is in the pack. The player may spend it while creating the character or during play. Creation is not a phase the app locks. Fill the sheet enough for the GM to run, the way a paper sheet is filled in.

The GM decides what loot exists, and the players receive it.

### Rewards

After a fight, Lex can open a reward screen. The GM puts up a stack of items and can type an experience award for each character. Experience is spent later, on the sheet.

One player holds an item at a time. They click to claim it and click again to let go. Someone else who wants it talks with them at the table. The holder can let go, or the GM can assign it. The GM can also start a fight over it. The GM controls the screen and can close it whenever they want. While an item is held, every tablet still shows the full item details.

Items nobody took stay on the ground, unclaimed. The GM can open that stack again. Nothing is discarded and nothing is given away by closing the screen.


## Server and logins

One local web server. The GM and the players are browsers on their own devices. This is not a cloud app and it is not real security.

Login is a username and a password. The password may be blank. The player or the GM can create the login. Usernames are unique. Becoming the GM is an explicit setup or promote step; the first account created is not automatically GM. More than one login may be GM. A tablet is signed in as one login at a time. A shared tablet at the table is just the GM's login; players who use it are handled the same way as players with paper.

The server can hold dozens of campaigns and dozens of adventures. The GM opens one campaign, and one adventure in that campaign is in play. Only one campaign is in play on the server at a time, even when there is more than one GM. Several GMs can co-run the same campaign, and every GM has full control of it. A GM can also play a character in a campaign they run; that character's turn opens the same locked modal as any player's.

A login can have characters in more than one campaign. Before a campaign is open, the tablet lists every character on that login. After the GM opens a campaign, the screen is built around that campaign and one character. The player can switch to another of their characters in the open campaign, and can still open characters from closed campaigns, but those sit further back. In a fight, the modal follows whichever of their characters has the turn. Outside that turn modal they may switch characters freely, including characters not in the fight. The turn modal itself stays locked to the character whose action it is.

The player does not browse campaigns or adventures. They see their characters, and anything the GM has shared.

Players edit their own characters inside the constraints. The GM sees every player character and every non-player character, and can change a non-player character as they see fit. A GM can also directly edit any player character. Ordinary GM edits follow the same constraints and experience costs as a player's. The GM can also always add a power or ability to a character, or add a constraint to one. An owned ability that breaks a constraint stops working until the constraint is removed.

The GM can generate a random non-player character before the game or during it. It is a full character. The pack decides which rolls are used. The GM can edit the result.


## Adventures

An adventure holds locations, stories in prose, maps, and non-player characters, plus any suggested experience, loot, and groups. The GM can edit it during the game. It is enough to run from.

Player characters belong to the campaign and stay as the adventures change.

For any adventure material, the GM can show it or hide it, for every player or for the players they pick. Players do not open the adventure. They see a map, or anything else, only when the GM sends it.


## Lore, ingest, and packs

Lore is prose the engine does not read when resolving the sheet or a fight.

An LLM can work with Lex in two ways: as a skill inside an existing LLM harness, or with Lex acting as the agentic harness itself. A goal is to ingest an entire book and produce a data pack of everything in it: characters, maps, abilities, powers, species, occupations, and so on. The GM drives the LLM. They iterate together on every stat and number, the way a planning session works, and the LLM can recommend stats and numbers based on existing material.

Ingest writes **rows** into `data/packs/` which is ingested into the Lex database; working notes and book links stay in `data/ingest/` (untracked except `data/ingest/README.md`).

During play, sqlite on the server is the live record. Packs are import and export. Characters move between Lex servers through data packs. An exported character can depend on other packs; how dependencies work is later detail. The repo ships only original packs. A pack converted from a copyrighted or licensed game lives only on the local server and is gitignored. It is never committed or published. Ingest notes about a copyrighted game follow the same rule: they stay local and gitignored, not committed to `data/ingest/`. `.gitignore` enforces this: everything under `data/packs/` and `data/ingest/` is ignored except the READMEs and the original `universal` and `u-simplified` packs.
