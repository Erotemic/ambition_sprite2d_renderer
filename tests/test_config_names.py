"""One target name has one config file."""

from __future__ import annotations

from ambition_sprite2d_renderer.registry.discovery import discover_all_targets


def test_no_review_config_has_the_name_of_a_main_config():
    """`raid_enforcer` and `goblin_forest_spear` had both. The registry
    published the main config, and the full publish installed the review
    render over it, so `--target` and a full publish shipped different art."""
    shadowed = [w for w in discover_all_targets().warnings if "shadowed by configs/" in w]
    assert shadowed == []
