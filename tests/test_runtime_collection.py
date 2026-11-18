"""The runtime collection is every registered target but a reasoned few.

A target is published by the regeneration because the renderer registers it,
not because a second list names it: the hand list this replaced had drifted
from discovery by 43 targets, among them the PCA's glider projectile, which a
manual publish had put in the store and no regeneration rebuilt.

⛔ The roster lives in the SUPERPROJECT (`authored/sprites.yaml`); the
`regen_roster` fixture resolves it and skips when this renderer is checked out
standalone."""

import json

from ambition_sprite2d_renderer import publication
from ambition_sprite2d_renderer.registry import discover_all_targets


def test_every_excepted_target_is_registered_and_has_a_reason(regen_roster: frozenset[str]):
    declared = publication.policy()["collections"]["runtime"]
    assert isinstance(declared, dict) and "except" in declared, declared
    registered = discover_all_targets().targets
    for name, reason in declared["except"].items():
        assert name in registered, f"the runtime collection excepts {name}, which the renderer does not register"
        assert isinstance(reason, str) and reason.strip(), f"{name} is excepted without a reason"
        assert name not in regen_roster
    # Non-vacuity: the roster is the registered targets, less the exceptions.
    assert len(regen_roster) == len(registered) - len(declared["except"]) > 1000


def test_no_excepted_target_is_in_the_published_store():
    """A full regeneration publishes the collection in place of the store's
    targets, so it drops an excepted target that is in the store: a target
    published by hand (`--target`) that the game reads is excepted by mistake.
    Before the collection was every registered target, a full regeneration
    dropped the glider this way."""
    published = publication.store_root() / "published.json"
    if not published.is_file():
        import pytest

        pytest.skip(f"no publication at {published}")
    units = {unit.removeprefix("target:") for unit in json.loads(published.read_text())["bundles"] if unit.startswith("target:")}
    assert len(units) > 1000, f"the store has {len(units)} target units; this is not the shipped publication"
    excepted = publication.policy()["collections"]["runtime"]["except"]
    assert not sorted(units & set(excepted)), "excepted targets a regeneration would drop from the store"
