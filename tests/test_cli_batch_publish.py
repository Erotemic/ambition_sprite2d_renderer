from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from ambition_sprite2d_renderer.cli import commands
from ambition_sprite2d_renderer.cli.parser import build_parser
from ambition_sprite2d_renderer.registry import RUNTIME_ADAPTER_CONFIG_STEMS

def test_portrait_files_can_report_multiple_targets_in_one_process(monkeypatch, capsys):
    targets = {
        "alice": SimpleNamespace(
            portrait_install_subdir=None,
            portrait_files=("alice_portraits.png", "alice_portraits.ron"),
        ),
        "boss": SimpleNamespace(
            portrait_install_subdir="boss",
            portrait_files=("boss_portraits.png", "boss_portraits.ron"),
        ),
    }
    monkeypatch.setattr(commands, "_get_target", targets.__getitem__)

    rc = commands._cmd_portrait_files(
        argparse.Namespace(targets=["alice", "boss"], with_target=True)
    )

    assert rc == 0
    assert capsys.readouterr().out.splitlines() == [
        "alice\talice_portraits.png",
        "alice\talice_portraits.ron",
        "boss\tboss/boss_portraits.png",
        "boss\tboss/boss_portraits.ron",
    ]

def test_publish_many_deduplicates_targets_and_uses_quiet_batch_path(monkeypatch):
    calls: list[tuple[str, Path, bool]] = []

    def fake_publish(name, dest_root, *, quiet=False, **opts):
        assert opts == {}
        calls.append((name, dest_root, quiet))
        return [dest_root / f"{name}.png"]

    def fake_bulk(op_name, names, op):
        assert op_name == "publish-many"
        for name in names:
            op(name)
        return 0

    monkeypatch.setattr(commands, "_publish_target", fake_publish)
    monkeypatch.setattr(commands, "_bulk_over", fake_bulk)
    dest = Path("sprites")

    rc = commands._cmd_publish_many(
        argparse.Namespace(
            targets=["alice", "alice", "boss"],
            dest_root=dest,
            quiet=True,
            quality_scale=None,
            downsample=None,
        )
    )

    assert rc == 0
    assert calls == [("alice", dest, True), ("boss", dest, True)]

def test_parser_accepts_explicit_publish_batch():
    args = build_parser().parse_args(
        ["publish-many", "--quiet", "--dest-root", "sprites", "alice", "boss"]
    )
    assert args.targets == ["alice", "boss"]
    assert args.dest_root == Path("sprites")
    assert args.quiet is True


def test_draw_review_reuses_loaded_jobs_and_emits_progress(
    monkeypatch, capsys, tmp_path
):
    jobs = [
        (
            Path("alice.yaml"),
            SimpleNamespace(target="robot", output_stem=lambda path: "alice"),
        )
    ]
    calls = []

    monkeypatch.setenv("AMBITION_RENDER_PROGRESS", "1")
    monkeypatch.setattr(commands, "load_jobs", lambda path: iter(jobs))

    def fake_draw_all(config_dir, out_dir, *, jobs=None):
        calls.append(("draw_all", list(jobs)))
        return [Path(out_dir) / "alice_spritesheet.png"]

    def fake_write_canonicals(config_dir, out_dir, *, jobs=None, progress=False):
        calls.append(("write_canonicals", list(jobs), progress))
        return [Path(out_dir) / "alice_canonical.png"]

    monkeypatch.setattr(commands, "draw_all", fake_draw_all)
    monkeypatch.setattr(commands, "write_canonicals", fake_write_canonicals)

    outputs = commands.draw_review(tmp_path / "configs", tmp_path / "out")

    assert [path.name for path in outputs] == [
        "alice_spritesheet.png",
        "alice_canonical.png",
    ]
    assert calls == [
        ("draw_all", jobs),
        ("write_canonicals", jobs, True),
    ]
    captured = capsys.readouterr().out
    assert "[draw-review] 1 configured character(s)" in captured
    assert "[draw-review] canonical gallery pass" in captured


def test_default_adapter_configs_reference_registered_generators():
    jobs = []
    jobs.extend(commands.load_jobs(commands.DEFAULT_CONFIG_DIR))
    jobs.extend(commands.load_jobs(commands.DEFAULT_REVIEW_CONFIG_DIR))

    commands._validate_adapter_jobs(jobs)


def test_draw_review_rejects_module_target_before_render(monkeypatch, tmp_path):
    config_dir = tmp_path / "review"
    config_dir.mkdir()
    config = config_dir / "pointed_polygon.yaml"
    config.write_text("target: pointed_polygon\n", encoding="utf8")

    def should_not_render(*args, **kwargs):
        raise AssertionError("rendering started before config validation")

    monkeypatch.setattr(commands, "write_spritesheet", should_not_render)

    with pytest.raises(ValueError, match="module-authored") as exc_info:
        commands.draw_review(config_dir, tmp_path / "out")

    message = str(exc_info.value)
    assert "pointed_polygon.yaml" in message
    assert "publish pointed_polygon" in message


def test_validate_configs_parser_defaults_to_both_character_job_surfaces():
    args = build_parser().parse_args(["validate-configs"])

    assert args.config_dir == commands.DEFAULT_CONFIG_DIR
    assert args.review_dir == commands.DEFAULT_REVIEW_CONFIG_DIR


def test_default_draw_all_runtime_adapter_population_is_explicit():
    assert {
        "boss",
        "goblin",
        "player_robot_v3",
        "robot",
        "ranged_skirmisher",
    } <= RUNTIME_ADAPTER_CONFIG_STEMS
    assert {
        "goblin_forest_spear",
        "player_extended",
        "robot_guardian",
        "robot_runner",
    }.isdisjoint(RUNTIME_ADAPTER_CONFIG_STEMS)
