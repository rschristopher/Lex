# Plan

What is still open in Lex. Settled rules are in [universal-system.md](universal-system.md); terms are in [glossary.md](glossary.md).

## Next

- Attributes, one at a time: Awareness, Presence, and Appearance are still proposals in the [attribute table](universal-system.md#attribute-table).
- The u-simplified adapter's Strength modifier conflicts with the Strength scale: Syrn's Strength 43 shows +16.
- Safe fall: whether a successful roll halves fall damage above the safe height is still proposed ([Safe fall](universal-system.md#safe-fall)).

## Open questions

**How is a check bonus computed?**
A check compares a score with a difficulty. For a lift, the difficulty is the Strength whose lift equals the mass. Below 30 the same difference in points is a different ratio at different scores: 10 against 20 is ×2, and 25 against 30 is ×1.2.
One proposal: the bonus is 10 × log10 of the ratio of the two measures, rounded. Above 30 it is twice the difference in score. A bonus of +3 is about twice what the task needs at any score. On a `d20` the target is 10 minus the bonus, as in [Dice](universal-system.md#dice). At +9 or more the check always succeeds. At −11 or less it always fails.

| Bonus | Chance | `d20` | `3d6` | `d100` |
|---|---|---|---|---|
| −3 | 40% | 13 or higher | 9 or lower | 61 or higher |
| 0 | 55% | 10 or higher | 10 or lower | 46 or higher |
| +1 | 60% | 9 or higher | 11 or lower | 41 or higher |
| +5 | 80% | 5 or higher | 13 or lower | 21 or higher |

* A Strength 21 soldier (126 kg) lifts a 100 kg crate. The difficulty is 17 and the bonus is +1.
* Strength 15 arm-wrestles Strength 30. The bonus is −3.
* A Strength 38 power armor flips a 1.8 t car. The difficulty is 35 and the bonus is +6.
* A Strength 43 dragon drags a 63 t tank. The difficulty is 43 and the bonus is +1.

**What makes two humans of the same mass have different flesh hit points?**

**Do flesh hit points grow with experience?**

**Does Lex need a knock-out track separate from flesh hit points?**

**How do two unitless scores above 30 compare in a check?**

**When two species meet, whose standard sets Appearance?**

**How is a contest between two characters at 100 settled?**

**How are creatures below 1 shown?** A kitten or an insect lifts less than 6 kg, and the damage prefixes already go down to deci and centi.

**How does the Willpower resist bonus scale?** Does it use the Agility and Intellect formula, and how does it rise from 30 to immunity at 100?

**How is a spell's or power's own bonus rated, and what bonus is mastery, which never fails?**

**How does Willpower set the size of Anima?**
Proposal: base Anima equals Willpower in `M`, so Willpower 12 gives `12 M`, as in the non-caster example in [Anima](universal-system.md#anima).

**How do abilities grow Anima per level?**
Proposal: a caster ability names a multiplier, and each level adds Willpower × that multiplier in `M`; Willpower 20 with ×10 gains `200 M` a level. Adapters pick the multiplier to match other systems' per-level amounts.

**How does Willpower set Anima recovery?**
