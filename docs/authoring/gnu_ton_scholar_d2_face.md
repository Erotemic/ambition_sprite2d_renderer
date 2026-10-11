# GNU-ton Scholar: accepted D2 eye layout

The canonical neutral face is based on the user's accepted **D2** layout from the
4 x 4 eye-placement reference grid. This document defines directions from the
character's perspective separately from the SVG canvas coordinate axes.

| Purpose | Actor side | Canvas side | Design-space center | Neutral radii |
| --- | --- | --- | --- | --- |
| Larger viewer-near eye | Actor-right | Canvas-left | `(206.0, 139.3)` | `(9.3, 8.2)` |
| Smaller viewer-far eye | Actor-left | Canvas-right | `(228.8, 135.4)` | `(5.0, 5.5)` |

The far eye is canvas-right and slightly higher. The larger near eye is closer
to the ear/wig ringlets. The existing triangular nose and mouth are unchanged.
`svgkit.py` shifts design coordinates during SVG creation; edit the constants
`D2_NEAR_EYE` and `D2_FAR_EYE` in
`scripts/svg_art/gnu_ton_scholar_villain_art.py`, not the generated XML, to
change these placements canonically.

Every expression variant uses these two landmarks: neutral, focused, surprised,
shut, knocked-out, and dizzy. The resting clip and the SVG's editor-visible
variant both use **eye.open**.

To regenerate, run from `tools/ambition_sprite2d_renderer`:

```bash
uv run python scripts/svg_art/gnu_ton_scholar_villain_art.py
uv run python scripts/build_gnu_ton_scholar_villain_rig.py
uv run python -m pytest -q tests/test_gnu_ton_scholar_villain_rig.py tests/test_svg_subset_hides_every_drawable.py
```

The new SVG remains a **candidate** `gnu_ton_scholar_villain`; it does not
replace the game's production `gnu_ton_rider` sprite, and it does not add
Smash/roster animations.
