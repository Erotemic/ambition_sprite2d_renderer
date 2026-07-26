"""Authoring-time animation constraints for rig documents.

The primary constraint is a frame-space *transform pin*.  A pin keeps an
arbitrary local point on a selected bone at a fixed frame-space target and can
also preserve the bone's world rotation.  Because the pin is evaluated after
channel sampling for every rendered time, parent motion may continue while a
hand, foot, prop, or other endpoint remains planted continuously.

A locked rotation makes the selected bone and every visual part attached to it
behave as one rigid assembly.  For example, pinning a foot bone holds both the
boot artwork and its toe point rather than merely baking the toe position at a
few keyframes.

The schema is stored outside clip channel data so rig generators can preserve
it while rebuilding animations::

    "animation_constraints": {
      "version": 2,
      "clips": {
        "idle": {
          "pins": [
            {
              "bone": "near_leg_foot",
              "anchor_local": [12.0, 0.0],
              "target": [94.0, 188.0],
              "rotation": 0.0,
              "lock_rotation": true,
              "scope": "clip",
              "solver": {
                "upper": "near_leg_u",
                "lower": "near_leg_l",
                "bend": 1.0
              },
              "role": "foot"
            }
          ]
        }
      }
    }

Version-one ``foot_plants`` are migrated in memory to version-two pins the
first time the clip constraints are accessed.  The game does not consume this
metadata directly.  It affects editor previews and any sprite frames later
rendered from the rig.
"""

from __future__ import annotations

from typing import Optional, Tuple

Point = Tuple[float, float]


def constraints_root(doc, *, create: bool = True) -> dict:
    """Return the versioned animation-constraint root."""
    root = doc.data.get("animation_constraints")
    if not isinstance(root, dict):
        if not create:
            return {}
        root = {"version": 2, "clips": {}}
        doc.data["animation_constraints"] = root
    root.setdefault("version", 2)
    root.setdefault("clips", {})
    return root


def _legacy_plant_to_pin(plant: dict) -> dict:
    bone = str(plant.get("foot") or plant.get("bone") or "")
    solver = {
        "upper": str(plant.get("upper") or ""),
        "lower": str(plant.get("lower") or ""),
        "bend": float(plant.get("bend", 1.0)),
    }
    return {
        "bone": bone,
        "anchor_local": [0.0, 0.0],
        "target": list(plant.get("target") or [0.0, 0.0]),
        "rotation": float(plant.get("pitch", plant.get("rotation", 0.0))),
        "lock_x": bool(plant.get("lock_x", True)),
        "lock_y": bool(plant.get("lock_y", True)),
        "lock_rotation": bool(plant.get("lock_rotation", True)),
        "scope": plant.get("scope", "clip"),
        "start_frame": int(plant.get("start_frame", 0)),
        "end_frame": int(plant.get("end_frame", 0)),
        "enabled": bool(plant.get("enabled", True)),
        "role": "foot",
        "channel_prefix": str(plant.get("channel_prefix", "")),
        "solver": solver,
    }


def clip_constraints(doc, clip_name: str, *, create: bool = True) -> dict:
    root = constraints_root(doc, create=create)
    clips = root.get("clips")
    if not isinstance(clips, dict):
        if not create:
            return {}
        clips = {}
        root["clips"] = clips
    entry = clips.get(clip_name)
    if not isinstance(entry, dict):
        if not create:
            return {}
        entry = {"pins": []}
        clips[clip_name] = entry

    # One-time, in-memory migration from the first foot-only schema.  Delete the
    # old list so there remains one authoring authority after the next save.
    if "pins" not in entry and isinstance(entry.get("foot_plants"), list):
        entry["pins"] = [
            _legacy_plant_to_pin(plant)
            for plant in entry.get("foot_plants", [])
            if isinstance(plant, dict) and (plant.get("foot") or plant.get("bone"))
        ]
        entry.pop("foot_plants", None)
        root["version"] = 2
    entry.setdefault("pins", [])
    return entry


def transform_pins(doc, clip_name: str, *, create: bool = True) -> list[dict]:
    entry = clip_constraints(doc, clip_name, create=create)
    pins = entry.get("pins")
    if not isinstance(pins, list):
        if not create:
            return []
        pins = []
        entry["pins"] = pins
    return pins


def pin_for_bone(doc, clip_name: str, bone_name: str) -> Optional[dict]:
    for pin in transform_pins(doc, clip_name, create=False):
        if pin.get("bone") == bone_name:
            return pin
    return None


def _frame_position(clip: dict, t: float) -> float:
    frames = max(1, int(clip.get("frames", 1)))
    if bool(clip.get("loop", True)):
        return (float(t) % 1.0) * frames
    if frames <= 1:
        return 0.0
    return max(0.0, min(1.0, float(t))) * (frames - 1)


def pin_active(clip: dict, pin: dict, t: float) -> bool:
    """Whether ``pin`` covers continuous time ``t``."""
    if pin.get("enabled", True) is False:
        return False
    if pin.get("scope") == "clip":
        return True
    frames = max(1, int(clip.get("frames", 1)))
    start = max(0, min(frames - 1, int(pin.get("start_frame", 0))))
    end = max(0, min(frames - 1, int(pin.get("end_frame", frames - 1))))
    if start == 0 and end == frames - 1:
        return True
    position = _frame_position(clip, t)
    position %= frames if bool(clip.get("loop", True)) else max(1, frames)
    lower = start - 0.5
    upper = end + 0.5
    if start <= end:
        return lower <= position <= upper
    return position >= lower or position <= upper


def active_pin_for_bone(doc, clip_name: str, bone_name: str, t: float) -> Optional[dict]:
    clip = doc.clips.get(clip_name) or {}
    pin = pin_for_bone(doc, clip_name, bone_name)
    if pin is not None and pin_active(clip, pin, t):
        return pin
    return None


def upsert_full_clip_pin(
    doc,
    clip_name: str,
    *,
    bone_name: str,
    anchor_local: Point,
    target: Point,
    rotation: float,
    upper: str,
    lower: str,
    bend: float,
    lock_rotation: bool = True,
    role: str = "part",
    channel_prefix: str = "",
    solver_mode: str = "endpoint_bone",
) -> dict:
    """Create or replace a whole-clip transform pin for one bone."""
    clip = doc.clips.get(clip_name) or {}
    frames = max(1, int(clip.get("frames", 1)))
    pin = pin_for_bone(doc, clip_name, bone_name)
    if pin is None:
        pin = {}
        transform_pins(doc, clip_name).append(pin)
    pin.clear()
    pin.update(
        {
            "bone": str(bone_name),
            "anchor_local": [
                round(float(anchor_local[0]), 3),
                round(float(anchor_local[1]), 3),
            ],
            "target": [round(float(target[0]), 3), round(float(target[1]), 3)],
            "rotation": round(float(rotation), 3),
            "lock_x": True,
            "lock_y": True,
            "lock_rotation": bool(lock_rotation),
            "scope": "clip",
            "start_frame": 0,
            "end_frame": frames - 1,
            "enabled": True,
            "role": str(role),
            "channel_prefix": str(channel_prefix),
            "solver": {
                "upper": str(upper),
                "lower": str(lower),
                "bend": float(bend),
                "mode": str(solver_mode),
            },
        }
    )
    return pin


def remove_pin(doc, clip_name: str, bone_name: str) -> bool:
    pins = transform_pins(doc, clip_name, create=False)
    before = len(pins)
    pins[:] = [pin for pin in pins if pin.get("bone") != bone_name]
    return len(pins) != before


def update_pin_target(
    doc,
    clip_name: str,
    bone_name: str,
    target: Point,
    *,
    rotation: Optional[float] = None,
) -> bool:
    pin = pin_for_bone(doc, clip_name, bone_name)
    if pin is None:
        return False
    new_target = [round(float(target[0]), 3), round(float(target[1]), 3)]
    changed = pin.get("target") != new_target
    pin["target"] = new_target
    if rotation is not None:
        new_rotation = round(float(rotation), 3)
        changed = changed or float(pin.get("rotation", new_rotation)) != new_rotation
        pin["rotation"] = new_rotation
    return changed


def pinned_bones(doc, clip_name: str) -> set[str]:
    return {
        str(pin.get("bone"))
        for pin in transform_pins(doc, clip_name, create=False)
        if pin.get("enabled", True) and pin.get("bone")
    }


# ---------------------------------------------------------------------------
# Backward-compatible foot-oriented API used by older editor call sites/tests.


def foot_plants(doc, clip_name: str, *, create: bool = True) -> list[dict]:
    return [
        pin
        for pin in transform_pins(doc, clip_name, create=create)
        if pin.get("role") == "foot"
    ]


def plant_for_foot(doc, clip_name: str, foot_name: str) -> Optional[dict]:
    pin = pin_for_bone(doc, clip_name, foot_name)
    return pin if pin is not None and pin.get("role") == "foot" else None


def plant_active(clip: dict, plant: dict, t: float) -> bool:
    return pin_active(clip, plant, t)


def active_plant_for_foot(doc, clip_name: str, foot_name: str, t: float) -> Optional[dict]:
    pin = active_pin_for_bone(doc, clip_name, foot_name, t)
    return pin if pin is not None and pin.get("role") == "foot" else None


def upsert_full_clip_plant(
    doc,
    clip_name: str,
    *,
    foot_name: str,
    channel_prefix: str,
    target: Point,
    pitch: float,
    lock_rotation: bool = True,
    upper: Optional[str] = None,
    lower: Optional[str] = None,
    bend: Optional[float] = None,
) -> dict:
    if upper is None or lower is None:
        leg = doc.foot_leg_for_bone(foot_name)
        if leg is not None:
            upper = str(leg.get("upper") or upper or "")
            lower = str(leg.get("lower") or lower or "")
            if bend is None:
                bend = float(leg.get("bend", 1.0))
        else:
            foot = doc.bone(foot_name)
            lower_bone = doc.bone((foot or {}).get("parent") or "")
            upper_bone = doc.bone((lower_bone or {}).get("parent") or "")
            upper = str((upper_bone or {}).get("name") or upper or "")
            lower = str((lower_bone or {}).get("name") or lower or "")
    return upsert_full_clip_pin(
        doc,
        clip_name,
        bone_name=foot_name,
        anchor_local=(0.0, 0.0),
        target=target,
        rotation=pitch,
        upper=str(upper or ""),
        lower=str(lower or ""),
        bend=float(1.0 if bend is None else bend),
        lock_rotation=lock_rotation,
        role="foot",
        channel_prefix=channel_prefix,
        solver_mode="endpoint_bone",
    )


def remove_foot_plant(doc, clip_name: str, foot_name: str) -> bool:
    return remove_pin(doc, clip_name, foot_name)


def update_plant_target(
    doc,
    clip_name: str,
    foot_name: str,
    target: Point,
    *,
    pitch: Optional[float] = None,
) -> bool:
    return update_pin_target(
        doc, clip_name, foot_name, target, rotation=pitch
    )


def planted_feet(doc, clip_name: str) -> set[str]:
    return {
        str(pin.get("bone"))
        for pin in foot_plants(doc, clip_name, create=False)
        if pin.get("enabled", True) and pin.get("bone")
    }
