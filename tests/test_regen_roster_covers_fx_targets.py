"""The root sprite regeneration roster must cover every discovered effect target.

Expected targets come from renderer discovery rather than per-target hand-kept
lists, so adding an effect without adding it to `regen_sprites.sh` fails once at
the root roster boundary."""

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
