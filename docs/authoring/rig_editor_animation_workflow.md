# Rig editor animation workflow

The rig editor distinguishes two different ideas that are easy to confuse:

- **channel keys** are the numeric values stored for an individual bone or
  parameter;
- **pose bookmarks** (stored as `pose_keys`) are editor-only landmarks for the important poses that explain
  the animation.

Generated clips may initially have channel keys on every frame. The editor can
still suggest a small pose-bookmark map from motion extrema, and shows those
suggestions as hollow diamonds. Double-click a frame in the pose strip or use
**Mark pose bookmark** to save/customize that map.

## Making in-betweens respond to edits

A densely baked channel has an explicit value on every frame, so changing one
frame cannot influence its neighbors. Use **Simplify selected** or **Simplify
full clip** to retain the sampled values at important pose frames and remove the
redundant per-frame keys. The remaining frames become interpolated in-betweens.
The operation is undoable and does not change the retained pose bookmarks.

Dragging a bone at an in-between automatically inserts only the channels that
the drag controls and marks the current frame as a pose bookmark. **Return selected
to interpolation** removes that current-frame key again.

A channel that has **never been authored before** is special: with only one key,
ordinary interpolation would make that value constant over the whole clip. The
editor therefore seeds the channel with its pre-edit value at every discrete
frame before changing the frame you touched. This keeps the first drag local.
Once a channel is sparse, editing one of its keys can still change the
*interpolated in-betweens* on either side; that is expected animation behavior.
`Ctrl+drag` is different again: it edits a bone attachment in the rig structure,
so that intentionally changes every frame.

## Viewport context

All overlays are independent and can be displayed together from the viewport
toolbar:

- current bones;
- previous/next pose ghosts;
- immediate frame onion skin;
- selected endpoint motion trail;
- selected-chain in-between ghosts;
- collision, hurtbox, and hitbox geometry.

Gameplay geometry remains visible while animation bones are edited. Enable
**Edit geometry** only when shapes should intercept canvas dragging; otherwise
bone manipulation remains the active canvas interaction.

## Pose strip legend

- filled diamond: saved pose bookmark;
- hollow diamond: automatically suggested pose bookmark;
- yellow dot: selected channel has an explicit key;
- gray bar: fraction of animation channels keyed at that frame;
- bright vertical line: current frame.

Click a frame to select it. Double-click to mark or unmark it as an important
pose.

## Temporal colors

The same colors are used everywhere temporal direction appears:

- **blue — BEFORE**: the previous important pose;
- **purple — AFTER**: the following important pose;
- **yellow — NOW**: the current editing frame.

The canvas includes a labeled legend. The corresponding pose diamonds and
navigation buttons on the timeline use the same colors, so authors do not need
to infer which ghost is earlier or later.

## Planting a hand or foot

Right-click a selected endpoint on the canvas and choose **Plant this endpoint
here through the animation**. The editor solves that world-space position at
every important pose and removes conflicting baked keys for the controlled
channels. Constant values then interpolate through the in-between frames.
Horizontal-only and vertical-only variants are available for sliding or floor
contact.

For an IK foot this writes its target x, lift, and pitch channels. This is the
recommended way to remove an accidental idle "march": park the main canvas on
the desired foot position, select the foot, and plant it through the animation.
The operation is undoable.

**Copy selected controls to every pose key** is the local-space alternative. It
copies the current channel values and is useful when matching orientation or a
repeated local pose matters more than matching a world-space endpoint.

## Live loop preview

The **Live Loop Preview** dock continuously plays the selected clip from the
current in-memory rig. It has its own play/pause and restart controls and never
moves the main editing playhead. This lets the main canvas stay focused on one
pose, selected limb, ghosts, and geometry while the separate pane immediately
shows the full-motion consequence of every edit.

## Editable pose sheet view

The editor has two **primary center views** and one independent Timeline dock:

- **Single pose** is the detailed art, gameplay-geometry, pin, and one-frame editing surface.
- **Pose sheet** lays the complete clip out horizontally and is itself a direct pose editor.
- **Timeline** remains visible independently for timing, interpolation, and channel details; the pose sheet does not replace it.

In the Pose sheet, every frame is a skeleton column. The column header shows both animation and editorial state: **diamonds are pose bookmarks**, a **gray bar is actual channel-key density**, and a **gold dot means the selected control has a real key on that frame**. Hollow diamonds are automatic pose suggestions; filled diamonds are saved bookmarks. Pose bookmarks do not drive interpolation.

Interactions are intentionally the same pose vocabulary as the single-pose canvas:

- click/drag a bone in any column to select that frame and write the FK rotation there;
- `Alt+drag` a free hand/foot endpoint to solve its two-bone limb and write the two pose keys into that column;
- drag a document-IK foot to write that frame's IK target;
- `Ctrl+drag` a joint to change the structural attachment offset (a rig-wide edit, not a per-frame value);
- double-click a **column header** to mark/unmark that frame as an important key pose;
- enable **pose bookmarks only** to reduce a long clip to its authored extremes;
- widen columns for reliable joint manipulation or narrow them for silhouette/motion review.

`Ctrl+Shift+P` switches the center to Pose sheet; `Ctrl+Shift+1` returns to Single pose. Selection and the current frame are shared, so the Bones/Parts panels and Timeline follow whichever column you are editing.

The sheet deliberately does **not** pretend gameplay geometry or persistent whole-clip pins are local to one frame. Those remain in Single pose, where their scope is explicit.

The Timeline remains a vertically resizable bottom dock. Drag its top splitter upward to give the advanced channel editor more room; the Timeline widget expands with the dock, while scroll bars still appear when the window becomes smaller than its contents. On a small screen it therefore scrolls instead of forcing the outer window larger than the desktop. `Ctrl+M` toggles maximize/restore and `F11` toggles full screen.
