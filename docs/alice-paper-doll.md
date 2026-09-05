# Alice — cipher courier

Alice wears a teal field jacket over dark tailored trousers, oxblood ankle
boots and cuffs, and short blue-black hair held by an inlaid headband. Her asymmetric bag,
sealed correspondence, and engraved brass cipher wheel identify a working courier.
Thin warm contours, restrained material gradients, and inset seams give the parts
a cut-paper illustration finish; the sprite has a transparent background.

`assets/alice.svg` owns named clothing and anatomy pieces and an assembled reference
pose. `alice_paper_doll.py` composes those pieces using shared two-bone limbs for
all views; `alice_cryptographer.py` owns action timing, props, and effects. The
ankle is the boot attachment, the solved wrist is the prop attachment, and the
near arm covers the torso and bag strap. Coat tails pivot at the pelvis. The
forward and profile heads are separately drawn for their projections.

From this renderer checkout, using its Python environment:

```bash
python scripts/review_alice.py
python -m ambition_sprite2d_renderer publish alice
```

The review command writes `generated/alice_review/alice.png` (1024 px transparent
cutout), `pose_review.png` (12 poses), and `walk.gif`. These are generated review
artifacts. The normal publisher supplies the runtime sheets and dialogue portraits.
From the Ambition root, update the installed quality tiers after publishing:

```bash
./scripts/regen/quality_variants.sh --sprites-only --target 'alice*'
python3 scripts/check_quality_variants_are_fresh.py
```
