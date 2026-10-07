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
    # An abbreviation and the full id are the same commit, so compare by prefix.
    for name, spec in _lineages().items():
        seen: list[tuple[str, object]] = []
        for era in spec.get("eras") or []:
            commit, ident = str(era["commit"]), era.get("id")
            for other, other_id in seen:
                assert not (
                    ident == other_id and (commit.startswith(other) or other.startswith(commit))
                ), f"{name} repeats {commit} ({other})"
            seen.append((commit, ident))


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


def _modules():
    import importlib

    return (
        importlib.import_module("design_history.attribution"),
        importlib.import_module("design_history.store"),
    )


def _commit(store, author, subject, body="", date="2026-01-01T00:00:00+00:00"):
    return store.Commit("a" * 40, "R1", date, author, subject, body)


def test_a_message_naming_a_model_outranks_a_human_author():
    """The ORDER, not just the presence: Jon's account committed a redraw whose
    subject names GPT-5.6, and that is a model mention, not "no model named"."""
    attribution, store = _modules()
    got = attribution.attribute(_commit(store, "joncrall", "Big GPT 5.6 Alice improvement"), {})
    assert got.basis == "message", got
    assert got.models and "GPT" in got.models[0].upper()


def test_the_ledger_outranks_a_trailer_and_a_trailer_outranks_the_ledgers_absence():
    attribution, store = _modules()
    trailer = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    ledger = {"a" * 40: [{"m": ["gpt-5.5"]}]}
    got = attribution.attribute(_commit(store, "agent", "x", trailer), ledger)
    assert (got.basis, got.models) == ("measured", ("GPT-5.5",)), got
    got = attribution.attribute(_commit(store, "agent", "x", trailer), {})
    assert (got.basis, got.models) == ("declared", ("Claude Opus 5.5",)), got


def test_trailers_are_read_the_way_git_writes_them():
    attribution, store = _modules()
    body = "\n".join([
        "Co-Authored-By: Claude Opus 5.5",                       # no email
        "co-authored-by: claude opus 5.5 <a@b>",                 # case: the same model
        "Co-Authored-By: Claude Opus 4.8 [1M] <a@b>",            # window is not a model
        "Co-Authored-By: Claude Sonnet 4.6 (1M context) <a@b>",
        "Co-Authored-By: Jane Doe <jane@example.com>",           # a human is no model
    ])
    got = attribution.attribute(_commit(store, "agent", "x", body), {})
    assert got.basis == "declared"
    assert got.models == ("Claude Opus 5.5", "Claude Opus 4.8", "Claude Sonnet 4.6"), got.models
    only_human = attribution.attribute(
        _commit(store, "agent", "x", "Co-Authored-By: Jane Doe <jane@example.com>"), {}
    )
    assert only_human.basis == "unknown", only_human


def test_commits_sort_by_their_instant_not_by_their_date_text():
    """`%aI` carries the author's own offset: 20:00-04:00 is midnight UTC, AFTER
    23:00+00:00 on the same calendar day, though its text sorts before."""
    _, store = _modules()
    earlier = _commit(store, "agent", "x", date="2026-01-01T23:00:00+00:00")
    later = _commit(store, "agent", "y", date="2026-01-01T20:00:00-04:00")
    assert later.date < earlier.date, "the premise: the strings sort the wrong way round"
    assert sorted([later, earlier], key=lambda c: c.instant) == [earlier, later]
    # And the survey sorts by it: a sort key of the raw text is how 15 of 343
    # positions in the renderer's history came out of order.
    survey = (HISTORY / "survey.py").read_text()
    assert "key=lambda row: row[0].instant" in survey and "key=lambda c: c.commit.instant" in survey
    assert not re.search(r"key=lambda [^:]+:\s*[^,)]*\.date\b", survey)


def test_the_scratch_root_is_found_however_deep_the_png_sits():
    import importlib
    import tempfile

    stills = importlib.import_module("design_history.stills")
    root = Path(tempfile.mkdtemp(prefix="dh-pick-"))
    try:
        nested = root / "a" / "b" / "x.png"
        nested.parent.mkdir(parents=True)
        nested.write_bytes(b"")
        assert stills.scratch_root(nested) == root
        assert stills.scratch_root(root / "flat.png") == root
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)
