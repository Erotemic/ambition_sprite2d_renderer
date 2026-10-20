# Oiler SVG rig

Oiler is a parody of Leonhard Euler as the game's scholar-mechanic. His look
follows Handmann's 1753 pastel:

- a broad, fleshy face, with the right eye screwed nearly shut and the left
  eye pale blue;
- a small closed mouth whose knowing smile pulls up at his left corner;
- a rumpled silk cap wound high on the head, its long end hanging behind the
  left ear;
- a teal silk banyan, damask-figured and lined in straw silk, worn open over
  his workshop clothes: shirt, ochre waistcoat, leather apron with a pouch,
  dark breeches and boots;
- sleeves pushed up, so his forearms and hands are bare.

He was redesigned on 2026-10-20 (design id `euler-banyan-v2`). The earlier
drawings are eras in `design_history/lineages.yaml`.

## Source

`oiler-multiview.svg` is GENERATED. Do not edit it by hand: the drawing is
`scripts/svg_art/oiler_art.py`.

```bash
uv run python scripts/svg_art/oiler_art.py --all DIR        # every view of every look, as single SVGs
uv run python scripts/svg_art/oiler_art.py --multiview \
    ambition_sprite2d_renderer/data/characters/oiler/oiler-multiview.svg
uv run python scripts/build_oiler_rig.py build --fresh      # the five view rigs and their clips
uv run python scripts/build_oiler_rig.py validate
```

## Views

The file holds five views, each a layer of rig parts (`data-rig-part`,
`data-rig-bone`, `data-rig-z`) plus its joint markers (`data-rig-joint`):

| Layer | Used for |
|---|---|
| `Oiler - Three Quarter` | idle, interact, portraits |
| `Oiler - Front` | talk (`data-rig-side-map="left=far,right=near"`) |
| `Oiler - Side Right` | walk and every fight row |
| `Oiler - Three Quarter Left` | the same rows, facing left |
| `Oiler - Side Left` | the same rows, facing left |

## He is asymmetric

His right eye fails, so a mirrored sprite would put the bad eye on the wrong
side. The two LEFT views show his left side but are drawn facing right
(`data-view-mirror="x"`), so they share their right-facing twins' skeleton and
clips. The target mirrors their frames into the sheet's `<row>~mirrored` rows,
and the game draws those rows instead of flipping (`SheetRow::mirror_of`). From
the front he looks the same whichever way he faces, so the front rows' twins
are those frames unflipped.

## Faces

The eyes, brows, mouth and the folds round it are drawn per expression. Each
expression is a layer behind its own opacity channel, `face_<name>_vis`:
knowing (the default), pleased, delighted, surprised, thinking, stern,
worried and hurt. Two overlays sit over any face: `blink_vis` and `talk_vis`.

Each clip wears a face (`FACE_OF` in the rig build): fights are stern, hit and
death are hurt, interact is thinking, and the taunt is delighted. Every
expression is also published as a portrait clip of the same name, for
`<<portrait_clip "name">>`.

## Art rules

- Flat cel shading: a shade band and a light band inside each shape, with thin
  warm ink.
- No gradients, filters or drop shadows.
- No props in the body art. Tools attach at the hand sockets as separate
  assets.
