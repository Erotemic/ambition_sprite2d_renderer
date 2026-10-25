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
import pytest

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


# ---- trailers: one spelling per model ------------------------------------------------


def test_trailer_spellings_name_one_model_each():
    attribution, store = _modules()
    body = "\n".join([
        "Co-authored-by: OpenAI GPT-5.6 Thinking <noreply@openai.com>",
        "Co-authored-by: GPT-5.6 Thinking [noreply@openai.com](mailto:noreply@openai.com)",
        "Co-Authored-By: Claude Opus 5 (claude-opus-5)",
        "Co-authored-by: qwen3.8-27b (LiteLLM) <noreply@litellm.ai>",
    ])
    got = attribution.attribute(_commit(store, "agent", "x", body), {})
    assert got.models == ("GPT-5.6 Thinking", "Claude Opus 5", "qwen3.8-27b (LiteLLM)"), got.models
    mentioned = attribution.attribute(_commit(store, "joncrall", "Big GPT 5.6 Alice improvement"), {})
    assert mentioned.models == ("GPT-5.6",), mentioned.models
    # The ledger's placeholder is not a model.
    ledger = {"a" * 40: [{"m": ["<synthetic>", "claude-opus-5"]}]}
    assert attribution.attribute(_commit(store, "agent", "x"), ledger).models == ("Claude Opus 5",)


# ---- generator authorship across the two imports ---------------------------------------


def _git(repo, *args, env=None):
    import os
    import subprocess

    full = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", **(env or {}))
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=full).stdout.strip()


def _commit_files(repo, files: dict, author: str, message: str, date: str, *, orphan: str | None = None) -> str:
    import shutil

    if orphan:
        _git(repo, "checkout", "-q", "--orphan", orphan)
        _git(repo, "rm", "-rq", "--cached", "--ignore-unmatch", ".")
        for child in repo.iterdir():
            if child.name != ".git":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    _git(repo, "add", "-A")
    env = {"GIT_AUTHOR_NAME": author, "GIT_AUTHOR_EMAIL": "a@b", "GIT_COMMITTER_NAME": author,
           "GIT_COMMITTER_EMAIL": "a@b", "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    _git(repo, "commit", "-q", "-m", message, env=env)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def history_store(tmp_path_factory):
    """Three stretches as in the real history: the renderer as a subdirectory
    of the main repository (A0), its own repository (R0, whose first commit is
    a copy), and the active repository (R1, whose first commit is a copy)."""
    repo = tmp_path_factory.mktemp("store")
    _git(repo, "init", "-q", "-b", "a0")
    foo = "ambition_sprite2d_renderer/targets/characters/foo.py"
    a0 = "tools/ambition_sprite2d_renderer/"
    _commit_files(repo, {a0 + foo: "one\ntwo\n"}, "agent", "Foo\n\nCo-Authored-By: Claude Opus 4.7 <x@y>", "2026-05-01T00:00:00+00:00")
    _git(repo, "update-ref", "refs/epochs/ambition/000/heads/main", "HEAD")
    _commit_files(repo, {foo: "one\ntwo\n"}, "joncrall", "Initial commit", "2026-06-25T00:00:00+00:00", orphan="r0")
    _commit_files(repo, {foo: "one\ntwo\nthree\n"}, "agent", "Three\n\nCo-authored-by: GPT-6 <x@y>", "2026-07-01T00:00:00+00:00")
    _git(repo, "update-ref", "refs/epochs/ambition_sprite2d_renderer/000/heads/main", "HEAD")
    # The import adds a line that no earlier commit has: its author is unknown.
    _commit_files(repo, {foo: "one\ntwo\nthree\nimported\n"}, "joncrall", "Start git epoch 1", "2026-09-06T00:00:00+00:00", orphan="r1")
    files = {
        foo: "one\ntwo\nthree\nimported\nfour\n",
        "ambition_sprite2d_renderer/data/characters/foo/foo.svg": "<svg>\n</svg>\n",
        "ambition_sprite2d_renderer/targets/characters/foo_v2.py": "v2\n",
        "ambition_sprite2d_renderer/targets/characters/_foo_v2_gear.py": "gear\n",
        "ambition_sprite2d_renderer/targets/characters/foo_family.py": "family\n",
        "ambition_sprite2d_renderer/targets/characters/_duo.py": "shared\n",
        "tests/test_foo.py": "test\n",
    }
    head = _commit_files(repo, files, "agent", "Four\n\nCo-Authored-By: Claude Opus 5.5 <x@y>", "2026-10-01T00:00:00+00:00")
    _git(repo, "update-ref", "refs/active/ambition_sprite2d_renderer/main", "HEAD")
    return repo, head


def test_a_line_is_followed_through_both_imports_to_the_commit_that_wrote_it(history_store, tmp_path):
    import importlib

    authorship = importlib.import_module("design_history.authorship")
    repo, head = history_store
    blamer = authorship.Blamer(repo, tmp_path)
    who = blamer.authorship(head, ["ambition_sprite2d_renderer/targets/characters/foo.py"])
    got = {s.who: s.lines for s in who.shares}
    assert got == {"Claude Opus 4.7": 2, "GPT-6": 1, "unknown": 1, "Claude Opus 5.5": 1}, got
    assert who.parts["art"] == [] and who.lines == 5
    # A second Blamer reads the cache and agrees.
    again = authorship.Blamer(repo, tmp_path).authorship(head, ["ambition_sprite2d_renderer/targets/characters/foo.py"])
    assert {s.who: s.lines for s in again.shares} == got


def test_the_files_of_a_target_are_found_by_name_not_by_a_longer_target(history_store):
    import importlib

    authorship = importlib.import_module("design_history.authorship")
    repo, head = history_store
    files, how = authorship.generator_files(repo, head, "", "foo", aliases=[], others={"foo", "foo_v2", "foo_family"}, patterns=["_duo"])
    assert how == "named"
    assert sorted(files) == [
        "ambition_sprite2d_renderer/data/characters/foo/foo.svg",
        "ambition_sprite2d_renderer/targets/characters/_duo.py",
        "ambition_sprite2d_renderer/targets/characters/foo.py",
    ], files
    v2, _ = authorship.generator_files(repo, head, "", "foo_v2", aliases=[], others={"foo", "foo_v2"})
    assert sorted(v2) == ["ambition_sprite2d_renderer/targets/characters/_foo_v2_gear.py",
                          "ambition_sprite2d_renderer/targets/characters/foo_v2.py"], v2
    # A variant takes its family's module as a helper; a generation does not.
    variant, how = authorship.generator_files(repo, head, "", "foo_family_red", aliases=[], others={"foo_family"}, patterns=["foo_family"])
    assert (variant, how) == (["ambition_sprite2d_renderer/targets/characters/foo_family.py"], "helper")
    v3, how = authorship.generator_files(repo, head, "", "foo_v3", aliases=[], others={"foo"}, patterns=["foo"])
    assert "ambition_sprite2d_renderer/targets/characters/foo.py" not in v3


# ---- from a character to its lineage ------------------------------------------------


def test_a_catalog_row_a_look_and_a_boss_key_each_find_their_lineage(tmp_path):
    import importlib

    characters = importlib.import_module("design_history.characters")
    data = tmp_path / "game" / "demo" / "assets" / "data"
    data.mkdir(parents=True)
    (data / "character_catalog.ron").write_text("""(
    brain_presets: {
        "idle": (
            manifest: "sprites/not_a_row_spritesheet.ron",
        ),
    },
    characters: {
        "npc_foo": (
            sprite: Some((manifest: "sprites/foo_v2_spritesheet.ron")),
        ),
        "npc_foo_armored": (
            form_of: Some("npc_foo"),
        ),
    },
)
""")
    (tmp_path / "game" / "ambition_content" / "assets" / "data").mkdir(parents=True)
    (tmp_path / "game" / "ambition_content" / "assets" / "data" / "boss_art_keys.ron").write_text(
        '(\n    sprite_filenames: {\n        "big_foo": "foo_v2_spritesheet.png",\n    },\n)\n'
    )
    lineages = {"foo": {"ids": ["foo_v2", "foo"], "eras": [{"commit": "aaaaaaa", "label": "x", "id": "foo"}]}}
    join = characters.join(lineages, tmp_path)
    assert set(join.rows) == {"npc_foo", "npc_foo_armored", "boss:big_foo"}
    assert [lineage for lineage, _ in join.find("npc_foo")] == ["foo"]
    assert [lineage for lineage, _ in join.find("npc_foo_armored")] == ["foo"]
    assert [lineage for lineage, _ in join.find("boss:big_foo")] == ["foo"]
    assert [lineage for lineage, _ in join.find("foo")] == ["foo"]
    assert join.find("npc_bar") == []
    assert characters.versioned_pairs({"foo", "foo_v2", "foo_v3", "bar_v2"}) == [("foo_v2", "foo"), ("foo_v3", "foo_v2")]


# ---- the census guard ------------------------------------------------------------------


def test_every_committed_versioned_target_is_in_one_lineage_with_the_target_it_redraws():
    """A `<base>_vN` target published beside `<base>` is a generation of the
    same character, so one lineage names both. A target that is still
    untracked (being drawn) is reported by the census and not held here."""
    import importlib
    import sys

    census = importlib.import_module("design_history.census")
    characters = importlib.import_module("design_history.characters")
    targets = census.registry(sys.executable)
    cov = census.coverage(_lineages(), targets, characters.repo_root())
    gaps = [g for g in cov["versioned_gaps"] if not g["in_progress"]]
    assert gaps == [], gaps
