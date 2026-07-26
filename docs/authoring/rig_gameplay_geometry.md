# Rig gameplay geometry authoring

`gameplay_geometry` is an authoring-only, versioned block stored in a
`.rig.json` document.  The first implementation deliberately does **not** feed
sheet publication or the game runtime.  It exists so collision, hurtbox,
hitbox, VFX, and SFX authoring can mature without changing current gameplay.

The Geometry tab reports missing coverage and can generate editable rectangle
seeds:

- **Collision** uses the alpha bounds of frame 0 of `idle` (or the first clip).
- **Hurtboxes** use the union alpha bounds of every frame in each clip, matching
  the broad behavior of the current automatically-derived sheet metadata.
- **Hitboxes** use the current clip's active frames and the most relevant
  hand/foot terminal path, extended by a conservative reach allowance.  This is
  only a starting suggestion and is marked with a review warning.

All geometry is stored in logical rig-frame pixels.  Generated entries carry
`provenance.generated`, `provenance.method`, and `provenance.edited`.  Numeric
edits in the GUI mark the entry edited.  A generator never overwrites existing
geometry without confirmation.

Hitbox entries also hold an active-frame interval and optional lists of VFX and
SFX cue identifiers.  These bindings are not resolved or published yet; they
reserve the authoring contract for the later attack-event integration.

The Player Robot builder preserves `gameplay_geometry` across deterministic
SVG/animation regeneration.  Unknown rig fields are otherwise ignored by the
current renderer and publication path.
