# Continuous rigid-part pins in the rig editor

A transform pin is a persistent frame-space IK constraint. It is different
from copying or baking joint angles at pose keys:

- a baked pose is exact only on keyed frames;
- a continuous pin is solved at every sampled time;
- the selected bone's position can remain fixed while its parents move;
- when rotation is locked, all artwork attached to the selected bone and its
  descendants behaves as one rigid assembly.

This does **not** mean that artwork on the foot's parent lower-leg bone is also
locked. A pin cannot make two independently articulated bones one rigid object.
The same mechanism can pin a hand, held tool, or another endpoint part with a
solvable parent chain.

## Idle workflow

1. Open the clip and choose a frame whose foot placement looks correct.
2. Click either foot.
3. Press **Pin both foot-bone assemblies** in the timeline, or right-click the
   foot and choose **Pin both foot-bone assemblies for entire clip**.
4. Animate `root_y`, pelvis motion, torso counter-motion, or other body controls.
5. Watch the independent loop preview. Green timeline bars and green transform
   pins show that both foot-bone assemblies are continuously constrained.
6. Drag either the green pin or the artwork controlled by that pin to reposition
   the target. Right-clicking elsewhere also offers **Move pin target to this
   point**. These operations edit the constraint, not animation keys.
7. Use **Release selected** when the part should move normally again.

## General part workflow

1. Select a hand, foot, prop endpoint, or another part with a two-segment parent
   chain.
2. Right-click the point on the artwork that should stay fixed.
3. Choose **Pin whole selected part here for entire clip**.
4. The clicked point becomes the anchor and the current world rotation is
   locked. The whole selected part remains rigid.
5. Alternatively choose **Pin this point, allow animated rotation** when the
   anchor should stay fixed but authored rotation should continue.

The timeline button **Pin selected part** uses the selected bone origin as the
anchor. The right-click action is often more intuitive because any visible
point on the selected part can become the anchor.

## Data format

Constraints are stored outside generated clip channels so rebuild scripts can
preserve them:

```json
{
  "animation_constraints": {
    "version": 2,
    "clips": {
      "idle": {
        "pins": [
          {
            "bone": "near_leg_foot",
            "anchor_local": [15.79, 0.0],
            "target": [110.55, 156.26],
            "rotation": 17.103,
            "lock_x": true,
            "lock_y": true,
            "lock_rotation": true,
            "scope": "clip",
            "start_frame": 0,
            "end_frame": 7,
            "role": "foot",
            "solver": {
              "upper": "near_leg_u",
              "lower": "near_leg_l",
              "bend": 1.0
            },
            "enabled": true
          }
        ]
      }
    }
  }
}
```

Version-one `foot_plants` are migrated to this single generic `pins` list when
the rig is opened and then saved. Whole-clip pins are the initial UX, while the
schema continues to support frame ranges for future walk-cycle contact windows.

## Kinematic limit

A continuous rigid transform pin requires a parent chain with enough degrees of
freedom. Hands and feet naturally have upper/lower limb chains. Very high-level
parts such as the pelvis or root cannot always be pinned without also deciding
which larger body chain is allowed to compensate; the editor leaves those parts
unavailable rather than silently disconnecting the skeleton.

### Player Robot boot grouping

The current Player Robot SVG has two separate lower-limb visual groups:

- `near_leg_l` / `far_leg_l`, labeled **Lower Leg / Boot**, are attached to the
  lower-leg bones;
- `near_foot` / `far_foot`, labeled **Foot / Toes**, are attached to the foot
  bones.

A foot pin exactly holds the foot-bone origin, orientation, and every visual
part attached to that bone. The lower-leg/boot group still rotates while the
knee bends, which is correct for its current bone ownership. If the white boot
shell is intended to remain rigid with the toes, the SVG must be redrawn or
split so the rigid shoe artwork belongs to the foot bone and only the shin
artwork belongs to the lower-leg bone. Trying to constrain both existing groups
while also allowing arbitrary pelvis bob would overconstrain the two-joint leg.

## Scope

This is submodule-side rig evaluation and authoring metadata. No game crate
reads `animation_constraints`. If a rig is later rendered or published, its
resulting sprite frames naturally include the constrained motion.
