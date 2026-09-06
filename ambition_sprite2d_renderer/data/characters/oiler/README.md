# Oiler SVG rig

Oiler is an Euler-inspired brilliant mechanic: the face, cloth cap, blue coat,
and pale neckcloth deliberately echo eighteenth-century portraits without
turning the sprite into a literal costume copy. The silhouette should read as
an older scholar-engineer before any tool or prop is attached.

`oiler-multiview.svg` is Oiler's editable source art. It is intentionally a
normal, hand-editable Inkscape SVG rather than Python that emits SVG.

The intermediate vector document is useful because it separates concerns:

- the SVG owns silhouette, flat paint, view-specific anatomy, clothing,
  expressions, and exact joint positions;
- the generated `.rig.json` files own the extracted skeleton bindings and
  animation channels;
- the runtime target only chooses which view rig supplies each animation;
- detachable props are separate runtime assets attached through character
  sockets, never baked into Oiler's body sheet.

This means art can be corrected in Inkscape without rewriting limb-placement
code, while the same generic FK/IK implementation continues to animate it.

## Art constraints

The root SVG carries `data-character-design="euler-mechanic-v1"`. The build
script treats that marker and the following view-local shapes as a maintained
contract: `cap-crown`, `cap-dark-fold`, `cap-front-fold`, `cap-hanging-tail`,
and `neckcloth`. Oiler is clean-shaven; do not reintroduce the generic beard
and moustache that made him converge on Bob's silhouette.

The cloth cap should remain asymmetric and visibly folded rather than reading
as a round skullcap. Use several flat overlapping pieces to describe the crown,
front roll, dark fold, and trailing cloth. Do not simulate cloth with gradients.

The character SVG contains anatomy and clothing only. Do not add tools,
machines, bags, flasks, carried objects, or scenery to the view layers. Those
belong in external prop assets and may attach to Oiler's hand sockets.

Use flat fills and explicit highlight shapes. Gradients, filters, drop shadows,
and other raster-like SVG effects are forbidden because they make the small
runtime sprites muddy and harder to edit consistently.

Each view includes a `pelvis_yoke` part bound to the pelvis bone. The upper-leg
roots must remain behind this yoke and the coat/apron. Hip markers belong inside
the yoke at the anatomical sockets, not on the belt line or the visible edge of
the apron.

The front view is independently authored rather than projected from the
three-quarter view. Its hip sockets intentionally sit lower and farther apart
inside the pelvis than the perspective-view markers, while the shorter leg
segments keep Oiler's overall height consistent across views. The frontal skull
must retain full cheek and temple volume; asymmetry belongs in Euler's gaze and
cap folds, not in a narrowed head silhouette. Bake temporary Inkscape
translations into the path geometry before committing so visible limbs and rig
markers share one coordinate system.

## Artist hierarchy and rig metadata

The layer tree intentionally follows the manually authored PCA SVG rather than
exposing machine syntax as layer names. Perspective views use camera-depth
names because one limb genuinely overlaps the other:

```text
Arm - Far
Leg - Far
Leg - Near
Torso
Head
Arm - Near
Joints
```

The front view has no meaningful near/far distinction. It is always named from
**Oiler's own anatomical frame**, so his right arm appears on screen-left and
his left arm appears on screen-right:

```text
Arm - Left
Leg - Left
Leg - Right
Torso
Head
Arm - Right
Joints
```

Arms and legs contain `Upper`, `Lower`, and `Hand`/`Foot` layers. `Torso`
contains `Pelvis`, `Coat and Torso`, and `Apron`. `Head` contains a rigged
`Head Base`, expression layers, and editable sublayers for the face shape, cap,
hair, and facial details. Perspective-view `Joints` are split into core,
near/far arm, and near/far leg groups. Front-view `Joints` use left/right arm
and leg groups. In either case, a whole joint chain is easy to select.

Inkscape labels are strictly for humans. Rig bindings use ordinary SVG data
attributes on the relevant group or marker:

- `data-rig-part="<part name>"`
- `data-rig-bone="<bone name>"`
- `data-rig-z="<number>"`
- optional `data-rig-opacity="<channel>"`
- `data-rig-joint="<joint name>"`
- optional view-level `data-rig-side-map="left=far,right=near"`

This separation means the part sublayers can use readable names without
encoding machine syntax, while Inkscape may still renumber leaf path ids
safely. The top anatomical layer names remain a maintained authoring contract
so every view presents the same predictable tree. The generic extractor also
retains compatibility with the older `part:...` and `joint:...` label syntax
for other SVGs.

Ancestor grouping and transforms are respected by extraction. You can move or
resize an anatomical art layer, then make the corresponding adjustment to the
matching subgroup under `Joints`; a rebuild reads the resulting world-space
geometry. Avoid ungrouping the `data-rig-part` layers themselves, because those
are the rigid sprite boundaries.

Perspective-view source joints are `waist`, `neck`, and the `near`/`far`
versions of `shoulder`, `elbow`, `wrist`, `handtip`, `hip`, `knee`, `ankle`,
and `toe`. The front SVG uses `left_*` and `right_*` instead. Its view-level
side map normalizes those anatomical names to the shared runtime channels only
during extraction; the editable SVG never asks an artist to call Oiler's right
arm “near.”

## Rebuild

From `tools/ambition_sprite2d_renderer`:

```bash
uv run python scripts/build_oiler_rig.py build
uv run python scripts/build_oiler_rig.py validate
```

A normal build refreshes geometry and preserves hand-tuned animation clips in
the existing rig documents. It also removes the retired `tool_vis` and
`machine_vis` channels from old files. Use `build --fresh` only when
intentionally resetting the clips to the Python seed animation.

Publishing remains the normal target command:

```bash
uv run python -m ambition_sprite2d_renderer publish oiler
```
