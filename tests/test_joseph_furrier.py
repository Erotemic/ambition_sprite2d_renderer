from __future__ import annotations

from ambition_sprite2d_renderer.registry.discovery import discover_module_targets
from ambition_sprite2d_renderer.targets.characters import joseph_furrier as target


def test_joseph_furrier_steps_are_only_in_the_rows_that_are_their_own():
    """The blanket is how he looks; the steps are something he does. A frame
    of a row that makes steps is not the frame he stands in."""
    idle = target.render_frame("idle", 1, 8)
    for animation in ("step_function", "spectral_descent", "harmonic_split"):
        assert target.render_frame(animation, 5, 8).tobytes() != idle.tobytes(), animation


def test_joseph_furrier_is_auto_discovered_with_local_metadata():
    report = discover_module_targets()
    discovered = report.targets[target.TARGET_NAME]
    assert discovered.category == "characters"
    assert discovered.supports_portraits
    assert discovered._actor_metadata["authoring_description"] == target.authoring_description
