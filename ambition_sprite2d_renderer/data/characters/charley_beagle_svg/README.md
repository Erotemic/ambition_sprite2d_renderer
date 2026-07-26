# Charley Beagle SVG rig

`charley_beagle_side.svg` is the editable vector-art authority for the
`charley_beagle_svg` target. `charley_beagle_side.rig.json` owns the skeleton,
part pivots, z-order, and animation clips.

The source is intentionally flat SVG:

- no drop shadows or floor ellipses;
- no filters or gradients;
- every arm and leg segment overlaps the next segment around a shared pivot;
- the pelvis yoke covers both hip roots;
- the torso covers both shoulder roots;
- head construction remains one rigid SVG part;
- notebook, magnifier, mouth overlay, and adaptation halo are optional rig parts.

The target is deliberately named `charley_beagle_svg`, so it does not overwrite
or publish over either earlier Charley Beagle experiment.

To edit animation, open
`targets/characters/rigged/charley_beagle_svg/charley_beagle_side.rig.json` in
the rig editor. To edit the character design, edit the SVG while preserving the
part group ids and pivots used by the rig JSON.
