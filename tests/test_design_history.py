"""The design-history viewer is walled off from the renderer, and its inputs parse.

These tests need no history store: they read `design_history/lineages.yaml` and
the package's own sources. What they protect is the wall (nothing in the
renderer imports the viewer, the viewer is not packaged) and the shape of the
curated eras, so a typo cannot silently become an empty sheet.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "design_history"


def _lineages() -> dict:
    return yaml.safe_load((HISTORY / "lineages.yaml").read_text())["lineages"]


def test_every_lineage_names_ids_and_every_era_is_one_commit_and_a_label():
    for name, spec in _lineages().items():
        assert spec.get("ids"), f"{name} names no target ids"
        for era in spec.get("eras") or []:
            assert re.fullmatch(r"[0-9a-f]{7,40}", str(era["commit"])), (name, era)
            assert era.get("label"), (name, era)


def test_no_lineage_lists_one_commit_twice_for_the_same_id():
    for name, spec in _lineages().items():
        seen = set()
        for era in spec.get("eras") or []:
            key = (era["commit"], era.get("id"))
            assert key not in seen, f"{name} repeats {key}"
            seen.add(key)


def test_the_renderer_does_not_import_the_viewer_and_the_package_does_not_ship_it():
    for source in (ROOT / "ambition_sprite2d_renderer").rglob("*.py"):
        assert "design_history" not in source.read_text(), source
    assert "design_history" not in (ROOT / "pyproject.toml").read_text()


def test_a_trailer_outranks_a_mention_and_a_human_author_names_no_model():
    import importlib

    attribution = importlib.import_module("design_history.attribution")
    store = importlib.import_module("design_history.store")
    make = lambda author, subject, body="": store.Commit("a" * 40, "R1", "2026-01-01T00:00:00+00:00", author, subject, body)

    declared = attribution.attribute(
        make("agent", "GPT-5.5 plan", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"), {}
    )
    assert (declared.basis, declared.models) == ("declared", ("Claude Opus 5.5",))
    mentioned = attribution.attribute(make("agent", "Big GPT 5.6 Alice improvement"), {})
    assert mentioned.basis == "message"
    human = attribution.attribute(make("joncrall", "tune a hurtbox"), {})
    assert (human.basis, human.models) == ("author", ())
    measured = attribution.attribute(make("agent", "x"), {"a" * 40: [{"m": ["claude-opus-5-5"]}]})
    assert (measured.basis, measured.models) == ("measured", ("Claude Opus 5.5",))
