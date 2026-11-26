"""Cached historical art is available without an authorship measurement."""

import sys
from pathlib import Path
from types import SimpleNamespace

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from design_history import characters, stills, view


def test_visual_projection_keeps_the_commits_image_without_attribution(tmp_path, monkeypatch):
    sha = "abc123456789" + "0" * 28
    monkeypatch.setattr(view, "git", lambda *args, **kwargs: sha)
    monkeypatch.setattr(view, "commit_info", lambda *args: SimpleNamespace(date="2026-05-01T12:00:00Z", subject="First design"))
    cache = tmp_path / "cache"
    image = cache / "stills" / (stills.still_key(sha, ["person"]) + ".png")
    image.parent.mkdir(parents=True)
    Image.new("RGBA", (12, 20), "blue").save(image)
    record = view.lineage_view("person", {"ids": ["person"], "eras": [{"commit": sha[:7], "label": "First"}]},
                               store=tmp_path / "store", cache=cache, blamer=None, current={"person"}, include_attribution=False)
    era = record["eras"][0]
    assert era["still"] == str(image)
    assert era["sha"] == sha and era["date"] == "2026-05-01T12:00:00Z"
    assert "pin" not in era


def test_lineage_follows_a_catalog_rename_by_character_id(tmp_path):
    catalog_path = tmp_path / "game" / "ambition_content" / "assets" / "data" / "character_catalog.ron"
    catalog_path.parent.mkdir(parents=True)
    spec = {"character_id": "npc_subject", "ids": ["subject"]}
    for label in ("Old Title", 'New "Title"'):
        escaped = label.replace('"', '\\"')
        catalog_path.write_text(
            '(\n    characters: {\n        "npc_subject": (\n'
            f'            display_name: "{escaped}",\n'
            '            manifest: "sprites/subject_spritesheet.ron",\n'
            '        ),\n    },\n)\n', encoding="utf8",
        )
        record = view.lineage_view("subject", spec, store=None, cache=None, blamer=None,
                                   current={"subject"}, catalog=characters.catalog_rows(tmp_path))
        assert record["name"] == label
        assert record["character_id"] == "npc_subject"
        assert record["targets"] == ["subject"]


def test_a_catalog_id_finds_its_history_without_a_published_target(tmp_path, monkeypatch):
    monkeypatch.setattr(characters, "registry_outputs", lambda: {})
    join = characters.join({"subject": {"character_id": "npc_subject"}}, tmp_path)
    assert join.find("npc_subject") == [("subject", "catalog npc_subject")]


def test_cast_lineages_reference_a_name_in_the_catalog():
    lineages = yaml.safe_load(Path(characters.__file__).with_name("lineages.yaml").read_text())["lineages"]
    rows = characters.catalog_rows(characters.repo_root())
    for name, spec in lineages.items():
        if character_id := spec.get("character_id"):
            assert "name" not in spec, name
            if rows:
                assert character_id in rows and rows[character_id].display_name, name
        else:
            assert spec.get("name"), name
