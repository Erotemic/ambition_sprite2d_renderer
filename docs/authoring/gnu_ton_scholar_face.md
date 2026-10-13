# GNU-ton Scholar: the face

The scholar is an old, stern man in a full wig: a long face, a long nose with
a small hook, small eyes under heavy brows, a hollow cheek, a thin mouth. The
wig is parted at the top, it has three big curls in front of the ear, and it
falls down his back (the part `wig_queue`, which swings on its own bone). No
hair is in front of his neck. Jon chose this head from a sheet of five on
2026-10-13; the head before it was a round face with a blush, a triangle for a
nose and large eyes (the "D2" eye layout).

He is seen three quarters, and his nose is between his eyes: its bridge
starts between them and goes down toward the far cheek, and its tip is round,
at the far cheek. The front edge of the face is its far side (the brow, the
socket of the far eye, the cheekbone, in to the mouth, the chin) and the nose
is not on it. Jon, 2026-10-13: a nose in profile at the edge of a face with two
eyes "looks like Picasso, which I don't like. I want the nose bridge to be
between the eyes." Two heads were wrong before this one: a straight wedge from
the brow at the edge of the face, and then a better profile nose in the same
wrong place.

Directions are from the character's perspective, not the axes of the canvas.

| Purpose | Actor side | Canvas side | Design-space center |
| --- | --- | --- | --- |
| Larger viewer-near eye | Actor-right | Canvas-left | `(207.8, 141.0)` |
| Smaller viewer-far eye | Actor-left | Canvas-right, by the nose | `(227.4, 140.4)` |

`svgkit.py` shifts design coordinates when it writes the SVG. To move the eyes,
change `NEAR_EYE` and `FAR_EYE` in
`scripts/svg_art/gnu_ton_scholar_villain_art.py`, not the generated XML.

Every eye variant is drawn about these two points: open, angry, surprised,
shut, dead and dizzy. The resting clip and the variant an SVG editor shows are
both **eye.open**.

To regenerate, run from `tools/ambition_sprite2d_renderer`:

```bash
uv run python scripts/svg_art/gnu_ton_scholar_villain_art.py
uv run python scripts/build_gnu_ton_scholar_villain_rig.py
uv run python scripts/build_gnu_ton_scholar_fighter_rig.py
uv run python scripts/build_gnu_ton_scholar_boss_rig.py
uv run python -m pytest -q tests/test_gnu_ton_scholar_villain_rig.py tests/test_gnu_ton_scholar_fighter_rig.py
```

The three rigs (`gnu_ton_scholar_villain`, `gnu_ton_scholar_fighter`,
`gnu_ton_scholar_boss`) use this one SVG. The game draws the fighter and the
boss sheets.
