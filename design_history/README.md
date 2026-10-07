# Design history

A viewing aid: **how each character looked over time, and which model drew each
look.** It makes progression sheets such as "Alice, May to October".

## Why this is walled off

An old design is not an authority. A retired drawing that sits in the tree
becomes something to import, to "just fix", or to keep in step. So this tool
keeps four promises:

1. **No old code or art enters the tree.** An era is a commit id in
   `lineages.yaml`. Nothing else about it is stored.
2. **Pixels are made on demand by that commit's own code.** The tool checks the
   commit out in a scratch worktree outside the repository, runs the renderer
   that existed then, and keeps the still in an ignored cache
   (`~/.cache/ambition-design-history`, or `$AMBITION_DESIGN_HISTORY_CACHE`).
3. **Nothing in `ambition_sprite2d_renderer` imports this package**, and
   `pyproject.toml` does not package it. Deleting this directory changes no
   behavior of the renderer.
4. **Output is ignored.** Sheets go to `generated/design_history/`; `*.png` and
   `generated/` are git-ignored here.

The cost of an era is one line of YAML, not a copy of a retired renderer.

## Where the history lives

The renderer's past is three repositories' worth of commits:

| Segment | What | Source |
|---|---|---|
| `A0` | the renderer as a subdirectory of the main repo, Apr-Jun 2026 | `ambition` epoch 0 |
| `R0` | the renderer's own repository, Jun-Sep 2026 | `ambition_sprite2d_renderer` epoch 0 |
| `R1` | the active renderer repository | this checkout |

Epoch 0 of both lives in the `ambition-history` store
(`refs/epochs/<repo>/000/heads/main`). `fetch` makes every ref exist; the store
defaults to a sibling `ambition-history` checkout, else a cache directory
(`--store`, `$AMBITION_HISTORY_STORE`).

## Which model drew it

`attribution.py` reads, strongest first:

| Basis | Evidence |
|---|---|
| `measured` | the resource ledger (`.llm_resource_tally`), keyed by commit id; from about August 2026 |
| `declared` | a `Co-Authored-By` trailer |
| `message` | the subject or body names a model ("Big GPT 5.6 Alice improvement") |
| `author` | none of the above, committed from Jon's account: a human commit or an unattributed one |
| `unknown` | nothing says |

A commit is evidence about a *session*, not proof that one model drew every
pixel, and an era's commit may be a polish over earlier art. The basis is shown
so a reader can discount it. Where it says nothing, the sheet says nothing.

## Use

Run from `tools/ambition_sprite2d_renderer/`, with the renderer's interpreter:

```bash
python -m design_history fetch                 # make the history refs exist
python -m design_history list                  # curated lineages
python -m design_history survey alice          # draw candidate commits, show distinct looks
python -m design_history survey alice --sweep 25   # also every 25th commit (shared-helper changes)
python -m design_history build alice           # the curated progression sheet
python -m design_history build --all
python -m design_history attribution <commit>
python -m pytest tests/test_design_history.py   # the wall and the curated shape
```

`survey` finds commits touching a lineage's `paths`, draws each (cached), and
keeps the first commit of every run of identical pixels. Read its sheet under
`generated/design_history/survey/`, then write the looks that matter into
`lineages.yaml` as `eras`. A path pattern cannot see a change made through a
helper that many characters share; name the helper in `paths` or `--sweep`.

Some commits do not render (an old command is missing, or the tree is broken at
that point). Those are skipped and cached as failures, so they cost nothing the
second time.

## Curated lineages

Written from the survey sheets (2026-10-07): Alice, Bob, Emmy (`noether`), the
player robot, the four vikings (and a combined `vikings` sheet), the
Mockingbird, the raptor stalker, GNU-ton (the scholar riding the gnu), the giant
gnu alone, the scholar alone, the burning flying shark, the treasure chest and
Oiler. `boss_chest` is surveyed and has one look, shown under `treasure_chest`.

* **The player robot** is one lineage of three deliberately distinct catalog
  characters (`robot` v0, `player_robot_v2`, `player_robot_v3`; there is no v1).
  The repo's own note is `game/ambition_content/src/player_robot_lineage.rs`:
  each version is its own catalog row (its own body, kit and voice, so you can
  meet, fight and play as an old version of yourself), and `derived_from` names
  the version before it as provenance only. Nothing is inherited along the chain,
  and no further character is part of it. Each era names its own target id
  because the id changed with the character. The Fable 5 bone-and-keyframe
  candidate sits in its place in time as an experiment, not a catalog character.
* **GNU-ton** was one fused sheet (scholar on the giant) until the 2026-07-05
  split; the giant and the scholar then have sheets of their own. The Hall of
  Characters does not draw the scholar standalone (observed, not changed).
* A model name shown with a commit is the session's, not proof about each pixel.

## Limits

* The still is the commit's own canonical image (or the idle frame in the
  earliest, config-driven eras). It is for comparing designs, not poses.
* A character whose id was reused for a different design looks like a change;
  that is why identity notes live in `lineages.yaml`.
* Old commits run under today's Python packages. A commit that needs an older
  dependency fails and is reported.
