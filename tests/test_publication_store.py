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


def test_a_target_check_does_not_require_library_atlases(tmp_path, monkeypatch, capsys):
    """A complete target is usable without unrelated shared atlas products."""
    import json
    from types import SimpleNamespace
    from ambition_sprite2d_renderer import publication as publication

    store = Store(tmp_path / "store")
    source = tmp_path / "one.png"
    source.write_bytes(b"pixels")
    key = store.accept("target:one", {"sprites/one.png": (source, "runtime", "full")}, {"inputs": {}})
    store.publish({"target:one": key}, None)
    target = SimpleNamespace(name="one", category="props", _actor_metadata={}, _inspection={})
    monkeypatch.setattr(publication, "RENDERER", tmp_path)
    monkeypatch.setattr(publication, "store_root", lambda: store.root)
    monkeypatch.setattr(publication, "discover", lambda: SimpleNamespace(targets={"one": target}, failures=[], warnings=[]))
    monkeypatch.setattr(publication, "library", lambda: {"producers": {"sprites": {"collection": "runtime"}}})
    monkeypatch.setattr(publication, "policy", lambda: {"collections": {"runtime": ["one"]}})
    monkeypatch.setattr(publication, "source_files", lambda: {})
    monkeypatch.setattr(publication, "toolchain", lambda: {})
    monkeypatch.setattr(publication, "recipe_state", lambda recipe, *args, **kwargs: ("current" if recipe else "missing", []))
    monkeypatch.setattr(publication, "definition", lambda target: {
        "id": "target:one", "target": "one", "root": "sprites", "required": ["sprites/one.png"],
        "tiers": [], "repair": "publish one",
    })

    assert publication.main(["--check", "--target", "one", "--json"]) == 0
    scoped = json.loads(capsys.readouterr().out)
    assert set(scoped["units"]) == {"target:one"}
    assert scoped["units"]["target:one"]["status"]["state"] == "current"

    assert publication.main(["--check", "--json"]) == 1
    complete = json.loads(capsys.readouterr().out)
    assert complete["units"]["atlas:full"]["status"]["state"] == "missing"


@pytest.mark.parametrize('owner', ['target:one', 'producer:sprites'])
def test_missing_only_keeps_accepted_bytes_and_unrelated_products(tmp_path, monkeypatch, owner):
    """An explicit missing-only build must keep an accepted stale target."""
    from types import SimpleNamespace
    from ambition_sprite2d_renderer import publication

    store = Store(tmp_path / 'store')
    source = tmp_path / 'one.png'
    source.write_bytes(b'accepted bytes')
    key = store.accept(owner, {'sprites/one.png': (source, 'runtime', 'full')}, {})
    other = store.accept('producer:music', {'audio/music/one.ogg': (source, 'runtime', 'full')}, {})
    selected = store.publish({owner: key, 'producer:music': other}, None)
    monkeypatch.setattr(publication, 'store_root', lambda: store.root)
    monkeypatch.setattr(publication, 'source_files', lambda: {})
    monkeypatch.setattr(publication, 'toolchain', lambda: {})
    monkeypatch.setattr(publication, 'discover', lambda: SimpleNamespace(targets={
        'one': SimpleNamespace(name='one', category='props', _actor_metadata={}, _inspection={})}, failures=[], warnings=[]))
    monkeypatch.setattr(publication, 'definition', lambda target: {
        'id': 'target:one', 'target': 'one', 'root': 'sprites', 'required': ['sprites/one.png'],
        'tiers': [], 'repair': 'publish one'})
    monkeypatch.setattr(publication, 'pack_parents', lambda report: {'sprites/unrelated.yaml': 'target:unrelated'})
    result = publication.build(requested=['one'], missing_only=True)
    assert result['generation'] == selected['generation']
    assert store.paths()['sprites/one.png'].read_bytes() == b'accepted bytes'
    assert result['bundles'] == {owner: key, 'producer:music': other}
    if owner == 'producer:sprites':
        report = publication.inventory(requested={'one'}, include_atlases=False)
        assert report['units']['target:one']['status']['state'] == 'partial'


def test_missing_only_publication_keeps_a_concurrent_publish(tmp_path):
    store = Store(tmp_path / 'store')
    source = tmp_path / 'pixels'
    source.write_bytes(b'planned')
    planned = store.accept('target:one', {'sprites/one.png': (source, 'runtime', 'full')}, {})
    base = store.selected()
    source.write_bytes(b'published elsewhere')
    current = store.accept('target:one', {'sprites/one.png': (source, 'runtime', 'full')}, {})
    accepted = store.publish({'target:one': current}, base)
    result = store.publish({'target:one': planned}, base, only_missing=True)
    assert result['generation'] == accepted['generation']
    assert store.paths()['sprites/one.png'].read_bytes() == b'published elsewhere'


def test_missing_only_publication_keeps_files_owned_by_a_collection(tmp_path):
    store = Store(tmp_path / 'store')
    source = tmp_path / 'pixels'
    source.write_bytes(b'pixels')
    collection = store.accept('producer:backgrounds', {'room_dressing/paint.png': (source, 'runtime', 'full')}, {}, roots=['room_dressing'])
    accepted = store.publish({'producer:backgrounds': collection}, None)
    scoped = store.accept('skin:paint', {'room_dressing/paint.png': (source, 'runtime', 'full')}, {}, roots=['room_dressing'])
    assert store.publish({'skin:paint': scoped}, accepted, only_missing=True)['generation'] == accepted['generation']
