"""Tests for the published-asset equivalence comparator.

These build a tiny synthetic rendered target (a RON manifest pair + a Pillow
sheet PNG) rather than rendering a real character, so they need only Pillow +
stdlib and stay fast — the comparator, not any target, is under test.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.core.equivalence import (
    CONTRACT,
    DIFFERS,
    EXACT,
    RASTER,
    compare_renders,
    load_render,
    parse_ron,
)

# --- RON reader ------------------------------------------------------------


def test_parse_ron_shapes_match_emitter() -> None:
    """The reader handles the emitted subset: list-wrapped struct, Some(( )),
    maps with string keys, nested tuples, negative floats, None/bools."""
    text = """
    // a comment
    [
    (
        target: "demo",
        frame_width: 124,
        tuning: Some((collision_scale: 1.72, frame_sample_inset: 0)),
        body_metrics: Some((
            body_pixel_bbox: Some((x: 26, y: 6, w: 82, h: 215)),
            feet_pixel: Some((x: 66.5, y: 220.0)),
            feet_anchor_norm: Some((x: 0.03629, y: -0.477778)),
        )),
        rows: [
            (animation: "idle", frame_count: 2, duration_ms: 120,
             rects: [(x: 0, y: 0, w: 16, h: 16, page: 0, off: (2, 3))]),
        ],
        maybe: None,
        flag: true,
    )
    ]
    """
    v = parse_ron(text)
    assert isinstance(v, list) and len(v) == 1
    sheet = v[0]
    assert sheet["target"] == "demo"
    assert sheet["frame_width"] == 124
    assert sheet["tuning"] == {"collision_scale": 1.72, "frame_sample_inset": 0}
    assert sheet["body_metrics"]["body_pixel_bbox"] == {"x": 26, "y": 6, "w": 82, "h": 215}
    assert sheet["body_metrics"]["feet_pixel"] == {"x": 66.5, "y": 220.0}
    assert sheet["body_metrics"]["feet_anchor_norm"]["y"] == -0.477778
    assert sheet["rows"][0]["rects"][0]["off"] == [2, 3]  # a tuple -> list
    assert sheet["maybe"] is None
    assert sheet["flag"] is True


def test_parse_ron_map_with_string_keys() -> None:
    v = parse_ron('(sockets: {"feet": (x: 1.0, y: 2.0), "head": (x: 3.0, y: 4.0)})')
    assert v["sockets"]["feet"] == {"x": 1.0, "y": 2.0}
    assert set(v["sockets"]) == {"feet", "head"}


# --- synthetic render fixtures --------------------------------------------

_SHEET_RON = """[
(
    target: "demo",
    image: "demo_spritesheet.png",
    label_width: 0,
    frame_width: 16,
    frame_height: 16,
    body_metrics: Some((body_pixel_bbox: Some((x: 2, y: 2, w: 12, h: 12)), feet_pixel: Some((x: 8.0, y: 14.0)))),
    rows: [
    (animation: "idle", row_index: 0, frame_count: 2, duration_ms: {idle_ms},
        rects: [
            (x: 0, y: 0, w: 16, h: 16, page: 0, off: (0, 0)),
            (x: 16, y: 0, w: 16, h: 16, page: 0, off: (0, 0)),
        ]),
    ],
)
]
"""

_ACTOR_RON = """(
    schema_version: 1,
    character_id: "demo",
    body: Some((collision: Some((w_px: 12.0, h_px: 12.0)))),
    sockets: {{
        "feet": (point: (x: 8.0, y: {feet_y})),
    }},
    tags: ["demo"],
)
"""


def _write_render(root: Path, *, idle_ms: int = 120, feet_y: float = 14.0,
                  color: tuple = (200, 60, 60, 255)) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "demo_spritesheet.ron").write_text(_SHEET_RON.format(idle_ms=idle_ms))
    (root / "demo_actor.ron").write_text(_ACTOR_RON.format(feet_y=feet_y))
    # A 32x16 sheet: two 16x16 frames, a filled 12x12 body box each.
    img = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for fx in (0, 16):
        for y in range(2, 14):
            for x in range(fx + 2, fx + 14):
                img.putpixel((x, y), color)
    img.save(root / "demo_spritesheet.png")
    return root


def test_self_compare_is_exact(tmp_path: Path) -> None:
    a = _write_render(tmp_path / "a")
    b = _write_render(tmp_path / "b")
    rep = compare_renders(load_render(a), load_render(b))
    assert rep.verdict == EXACT
    assert rep.structural_ok


def test_duration_drift_breaks_contract(tmp_path: Path) -> None:
    a = _write_render(tmp_path / "a", idle_ms=120)
    b = _write_render(tmp_path / "b", idle_ms=90)
    rep = compare_renders(load_render(a), load_render(b))
    assert rep.verdict == DIFFERS
    assert not rep.structural_ok
    anim = next(d for d in rep.dimensions if d.name == "animations")
    assert not anim.ok and any("duration_ms" in x for x in anim.diffs)


def test_socket_drift_breaks_contract(tmp_path: Path) -> None:
    a = _write_render(tmp_path / "a", feet_y=14.0)
    b = _write_render(tmp_path / "b", feet_y=9.0)
    rep = compare_renders(load_render(a), load_render(b))
    assert rep.verdict == DIFFERS
    meta = next(d for d in rep.dimensions if d.name == "metadata")
    assert not meta.ok and any("feet" in x for x in meta.diffs)


def test_pixel_only_redesign_is_contract_match(tmp_path: Path) -> None:
    """Same contract, materially different pixels -> a valid redesign result."""
    a = _write_render(tmp_path / "a", color=(200, 60, 60, 255))
    b = _write_render(tmp_path / "b", color=(40, 90, 220, 255))
    rep = compare_renders(load_render(a), load_render(b))
    assert rep.verdict == CONTRACT
    assert rep.structural_ok  # layout/animations/geometry/metadata all match
    pix = next(d for d in rep.dimensions if d.name == "pixels")
    assert not pix.ok


def test_small_pixel_delta_is_raster_equivalent(tmp_path: Path) -> None:
    a = _write_render(tmp_path / "a", color=(200, 60, 60, 255))
    b = _write_render(tmp_path / "b", color=(203, 63, 62, 255))  # within edge_tol=6
    rep = compare_renders(load_render(a), load_render(b), edge_tol=6, area_tol=1.0)
    assert rep.verdict == RASTER
    assert rep.structural_ok
