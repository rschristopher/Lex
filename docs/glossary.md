# Glossary

The following terms are ussd in the Lex engine rules, defined in [universal-system.md](universal-system.md).


**Fold** -- a function that takes all character effects and constraints and outputs a character sheet (exact stats and attributes).

**Adapter** -- a presentation layer of a character sheet that is compatible with the Lex universal engine.

**Data Pack** -- parsed characters, classes, equipment, and adapter data that can be loaded into the Lex engine.


**Armor Prefix** or **Damage Prefix** -- SI metric for for scale. Armor is usually a number, e.g., `75 hA` body armor, and damage is a usually a roll, `3d6 hD`. Base units have no prefix, a punch might be `1d6 D` and a leather hackey might offer `25 A`. Common prefixes are deka **daA**, hecto **hA**, kilo **kA**, and so on. Always print a space: `800 hA`. Dice rolls rarely need multipliers. `4d6×10 hD` is `4d6 kD`. Do not write ×10 on the dice when a prefix is available.

**Scale** -- SI metric scale, e.g., deka x10, hecto x100, kilo x1000. Display and conversion between layers is automatic in Lex, which uses these prefixes.

**Damage Threshold** -- Minimum damage, in that layer’s units. Damage less than the threshold does nothing, fractions and remainder round to 0. Default 1. In the Lex character UI, a leather armor might be `40 A` with threshold 6: the bar would show `40 A` plus HP; blows under 6 do nothing to the armor. Color follows the SI prefix (base HP is red). Dim remainder (not black) means the remaining band still has a damage threshold. Hover over the dim part of the bar identifies the threshold.

**HUD** -- Heads Up Display on the Lex character sheet, shows core stats needed for combat.

**Hit Points** -- The number of damage a character can take. On the HUD this is a stacked bar with armor stacked from left to right (damage applies to the right-most layer) and it is ordered: flesh, body armor, magic fields, psionic fields). On the HUD HP bar we see black (empty) only when the remaining band is base (Damage Threshold of 1) and the value is under `100 A`. Color on the HUD HP bar indicates the Damage Threshold: blood red (base, no prefix) through orange (deka), amber (hecto), and so on towards white.

**Armor** -- Worn gear (from a leather jacket to a suit of power armor). Typically one body slot, magic and then psionics applied on top.


**Anima** — One spendable capacity for hard effort, spells, and psionics. Universal prints Anima. U-simplified prints Stamina. Same gauge. Blue bar. Not hit points. Not a second magic battery.

## Combat

**Strike** — The attacker’s roll (the Attack channel).

**Parry / Dodge** — The optional roll after a strike. One attempt. Fail and you were hit. Automatic dodge is still dodge; it does not cost an action.

**Activated** — What is on now (suit, shield, field, warding tattoo). Play state.

**Attack** — The one strike in hand (gun, punch, fire bolt, coil tattoo).

**Punch / Kick** — Unarmed attacks. Not a row named Unarmed. A worn chassis may replace them with hecto fists while it is on.

**Segment** — One slice of the Hit Points bar. Hover names it.

**Hit order** — Adapter list of which layer is hit first. Default: psionic, then spell, then tattoo, then body.

**Scale** — HUD dropdown next to View. Auto, or force A / daA / hA / kA / …. Display only. Conversion does not change.

## Sheet groups

**Magic** — Spells. A magic shield is a spell you turn on, not armor you wear.

**Psionics** — Psychic abilities. A telekinetic field is a power you turn on, not armor.

**Magic tattoos** — Ink on the skin. Sigilist is personal (**A**). Aegis is war-scale (**hA**).

## Do not use

Soak. Energy (the old gauge name). Body (as the life bar). Unarmed (as a weapon name). Pool. Factor. 
