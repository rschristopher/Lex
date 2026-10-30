# Glossary

The following terms are used in the Lex engine, see [universal-system.md](universal-system.md) for details. Keep these entries in alphabetical order.


**Actions** -- the total number of actions (usually attacks) a player can take per 10-second melee.

**Adapter** -- a presentation layer of a character sheet that is compatible with the Lex universal engine. Adapters provide labels, attribute conversions, and dice math. The decision of whether to use a classic `d20` roll where a high roll is a hit, or a `3d6` roll where a low roll is a hit, is defined in the adapter. Lex simply converts to/from the universal engine, giving the GM full control, and dice stay on the table.

**Adventure** -- locations, stories, maps, and non-player characters for one story, plus any suggested experience, loot, and groups. Adventures live in a campaign. See [decisions.md](decisions.md).

**Anima** -- numeric capacity for magic and psionics. All living creatures contain Anima. Adapters can relabel as needed, e.g., U-simplified calls this Stamina. It is rendered with a blue bar on the HUD.

**Armor** -- worn gear (from a leather jacket to a suit of power armor). Typically one body slot, magic and then psionics applied on top.

**Armor Prefix** or **Damage Prefix** -- SI metric for scale. Armor is a number, e.g., `75 hA` body armor, and damage is usually a roll, e.g., `3d6 hD`.
Base units have no prefix; a punch might be `1d6 D` and a leather jacket might offer `25 A`.
Common prefixes are x10 deka **dA**, x100 hecto **hA**, less common is x1000 kilo **kA**, and above.

**Attack** -- a player action attacking a called target, unarmed (punch or kick) or armed.

**Campaign** -- the container for player characters and adventures. One campaign is open at a time. See [decisions.md](decisions.md).

**Damage Threshold** -- Damage less than the threshold does nothing, fractions and remainder round to 0. Default 1. In the Lex character UI, knight's armor might be `40 dA` with threshold 10: the bar would show `40 dA` plus HP; blows under 10 do nothing to the armor.

**Data Pack** -- parsed characters, species, occupations, equipment, and adapter data that can be loaded into the Lex engine. The GM sets ability prices and starting experience here, before play.

**Experience** -- total, spent, and unspent. Any two fix the third. Unspent is what the player saves or spends. The GM adds it per character after a scene.

**Group** -- a list the GM makes to see who is together. A fight is two or more groups. During a fight a character is in only one of those groups.

**Hit Points** -- The number of damage a character can take. On the HUD this is a stacked bar with armor stacked from left to right (damage applies to the right-most layer) and it is ordered: flesh, then body armor, then magic fields, then psionic fields. On the HUD HP bar, black (empty) is shown only when the remaining band is base (Damage Threshold of 1) and the value is under `100 A`. Color on the HUD HP bar indicates the Damage Threshold: blood red (base, no prefix) through orange (deka), amber (hecto), and so on towards white.

**HUD** -- Heads Up Display on the Lex character sheet, showing core stats needed for combat.

**Magic** — spells, tattoos, or any innate abilities that cost Anima to activate. A magic shield is a spell you turn on, not armor you wear.

**Occupation** -- what the character does. A soldier, a politician, a wizard. Species is a separate fact. This is not Armor Class.

**Parry / Dodge** -- the numeric bonuses applied to an optional roll (usually a `d20`) after an attack to determine if the attack is parried or dodged. A parry or dodge typically costs one action, although some characters have an automatic parry (from combat training), and some fighting skills, occupations, and species grant a reflex dodge (a dodge that takes no action).

**Psionics** -- psychic abilities that cost Anima to activate. A telekinetic field is a power you turn on, not armor you wear.

**Scale** -- SI metric scale, e.g., deka x10, hecto x100, kilo x1000. Display and conversion between layers is automatic in Lex, which uses these prefixes.

**Species** -- what the character is, and exactly one. A human, an elf, a mutant, a dragon. Occupation is a separate fact.

**Strike** -- the numeric bonus applied to a roll (usually `d20`) to determine if an attack is a hit or a miss.


## Do not use

NO JARGON!

Do not use the following in the Lex engine: Aegis, Ancestry (use Species), Body (as the life bar), Class (use Occupation), Energy (as a gauge name), Factor, Fold, Ink, Pool, Sigilist, Soak, Unarmed (as a weapon name).
