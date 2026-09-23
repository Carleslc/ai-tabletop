# Rules reference (load on demand)

Read this the moment play enters a rules-dense situation: **combat starts**, a
**sanity loss / madness** triggers, an **opposed contest** is needed, or a player
**pushes a roll**. Do not load it for ordinary investigation — the always-on micro-rules
in `SKILL.md` (Dice and checks section) cover routine single checks. Resolve fast and in fiction;
report results compactly with `scripts/roll.py`.

All values below are CoC 7e (this rulebook). For weapon damage and monster specials,
use the weapon table / module stat block, not memory. The full rules, weapon tables, and
monster stats are in `assets/CoC/` — see `library.md` for where each chapter starts.

---

## Opposed checks

Use for PC-vs-PC, PC-vs-NPC active resistance, and as the standard for melee. Outside
combat, prefer a plain difficulty level; only use opposed rolls when both sides actively
strive and the drama warrants it.

- Both sides declare mutually exclusive goals, each picks a skill or characteristic
  (need not match; Keeper approves).
- Both roll d100, get a success level. **Higher success level wins.** Tie → higher
  skill/characteristic value wins; still tied → stalemate or both reroll.
- Success-level order: Critical > Extreme > Hard > Regular > Failure/Fumble.
- **Opposed checks cannot be pushed.**

## Difficulty levels

Keeper sets difficulty by how hard the task is, against the roller's own value:
- Regular: roll ≤ value. Hard: roll ≤ ½ value. Extreme: roll ≤ ⅕ value.
- Set difficulty from the situation *before* rolling; do not also stack bonus/penalty
  dice on top except as a rare special case.

**Against a living opponent**: derive difficulty from their relevant skill/attribute —
< 50 → Regular; ≥ 50 → Hard; ≥ 90 → Extreme. (Also in SKILL.md always-on layer.)

## Combined skill checks

When a task simultaneously requires two skills (e.g. a device that is both mechanical
and electrical), roll **once** and compare the single result to each skill separately.
Keeper decides in advance whether *all* must succeed or *any one* is enough.

Do not ask for two separate rolls — a single roll maintains the correct probability.
Example: Mechanical 10% and Electrical 10% → a single roll gives 10% chance of passing
both, instead of 1% if rolled separately.

## Skill level benchmarks

Use to judge whether a skill value makes sense for a character concept, and for quick
NPC stat creation:

| Skill value | Level | Meaning |
|---|---|---|
| 01-05% | Novice | Complete layperson |
| 06-19% | Neophyte | Rudimentary knowledge |
| 20-49% | Amateur | Hobbyist level |
| 50-74% | Professional | Can make a living from it; bachelor's-degree level |
| 75-89% | Expert | Master's/doctorate level |
| 90%+ | Master | Among the world's best in the field |

A 50% skill is the professional threshold — enough to make a living from it.

## Bonus / penalty dice

Only for a **significant** advantage or disadvantage — if a factor is worth just a few
percent, ignore it (light rain = nothing; blinding downpour = penalty die). Mechanics:
- Roll one **extra tens die** alongside the normal d100. Bonus die → keep the better
  (usually lower) tens result; penalty die → keep the worse (usually higher).
- **One bonus and one penalty cancel.** Normally at most one; in extreme cases two.
- Prefer bonus/penalty dice over ad-hoc % modifiers.
- Roll them with `scripts/roll.py check <value> --bonus N` or `--penalty N`: it shows every tens die.

## Pushing a roll

When a normal check fails, the player may push by **committing harder / a new in-fiction
approach** ("I tear the whole drawer out", "I stake my reputation on it"). Reroll once.
- A **failed pushed roll brings a real, escalated consequence** — not just "nothing
  happens." That is the price of pushing; narrate it.
- Cannot push opposed checks, combat attack/defense rolls, or sanity checks.

## Luck checks & clues (don't gate the spine)

- If an outcome depends on **environment/chance rather than the PC's action**, use a
  **Luck check**, not a skill (is a cab passing at 2am? does the shop stock the item?).
- **Never gate a critical/plot-advancing clue behind a roll.** Hand core (overt) clues
  to anyone who looks; reserve rolls for *extra* detail or hidden bonuses. Describe the
  evidence and let players infer — don't explain the conclusion.
- **Idea roll** to unstick a stalled table: success → the lead resurfaces
  cleanly; failure → it surfaces but at a cost (lost time, a worse position).

---

## Combat

Only enter the combat round once blows are committed. Surprise first if applicable.

**Surprise / first strike:** an unexpected attacker should get their hit before the
combat round (don't bury them at the bottom of DEX order). Defender may get a Listen/
Spot/Psychology check (vs attacker's Stealth) to be ready. If unready: melee can be
auto-hit (except fumble) or attacker gets a bonus die; ranged always still rolls.

**Round order:** act in **DEX order, high to low.** Each combatant gets one action on
their turn (attack, maneuver, flee, take cover, etc.).

**Attack & defense:** the attacker rolls their Fighting/Firearms skill; for melee the
**defender chooses to dodge or fight back**, resolved as an opposed check.
- **Dodge:** defender's Dodge vs attacker's Fighting; defender wins/ties → avoids.
- **Fight back:** defender's Fighting vs attacker's Fighting; whoever wins deals damage.
- **Firearms:** a target cannot "fight back" against a gun and normally cannot dodge a
  bullet except by **diving for cover** (then prone/out of position). Point-blank,
  range, and cover shift the shooter's difficulty instead.

**Outnumbered:** once a character has dodged or fought back once in a round, every
further melee attack against them that round gets a **bonus die.**

**Maneuvers (disarm, grapple, shove, knock down):** compare **Build**. Per
size step the target is larger, the user takes a penalty die (max 2); 3+ steps larger →
impossible. Resolve like an attack (opposed dodge/fight-back); success applies the
effect instead of (or with) damage. A maneuver needs a concrete stated objective, not
just an action.

**Damage:** roll the weapon's damage; add **damage bonus (DB)** for relevant melee/
unarmed. A successful fight-back means the winner deals their damage.

**Major wound:** a single hit dealing **≥ half the target's max HP** is a major
wound → target makes a **CON check**; fail → knocked prone/unconscious. At **0 HP** the
character is dying — First Aid stabilizes; otherwise track the dying rules.

---

## Sanity & madness

**Sanity check:** loss is written **X/Y** (e.g. 0/1D6). Roll 1D100 vs **current** SAN;
success → lose X, failure → lose Y. A fumbled SAN check loses the max possible. One SAN
check per *encounter*, not per monster.

**Max SAN = 99 − Cthulhu Mythos skill.** When Mythos rises, drop max SAN by the same amount.

**Triggers into madness:**
- **Lose 5+ SAN in one go** → the player makes an **INT check**. *Pass* = they grasp the
  horror → **temporary insanity**. *Fail* = they repress it, no insanity this time.
  (Note: here passing INT is the *bad* outcome.)
- **Lose ≥ 1/5 of current SAN within one game-day** → **indefinite insanity** (lasts
  until treated/recovered; a game-day usually ends at safe rest).
- **SAN reaches 0** → **permanent insanity**; the PC leaves play.

Temporary insanity lasts **1D10 hours**; indefinite insanity, much longer. Both begin
with a **bout of madness (phase 1)**, then an underlying-insanity period (phase 2).

### Bout of madness — duration & control

Run the bout **per the rulebook**: during it the PC is **under Keeper control** — narrate
their mad actions (or hand the player a madness prompt to play out). Two forms:

- **Real-time:** use when other investigators are present (or Keeper wants it
  beat-by-beat even if alone). **The bout lasts 1D10 combat rounds.** Roll **1D10 on
  Table VII** (or pick a fitting result). Most entries themselves last 1D10 rounds. This
  is the answer to "how many rounds": **1D10 rounds.**
- **Summary:** use when the PC is alone, or everyone present goes mad at once.
  Fast-forward and narrate the aftermath; the PC is lost to madness for **1D10 hours**
  (or Keeper's call). Roll **1D10 on Table VIII.** If another PC encounters them before it
  ends, hand control back and play it out.

**Table VII (Bouts of Madness — Real Time, 1D10, each ~1D10 rounds):** 1 Amnesia /
2 Psychosomatic disability (blindness, deafness, loss of use of limbs) / 3 Violence
(lashes out indiscriminately) / 4 Paranoia / 5 Significant person (mistakes someone for
their significant person) / 6 Faint / 7 Flee in panic / 8 Physical hysterics or
emotional outburst / 9 Phobia (roll Table IX) / 10 Mania (roll Table X).

**Table VIII (Bouts of Madness — Summary, 1D10, ~1D10 hours):** 1 Amnesia / 2 Robbed
(Luck roll per valuable item, everything else is lost) / 3 Battered (HP halved, not a
major wound) / 4 Violence / 5 Ideology/beliefs (acts on them in an extreme way) /
6 Significant people (rushes to them) / 7 Institutionalized (asylum or jail cell) /
8 Flee in panic (wakes up far away) / 9 Phobia (new phobia, Table IX) / 10 Mania (new
mania, Table X).

A "Phobia/Mania" result installs a new **phobia/mania** (Table IX/X — roll d100 or Keeper
picks). After the bout, the PC enters phase-2 underlying insanity and is prone to further
bouts under stress until recovered.

**Safety override:** running the bout per RAW does **not** override the skill's Safety &
consent rules — still fade to black for sexual violence/torture, and avoid forcing
irreversible harm onto *another player's* PC without a check or consent. Within those
limits, play the madness straight.
