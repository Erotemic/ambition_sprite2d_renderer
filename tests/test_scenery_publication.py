"""The scenery publication's selection: what `--missing-only` with no scope
looks at, and which command draws each kind of product."""
from pathlib import Path

import pytest

from ambition_sprite2d_renderer import scenery_publication as sp


def test_every_unit_is_the_scenes_skins_and_sky_parts_and_nothing_else():
    definitions = {uid: {} for uid in ("theme:art", "skin:art", "sky:mockingbird_moon", "atlas:full", "target:robot")}
    assert sp.every_unit(definitions) == ["theme:art", "skin:art", "sky:mockingbird_moon"]


def test_each_kind_of_product_has_its_own_command():
    out = Path("/out")
    assert sp._command("theme", "art", out) == ["backgrounds", "draw", "--out-dir", "/out", "art"]
    assert sp._command("skin", "art", out) == ["terrain", "draw", "--out-dir", "/out", "art"]
    # The parts are drawn together; the unit keeps only its own files.
    assert sp._command("sky", "mockingbird_moon", out) == ["backgrounds", "parts", "--out-dir", "/out"]


def test_no_scope_needs_missing_only():
    with pytest.raises(SystemExit):
        sp.main([])


def test_scoped_scene_replaces_its_legacy_files_and_keeps_other_scenery(tmp_path):
    store = sp.Store(tmp_path / "publication")
    source = tmp_path / "asset.png"
    source.write_bytes(b"legacy")
    hub = "backgrounds/parallax_layers/hub.png"
    other = "backgrounds/parallax_layers/other.png"
    half = "backgrounds/parallax_layers_0_5x/hub.png"
    bulk = store.accept("producer:backgrounds", {name: (source, "runtime", "full") for name in (hub, other)}, {})
    variant = f"producer:variants:half:{half}"
    derived = store.accept(variant, {half: (source, "runtime", "half")}, {})
    selected = store.publish({"producer:backgrounds": bulk, variant: derived}, None)
    source.write_bytes(b"new scene")
    scene = store.accept("theme:hub", {hub: (source, "runtime", "full"), half: (source, "runtime", "half")}, {})
    result = sp.publish_scenery(store, {"theme:hub": scene}, selected, missing_only=False)
    assert result["files"][hub]["unit"] == "theme:hub"
    assert result["files"][half]["unit"] == "theme:hub"
    assert store.paths()[other].read_bytes() == b"legacy"
    assert variant not in result["bundles"]
