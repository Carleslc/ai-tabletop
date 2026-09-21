# Prep persistence notes

Use these notes when a CoC session has a provided scenario file, a continuing campaign, multiple NPC teammates, strict character-card requirements, or the user asks to store prep outside chat memory.

Folder and file names below are in English. Write file *contents* (cards, logs, briefings) in the table's language.

## Create a campaign prep folder

When a writable workspace is available, create a durable project folder before or during prep. Prefer the workspace root unless the user specifies another location.

Recommended structure:

```text
campaigns/<scenario-name>/
├── README.md
├── 00_keeper/
│   ├── prep_index.md
│   └── scenario_frame.md
├── 01_source/
│   ├── <scenario>.docx|pdf|txt
│   └── <scenario>.txt
├── 02_player_materials/
│   └── handouts/
├── 03_character_cards/
│   ├── investigator_<name>.md
│   └── npc_teammate_<name>.md
├── 04_session_logs/
│   └── session_log.md
└── 05_rules_and_conventions/
    ├── card_and_play_format.md
    └── style_reference.md
```

Keep player-facing and Keeper-only materials separate. Never expose `00_keeper/` or full `01_source/` content to the player unless that content is explicitly player-facing.

For a solo gamebook, the same layout works: the book goes in `01_source/`, and `04_session_logs/session_log.md` also records the current entry number, visited entries, and flags/codewords.

## Populate the folder

- Copy the original scenario file into `01_source/`.
- Extract text to `01_source/<scenario>.txt` when possible for fast search (e.g. `pdftotext -layout <scenario>.pdf <scenario>.txt`).
- Extract player-facing images/maps/handouts into `02_player_materials/handouts/`; create an index in `00_keeper/prep_index.md`.
- Create `00_keeper/scenario_frame.md` with a spoiler-safe-for-KP framework: major locations, NPCs, timeline/day events, clue gates, handouts, night/dream triggers, hazards, and likely endings. This is a private guardrail, not a player summary.
- Create `05_rules_and_conventions/style_reference.md` when scenario text is available. Record compact, spoiler-safe player-facing style samples or paraphrases for opening tone, location texture, document/object framing, and NPC dialogue cadence.
- Write strict character cards into `03_character_cards/` instead of leaving them only in chat.
- Write current state and stop point into `04_session_logs/session_log.md` after each meaningful scene.
- Write local card requirements and running conventions into `05_rules_and_conventions/card_and_play_format.md`.

If the workspace is a Git repository, check `git status` and recent history before creating files. Do not stage or commit unless the user asks or the workspace instructions require it.

## Build a Keeper scenario frame

Before play, skim the extracted scenario text and create `00_keeper/scenario_frame.md`. Keep it concise and indexed for fast return-to-canon during play:

```markdown
# Scenario frame

## Core structure
- Prologue / opening:
- Daytime real-world investigation:
- Night / dream / otherworld triggers:
- Endings or major branches:

## Location index
- <Location>: source keywords; visible information; hidden information; related NPCs; hazards; obtainable clues.

## NPC index
- <NPC>: public identity; where/when they appear; immediate goal; pressure/fear; attitude to investigators; speech style; what they know; what they won't say; related side threads; sample lines.

## Timeline / events
- Day 1:
- Day 2:
- Day 3:
- Other triggers:

## Player-facing materials / images
- <internal id or name>: when the players can see it; how it's presented in the fiction; file path.

## Style reference
- Opening tone:
- Location description:
- Document / object presentation:
- NPC dialogue:
- Intended player emotions:

## Source search keywords
- <location/NPC/event>: keyword A / keyword B / old name / typos or synonyms.
```

Do not expose this file to the player. Use it to keep pacing and canon aligned.

Keep Keeper-facing labels in private notes. In visible play, never call a clue "Handout 2", "Player Material", or "boxed text". Present it as an in-world object: a folded note, clipping, ledger page, police abstract, diary entry, symbol sketch, photograph, map, or testimony.

## Build module style references

When scenario text is available, skim for player-facing prose before play and record compact style references in `05_rules_and_conventions/style_reference.md`. Prefer passages that are safe to imitate without revealing secrets:

- Opening read-aloud or premise wording.
- Location sensory details such as smell, light, noise, paper texture, architecture, crowd, weather, and silence.
- Handout wording and object presentation, such as how a clipping, letter, diary, or official record looks in the fiction.
- NPC dialogue rhythm, social pressure, and era-specific vocabulary.
- The intended emotional ride for players: curiosity, suspicion, grounded dread, social friction, relief after discoveries, or pressure to act.

Use these references as a voice guide, not as a public quote bank. During play, adapt the style into the current scene and avoid copying Keeper instructions, section titles, labels, or future-scene structure.

## Prepare NPC performance cards

For recurring or scene-important NPCs, prepare a compact private performance card before play or before their first scene:

```markdown
## <NPC name>
- Public role:
- Scene function:
- Immediate want:
- Pressure/fear:
- Attitude to investigators:
- Speech style:
- Knows:
- Withholds/does not know:
- Emotional use:
- Sample lines:
```

Use these cards to make NPC dialogue distinct and emotionally useful. A nervous landlord, bored editor, proud archivist, frightened witness, and street gossip should not sound interchangeable. Keep sample lines spoiler-safe unless they are stored in Keeper-only notes.

## Create a spoiler-free player briefing

Before character creation, create or present a spoiler-free briefing. It may live in `05_rules_and_conventions/briefing.md` or the visible setup response.

Include:

- Scenario title, rule edition, era, and tone.
- Non-spoiler premise: what brings the investigator into the story.
- Recommended real player count and recommended AI PC teammate count.
- Recommended skills and why they are useful in broad terms, not exact clue gates.
- Character concept guidance: fitting occupations, emotional hooks, relationships, wounds, or reasons to investigate.
- Team coverage suggestions: one social/investigation lead, one medical/practical support, one local culture/research support, etc.
- Content notes and table preferences when relevant.

Do not include hidden truth, monster identity, exact ending conditions, scripted betrayals, future scene secrets, stat blocks, or route solutions.

## Search-before-scene rule

When the player chooses a location, NPC, clue, or keyword from a provided scenario, return to the extracted scenario text before narrating if there is any chance the scene has canon details.

Use fuzzy local search, not memory:

```bash
rg -n -i "keyword1|keyword2|old name|synonym" "01_source/<scenario>.txt"
sed -n '<start>,<end>p' "01_source/<scenario>.txt"
```

Search in the scenario's own language (a Spanish PDF needs Spanish keywords, even if the table plays in English).

Examples:

- Player goes to a location: search the location name, alternate names, nearby landmarks, and scene title.
- Player asks about an NPC: search the NPC name, family names, job titles, and fixed refresh/location notes.
- Player enters night/dream/rest: search dream, night, otherworld, event/day triggers, and current hotel/location.
- Player inspects a document/image/object: search internal handout title, caption, media index, visible text, and the in-world object name.
- Solo gamebook: search the entry number as it's formatted in the book (e.g. `^\s*123\b`).

After reading the passage, adapt it to the current table state:

- Preserve canon facts, NPC positions, hazards, and clue gates.
- Change surface framing only when needed to respect player choices.
- If the player created a new approach, map it onto the closest canon scene rather than inventing a disconnected scene.
- If you intentionally diverge, record the divergence and reason in `session_log.md`.

## Scene-drift audit

After each major scene, update the log with:

- Canon source used: searched terms or rough source passage.
- What was revealed.
- What remains hidden.
- Any deliberate deviation from the module.

If a session has drifted for several scenes without touching a prepared location, NPC, clue gate, night/dream trigger, or timeline event, actively offer or narratively surface the next module-relevant hook.

## Narrative steering without railroading

The KP owns pacing and scenario integrity. The player owns their character's choices. When the player wanders, jokes, delays, or follows a side idea, do not simply abandon the module spine. Use soft in-world pressure to bring the table back:

- Let time pass and advance the module timeline.
- Have prepared NPCs move, call, disappear, refuse access, request help, or create consequences.
- Surface a clue through environment, handout, dream, news, official process, or overheard talk.
- Close unproductive loops with a clear result, then point the scene toward a prepared lead.
- Use night/rest/dream triggers proactively when the module expects them.
- Let risky off-route actions produce costs or partial information rather than creating a new unrelated plot.
- Say out of character only when needed: "KP note: this seems outside the scenario spine; I can resolve it briefly and move us back."

Do not force a single solution, teleport the PC without cause, or negate reasonable player plans. Redirect through believable fiction and consequences.

## Strict investigator-card template

Use this shape for player investigators (translate the field labels into the table's language):

```markdown
# Investigator: <name>

Sex/gender:
Age:
Occupation:
Education:
Residence:
Birthplace:
Current date/time:
Credit Rating: <number>, <lifestyle description>

## Short background story

<coherent growth history and reason to enter the case>

## Characteristics

STR
CON
SIZ
DEX
APP
INT
POW
EDU
Total:

HP
MP
SAN
Luck
MOV
Damage bonus, Build

## Skills

<10-14 skills with percentages, including Language (Own) when appropriate>

## Possessions

<scenario-relevant carried items>

## Backstory

Personal description / appearance:
Ideology / beliefs:
Significant people:
Meaningful locations:
Treasured possessions:
Traits:
Injuries & scars / phobias & manias / secrets:

Key Connection ★: <mark one of the entries above; losing it costs 1/1D6 SAN, and the Keeper may not destroy it without giving the player a roll to save it>
```

Omit optional background entries only when they truly do not fit, not for brevity.

## NPC teammate-card template

Use this shape for recurring NPC teammates:

```markdown
# NPC teammate: <name>

Sex/gender:
Age:
Occupation / current status:
Education:
Residence:
Birthplace:
Credit Rating: <number>, <lifestyle description>

## How they enter the case & relationships

<how they enter the case; relationship to PC and other teammates>

## Appearance

<player-facing first impression>

## Short background story

<coherent growth history, skills, beliefs, and reason to join>

## Characteristics

STR
CON
SIZ
DEX
APP
INT
POW
EDU
Total:

HP
MP
SAN
Luck
MOV
Damage bonus, Build

## Skills

<8-12 relevant skills, including Language (Own) and Credit Rating>

## Possessions

<items likely to matter in scenes or checks>

## Backstory

Ideology / beliefs:
Significant person / meaningful location:
Treasured possession:
Trait:
Weakness:
Key Connection ★: <mark one>
```

NPC teammates may exceed or fall short of PC point-buy totals, but their values should stay ordinary unless the scenario justifies otherwise.

## Session log template

Update `04_session_logs/session_log.md` after each scene, before long pauses, and whenever HP/SAN/Luck/resources or clue state changes:

```markdown
## Current stop point

<where play should resume; include the exact last prompt or scene beat (solo gamebook: current entry number)>

## Clues found

<player-facing clues only>

## Open leads

<known leads the investigators can pursue>

## Status

- PC: HP / SAN / Luck / notable resources
- NPC: HP / SAN / Luck / notable resources

## NPC attitudes

<brief relationship and attitude notes>
```

Keep the log spoiler-safe from the player's perspective unless it is stored under `00_keeper/`.
