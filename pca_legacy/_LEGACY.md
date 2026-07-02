# pca_legacy — disposable

This is the **abandoned** approach to authoring the Perfect Cellular Automaton
(PCA): optimizing polygons to fit a reference PNG (`pca_fit` / `pca_pipeline` /
`pca_paperdoll` / the `*_v14` fit harness + data, etc.). It was superseded by a
manually authored SVG.

**Nothing here is on the live sprite path.** It is kept only as a staging area
and is safe to delete wholesale.

The live PCA path is:

- Art:   `assets/perfect-cellular-automaton/PCA-multiview.svg` (hand-authored)
- Build: `ambition_sprite2d_renderer/targets/characters/rigged/pca_rig_extract.py`
         (SVG → bone rig; run `... pca_rig_extract.py build`)
- Rig:   `ambition_sprite2d_renderer/targets/characters/rigged/perfect_cellular_automaton.rig.json`
- Render: `python -m ambition_sprite2d_renderer publish perfect_cellular_automaton`
