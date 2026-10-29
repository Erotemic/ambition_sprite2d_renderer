"""Publication keeps accepted bytes, refuses incomplete bundles, and merges
concurrent publications instead of refusing them."""
from pathlib import Path
import pytest
from ambition_sprite2d_renderer.publication_store import Store


def bundle(store, tmp_path, name, contents=b"pixels", parents=None):
    source = tmp_path / (name + ".png")
    source.write_bytes(contents)
    return store.accept(name, {f"sprites/{name}.png": (source, "runtime", "full")}, {"source": "fixture"}, parents=parents)


def test_a_failed_accept_keeps_the_selected_generation(tmp_path):
    store = Store(tmp_path / "store")
    first = bundle(store, tmp_path, "one")
    selected = store.publish({"one": first}, None)
    with pytest.raises(ValueError, match="Missing bundle member"):
        store.accept("broken", {"sprites/broken.png": (tmp_path / "absent", "runtime", "full")}, {})
    assert store.selected() == selected


def test_two_agents_that_planned_on_one_selection_both_publish(tmp_path):
    """Agents do not wait on each other: the second publication is merged onto
    the first, unit by unit, and is not refused."""
    store = Store(tmp_path / "store")
    base = store.publish({"one": bundle(store, tmp_path, "one"), "gone": bundle(store, tmp_path, "gone")}, None)
    # Both agents plan against `base`.
    alice = store.publish(base["bundles"] | {"two": bundle(store, tmp_path, "two")}, base, replace=True)
    bob_bundles = {unit: key for unit, key in base["bundles"].items() if unit != "gone"}
    bob_bundles["three"] = bundle(store, tmp_path, "three")
    bob_bundles["one"] = bundle(store, tmp_path, "one", b"bob")
    merged = store.publish(bob_bundles, base, replace=True)
    assert merged["generation"] != alice["generation"]
    assert set(merged["bundles"]) == {"one", "two", "three"}, "Alice's unit stays; Bob's removal and changes apply"
    assert store.paths()["sprites/one.png"].read_bytes() == b"bob"
    # With only a generation, the changes are the replacements.
    four = store.publish({"four": bundle(store, tmp_path, "four")}, base["generation"])
    assert set(four["bundles"]) == {"one", "two", "three", "four"}


def test_every_member_is_checked_and_old_bundles_keep_their_bytes(tmp_path):
    store = Store(tmp_path / "store")
    first = bundle(store, tmp_path, "one", b"old")
    selected = store.publish({"one": first}, None)
    original = store.paths()["sprites/one.png"]
    second = bundle(store, tmp_path, "one", b"new")
    store.publish({"one": second}, selected["generation"])
    assert original.read_bytes() == b"old"
    assert store.paths()["sprites/one.png"].read_bytes() == b"new"
    store.paths()["sprites/one.png"].write_bytes(b"damaged")
    assert store.integrity(second) == [{"code": "changed-output", "path": "sprites/one.png"}]


def test_a_changed_parent_leaves_its_derived_bundle_selected_and_stale(tmp_path):
    store = Store(tmp_path / "store")
    parent = bundle(store, tmp_path, "one")
    derived = bundle(store, tmp_path, "atlas", parents={"one": parent})
    selected = store.publish({"one": parent, "atlas": derived}, None)
    assert "stale" not in selected
    changed = bundle(store, tmp_path, "one", b"changed")
    published = store.publish({"one": changed}, selected["generation"])
    assert published["bundles"] == {"one": changed, "atlas": derived}
    assert list(published["stale"]) == ["atlas"], "the atlas is reported, not refused"
    assert store.selected() == published


def test_a_full_sprite_replacement_retires_sprites_and_keeps_other_media(tmp_path):
    from ambition_sprite2d_renderer.publication import publish_sprites
    store = Store(tmp_path / "store")
    source = tmp_path / "media"
    source.write_bytes(b"accepted")
    def accept(unit, logical):
        return store.accept(unit, {logical: (source, "runtime", "full")}, {})
    first = {"target:old": accept("target:old", "sprites/old.png"),
             "producer:fonts": accept("producer:fonts", "fonts/face.ttf"),
             "producer:music": accept("producer:music", "audio/music/track.ogg")}
    selected = store.publish(first, None)
    next_key = accept("target:new", "sprites/new.png")
    publish_sprites(store, {"target:new": next_key}, selected, replace=True)
    assert set(store.paths()) == {"sprites/new.png", "fonts/face.ttf", "audio/music/track.ogg"}
