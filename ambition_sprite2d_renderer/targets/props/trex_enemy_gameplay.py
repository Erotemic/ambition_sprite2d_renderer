"""Compile the T-rex's gameplay geometry without a sheet or image payloads."""
from pathlib import Path

from ..characters import trex_enemy
from ..characters._trex_enemy_body_rig import body_rig
from ...authoring.sheet_build import alpha_bbox_metrics

TARGET_NAME = "trex_enemy_gameplay"
SHEET_FILES = (TARGET_NAME + "_body_rig.ron",)
PORTRAIT_FILES = ()
PUBLICATION_TIERS = ["full"]


def render(out_dir, **opts):
    # Sheet metrics use frame zero of the first row. Measure the same pose.
    animation, frames, _duration = trex_enemy.ROWS[0]
    frame = trex_enemy.render_frame(animation, 0, frames)
    feet = alpha_bbox_metrics(frame)["feet_pixel"]
    point = (float(feet["x"]), float(feet["y"]))
    product = body_rig(trex_enemy._doc(), TARGET_NAME, trex_enemy.ROWS, {}, point)
    product.origin_from_centre = (point[0] - frame.width / 2.0, point[1] - frame.height / 2.0)
    return [product.write(Path(out_dir))]
