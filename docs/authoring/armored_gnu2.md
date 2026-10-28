# Armored Gnu2 — procedural art prototype

Gnu2 is an armored, psychic-clone parody of the Giant Gnu. This first pass is
**art only**. It neither replaces GNU-ton nor registers a playable character
or a new sprite-sheet target.

## Source and shape

- Original anatomical and pose source: `ambition_sprite2d_renderer/targets/characters/gnu_ton_boss/giant_art.py`.
- Armored art variant: `ambition_sprite2d_renderer/targets/characters/gnu_ton_boss/gnu2_art.py`.
- Render entry point: `scripts/svg_art/gnu2_art.py`.

The variant reuses the original part transforms (head, horns, chest, barrel,
tail, articulated arms, and four legs). Fur colors are changed in SVG piece
strings rather than in `giant_art.C`; the original giant's appearance is
unchanged. Armor pieces follow the same transforms. The original shoulder and
hump ledge geometry is not changed.

The design emphasizes a lavender/ivory clone body, horn restraints, a neural
crown, chest containment core, armored forearms/hooves, long synthetic violet
tail, and paired II markings on the flank. Colors and armor are editable in
`gnu2_art.py`; the result is vector SVG.

## Produce review poses

From this submodule root:

```bash
python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2.svg
python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2_reared.svg reared angry
python scripts/svg_art/gnu2_art.py /tmp/armored_gnu2_walk.svg --animation armed_walk --phase 0.35
```

These commands require the renderer's Python dependencies and do not run the
full runtime sprite regeneration or modify a checked-in SVG source.

## What is not built yet

- A registered `gnu2` target with packed sprite sheets, metadata, attack
  frames, and an engine-side character definition.
- Armor for the special **portal-cut** attack-arm pieces. Whole arms and
  conventional poses (including walking and rearing) are supported now.
- An unarmored Gnu2 variant, separate from this first armored visual form.

When gameplay integration is desired, publish the variant via a normal
renderer target. Preserve the original giant's semantics where anatomy is
shared, and explicitly review altered combat silhouettes, hit volumes,
anchor/seam metadata and portrait contracts rather than treating an SVG
preview as a ready-to-use runtime atlas. Do not bake a contact shadow into
sprites; the game owns environmental shadows and effects.
