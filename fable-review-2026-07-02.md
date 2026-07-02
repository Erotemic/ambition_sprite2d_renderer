# Fable review — ambition_sprite2d_renderer — 2026-07-02

Audit of this package as (a) a standalone sprite-authoring tool and (b) the
system that defines the characters the data-driven Ambition engine ingests.
Method: four parallel deep audits (core/authoring layers; targets + repo-root
hygiene; CLI/registry/packaging/docs; Rust-side integration contract), then
fixes applied in this same pass. Everything in §1 is **done and committed**;
§2 is the **actionable backlog**, written as recipes a weaker agent can
execute without re-deriving the analysis. §3 records verified-clean areas so
future reviews don't re-check them.

Verification state at the end of this pass:

- `pytest tests/` → 201 passed, 30 skipped (baseline had **3 failures**).
- `python -m ambition_sprite2d_renderer list` runs clean (baseline printed a
  discovery warning for a dead module).
- Pixel parity vs pre-review commit `b4c9dcd` confirmed byte-identical on one
  target per render spine (generator: `sandbag`, tack-on: `ghoul_skulker`,
  rigdoc: `noether`). The only intended output-byte change is the RON header
  *comment* (stale Rust module path). Note: `.parity-baseline/` itself is
  stale (captured ~Jun 21, predates the ultrapack/PCA commits) — recapture it
  before the next behavior-preserving refactor.

---

## 1. Fixed in this pass

### 1.1 Broken at baseline (bugs, not style)

- **`draw-all` / `regenerate-all` were broken** — `data/pack_plan.yaml`
  (then `configs/pack_plan.yaml`, landed in `b4c9dcd`) sat in the directory
  `load_jobs()` globs for CharacterJob YAMLs and crashed every bulk job load
  with a bare `KeyError: 'target'`. Moved to `data/`;
  `CharacterJob.load` now names the offending file when a non-job YAML sneaks
  into `configs/`. Parent's `regen_sprites.sh` and the planning doc updated to
  the new path.
- **Per-sheet regen cache went stale silently** (parent repo,
  `regen_sprites.sh::compute_core_shared`) — it hashed package `*.py` at
  `-maxdepth 1`, but the shared infra had moved into `core/ authoring/
  registry/ cli/` subpackages, so those three remaining top-level files were
  the *only* "shared infra" in per-sheet cache keys. Editing e.g.
  `authoring/sheet_build.py` re-rendered **nothing** (each unit reported
  `[cache] up to date`, then the global fingerprint re-armed). Now hashes the
  four subpackages explicitly.
- **Two stale tests**: `test_ldtk_manifest` pinned the abandoned 4-entry
  entity map (the PlayerStart-only reduction was deliberate, documented on
  `DEFAULT_ENTITY_SPRITE_MAP`); the two `test_render_scale` failures were the
  pack-plan collision above.
- **Mockingbird `TOOL_ROOT` pointed at `targets/`** — default renders landed
  *inside the package tree* (`<pkg>/targets/generated/…`) and a bare
  `install` would have created a junk `crates/…` tree under the tool root
  (masked only because regen always passes `--install-dir`). Fixed to the
  real tool root; `gnu_ton_boss`'s display-path root aligned.
- **`rigdoc_codegen` diverged from the live rigdoc renderer** — ejected
  Python ignored a rig's `rest_lift` / `rest_pitch` IK fallbacks, so an
  ejected rig rendered its feet differently than the GUI showed. Codegen now
  emits the same fallbacks.
- **rigdoc sprite-raster cache collided** — keyed by `(part name, scale)`, so
  two `sprite` parts with the same/absent name silently shared the first
  part's art. Now keyed by `(name, include-list, pivot, scale)`.
- **`ron_tuning` emitted `feet_anchor_y_override`, which Rust never parsed**
  — `SheetTuningSpec` (crates/ambition_sprite_sheet) deserializes only
  `collision_scale` + `frame_sample_inset`; serde ignores unknown fields, so
  an authored feet override would silently do nothing. Removed the emit (feet
  placement rides `body_metrics.feet_anchor_norm`, the one real channel) and
  pinned a comment listing the exact Rust-parsed fields at the emit site.
- **`svg_canonicalize` sodipodi namespace typo** (`sodipodi-0.dtd` →
  `sodipodi-0.0.dtd`) put `sodipodi:role` in the wrong attribute sort band.
- **Fresh-clone gap** (parent repo): seven runtime-referenced targets were
  registered in the tool but absent from `regen_sprites.sh`'s
  `tackon_targets` + `expected_files` — `cut_rope_anvil/piano/rope`,
  `generic_explosions`, `smirking_behemoth_boss`, `stochastic_parrot`,
  `imperfect_cellular_automaton`. On a fresh clone these silently fell back
  to colored rectangles (the postcondition couldn't catch them: it validates
  the same hand-list). Added; see §2.9 for the structural fix.

### 1.2 Silent failure modes made loud

- `ultrapack()` (fresh-render path) swallowed every per-target exception with
  a bare `continue` — the exact failure mode `ultrapack_rendered`'s docstring
  records as "once dropped 59 targets from one tier with no trace." Both
  paths now report dropped targets on stderr.
- `authoring/sheet.py` swallowed raising `hurtbox_parts` / `attack_hitboxes`
  hooks and silently published auto-derived combat geometry. Now fails the
  render with the generator + hook named.
- Bulk `sheet` / `install` / `publish` never showed discovery warnings (only
  `list` did) — a target that failed discovery was silently un-shipped by a
  bulk publish. Bulk ops now print the discovery report to stderr.
- Discovery: registry name collisions now warn (previously last-writer-wins,
  documented in `rigged.py` as "silently shadows"); a package dir with `.py`
  files but no `__init__.py` now warns instead of vanishing (dirs paired with
  a same-named sibling module, e.g. `rigged/` + `rigged.py`, stay quiet).

### 1.3 Layering made real (`core` ← `authoring` ← `targets`)

- `authoring/generators.py` — the concrete-target roster, which imported nine
  `targets.characters.*` modules INTO the authoring layer — moved to
  **`registry/character_generators.py`**. This also killed the
  `generator.py`/`generators.py` name trap.
- `authoring/lasersword_common.py` (1143 lines of one weapon family's art)
  moved to **`targets/props/_lasersword_common.py`** (the `_pirate_common`
  precedent; underscore = discovery skips it, and regen's CORE_SHARED hashes
  `_*.py` family helpers).
- `ldtk_manifest.py` (an editor-bridge exporter, not rendering) moved from
  package top level to **`devtools/ldtk_manifest.py`**.
- `authoring/rendering.py` deleted — its `load_font` was a byte-identical
  copy of `core.draw.font` (the third font loader in the package); the rest
  was dead.

### 1.4 Dead weight deleted

- Tracked binaries: the two root `pca_*.zip` archives (~3.8 MB, one literally
  named `… (1).zip`; payload already extracted into `pca_legacy/`).
- Root mockingbird duplicates: three YAMLs (the root `scene.yaml` was *stale*
  — it still had the pre-rename `hover:` row) and both root shim scripts.
  The generator is now `python -m
  ambition_sprite2d_renderer.targets.characters.mockingbird_boss` (new
  `__main__.py`); regen repointed; the four root `README_*.md` overlay
  changelogs consolidated into
  `targets/characters/mockingbird_boss/README.md`.
- `targets/characters/pirate_heavy_v2.py` — no `render()`, warned on every
  `list`, referenced by nothing.
- `core/manifest.py` — an unwired dataclass "schema mirror" that could only
  drift from the real emitter (`core/manifest_ron.py` works on dicts and is
  the single emitter).
- `authoring/backgrounds.py` (513 lines) — zero importers; its own docstring
  cited a `draw-backgrounds` CLI command that no longer exists. The live
  pipeline is the sibling `tools/ambition_parallax_renderer` (which, unlike
  this copy, already draws with `ImageDraw`'s `"RGBA"` mode — the dead copy
  carried a translucent-fill alpha-clobber bug in every drawer).
- `specs/` (an "informational" YAML nothing read), `PackPolicy.group` (dead
  field — locality grouping landed as the ultrapack PackPlan instead), dead
  helpers (`rig.bbox_from_center`, `backgrounds.soft_layer/composite_soft`,
  `common_draw.scaled_color/alpha_bbox/force_opaque_inside`), dead locals in
  `sheet.py`.

### 1.5 Packaging repaired

- **`uv.lock` was stale** — missing `rectpack`/`resvg-py`/`lxml`, so a
  `uv sync` env couldn't import a single target (`packer.py` imports rectpack
  at module top and everything imports through it). Relocked.
- package-data now ships `data/**` (rig templates + pack_plan) and
  `targets/characters/rigged/*.rig.json`. **Important invariant, now pinned
  in a pyproject comment: `rigged/` must NEVER get an `__init__.py`** — it
  would shadow the sibling `rigged.py` module; the rig docs ship as package
  data, not as a package.
- Added `[build-system]`, a `gui = ["PySide6>=6.6"]` extra, and an
  `AMBITION_REPO_ROOT` env override for `repo_root()` (standalone checkouts).

### 1.6 Docs brought in line with the code

- README: `CharacterGenerator`/`GENERATORS` replace the dead
  `BaseAdapter`/`adapters.py` walkthrough; `list`/`publish` replace dead
  `list-targets`/`render-publish`; `sheet_build` replaces dead `tackon_sheet`
  links; `GENERATOR_MODULE_STEMS` replaces `ADAPTER_HELPER_STEMS`; the
  `projectiles/` category and the `gifs`/`debug-hitboxes`/`ultrapack`/
  `ldtk-manifest` commands are now documented; the `SHEET_FILES` default
  documents the auto-appended `_actor.ron` sidecar.
- Same sweep over `docs/design.md`, `GOALS.md`, `docs/ENTITY_TODOS.md`,
  `cli/parser.py`'s module docstring, and help texts (rosters de-enumerated —
  help now points at `RUNTIME_REVIEW_NPCS` instead of listing 13 of 20 NPCs).
- **56 modules had their docstring AFTER `from __future__ import`**, so
  module `__doc__` was `None` package-wide. Statement order swapped
  everywhere. Don't reintroduce: docstring first, then `__future__` import.

---

## 2. Actionable backlog (ordered; each item is self-contained)

### 2.1 Split `authoring/sheet_build.py` (781 lines, 3 concerns) — P1

The tack-on spine mixes three separable things. Split, keeping import
compatibility via re-exports in `sheet_build.py` for one commit, then update
importers and drop the re-exports:

1. **Drawing prims + constants** (lines ~48–218: `SCALE`, `ANIMATIONS`,
   `font`, `lerp`, `ease_in_out`, `oscillate`, `rot`, `transform`, `poly`,
   `rotated_rect*`, `circle`, `ellipse`, `line`, `downsample`) →
   `authoring/draw2d.py` (or fold into `common_draw.py`). While moving:
   - Rename `downsample` → `fit_to_frame`; it *shadows*
     `core.draw.downsample` with completely different semantics (fit-to-
     canvas letterboxing vs plain LANCZOS resize).
   - `ANIMATIONS` is pirate-family data (only consumer:
     `targets/characters/_pirate_common.py:35`) — move it there.
   - `sheet_build.font` loads regular-weight only, unlike `core.draw.font`
     (bold-first). Unify on `core.draw.font`; this may change preview-label
     glyphs (cosmetic, debug-only images) — acceptable.
2. **Layout engine** (lines ~244–360: `_grid_sheet_rows`,
   `_packed_sheet_rows`, `layout_sheet_rows`) → `authoring/sheet_layout.py`.
3. **Pipeline** (`build_sheet` / `render_sheet` / `write_canonical` /
   `diagnose_idle_coverage`) stays as `sheet_build.py`.

Acceptance: pytest green; `parity_harness.py check` clean (recapture baseline
first — see header note); `grep -rn "from .sheet_build import" | wc -l`
unchanged consumers still resolve.

### 2.2 Split `authoring/actor_contract.py` (1034 lines, 4 concerns) — P1

Four separable concerns: generic RON value emitter (lines ~26–122 →
`authoring/ron_emit.py`), Rust-catalog regex scraper (~126–218 →
`authoring/catalog_probe.py`), heuristic actor inference (~221–757, stays),
writer entry points (~801–1034, stays). While splitting, dedupe:
`_ron_escape` duplicates `manifest_ron._ron_escape`; `_deep_merge` duplicates
`actor_profiles.merge_actor_metadata` minus a deepcopy. Also: the catalog
scraper walks `Path(__file__).parents` for the game repo's
`character_catalog.ron`, so `_actor.ron` bytes differ between in-repo and
standalone checkouts, and `lru_cache` pins the first probe for the process —
make the probe explicit (pass a repo root or None) instead of ambient.

### 2.3 One animation vocabulary — P1 (Rust-side test first)

Two independent copies exist with **no programmatic link**:
`authoring/animation_vocab.py` (Python name lists + timings) and Rust
`CharacterAnim::from_name` (crates/ambition_gameplay_core/src/
character_sprites/anim/mod.rs — its alias history shows reactive patching).
Concrete drift today: Rust accepts `punch`/`special`/`front_idle`/`taunt`
(absent from Python vocab); Python ships `talk`/`land`/`pickup`/`throw`/
`cast`/`celebrate`/`sit`/`sleep`/`stomp`/`wall_slide` rows that `from_name`
silently drops. Recipe:

1. (Rust) Add a test that walks every generated `*_spritesheet.ron`, collects
   row names, and asserts each is either resolvable by
   `CharacterAnim::from_name` or present in an explicit
   `AUTHORED_AHEAD: &[&str]` allowlist — turning the de-facto contract into a
   pinned one. Model it on the existing
   `every_spritesheet_ron_parses_into_sheet_record` test.
2. (Later) Emit the vocab from one side. The natural direction: Python
   `animation_vocab.py` emits a small `animation_vocab.ron` the Rust side
   parses in that test (NOT at runtime), so drift fails CI instead of
   dropping rows. Related in-package dedup: `sheet_build.IDLE_ALIASES` /
   `CHARACTER_ANIM_NAMES` vs `actor_contract.IDLE_CANDIDATES/…` both claim to
   mirror `CharacterAnim` — fold both into `animation_vocab.py`.

### 2.4 Finish the registry/authoring untangle — P2

Remaining (after this pass moved the roster): `authoring/sheet.py`, `canonical.py`,
`faction_lineup.py`, `generator.py` import `..registry` (for
`CharacterJob`/`RenderConfig`/`policy_for`) while `registry/discovery.py`
imports `..authoring.actor_profiles` at module level and
`authoring.sheet`/`registry.character_generators` lazily. No import error
today, but the cycle is only broken by deferred imports. Recipe: move the
pure-data pieces DOWN — `registry/config.py` (CharacterJob/RenderConfig) and
`registry/pack_groups.py` (PackPolicy) into `authoring/` (they are authoring
inputs, not discovery) — leaving `registry/` = discovery + roster only, which
may import authoring freely. Mechanical: `git mv`, fix imports, keep
`registry/__init__` re-exports for one commit.

### 2.5 Target-helper dedup (GOALS goal #1, now quantified) — P2

The same private micro-library is copy-pasted across targets: `_s` in **36**
files, `_downsample` in **28**, `_ease` in **24**. Worst: the viking quartet
is four diverged ~750-line copies of one file (warrior↔shieldmaiden diff is
781 lines). `portal_gun_blue/orange` (29-line files over
`targets/props/_portal_gun_art.py`) and the admiral/raider/lookout/navigator/
quartermaster pirates (~100-line parameterizations of
`_pirate_common.render_target`) are the target shape. Recipe per family:
extract `targets/characters/_viking_common.py` (palette + rig + poses),
reduce each variant to a parameterization, verify with the parity harness
(drift policy per its docstring: eyeball dumps in `tmp/sprite-drift/`, bless
or fix). Then sweep single-file targets onto `authoring` prims
(`common_draw`, and `draw2d` once 2.1 lands) instead of local `_s/_ease/
_downsample` copies. Also fold `_lasersword_common.with_alpha/lerp/
ease_in_out` (local dupes of core/sheet_build helpers) while touching it.
Note `pirate_heavy` is deliberately bespoke (its docstring says so) — skip.

### 2.6 Delete the ~22 unreachable `__main__` blocks — P2

Single-file targets with relative imports carry `if __name__ == "__main__":`
+ argparse `main()` that die with "attempted relative import" if actually
run (e.g. `viking_warrior.py:760`, `pirate_cutlass_viper.py:1120`,
`bear_mauler.py:503`, `galwah.py:1710`). Find them:
`grep -rln 'if __name__' ambition_sprite2d_renderer/targets/` then delete the
block + now-unused `import argparse` in files using relative imports. The CLI
(`sheet <target>`) is the real entry. Don't copy the pattern into new
targets.

### 2.7 Import-style normalization — P3

13 target files use absolute `from ambition_sprite2d_renderer....` imports vs
the majority relative style; `item_icons.py` does a mid-file cross-category
import (`from ..props.shrine import write_shrine_prop` — a real dependency
regen's leaf-hash cannot see; consider promoting the shared piece to
`targets/props/_shrine_common.py` or noting it in CORE_SHARED);
`rigged/pca_rig_extract.py` uses a deliberate `sys.path` hack for loose-
script use. Normalize opportunistically when touching each file.

### 2.8 `frame_source` / `core.pipeline` seam: wire or fold — P3

The staged "one contract" spine is only partially adopted:
`generator.frames_for` + `frame_source.GeneratedFrameSource` have no
production caller (the generator spine still renders via
`sheet.build_spritesheet`); `core/frameset.py` + `core/pipeline.py` are
consumed only by `targets/props/entities.py` and tests. Either (a) route
`sheet.build_spritesheet`'s render loop through `GeneratedFrameSource` (the
plan of record — do it harness-first), or (b) if the seam has been
overtaken by events, fold `frameset/pipeline` into `entities.py` and delete
`frame_source`. Decide once; today it reads as two half-built bridges.

### 2.9 Registry-driven regen (kill the hand lists) — P2, parent repo

`regen_sprites.sh` hand-maintains `tackon_targets` + `expected_files`; §1.1
patched seven omissions, but the class of bug survives. Recipe:

1. Replace the `tackon_targets` loop with `publish` (no target = bulk over
   every module target) — it already exists; keep per-sheet caching by
   looping over `python -m ambition_sprite2d_renderer list --names-only`
   (add that trivial flag) so `publish_cached` still works per target.
2. Derive `expected_files` from the actual consumers: a small Python step
   that scans `character_catalog.ron` + `crates/ambition_content/src/**`
   for `sprites/<stem>_spritesheet` references and emits the list. Then a
   new runtime consumer can't be forgotten — the postcondition inherits it.

### 2.10 Decide the quality-variant story — P2, needs Jon

Two overlapping pipelines: (a) `scripts/generate_visual_quality_variants.py`
→ `assets/sprites_0_5x/_0_25x/_potato` dirs (baked by build.rs, but the
script is invoked by NOTHING — fresh clones never have variants and tests
tolerate their absence), and (b) the wired ultrapack tiers
(`assets/sprite_packs/{full,half,quarter,potato}`). Either retire the variant
dirs in favor of packs (delete the script, the `try_load_spec_for_target_scaled`
fallback, and the `sprites_0_5x` bake) or wire the script into
`regen_sprites.sh`. Also fix the stale Rust header in
`crates/ambition_sprite_sheet/src/pack.rs` (tier named `base` → `full`;
"nothing bakes it yet" — build.rs does).

### 2.11 Rust-side follow-ups — P2/P3 (land in crates/, not here)

- `BodyMetrics::body_pixel_parts` (ambition_sprite_sheet lib.rs:169): zero
  emitters anywhere, but the consumer-rule doc tells readers to prefer it.
  Mark the doc "reserved — no emitter yet" or wire the emit.
- Per-frame melee boxes (`AnimationMetrics::frame_duration_secs`,
  `AnimationBox::frames`): declared on both sides, no emit path — this is
  the open pillar-4 (melee hitbox agreement), explicitly blocked on a spec
  from Jon. Don't half-wire it.
- Orphan runtime assets: `assets/sprites/pirate_heavy_v2_spritesheet.ron`
  (+ variant-dir copies) — its source was deleted this pass; delete the
  on-disk artifacts (they're gitignored, regen won't recreate them). Also
  `assets/sprites/perfect_cellular_automaton_rig_v2.json` is untracked with
  zero consumers — likely a stray authoring artifact; confirm and delete.

### 2.12 Small in-package items — P3

- `cli/commands.py` runs full discovery at import time (~0.5 s before
  `--help` prints; ~100 module imports). Wrap `_REPORT`/`_ALL_TARGETS` in a
  lazy accessor when it starts to hurt.
- Flag naming: `--dest-root` (install/publish/regenerate-all) vs `--out-dir`
  (draw-runtime-npcs) for the same destination concept. Unify on
  `--dest-root` with a deprecation alias.
- Single-target `install` returns rc 1 silently when zero files copied;
  bulk mode treats zero-copied as success. Make both print what was expected.
- `gifs`: `FileNotFoundError` traceback when a target has no standard
  manifest; per-frame extraction failures are swallowed. Mirror the
  ultrapack loud-drop pattern.
- `_ensure_actor_sidecars` (discovery.py) swallows manifest parse errors
  with bare `continue` — add the stderr line.
- `core/measure.py` uses all-channel `getbbox()` (docstring now says so) —
  switching to alpha-only `getchannel("A").getbbox()` is more correct (the
  crop paths already do) but changes bytes: do it harness-first, eyeball the
  drift dumps, bless.
- `core/draw.composite_polygon` is the intended canonical home but targets
  use `skeleton.composite_polygon` or local copies — migrate callers, delete
  the `skeleton` copy.
- `pca_legacy/` invites its own deletion (`_LEGACY.md`: "safe to delete
  wholesale; nothing here is on the live sprite path"). When the PCA sprite
  is final, `git rm -r pca_legacy/`.
- `tpl/` holds an untracked 133 MB Godot binary referenced by nothing —
  Jon's call to delete (left in place).
- `tests/test_render_scale._published_frame` uses `tempfile.mkdtemp()`
  without cleanup — use the `tmp_path` fixture.

---

## 3. Verified clean (don't re-audit)

- **core/ minimal-deps invariant** holds: every `core/*.py` is PIL+stdlib
  only, guarded by `tests/test_core_minimal_deps.py` (parametrized per file —
  the count drops when a core file is deleted; that's the test working).
- **Determinism**: no unseeded random / time / uuid anywhere on the render
  path; the only randomness is `random.Random(seed)` from job configs; all
  RON/JSON map emissions are sorted; the packer is deterministic and
  self-verifies losslessness. One caveat lives in §2.2 (catalog-probe
  environment dependence).
- **Python→Rust RON schema sync**: field-for-field match on everything
  actually emitted; every Python-conditional field carries `#[serde(default)]`
  on the Rust side; pack-catalog JSON matches `SpritePackCatalog` 1:1
  including `page_groups`. The project-rule Rust-side parse tests over real
  generated files exist (`every_spritesheet_ron_parses_into_sheet_record`,
  `live_boss_spritesheet_ron_round_trips`,
  `baked_pack_tiers_parse_and_agree_on_coverage`, et al).
- **Install-path contract**: `assets/sprites/` (+ `entities/`, `props/`,
  boss subdirs) and `assets/sprite_packs/<tier>/` line up end-to-end with
  the Rust loaders; tier names agree; regen's tier-coverage postcondition
  mirrors the Rust test. (Note `sprites/entities/*.png` are `include_bytes!`
  — regen must precede first build on a fresh clone.)
- **Sprite-renderer refactor plan** (docs/planning/engine/sprite-renderer.md):
  pillars 1–3 (reorg / minimal-dep core / plural authoring) are genuinely
  done; pillar 4 (melee) is open and blocked on a spec (see §2.11).
- **CLI wiring**: every subcommand has a handler, exit codes propagate,
  `_get_target`'s near-miss diagnostics are genuinely good. `regen_assets.sh`
  and every `regen_sprites.sh` invocation match the current CLI.
- **gui/** imports cleanly without PySide6 (Qt imports deferred);
  `pca_legacy/` is quarantined (nothing live imports it);
  `targets/characters/rigged/pca_rig_extract.py` is independent of it.
- **Root entry points that remain are live**: `main.py` (CLI alias),
  `gen_noether_rig.py` (regenerates the committed noether rig),
  `parity_harness.py` + `tools_diff_sheets.py` (refactor harnesses).

---

## 4. Framing: this package as the character-definition system

The engine-facing contract is already in decent shape: one `Target` concept,
one RON emitter, measured-by-default body metrics, data-driven pack policy,
quality tiers, and Rust-side parse tests over real output. The three gaps
that matter for "characters are data the engine ingests":

1. **Vocabulary is duplicated, not shared** (§2.3) — animation names are the
   spine of the contract and currently drift reactively.
2. **The actor contract has no Rust consumer yet** — `*_actor.ron` sidecars
   are emitted (and regen-required for gnu_ton_boss) but only the hygiene
   classifier reads them. When EntityCatalog adoption lands, aim the sidecar
   schema at it deliberately rather than letting the inference heuristics in
   `actor_contract.py` ossify into a de-facto schema (§2.2 makes that
   separable).
3. **Coverage is enumerated by hand** on the regen side (§2.9) — the
   registry knows the truth; the shell script should ask it.
