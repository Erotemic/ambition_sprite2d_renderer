"""Cached historical art is available without an authorship measurement."""

import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from design_history import stills, view


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
