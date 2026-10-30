"""Strictly stale vs possibly stale: a unit's own inputs, or only shared renderer code."""
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from ambition_sprite2d_renderer import publication
from ambition_sprite2d_renderer.publication import direct_input, readers, recipe_state, stale_scope
from ambition_sprite2d_renderer.registry.discovery import Target

CORE = "tools/r/ambition_sprite2d_renderer/authoring/packer.py"


def test_an_input_is_direct_when_few_bundles_read_it_or_its_name_matches_the_target():
    count = {CORE: 600, "t/_goblin_look.py": 26, "t/alice.py": 26, "t/goblin.yaml": 2, "t/mockingbird_boss/sprite_generator.py": 40}
    assert direct_input("target:goblin_bruiser_club", "t/goblin.yaml", count)
    assert direct_input("target:goblin_bruiser_club", "t/_goblin_look.py", count)
    assert not direct_input("target:goblin_bruiser_club", "t/alice.py", count)
    assert direct_input("target:alice_cryptographer", "t/alice.py", count)
    assert direct_input("target:mockingbird_boss", "t/mockingbird_boss/sprite_generator.py", count)
    assert not direct_input("target:goblin", CORE, count)
    assert direct_input("target:goblin", CORE, None), "without a count every input is direct: the strict answer"


def test_recipe_state_stays_strict_and_names_the_scope(tmp_path):
    own, core = tmp_path / "goblin.yaml", tmp_path / "packer.py"
    own.write_text("a"); core.write_text("a")
    files = {"t/goblin.yaml": own, CORE: core}
    recipe = {"toolchain": {}, "membership": publication.identity(sorted(files)),
              "inputs": {name: publication.digest(path) for name, path in files.items()}}
    count = readers([recipe] * 3) | {CORE: 600}
    assert recipe_state(recipe, files, {}, unit="target:goblin", count=count) == ("current", [])
    core.write_text("b")
    state, reasons = recipe_state(recipe, files, {}, unit="target:goblin", count=count)
    assert state == "stale" and stale_scope(reasons) == "shared" and reasons[0]["readers"] == 600
    own.write_text("b")
    assert stale_scope(recipe_state(recipe, files, {}, unit="target:goblin", count=count)[1]) == "direct"


def test_a_loose_build_keeps_a_bundle_that_only_shared_code_made_stale(tmp_path, monkeypatch):
    renderer = tmp_path / "repo/tools/ambition_sprite2d_renderer"
    package = renderer / "ambition_sprite2d_renderer"
    shutil.copytree(publication.RENDERER / "ambition_sprite2d_renderer", package, ignore=shutil.ignore_patterns("__pycache__"))
    library = tmp_path / "repo/game/ambition_content_library"
    (library / "authored").mkdir(parents=True)
    (library / "library.json").write_text('{"schema":"ambition.content_library.v1","id":"fixture","version":"1","asset_roots":{"generated":"generated/runtime"},"publication":"generated/art_publication","provenance":"generated/asset_provenance","producers":{"sprites":{"collection":"runtime","policy":"authored/sprites.yaml","sources":["authored"]}}}')
    (library / "authored/sprites.yaml").write_text("collections: {runtime: [scope_probe]}\nstatic_props: {}\n")
    (package / "targets/props/scope_probe.py").write_text('''from pathlib import Path
from PIL import Image
SHEET_FILES = ["scope_probe.png"]
PUBLICATION_TIERS = ["full"]
def render(out_dir, **opts):
    path = Path(out_dir)/"scope_probe.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (4,4), "red").save(path)
    return [path]
''')
    target = Target.from_module(name="scope_probe", category="props", module_path="ambition_sprite2d_renderer.targets.props.scope_probe",
                                render=lambda *_: (), sheet_files=("scope_probe.png",))
    target.publication_tiers = ["full"]
    report = SimpleNamespace(targets={"scope_probe": target}, failures=[], warnings=[])
    monkeypatch.setattr(publication, "RENDERER", renderer)
    monkeypatch.setattr(publication, "names_in", lambda *_: (["scope_probe"], report))
    monkeypatch.setattr(publication, "pack_parents", lambda *_: {})
    monkeypatch.setenv("AMBITION_ART_STORE", str(tmp_path / "store"))
    monkeypatch.setenv("AMBITION_REPO_ROOT", str(tmp_path / "repo"))
    monkeypatch.setattr(publication, "toolchain", lambda: {"python": "fixture"})
    first = publication.build(requested=["scope_probe"])
    # Only shared renderer code changes: the recipe owner, an input of every bundle.
    shared = package / "publication.py"
    shared.write_text(shared.read_text() + "\n# a comment that changes no pixels\n")
    monkeypatch.setattr(publication, "direct_input", lambda unit, path, count: not path.endswith("/publication.py"))
    with monkeypatch.context() as kept:
        kept.setattr(publication.subprocess, "run", lambda *a, **k: pytest.fail("A loose build must keep a bundle stale only for shared code"))
        loose = publication.build(requested=["scope_probe"], loose=True)
    assert loose["bundles"] == first["bundles"]
    strict = publication.build(requested=["scope_probe"])
    assert strict["bundles"]["target:scope_probe"] != first["bundles"]["target:scope_probe"]
