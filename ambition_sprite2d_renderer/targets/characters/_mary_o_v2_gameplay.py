"""Mary-O's gameplay body, per pose.

Her form authors ONE rectangle (`form_collision_box`): a fixed width around her
torso, from `collision_top_px` down to the shoe line. The width is the authored
half — it is what keeps her cap tip, ponytail, sleeves and flame frills from
stopping her against a wall — and it does not change with the pose.

Her HEIGHT does. Grown Mary-O has real crouch art: measured on the drawing, her
crouch silhouette starts 42 px lower than her standing one, a quarter of her
167 px stature, with the shoes on the same line. Publishing one rectangle for
every pose threw that away and left a crouching Mary-O with a standing body.

So: width and floor from the form, ceiling from the DRAWING, and a pose may
only be SHORTER than standing. That last clause is the whole rule — her jump art
reaches 12 px higher than her authored top because her cap does, and a body that
followed it would grow every time she leaves the ground.

The small form has no crouch row (small Mario cannot duck, and neither can she),
so every one of her poses resolves to the standing rectangle. That is the honest
answer, not a missing one.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from ._mary_o_v2_model import FormSpec, form_collision_box

RenderFrame = Callable[[str, int, int], "object"]


def _row_art_top(render_frame: RenderFrame, animation: str, frames: int) -> int | None:
    """The highest drawn pixel across one row, in published frame pixels."""
    top = None
    for index in range(max(1, frames)):
        bbox = render_frame(animation, index, frames).convert("RGBA").getbbox()
        if bbox is None:
            continue
        top = bbox[1] if top is None else min(top, bbox[1])
    return top


def _idle_row(form: FormSpec) -> Tuple[str, int]:
    for name, frames, _duration in form.rows:
        if name == "idle":
            return name, int(frames)
    name, frames, _duration = form.rows[0]
    return name, int(frames)


def body_rect(
    form: FormSpec,
    render_frame: RenderFrame,
    animation: str,
    frames: int,
    calibration: int,
) -> Dict[str, int]:
    box = form_collision_box(form)
    top = _row_art_top(render_frame, animation, frames)
    if top is not None:
        # `max`, not the art's own top: shorter than standing is a pose, taller
        # is a flourish. `calibration` is what makes `idle` reproduce the
        # authored rectangle to the pixel — her fire form's authored ceiling
        # sits 2 px above her drawn one, and without it every pose including
        # standing quietly lost those two pixels.
        box = {**box, "y": max(int(box["y"]), int(top) + calibration)}
        box["h"] = form.collision_bottom_px - box["y"]
    return {"name": "body", **{k: int(v) for k, v in box.items() if k != "name"}}


def hurtbox_parts_for_form(form: FormSpec, render_frame: RenderFrame) -> Dict[str, dict]:
    idle_name, idle_frames = _idle_row(form)
    idle_top = _row_art_top(render_frame, idle_name, idle_frames)
    calibration = 0 if idle_top is None else int(form.collision_top_px) - int(idle_top)
    out: Dict[str, dict] = {}
    for name, frames, _duration in form.rows:
        rect = body_rect(form, render_frame, name, int(frames), calibration)
        if rect["h"] > 0 and rect["w"] > 0:
            out[name] = {"parts": [rect]}
    return out
