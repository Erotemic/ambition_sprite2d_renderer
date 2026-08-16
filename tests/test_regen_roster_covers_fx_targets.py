"""The root regen roster must name every effect target this renderer defines.

Three sheets each carry their own `test_full_sprite_regen_roster_publishes_X`,
written by whoever added that sheet. That is a hand-kept list guarded by a
hand-kept list, and on 2026-08-16 it failed exactly the way that shape fails:
`george_booul_vfx` and `oiler_vfx` were authored here, and NEITHER was ever
added to `regen_sprites.sh`. George's sheet is published in the game assets only
because someone ran it with a focused `--target`, so a fresh clone's regen would
have quietly dropped it; Oiler's had no published sheet and no cues in the bank.

So the invariant is stated once, over what discovery actually finds, rather than
once per target by whoever remembers.
"""

from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets


def _effect_targets() -> list[str]:
    """Every discovered target whose name marks it as an effect catalog."""
    return sorted(
        name
        for name in discover_all_targets().targets
        if name.endswith("_fx") or name.endswith("_vfx")
    )


def test_every_effect_target_is_in_the_full_regen_roster():
    repo_root = Path(__file__).resolve().parents[3]
    regen = (repo_root / "regen_sprites.sh").read_text(encoding="utf8")

    targets = _effect_targets()
    # Non-vacuity: an empty list would make the assertion below pass while
    # observing nothing at all, which is the failure this file is about.
    assert len(targets) >= 10, f"discovery found too few effect targets: {targets}"

    missing = [name for name in targets if f"\n    {name}\n" not in regen]
    assert not missing, (
        "authored effect targets missing from regen_sprites.sh — a fresh clone's "
        f"regen would not produce them: {missing}"
    )
