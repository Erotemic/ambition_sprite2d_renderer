# Mockingbird boss — multi-file tack-on target

The boss renders from a nested scene-graph rig authored in
`mockingbird_boss_scene.yaml` (source of truth; `mockingbird_boss_parts.yaml`
is a compatibility copy the editor keeps in sync, and
`mockingbird_boss_legacy_parts.yaml` preserves the original imported YAML for
reference). `sprite_generator.py` rasterizes the vector geometry;
`part_editor.py` is a PySide6 scene-graph editor for tuning the rig.

This directory is also the canonical example of a **multi-file target**: its
`__init__.py` exposes the same tack-on API (`TARGET_NAME`, `SHEET_FILES`,
`render()`, `install()`, `ACTOR_METADATA`) as a single-file target, so
discovery registers it like any other. Copy this directory shape for the next
multi-file character.

## Commands

Normal builds go through the standard registry CLI
(`python -m ambition_sprite2d_renderer publish mockingbird_boss`). The
generator also has its own CLI for iterating on the rig:

```bash
python -m ambition_sprite2d_renderer.targets.characters.mockingbird_boss render [--quick] [--force]
python -m ambition_sprite2d_renderer.targets.characters.mockingbird_boss preview
python -m ambition_sprite2d_renderer.targets.characters.mockingbird_boss install
python -m ambition_sprite2d_renderer.targets.characters.mockingbird_boss render-publish
python -m ambition_sprite2d_renderer.targets.characters.mockingbird_boss.part_editor  # editor (PySide6)
```

Renders land in `<tool root>/generated/mockingbird_boss/`; `install` /
`render-publish` copy into
`crates/ambition_actors/assets/sprites/mockingbird_boss/`.

## Scene schema

Every node is `kind: group` or `kind: shape`. Both carry `id`, `label`,
`visible`, `locked`, integer `z_order`, and a `transform`; shapes add a
`primitive`. Groups nest recursively; render order is **local** — children
draw in ascending `z_order` within their parent. Primitives are grouped by
role (body hull, sensor ports, dorsal spikes, tail boom/fins/flame, head
teeth/skull/jaw/eye, legs, foreclaws, rotor masts/discs) so the editor tree
stays navigable. All transforms apply to vector geometry before
rasterization; the sheet's animation rows are per-node vector-space
transforms, not duplicated static frames.

## Animation rows

Manifest / PNG row order: `rest`, `thrust`, `bite`, `slash`, `hit`, `death`.
The resting row is named `rest` (not `hover`) to match the boss-encounter
idle convention — Rust's `MOCKINGBIRD_SHEET` maps row 0 to `BossAnim::Rest`
and the runtime maps `rest` → `CharacterAnim::Idle`, while `hover` means the
airborne Fly pose.

## Inspiration links

- https://archive.org/download/htkam/TKAM%28www.albinoblacksheep.com%29.swf
- https://archive.org/download/how-to-kill-a-mockingbird/how-to-kill-a-mockingbird.swf
