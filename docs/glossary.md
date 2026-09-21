# Glossary

Lex terms. Use these words. Do not invent replacements, and do not bring back names we dropped.

The rules they sit in are [universal-system.md](universal-system.md).

## Engine

**Fold** — Character JSON plus adapter JSON become a sheet. Combat reads the sheet. The browser does not invent numbers.

**Adapter** — A sheet language. Universal and U-simplified are adapters. An adapter relabels and hides. It is not a second combat system.

**Pack** — A directory of characters, classes, and adapter data. Packs load together. They are not exclusive.

**Universal** — The native sheet: nine attributes, full combat scores, prefixes, Anima.

**U-simplified** — The six-score sheet of the same character. Stamina is Anima. Same combat sequence as Universal.

## Harm

**Prefix** — SI nickname for scale: unit **A** / **D**, deka **daA**, hecto **hA**, kilo **kA**, and so on. Always print a space: `800 hA`. Dice are the roll only. `4d6×10 hD` is `4d6 kD`. Do not write ×10 on the dice.

**Factor** — SI scale versus unit: deka 10, hecto 100, kilo 1000. Display and conversion between layers use these prefixes only.

**Threshold** — Minimum damage, in that layer’s units, that counts. Default 1. Mora’s field is 40 A with threshold 6: the bar is still 40 A plus body A; blows under 6 do nothing to the field. Color follows the SI prefix (unit is red). Dim remainder (not black) means the remaining band still bounces weak blows. Hover names the threshold.

**Conversion** — Each hit is turned into the target’s prefix and truncated toward zero. If the result is below that layer’s threshold, it is 0. Remainders are not saved.

**Hit Points** — Remaining hits. On the HUD this is one bar: armor layers plus flesh. Flesh on the left, remaining armor next, depleted on the right. Black empty only when the remaining band is unit and threshold 1 and the bar is under 100 of the displayed prefix. Color is blood red (unit) through orange (deka), amber (hecto), gold (kilo and up).

**Armor** — Worn gear (plate, a siege suit). One body slot. Not a spell, tattoo, or psionic ability.

**Anima** — One spendable capacity for hard effort, spells, and psionics. Universal prints Anima. U-simplified prints Stamina. Same gauge. Blue bar. Not hit points. Not a second magic battery.

## Combat

**Channel** — Combat scores: Actions, Attack, Parry, Dodge, Block, Initiative.

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

Soak. Energy (the old gauge name). Body (as the life bar). Unarmed (as a weapon name). Pool. Dice multipliers that duplicate a prefix (`×10 hD`). A static “hard to hit because of armor” number.
