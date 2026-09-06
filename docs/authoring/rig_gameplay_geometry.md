# Rig gameplay geometry authoring

`gameplay_geometry` is an authoring-only, versioned block stored in a
`.rig.json` document. The implementation deliberately does **not** feed sheet
publication or the game runtime yet. It exists so collision, hurtbox, hitbox,
VFX, and SFX authoring can mature without changing current gameplay.

## Generated seeds

The Geometry tab reports missing coverage and can generate editable rectangle
seeds:

- **Collision** uses the alpha bounds of frame 0 of `idle` (or the first clip).
- **Hurtboxes** measure the union alpha bounds of every frame in each clip, then
  cluster similar measurements into a small set of named shared profiles. Clips
  reference a profile instead of receiving unrelated copies. The generated
  profile rectangle uses the median bounds of its member clips.
- **Hitboxes** use the current clip's active frames and the most relevant
  hand/foot terminal path, extended by a conservative reach allowance. This is
  only a starting suggestion and is marked with a review warning.

Rectangles are the compatibility seed, not a schema restriction. Collision,
hurtbox, and hitbox entries each own a `shapes` list. A shape may be:

- `rect`: `x`, `y`, `w`, `h`
- `circle`: `cx`, `cy`, `r`
- `capsule`: `ax`, `ay`, `bx`, `by`, `r`
- `polygon`: an ordered `points` list

An older authoring document with a singular `shape` field remains readable and
is migrated to `shapes` when it is first edited.

## Shared hurtbox profiles

Collision remains one global character-level entry. Hurtboxes use explicit
named profiles plus clip assignments:

```json
{
  "hurtboxes": {
    "profiles": {
      "standing": {"shapes": []},
      "airborne": {"shapes": []}
    },
    "clips": {
      "idle": {"profile": "standing"},
      "walk": {"profile": "standing"},
      "jump": {"profile": "airborne"}
    }
  }
}
```

The Geometry panel always states the source being edited and lists the clips
that share it. Editing `standing` while viewing `idle` therefore updates every
clip linked to `standing`. A clip may be reassigned to another profile, may
duplicate its current geometry into a new profile, or may create a local
override. Local overrides copy the resolved profile once and then affect only
the current clip. **Use shared profile** removes the override and rejoins the
assigned profile.

Version-1 per-clip hurtbox entries remain readable as legacy local overrides.
They can be assigned or duplicated into named profiles from the editor.

## Visual editing

Choose the active collision, hurtbox, or hitbox layer in the Geometry panel and
enable **Edit selected layer by dragging on canvas**. Click a shape to select it.

- Drag inside any shape to translate it.
- Drag rectangle corners to resize it.
- Drag a circle center or radius handle.
- Drag capsule endpoints or its radius handle.
- Drag individual polygon vertices.

Only the selected geometry layer intercepts canvas clicks. Disable canvas
geometry editing when ordinary bone manipulation should take priority.

The panel provides exact numeric control over all primitive parameters. It can
add and delete shapes, convert a selected primitive while retaining its visual
bounds, and edit polygon vertices in a coordinate table. Concave polygons are
preserved but visibly reported because a future deterministic runtime export may
require convex polygons.

## Provenance and bindings

All geometry is stored in logical rig-frame pixels. Generated entries carry
`provenance.generated`, `provenance.method`, and `provenance.edited`. Visual or
numeric edits mark the owning entry edited. A generator never overwrites
existing geometry without confirmation.

Hitbox entries also hold an active-frame interval and optional lists of VFX and
SFX cue identifiers. These bindings are not resolved or published yet; they
reserve the authoring contract for later attack-event integration.

The Player Robot builder preserves `gameplay_geometry` across deterministic
SVG/animation regeneration. Unknown rig fields are otherwise ignored by the
current renderer and publication path.
