"""A build uses frozen sources and publishes only its accepted request."""
import shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from ambition_sprite2d_renderer import publication
from ambition_sprite2d_renderer.registry.discovery import Target
from ambition_sprite2d_renderer.publication_store import Store


def test_source_changes_invalidate_the_bundle_and_an_inflight_edit_keeps_the_selection(tmp_path, monkeypatch):
    renderer = tmp_path / "repo/tools/ambition_sprite2d_renderer"
    package = renderer / "ambition_sprite2d_renderer"
    shutil.copytree(publication.RENDERER / "ambition_sprite2d_renderer", package,
                    ignore=shutil.ignore_patterns("__pycache__"))
    library = tmp_path / "repo/game/ambition_content_library"
    (library / "authored").mkdir(parents=True)
    (library / "library.json").write_text('{"schema":"ambition.content_library.v1","id":"fixture","version":"1","asset_roots":{"generated":"generated/runtime"},"publication":"generated/art_publication","provenance":"generated/asset_provenance","producers":{"sprites":{"collection":"runtime","policy":"authored/sprites.yaml","sources":["authored"]}}}')
    (library / "authored/sprites.yaml").write_text("collections: {runtime: [bundle_probe]}\nstatic_props: {}\n")
    module = package / "targets/props/bundle_probe.py"
    module.write_text('''from pathlib import Path
from PIL import Image
SHEET_FILES = ["bundle_probe.png"]
PUBLICATION_TIERS = ["full"]
def render(out_dir, **opts):
    color = Path(__file__).with_name("probe_ink.txt").read_text()
    path = Path(out_dir)/"bundle_probe.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (4,4), color).save(path)
    return [path]
''')
    ink = module.with_name("probe_ink.txt")
    ink.write_text("red")
    target = Target.from_module(name="bundle_probe",category="props",
        module_path="ambition_sprite2d_renderer.targets.props.bundle_probe", render=lambda *_: (),
        sheet_files=("bundle_probe.png",))
    target.publication_tiers = ["full"]
    report = SimpleNamespace(targets={"bundle_probe":target},failures=[],warnings=[])
    monkeypatch.setattr(publication,"RENDERER",renderer)
    monkeypatch.setattr(publication,"names_in",lambda *_:(['bundle_probe'],report))
    monkeypatch.setattr(publication,"pack_parents",lambda *_:{})
    monkeypatch.setenv("AMBITION_ART_STORE",str(tmp_path/'store'))
    monkeypatch.setenv("AMBITION_REPO_ROOT",str(tmp_path/'repo'))
    monkeypatch.setattr(publication,"toolchain",lambda:{"python":"fixture"})
    resolved = publication.build(requested=["bundle_probe"],publish=False)
    assert not Store(tmp_path/'store').selected()["generation"]
    with monkeypatch.context() as cached:
        cached.setattr(publication.subprocess,"run",lambda *a,**k: pytest.fail("An accepted current bundle must be reusable"))
        first = publication.build(requested=["bundle_probe"])
    assert first["bundles"] == resolved["bundles"]
    second = publication.build(requested=["bundle_probe"])
    assert first["generation"] == second["generation"]
    old_pixels = Store(tmp_path/'store').paths()["sprites/bundle_probe.png"]
    ink.write_text("blue")
    changed = publication.build(requested=["bundle_probe"])
    assert changed["generation"] != first["generation"]
    assert old_pixels.read_bytes() != Store(tmp_path/'store').paths()["sprites/bundle_probe.png"].read_bytes()
    accept = Store.accept
    def edit_during_accept(self,*args,**kwargs):
        result = accept(self,*args,**kwargs)
        ink.write_text("green")
        return result
    monkeypatch.setattr(Store,"accept",edit_during_accept)
    # An edit while a build runs does not throw the build away: the bundle is
    # published with the inputs it was built from, so it reads as stale.
    edited = publication.build(requested=["bundle_probe"],force=True)
    # Built from "blue", which is what `changed` published: a content-addressed
    # store answers the same generation, so the generation is not the evidence.
    # The evidence is that the bundle it selected reads stale for the edit.
    store = Store(tmp_path/'store')
    assert edited["generation"] == store.selected()["generation"]
    recipe = store.bundle(store.selected()["bundles"]["target:bundle_probe"])["recipe"]
    state, reasons = publication.recipe_state(recipe, publication.source_files(), publication.toolchain())
    assert state == "stale"
    assert any(reason.get("path", "").endswith("probe_ink.txt") for reason in reasons), reasons
