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

Dragging a bone at an in-between inserts only the channels that control owns.
It does **not** create a pose bookmark: numerical/property keys and editorial
bookmarks are intentionally independent. **Remove selected key → interpolate**
removes that current-frame control key again.

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

## Keying model and legends

The rig follows the same core model used by professional animation tools: **a
control/property is keyed at a time**, not an entire frame. One elbow can have a
key while the shoulder and opposite leg interpolate. A persistent pin is a
constraint, not a stronger kind of key.

Timeline / pose-strip header:

- filled diamond: saved pose bookmark;
- hollow diamond: automatically suggested pose bookmark;
- yellow dot: selected channel has an explicit property key;
- gray bar: fraction of animation channels keyed at that frame;
- bright vertical line: current frame.

Pose-sheet joint/control handles:

- **gold filled**: every property of that handle is explicitly keyed here;
- **half gold / half cyan**: a multi-axis control is partially keyed;
- **cyan ring**: the control has animation channels but this frame is interpolated;
- **gray ring**: untouched/static rest value;
- **violet ring**: constant or procedural channel;
- **magenta ring**: the joint is solver output from an IK endpoint;
- **green outer box**: a persistent transform pin/constraint is active.

For IK feet/hands, the endpoint **origin** and **tip** are separate controls:
origin keys position, while the tip keys orientation/pitch.

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

In the Pose sheet, every frame is a skeleton column. The column header shows
both animation and editorial state: **diamonds are pose bookmarks** and a **gray
bar is actual property-key density**. The joints themselves show the detailed
control state using the colors above. Hollow diamonds are automatic pose
suggestions; filled diamonds are saved bookmarks. Pose bookmarks do not drive
interpolation.

Interactions are intentionally the same pose vocabulary as the single-pose canvas:

- click/drag an FK control in any column to select that frame and write its rotation there;
- `Alt+drag` a free endpoint to solve its two-bone limb and write the two FK control keys into that column;
- drag an IK foot/hand **origin** to write its position target;
- drag the endpoint **tip/arc handle** to pivot its orientation independently;
- `Ctrl+drag` a joint to change the structural attachment offset (a rig-wide edit, not a per-frame value);
- double-click a **column header** to mark/unmark that frame as an important key pose;
- enable **pose bookmarks only** to reduce a long clip to its authored extremes;
- widen columns for reliable joint manipulation or narrow them for silhouette/motion review;
- mouse-wheel/trackpad-scroll over the sheet to zoom every pose around the same anatomical point; **the entire frame column grows with the anatomy**, including its header, hit region, separator, and scroll extent, so zoomed rigs never drift away from their frame labels or overlap adjacent poses;
- middle-drag or hold `Space` and left-drag to pan the shared body-space camera;
- use **Fit poses** to return to the common fitted view.

`Ctrl+Shift+P` switches the center to Pose sheet; `Ctrl+Shift+1` returns to Single pose. Selection and the current frame are shared, so the Bones/Parts panels and Timeline follow whichever column you are editing.

The sheet deliberately does **not** pretend gameplay geometry or persistent whole-clip pins are local to one frame. Those remain in Single pose, where their scope is explicit.

The Timeline remains a vertically resizable bottom dock. Drag its top splitter upward to give the advanced channel editor more room; the Timeline widget expands with the dock, while scroll bars still appear when the window becomes smaller than its contents. On a small screen it therefore scrolls instead of forcing the outer window larger than the desktop. `Ctrl+M` toggles maximize/restore and `F11` toggles full screen.

## Endpoint position versus orientation

The pose sheet exposes endpoint position and orientation as separate handles. In
Single pose, where there is only one compact joint hit target, **Shift+drag** an
IK foot/hand to pivot its pitch without moving the target. Ordinary drag moves
the IK target; `Alt+drag` remains temporary two-bone IK for free FK endpoints.
This mirrors the storage model: translation and rotation can be keyed
independently.
