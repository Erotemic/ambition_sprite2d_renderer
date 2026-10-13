# GNU-ton Scholar: fighting-game / roster animation candidate

**Art authority:** the previously accepted D2 character, `gnu_ton_scholar_villain.svg` and its Python generator. This work **does not redraw the face, nose, costume, or underlying body**. It adds fighter-specific pose authoring to the same 19-bone SVG rig.

**Fighter output:** `gnu_ton_scholar_fighter.rig.json`, independently discoverable as target `gnu_ton_scholar_fighter`. The 10 original `gnu_ton_scholar_villain` boss animation rows remain untouched. Both rigs use the same editable SVG art and the same skinned part layers.

## Motion direction

The scholar is a fencer/caster, not a generic sword fighter:

- **Duelist neutral:** bent knees, staggered planted feet, quill presented in the near hand, book at the back hip.
- **Ground attacks:** rapid quill jabs, a fencing tilt, vertical flourish, low sweep, charged book/quill strikes. Anticipation, active silhouette and recovery are distinct poses.
- **Aerials:** distinct neutral spin, forward and backward swipes, upward quill reach and downward attack. Both feet move with the body instead of staying pinned to the floor.
- **Defense:** a book-led shield/parry that raises the actual far-hand book *in front of the coat*, rather than a generic clenched-fist block; spot dodge, forward/back rolls, air dodge and tech.
- **Concept specials:** neutral open-book invocation, advancing quill thrust, upward casting lift, and book counter. These are **visual candidates**, not executable moves.
- **Grabs and throws:** both arms reach without weapon props, hold, pummel, release and four directional throw poses.
- **Reactions and traversal:** knockback, tumbling, prone/getup, jumps and landings, ledge and wall transitions, item poses, taunt, entrance, victory and loss.

There are **94 authored animation clips**. Ground movement and defensive holds loop; attacks have anticipation → active → follow-through/recovery beats. The common `humanoid.Body` forward kinematics and two IK legs remain the only pose solver. The drawing remains an editable labeled SVG.

## Source paths (submodule-relative)

- `scripts/gnu_ton_scholar_fighter_poses.py`: semantic pose *values* and reusable clip helpers
- `scripts/build_gnu_ton_scholar_fighter_rig.py`: generates the new fighter rig doc without rewriting the boss SVG/catalog
- `ambition_sprite2d_renderer/targets/characters/rigged/gnu_ton_scholar_fighter.rig.json`: generated independent fighter target
- `tests/test_gnu_ton_scholar_fighter_rig.py`: renderer and geometry contract tests

## Rebuild and test

From the submodule root:

```bash
cd /home/joncrall/code/ambition/tools/ambition_sprite2d_renderer
uv run python scripts/build_gnu_ton_scholar_fighter_rig.py
uv run python -m pytest -q tests/test_gnu_ton_scholar_fighter_rig.py
```

The builder requires the D2 SVG and boss rig to be installed first (the previous D2 overlay). **Do not regenerate the SVG to change fighter poses**. Edit the fighter pose library, run the fighter builder, and publish `gnu_ton_scholar_fighter` via the existing sprite renderer workflow.

## The face stays clear

A pose that is held (the stance, a loop, the end of a row) does not put the quill arm, the hand or the quill in front of the face. The stance is a low guard: the hand in front of the chest, the quill forward as a foil. A strike can go through the face; a hold can not. An arm that is up reaches forward of the face (`nu` near -40) and not along it (`nu` near -80). The boss rig copies the stance, so build the boss rig also (`scripts/build_gnu_ton_scholar_boss_rig.py`) after a change of it.

## Integration limits

- This is a **publishable animation/rig target**, not yet a selectable fighter in Ambition. The game still needs character registration, move commands, timing/active-frame binding, hitbox/hurtbox authoring, projectile/reflect/counter behavior, shield/dodge rules, asset selection and facing acceptance tests.
- The motion library's in-sheet root offsets illustrate poses; the runtime movement controller remains authoritative for horizontal motion, jumps and knockback.
- Standard fist artwork is reused for grabs and item poses; open palms and distinct item sockets can be authored later if needed.
- This rig shares the D2 *face* with the boss but does not alter the game's currently shipped rider.
- Sprite image acceptance should be repeated with the native `resvg-py` renderer. Review renders produced with CairoSVG are not guaranteed pixel-identical.
