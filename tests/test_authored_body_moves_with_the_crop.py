"""An authored body is published in the frame the sheet publishes.

Regression: ``body_metrics_fn`` and ``hurtbox_parts`` state a body in the frame
a target draws, and the auto-crop then cut that frame without moving them. The
Officer's feet were drawn 29 px above the bottom of his box, which stood below
the bottom of his cropped frame.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw
from yaml import safe_load

from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

#: The figure, drawn in a 64x64 frame: the auto-crop (margin 2) cuts 18 rows
#: off the top and 8 columns off the left.
FIGURE = (10, 20, 30, 50)


def _frame(_anim, _idx, _count):
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((FIGURE[0], FIGURE[1], FIGURE[2] - 1, FIGURE[3] - 1), fill=(200, 40, 40, 255))
    return image


def test_an_authored_body_and_its_parts_move_with_the_auto_crop(tmp_path: Path):
    x0, y0, x1, y1 = FIGURE
    body = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
    outputs = build_sheet(
        target="crop_body_test",
        rows=[("idle", 1, 100)],
        render_fn=_frame,
        out_dir=tmp_path,
        frame_size=(64, 64),
        label_width=1,
        crop_margin=2,
        body_metrics_fn=lambda fw, fh: {
            "body_pixel_bbox": dict(body),
            "feet_pixel": {"x": (x0 + x1) / 2.0, "y": float(y1 - 1)},
            "feet_anchor_norm": {"x": 0.0, "y": 0.0},
        },
        animation_key_map={"idle": "idle"},
        hurtbox_parts={"idle": {"parts": [{"name": "body", **body}]}},
        pose_bodies="authored",
    )
    manifest = safe_load(outputs["yaml"].read_text(encoding="utf8"))
    fh = manifest["frame_height"]
    published = {"x": x0 - 8, "y": y0 - 18, "w": x1 - x0, "h": y1 - y0}
    metrics = manifest["body_metrics"]
    assert metrics["body_pixel_bbox"] == published
    assert metrics["animations"]["idle"]["hurtbox"]["bbox"] == published
    assert metrics["feet_pixel"]["y"] == y1 - 1 - 18
    assert abs(metrics["feet_anchor_norm"]["y"] - (0.5 - (y1 - 1 - 18) / fh)) < 1e-6
