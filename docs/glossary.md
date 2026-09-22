# Glossary

The following terms are used in the Lex engine, see [universal-system.md](universal-system.md) for details.


**Adapter** -- a presentation layer of a character sheet that is compatible with the Lex universal engine.

**Data Pack** -- parsed characters, classes, equipment, and adapter data that can be loaded into the Lex engine.


**Armor Prefix** or **Damage Prefix** -- SI metric for for scale. Armor is a number, e.g., `75 hA` body armor, and damage is usually a roll, e.g., `3d6 hD`. 
Base units have no prefix; a punch might be `1d6 D` and a leather jacket might offer `25 A`. 
Common prefixes are x10 deka **daA**, x100 hecto **hA**, less common is x1000 kilo **kA**, and above. 

**Scale** -- SI metric scale, e.g., deka x10, hecto x100, kilo x1000. Display and conversion between layers is automatic in Lex, which uses these prefixes.

**Damage Threshold** -- Damage less than the threshold does nothing, fractions and remainder round to 0. Default 1. In the Lex character UI, knight's armor might be `40 dA` with threshold 10: the bar would show `40 dA` plus HP; blows under 10 do nothing to the armor.

**HUD** -- Heads Up Display on the Lex character sheet, showing core stats needed for combat.

**Hit Points** -- The number of damage a character can take. On the HUD this is a stacked bar with armor stacked from left to right (damage applies to the right-most layer) and it is ordered: flesh, then body armor, then magic fields, then psionic fields. On the HUD HP bar, black (empty) is shown only when the remaining band is base (Damage Threshold of 1) and the value is under `100 A`. Color on the HUD HP bar indicates the Damage Threshold: blood red (base, no prefix) through orange (deka), amber (hecto), and so on towards white.

**Armor** -- worn gear (from a leather jacket to a suit of power armor). Typically one body slot, magic and then psionics applied on top.


**Anima** -- numeric capacity for magic and psionics. All living creatures comtain Anima. Adapters can relabel as needed, e.g., U-simplified calls this Stamina. It is rendered with a blue bar on the HUD.


**Actioms** -- the total number of actions (usually attacks) a player can take per 10-second melee.

**Strike** -- the numeric bonus applied to a roll (usually `d20`) to determine if an attack is a hit or a miss.

**Parry / Dodge** -- the numeric bonuses applied to an optional roll (usually a `d20`) after an attack to determone if the attack is parried or dodged. A parry or dodge typically costs one action, although some characters have an automatic parry (from combat training), and some rare classes possess an automatic dodge (a dodge that takes no action).

**Attack** -- a player action attackimg a called target, unarmed (punch or kick) or atmed.

**Magic** — spells, tattoos, or any innate abilities that cost Anima to activate. A magic shield is a spell you turn on, not armor you wear.

**Psionics** -- psychic abilities that cost Anima to activate. A telekinetic field is a power you turn on, not armor you wear.




## Do not use

Soak. Energy (the old gauge name). Body (as the life bar). Unarmed (as a weapon name). Pool. Factor. Fold. Ink, Sigilist. Aegis.
