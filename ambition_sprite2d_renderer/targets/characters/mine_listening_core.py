"""Draw the mineral core that speaks after Mother Lode's shell breaks."""
from math import sin, tau
from pathlib import Path

from ._clockwork_enemy_art import Canvas, phase
from .mother_lode import AMBER, BEDROCK, COPPER, IRON, OXIDES, SLATE, bevel, core, crystal, vein
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = "mine_listening_core"
FRAME_SIZE = (240, 190)
BODY = (68, 70, 176, 170)
ROWS = [("idle", 12, 125)]
ACTOR_METADATA = {
    "actor": {"character_id": "npc_mine_lode_core", "display_name": "The Listening Seam"},
    "body": {"body_plan": "Prop", "body_kind": "Wide", "mass_class": "Heavy", "locomotion_hint": "Static"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "tags": ["science", "mine", "elemental", "peaceful"],
}


def render_frame(_animation, index, count):
    c = Canvas(FRAME_SIZE, super_scale=2)
    pulse = 0.55 + 0.24 * sin(tau * phase(index, count, True))
    bevel(c, [(23, 168), (31, 137), (59, 125), (78, 92), (109, 86), (128, 112),
              (157, 102), (181, 127), (203, 134), (218, 166), (199, 170), (37, 170)],
          BEDROCK, width=0.19, seed=15)
    crystal(c, (65, 135), (45, 82), 14, OXIDES[2])
    crystal(c, (90, 118), (74, 59), 15, OXIDES[1])
    crystal(c, (159, 126), (179, 66), 17, OXIDES[3])
    crystal(c, (173, 154), (200, 116), 13, OXIDES[4])
    bevel(c, [(35, 166), (46, 143), (69, 129), (91, 134), (112, 161), (95, 169)],
          SLATE, width=0.17, seed=31)
    bevel(c, [(143, 156), (159, 132), (185, 130), (207, 147), (214, 167), (174, 170)],
          IRON, width=0.17, seed=37)
    vein(c, [(52, 155), (69, 146), (90, 149), (107, 131)], COPPER, pulse * 0.65)
    vein(c, [(147, 131), (166, 149), (179, 146), (197, 156)], COPPER, pulse * 0.65)
    core(c, (126, 130), 1.55, pulse)
    bevel(c, [(82, 167), (97, 150), (113, 156), (134, 154), (153, 149), (174, 168), (148, 170), (95, 170)],
          BEDROCK, light=0.41, seed=42)
    vein(c, [(104, 161), (117, 164), (132, 158), (151, 158)], AMBER, pulse * 0.5)
    return c.finish()


def render(out_dir: str | Path, **_opts):
    outputs = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=render_frame, out_dir=Path(out_dir),
                          frame_size=FRAME_SIZE, auto_crop=False, actor_metadata=ACTOR_METADATA,
                          body_metrics_fn=lambda w, h: body_metrics_for_box(BODY, w, h), sits_on_ground=True)
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]
