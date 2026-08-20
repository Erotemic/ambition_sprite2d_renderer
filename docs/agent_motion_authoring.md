# Agent motion authoring toolkit


> **Fighting Polygon motion-IR pilot.** The sword and brawler no longer treat
> `*.rig.json` as their editable motion authority. Their SVGs own static rig
> geometry and `data/motion/humanoid/fighting_polygon_v1/` owns poses/clips.
> Use `python -m ambition_sprite2d_renderer.devtools.motion_ir_tool describe|validate`
> for that pilot. The RigDocument-oriented commands below remain the transition
> workflow for characters that have not migrated yet. See
> `docs/authoring/motion_ir_v1.md` for the schema boundary.

The sprite renderer has a text-first semantic motion toolkit for bone-rigged
characters. It complements the GUI rather than replacing it: the GUI remains
best for interactive posing, while automation agents can now reason in terms of
hands, feet, phases, contacts, support, and motion paths instead of raw joint
angles alone.

The toolkit is deliberately exposed as an additive module entrypoint, so adding
or changing agent tooling does not require editing the renderer's central CLI
parser:

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools templates
```

## Review an existing animation

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools review \
  carl_stargan \
  --clip walk \
  --art \
  --out /tmp/carl_walk_review
```

The review writes:

- `motion_review.png` — skeletons, inferred contacts, COM/support markers, phase
  names, and the focus endpoint's speed graph;
- `motion_paths.png` — overlaid hand/foot/pelvis/head trajectories in one rig frame;
- `motion_review.json` — machine-readable frame samples and metrics;
- `motion_review.md` — concise agent/human interpretation;
- `motion_silhouettes.png` — optional flat-black per-frame silhouettes and width/area metrics when `--art` is requested and rasterization is available.

For in-place locomotion clips, local foot motion is not automatically foot slide:
the runtime may translate the controlled body while the planted foot moves backward
in sprite-local space. The review therefore estimates body travel from alternating
contact phases and reports both local drift and travel-compensated slide. You can
override the estimate with `--travel-px-per-cycle N` when gameplay speed is known.

Current metrics include inferred planted-foot slide, pelvis excursion,
center-of-mass versus support, arm/leg joint extension, opposite-limb
correlation, endpoint velocity, strike-speed/contact alignment, and loop seam.
They are descriptive authoring feedback, not runtime validation rules.

## Add meaningful phase bookmarks

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools phases \
  carl_stargan \
  --clip walk \
  --template walk \
  --out /tmp/carl_stargan_side.phased.rig.json
```

Templates currently cover `walk`, `run`, `dash`, `jump`, `melee_strike`, and
`smash_attack`. They populate ordinary `pose_keys` and a non-runtime
`authoring_phase_keys` block carrying semantic roles such as contact, passing,
anticipation, contact, follow-through, and recovery.

## Pose by semantic endpoints

Generate a goal scaffold from the current pose:

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools scaffold \
  carl_stargan --clip jab --frame 2 --out /tmp/jab_pose.yaml
```

Edit the YAML. A useful strike can be expressed as:

```yaml
schema: ambition.semantic_pose_goals.v1
goals:
  root:
    shift: [3, 1]
  bones:
    torso:
      angle_deg: -10
  near_hand:
    target:
      space: frame
      value: [108, 61]
    bend: down
  far_hand:
    target:
      space: root
      value: [5, -45]
    bend: down
  near_foot:
    target:
      space: frame
      value: [77, 101]
    bend: forward
  head:
    look_at:
      space: frame
      value: [112, 56]
```

Apply it to a copy:

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools apply \
  carl_stargan --clip jab --frame 2 \
  --goals /tmp/jab_pose.yaml \
  --out /tmp/carl_stargan_side.posed.rig.json
```

Semantic hand/foot targets are translated to the rig's existing IK channels.
`bend: up/down` selects an elbow branch geometrically; `bend: forward/back`
selects a knee branch. Explicit channel values remain available as an escape
hatch under `goals.channels`.

The tool writes normal rig keys, preserving existing constants/expressions by
baking their prior sampled motion before a local edit. No new runtime format is
required.

## Retarget a strong motion to another humanoid

Raw joint angles do not transfer cleanly between characters with different limb
lengths. The toolkit can instead sample source hand/foot positions relative to
the pelvis, normalize them by source leg scale, and solve equivalent endpoints
through the destination rig's IK:

```bash
python -m ambition_sprite2d_renderer.authoring.pose_tools retarget \
  carl_stargan patent_clerk \
  --clip walk \
  --target-clip walk_from_carl \
  --out /tmp/patent_clerk_side.retargeted.rig.json
```

The new clip records `authoring_retarget` metadata identifying its source and
scale. This is a starting pose/motion transfer, not finished art: review the
result, then exaggerate posture, spacing, anticipation, and follow-through to
fit the destination character.
