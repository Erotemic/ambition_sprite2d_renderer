"""The superproject's sprite regeneration roster must cover every effect target.

Expected targets come from renderer discovery rather than per-target hand-kept
lists, so adding an effect without adding it to the game repo's
`scripts/regen/sprites.sh` fails once at the roster boundary.

⛔ The roster lives in the SUPERPROJECT, not here. The `regen_roster` fixture
owns that path and skips when this renderer is checked out standalone."""

from ambition_sprite2d_renderer.registry import discover_all_targets


def _effect_targets() -> list[str]:
    """Every discovered target whose name marks it as an effect catalog."""
    return sorted(
        name
        for name in discover_all_targets().targets
        if name.endswith("_fx") or name.endswith("_vfx")
    )


def test_every_effect_target_is_in_the_full_regen_roster(regen_roster: str):
    targets = _effect_targets()
    # Non-vacuity: an empty list would make the assertion below pass while
    # observing nothing at all, which is the failure this file is about.
    assert len(targets) >= 10, f"discovery found too few effect targets: {targets}"

    missing = [name for name in targets if f"\n    {name}\n" not in regen_roster]
    assert not missing, (
        "authored effect targets missing from the superproject's "
        "scripts/regen/sprites.sh — a fresh clone's regen would not produce "
        f"them: {missing}"
    )
