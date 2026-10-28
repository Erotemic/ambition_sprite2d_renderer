"""The art provenance records (`provenance.py`): which generator made which
published file, from which inputs."""

from __future__ import annotations

import json
from pathlib import Path

from ambition_sprite2d_renderer import provenance


def test_a_destination_records_only_under_the_game_asset_root(tmp_path, monkeypatch):
    monkeypatch.delenv(provenance.ENV, raising=False)
    assert provenance.record_dir(tmp_path / "sprites") is None
    sprites = provenance.asset_root() / "sprites"
    assert provenance.record_dir(sprites) == provenance.provenance_root() / "sprites"
    # The records are never inside a runtime asset root, which is packaged whole.
    assert not provenance.record_dir(sprites).resolve().is_relative_to(provenance.asset_root().resolve())
    monkeypatch.setenv(provenance.ENV, str(tmp_path / "records"))
    assert provenance.record_dir(tmp_path / "staging" / "sprites") == tmp_path / "records"


def test_a_record_names_each_output_its_digest_and_the_callable_that_drew_it(tmp_path):
    dest = tmp_path / "dest"
    (dest / "sub").mkdir(parents=True)
    (dest / "sub" / "a.png").write_bytes(b"pixels")
    path = provenance.write_record(
        tmp_path / "records",
        "unit",
        generator={"family": "test", "id": "unit"},
        dest=dest,
        outputs=[(dest / "sub" / "a.png", provenance.made_by(provenance.write_record)), (dest / "missing.png", None)],
        inputs=[],
    )
    record = provenance.read_record(path)
    assert record["schema"] == provenance.SCHEMA and record["basis"] == "rendered"
    (out,) = record["outputs"]
    assert out["path"] == "sub/a.png" and out["sha256"] == provenance.digest(dest / "sub" / "a.png")
    assert out["made_by"]["callable"].endswith(":write_record")
    assert out["made_by"]["source"].endswith("ambition_sprite2d_renderer/provenance.py") and out["made_by"]["line"] > 0




def test_the_terrain_plan_is_what_draw_writes_and_draw_records_it(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.terrain.__main__ import main, plan

    monkeypatch.setenv(provenance.ENV, str(tmp_path / "records"))
    out = tmp_path / "room_dressing"
    assert main(["draw", "--out-dir", str(out), "hub"]) == 0
    planned = {p.name for outputs in plan(out, ["hub"]).units.values() for p, _ in outputs}
    assert planned == {p.name for p in out.glob("*.png")}
    records = {p.stem: json.loads(p.read_text()) for p in (tmp_path / "records").glob("*.json")}
    assert "hub" in records
    assert all(o["made_by"]["callable"] for r in records.values() for o in r["outputs"])
    assert sum(len(r["outputs"]) for r in records.values()) == len(planned)


def test_the_background_plan_names_every_layer_of_every_theme(tmp_path):
    from ambition_sprite2d_renderer.backgrounds import scenes
    from ambition_sprite2d_renderer.backgrounds.__main__ import plan

    book = plan(tmp_path, [])
    assert set(book.units) == set(scenes.THEMES)
    for theme, outputs in book.units.items():
        assert {p.name for p, _ in outputs} == {f"{theme}_{layer}.png" for layer in (*scenes.LAYERS, "flat")}
        assert all(by and by["callable"] for _, by in outputs)
