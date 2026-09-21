# The Lex universal system

Terms are in [glossary.md](glossary.md). Use those words.

Lex is a complete, playable RPG system. Characters, combat, armor, and damage are defined here. Other games are not separate engines. They are **adapters**: JSON that relabels, subsets, and derives a sheet from the same Lex character.

Dice stay on the table. The app is a roster and a sheet.

**Packs are not exclusive.** Load as many as you want. Characters, classes, and lore from every pack sit in one campaign. Every adapter with `"view": true` is a sheet language for that same campaign. Each player picks an adapter; the engine does not change.

## What has to be true

1. **One harm dimension.** Weapon damage, armor hits, and hit points are the same kind of quantity.
2. **Every quantity has a factor** relative to a reference unit of 1. The factor is any positive number (1, 42, 100, 1 000 000, …).
3. **A hit is converted into the target’s factor, then truncated toward zero.** If the result is less than 1, the hit is 0. Remainders are not saved for later. Infinite weak blows never chew through a much larger factor.
4. **Armor never modifies hit or miss.** A tank is easy to land on and ignores weak blows. A flyer is hard to land on. Suit thickness is not a dodge.
5. **Attributes, armor, hit points, anima, and combat scores are open lists.** A character keeps every score they have. An adapter chooses what to print and how to label it.
6. **Fold is character + adapter → sheet.** Adapter identity is never a Python branch. Formulas live in adapter JSON (`from`, `mod`, `terms`).
7. **Worn gear may change attributes.** `mod` adds; `set` replaces while worn. A siege suit that *is* P.S. 30 / 60 mph uses `set`, not a small add. Taking it off restores the person. The sheet paints a changed score green.
8. **Punch and kick are attacks, not a row called Unarmed.** Out of a suit they are unit. A worn chassis that lists `attacks` replaces those while it is on: the suit’s fist is hecto, because the metal is what lands. Taking the suit off restores the person’s punch.
9. **Worn armor and powers are different things.** Plate and a siege suit live under Armor and use the body slot. A telekinetic field is a psionic ability; a magic shield is a spell. You turn those **on**, you do not wear them. If a turned-on power has hits, fold puts a slice on the one armor bar. Hit order comes from adapter `hit_order` (default: psionic, then spell, then body).
10. **The sheet is fold output.** Combat later reads `activated`, `attack`, `defense.segments`, and `using`. The UI does not invent layers the fold did not emit.
11. **HUD is Hit Points and Anima.** Combined Hit Points: flesh on the left, remaining armor next, depleted on the right. Remainder is a darker same-color fill when the displayed factor is greater than 1; hover on that remainder names the damage threshold. Black empty only when you are on base unit hits (threshold 1) and under 100. Hit Points colors are blood red (unit) → orange (deka) → amber (hecto) → gold (kilo and up). Anima is blue. Anima is HUD only. Roster and sheet use the same HUD. Print `800 hA` with a space. Scale sits next to View.

## Harm

Call the reference **unit**. A blow of `4d6` at factor 1 is `4d6 D`. Armor or hit points of 32 at factor 1 is `32 A`. **D** is damage; **A** is hits remaining (the suit or the person).

**Prefixes are notation**, not mechanics. They are the SI multipliers, used because armor and damage in this system routinely leave the 1–20 range:

| Prefix | Factor | Damage | Armor |
|--------|--------|--------|--------|
| centi  | 10⁻²   | cD     | cA     |
| deci   | 10⁻¹   | dD     | dA     |
| (none) | 1      | D      | A      |
| deka   | 10     | daD    | daA    |
| hecto  | 100    | hD     | hA     |
| kilo   | 1 000  | kD     | kA     |
| mega   | 10⁶    | MgD    | MgA    |
| giga   | 10⁹    | GD     | GA     |
| tera   | 10¹²   | TD     | TA     |

Do not write `×10` or `×100` on the dice. That is the next prefix: `4d6x10 hD` is `4d6 kD`. `42 A` is `4.2 daA`. Prefixes exist so a sheet can say `770 hA` instead of `77 000 A`.

### Per-hit conversion

```
points = trunc(amount × attack_factor / target_factor)
if abs(points) < 1: points = 0
```

A club at factor 1 against armor at factor 100 is 0, every time. A hecto weapon against unit flesh is ×100 into hit points. A kilo blow against mega armor is 0.

This is not a miss. The rock hit the tank. It did not matter.

## Combat sequence

1. **Strike.** Attacker rolls (Attack). A very low roll misses even a tank.
2. **Optional: parry or dodge, once.** Defender picks **one** roll after the strike (parry *or* dodge, not both, not two dodges). Same question as hit/miss: did it land? Fail means it landed. You do not get a second dodge because the first one was automatic. Automatic only means that **one** dodge did not cost an action. Armor is not in this roll.
3. **If it landed: damage.** Roll the weapon.
4. **Convert** into the target’s factor. Truncate toward zero. Less than 1 is 0.
5. Remaining points come off the outer layer first (a field, then the suit), then hit points.
6. A roll that reduces damage *after* a hit is an effect, not a score on the sheet.

Do not put armor on the hit/miss roll. A steel box is easy to land on. Weak blows fail conversion, they are not misses.

## U-simplified is a sheet language, not a second engine

Same character as Universal. Six scores plus the same combat sequence. Adapter: `data/packs/u-simplified/adapter.json`. Fold does not know the name.

| On the sheet | From the character |
|---|---|
| Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma | strength, agility, endurance, intellect, awareness, presence. Modifier `(score − 10) / 2` floored. |
| Hit points | hit points gauge |
| Stamina | anima gauge, relabeled |
| Attack, Parry, Dodge, Block (if any), Initiative, Actions | those channels. Initiative also adds the Dexterity modifier. Dodge may be marked automatic (does not cost an action). |
| Skills, Weapons, Armor, Coin | groups + purse. Armor *items* still print `hA` / `A`. Weapons still print `hD` / `D`. |

Hidden on this sheet (still on the character): speed, will, appearance; the armor *hits* gauge. Armor hits still exist; they are not a strike target.

Speed, will, and appearance stay on the Universal sheet. They have no sixth-score slot.

## Prefixes stay. Do not expand.

A `770 hA` suit printed as `77 000` on a 10–400 hit-points sheet is noise. Keep SI prefixes on damage and armor in every adapter, including U-simplified. Print `770 hA` and `4d6 kD`. Conversion still zeros a `D` stick against `hA`.

If another game’s heavy harm is 100:1 (or 42:1, or 1 000:1), that split **is** a factor. Put those numbers at that factor. Do not invent a second harm dimension.

The universal sheet is the full character: nine attributes, Actions / Attack / Parry / Dodge / Block / Initiative, armor hits, powers, hit points, anima, gear, coin. An adapter hides, relabels, or derives. It does not shrink the entity.

## Anima

One pool. Sprinting, a spell, and a telekinetic field spend the same gauge. Adept and Sensitive are how they spend it, not a second number. Universal prints **Anima**. U-simplified prints **Stamina** from the same gauge (`from: anima`). No prefix: it is not damage.

## Classes and lore

Classes are mechanical packages (effects and constraints). Collapse occupational variants into kits. Ancestry/species is a separate axis. Lore is prose the fold does not read. Ingest writes **rows** into `data/packs/`; working notes and book links stay in `data/ingest/` (untracked except `data/ingest/README.md`).
