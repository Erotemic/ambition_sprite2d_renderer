# Rig editor animation workflow

The rig editor distinguishes two different ideas that are easy to confuse:

- **channel keys** are the numeric values stored for an individual bone or
  parameter;
- **pose keys** are editor-only bookmarks for the important poses that explain
  the animation.

Generated clips may initially have channel keys on every frame. The editor can
still suggest a small pose-key map from motion extrema, and shows those
suggestions as hollow diamonds. Double-click a frame in the pose strip or use
**Mark key pose** to save/customize that map.

## Making in-betweens respond to edits

A densely baked channel has an explicit value on every frame, so changing one
frame cannot influence its neighbors. Use **Simplify selected** or **Simplify
full clip** to retain the sampled values at important pose frames and remove the
redundant per-frame keys. The remaining frames become interpolated in-betweens.
The operation is undoable and does not change the retained key poses.

Dragging a bone at an in-between automatically inserts only the channels that
the drag controls and marks the current frame as a pose key. **Return selected
to interpolation** removes that current-frame key again.

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

- filled diamond: saved pose key;
- hollow diamond: automatically suggested pose key;
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
