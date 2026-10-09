"""`publish-many --published-list` names each target that published.

A batch with one failure exits 1. The regen script then keeps the cache keys of
the targets in this list, so a list that is empty or too long is a cache that
renders work again or keeps a stale sheet."""

import argparse

import pytest

from ambition_sprite2d_renderer.cli import commands


def _fake_publish(name, dest_root, quiet=False, **opts):
    if name == "breaks":
        raise RuntimeError("this target fails")
    if name == "exits":
        raise SystemExit(2)
    (dest_root / f"{name}.png").write_text(name)


@pytest.mark.parametrize("workers", [1, 3])
def test_a_failed_batch_names_the_targets_that_published(tmp_path, monkeypatch, workers):
    monkeypatch.setattr(commands, "_publish_target", _fake_publish)
    monkeypatch.setattr(commands, "PUBLISH_SECONDS", tmp_path / "seconds.json")
    monkeypatch.setenv("AMBITION_SPRITE_JOBS", str(workers))
    listed = tmp_path / "published"
    targets = ["first", "breaks", "second"] + (["exits", "third"] if workers > 1 else [])
    args = argparse.Namespace(
        targets=targets,
        dest_root=tmp_path,
        quiet=True,
        published_list=str(listed),
        quality=None,
    )
    monkeypatch.setattr(commands, "_target_render_opts", lambda args: {})

    assert commands._cmd_publish_many(args) == 1
    published = [t for t in targets if t not in ("breaks", "exits")]
    assert sorted(listed.read_text().split()) == sorted(published)
    assert sorted(p.stem for p in tmp_path.glob("*.png")) == sorted(published)


def test_the_slowest_known_target_starts_first(tmp_path):
    seconds = {"quick": 1.0, "slow": 90.0, "middle": 20.0}
    assert commands._longest_first(["quick", "new", "slow", "middle"], seconds) == [
        "new",
        "slow",
        "middle",
        "quick",
    ]


def test_a_parallel_batch_keeps_the_seconds_of_each_published_target(tmp_path, monkeypatch):
    monkeypatch.setattr(commands, "_publish_target", _fake_publish)
    monkeypatch.setattr(commands, "PUBLISH_SECONDS", tmp_path / "seconds.json")
    (tmp_path / "seconds.json").write_text('{"older": 5.0}')
    monkeypatch.setenv("AMBITION_SPRITE_JOBS", "2")
    monkeypatch.setattr(commands, "_target_render_opts", lambda args: {})
    args = argparse.Namespace(
        targets=["first", "breaks", "second"],
        dest_root=tmp_path,
        quiet=True,
        published_list=None,
        quality=None,
    )
    assert commands._cmd_publish_many(args) == 1
    kept = commands._read_publish_seconds(tmp_path / "seconds.json")
    assert {"older", "first", "second"} <= set(kept), f"the published targets' seconds were not kept: {kept}"
    assert "breaks" not in kept, "a failed target's seconds are not a duration"
