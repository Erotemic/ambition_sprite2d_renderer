# Code smell backlog

Running log of smells noticed *opportunistically* while doing other work. The
rule: while focused on a big task, don't chase smells — append them here so they
aren't forgotten, and revisit later. Only fix inline when the fix is very clear
AND carries no risk of slowing the main task.

Append-only during runs; triage/prune during cleanup passes (move fixed items to
a Resolved section, condensed to a one-liner with the verdict/commit).

Entry format:

```
## YYYY-MM-DD <short title>
- **Where:** file:line (or module)
- **Smell:** what's wrong, one or two sentences
- **Noticed while:** the task being worked
- **Suggested fix / size:** sketch + rough effort (S/M/L)
```

---

## Open

## 2026-07-26 `draw-all`'s runtime allowlist duplicates the game's required-sheet list
- **Where:** `ambition_sprite2d_renderer/cli/commands.py` — the `runtime_stems` set in `draw_all()`.
- **Smell:** two hand-maintained lists encode "which sheets the game requires" — this set, and `regen_sprites.sh:261-305`'s `expected_files` in the ambition superproject. Nothing keeps them in sync, and they disagreed silently: `ranged_skirmisher`, `exploding_mite`, and `dividing_mite` had configs in `configs/` and were required by the game, but were filtered out here, so every asset regen rendered for ~21 minutes and *then* failed a postcondition. The filter exists only because `configs/` accumulated older review jobs, so it is a workaround for an unsorted directory, not a real policy.
- **Noticed while:** verifying zero-to-runnable setup from a fresh clone (2026-07-26); the three stems were added to the set as the unblocking fix, which leaves the duplication intact.
- **Suggested fix / size:** S–M — let the data say it instead of a code-side allowlist: either move review-only jobs out of `configs/` so "everything in `configs/` is runtime" becomes true, or add an explicit `runtime: true`/`review: true` field to `CharacterJob` and filter on that. Either way the superproject's `expected_files` should be *derived* from the renderer's own target list rather than restated.

## 2026-07-26 Prose-era `configs/review/*.yaml` never migrated to the keyed notes schema
- **Where:** `ambition_sprite2d_renderer/configs/review/*.yaml` (15 files: alice, bob, craig, erdish, eve, judy, mallory, oiler, olivia, peggy, sybil, trent, trudy, victor, walter).
- **Smell:** `32aec19` converted `authoring_description` / `gameplay_description` from freeform prose to keyed mappings (`parody_of`, `core_joke`, `visual_inspirations`, … / `role`, `combat_identity`, `signature_moves`, …) and rewrote the `targets/characters/*.py` authors, but left these YAMLs carrying bare strings. `dict("some prose")` raises, so *every* sprite regen died in `CharacterJob.from_dict` until the loader was made tolerant. The data is still prose-era; the loader now lifts it into `design_notes` / `authoring_notes`, which is a compatibility shim, not the intended authoring.
- **Noticed while:** same fresh-clone verification — this was the crash that had to be fixed first.
- **Suggested fix / size:** M — rewrite the 15 files into the keyed schema (the prose is good raw material and mostly already states the parody source), then consider dropping the string branch in `_notes_mapping`. Worth doing in the same pass as any NPC-writing sweep, since it is content editing more than code.

## 2026-07-26 Two competing vocabularies for `dialogue_hints`
- **Where:** `ambition_sprite2d_renderer/registry/config.py:102-105` (docstring) vs `configs/**.yaml` and `targets/characters/*.py`.
- **Smell:** the field documents `suggested_barks` (short) and `fallback_dialogue` (long), and the newer `.py` targets plus `configs/player_robot_v2.yaml` use exactly those keys — but 16 configs use a plain `barks:` key instead. `dialogue_hints` is passed through as a loose dict, so both shapes survive and any consumer must know both. Nothing fails loudly; a consumer reading only `suggested_barks` silently sees a mute character.
- **Noticed while:** same fresh-clone verification, while auditing what `publish_character_notes` actually emits.
- **Suggested fix / size:** S — pick `suggested_barks`/`fallback_dialogue` (already the documented pair), normalize `barks` into it at the loader boundary the same way notes are normalized, and migrate the 16 configs so the alias can be deleted.

## 2026-07-26 `publish_character_notes` silently dropped notes for a whole schema era
- **Where:** `ambition_sprite2d_renderer/authoring/sheet_build.py` — `publish_character_notes()`.
- **Smell:** the function copied `authoring_description`/`gameplay_description` only when `isinstance(value, str)`. Once `32aec19` made those fields mappings, the check stopped matching and every structured character quietly stopped publishing its notes into the sheet YAML — no error, no warning, just missing output. A type check used as a "should I publish this?" gate degrades into silence the moment the type changes. Fixed inline (mappings are now published too), but the *class* of bug is worth remembering: this is the second place the same schema migration broke something without saying so.
- **Noticed while:** same fresh-clone verification; caught only because the regenerated `mockingbird_boss` manifest visibly regained its notes.
- **Suggested fix / size:** S — when a field's shape is part of a contract, assert on it rather than branching on `isinstance` and falling through to "do nothing."
