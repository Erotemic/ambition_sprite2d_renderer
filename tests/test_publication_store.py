"""Publication keeps accepted bytes and refuses incomplete or conflicting work."""
from pathlib import Path
import pytest
from ambition_sprite2d_renderer.publication_store import Store


def bundle(store, tmp_path, name, contents=b"pixels", parents=None):
    source = tmp_path / (name + ".png")
    source.write_bytes(contents)
    return store.accept(name, {f"sprites/{name}.png": (source, "runtime", "full")}, {"source": "fixture"}, parents=parents)


def test_failure_and_a_changed_base_keep_the_selected_generation(tmp_path):
    store = Store(tmp_path / "store")
    first = bundle(store, tmp_path, "one")
    selected = store.publish({"one": first}, None)
    with pytest.raises(ValueError, match="Missing bundle member"):
        store.accept("broken", {"sprites/broken.png": (tmp_path / "absent", "runtime", "full")}, {})
    assert store.selected() == selected
    next_bundle = bundle(store, tmp_path, "two")
    with pytest.raises(ValueError, match="selection changed"):
        store.publish({"two": next_bundle}, None)
    assert store.selected() == selected


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


def test_parent_changes_require_a_new_derived_bundle(tmp_path):
    store = Store(tmp_path / "store")
    parent = bundle(store, tmp_path, "one")
    derived = bundle(store, tmp_path, "atlas", parents={"one": parent})
    selected = store.publish({"one": parent, "atlas": derived}, None)
    changed = bundle(store, tmp_path, "one", b"changed")
    with pytest.raises(ValueError, match="Changed bundle dependency"):
        store.publish({"one": changed}, selected["generation"])
    assert store.selected() == selected


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
