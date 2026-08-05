"""Probes for the install audit.

Each test here was written to FAIL FIRST against a deliberately broken oracle,
because the failure mode this tool exists to prevent — calling a live asset
unclaimed — is invisible in a passing run. The comments record which mutation
turned each one red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ambition_sprite2d_renderer.devtools.installed_audit import (
    COMMAND_PRODUCED,
    AuditResult,
    audit,
    format_report,
)
from ambition_sprite2d_renderer.registry import DiscoveryReport, Target


def _target(name: str, **kwargs) -> Target:
    kwargs.setdefault("category", "props")
    kwargs.setdefault("module_path", f"fake.{name}")
    kwargs.setdefault("render", lambda out_dir, **opts: [])
    kwargs.setdefault(
        "sheet_files",
        (
            f"{name}_spritesheet.png",
            f"{name}_spritesheet.yaml",
            f"{name}_spritesheet.ron",
            f"{name}_actor.ron",
        ),
    )
    return Target.from_module(name=name, **kwargs)


def _report(*targets: Target, warnings: list[str] | None = None) -> DiscoveryReport:
    return DiscoveryReport(
        targets={target.name: target for target in targets},
        warnings=list(warnings or []),
    )


def _install(root: Path, *names: str) -> None:
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")


def test_a_registered_targets_files_are_never_orphans(tmp_path: Path) -> None:
    """`glider` is the row's own proof case: a live registered target whose
    files are absent from the renderer's `generated/` tree on the machine that
    measured. An oracle built on `generated/` flags all four.

    PROBE: dropping `glider` from the injected registry turns this red with all
    four files listed as orphans — which is exactly what a `generated/`-based
    tool reports for it, and exactly what a GC would have deleted.
    """
    _install(
        tmp_path,
        "glider_spritesheet.png",
        "glider_spritesheet.yaml",
        "glider_spritesheet.ron",
        "glider_actor.ron",
    )
    result = audit(tmp_path, report=_report(_target("glider")))
    assert not result.refused
    assert result.orphans == []


def test_an_unclaimed_file_is_reported(tmp_path: Path) -> None:
    """The other direction: a file no target declares must be named.

    PROBE: adding `retired_v1` to the injected registry turns this red — the
    audit stops reporting the file and the assertion on `orphans` fails.
    """
    _install(
        tmp_path,
        "glider_spritesheet.png",
        "retired_v1_spritesheet.png",
        "retired_v1_actor.ron",
    )
    result = audit(tmp_path, report=_report(_target("glider")))
    assert result.orphans == [
        "retired_v1_actor.ron",
        "retired_v1_spritesheet.png",
    ]


def test_sidecars_the_installer_copies_without_declaring_are_claimed(
    tmp_path: Path,
) -> None:
    """`_copy_sheet_files` copies `<x>.ron` beside `<x>.yaml` and `<stem>_actor.ron`
    beside any sheet file, whether or not `SHEET_FILES` lists them. The audit
    claims by the same rule (`install_companions`), so those sidecars are not
    orphans.

    PROBE: making `claimed_install_names` skip `install_companions` turns this
    red with `widget_spritesheet.ron` and `widget_actor.ron` reported.
    """
    _install(
        tmp_path,
        "widget_spritesheet.png",
        "widget_spritesheet.yaml",
        "widget_spritesheet.ron",
        "widget_actor.ron",
    )
    target = _target(
        "widget",
        sheet_files=("widget_spritesheet.png", "widget_spritesheet.yaml"),
    )
    result = audit(tmp_path, report=_report(target))
    assert result.orphans == []


def test_a_shrunken_multi_page_sheet_leaves_its_extra_page_behind(
    tmp_path: Path,
) -> None:
    """Page siblings are claimed by the installed manifest's `images` list, not
    by a glob of whatever pages this machine last rendered. A sheet whose page
    count SHRANK leaves the extra page installed, and only the manifest records
    how many pages are current.

    PROBE: claiming page siblings by globbing `<stem>_spritesheet.*.png` in the
    install root instead — the tempting implementation — turns this red: the
    stale `.3.png` claims itself.
    """
    _install(tmp_path, "big_spritesheet.png", "big_actor.ron", "big_spritesheet.ron")
    (tmp_path / "big_spritesheet.yaml").write_text(
        "target: big\n"
        "image: big_spritesheet.png\n"
        "images:\n"
        "- big_spritesheet.png\n"
        "- big_spritesheet.1.png\n"
        "- big_spritesheet.2.png\n"
    )
    _install(
        tmp_path,
        "big_spritesheet.1.png",
        "big_spritesheet.2.png",
        "big_spritesheet.3.png",
    )
    result = audit(tmp_path, report=_report(_target("big")))
    assert result.orphans == ["big_spritesheet.3.png"]


def test_a_subdir_installing_target_claims_only_its_subdir(tmp_path: Path) -> None:
    """`INSTALL_SUBDIR` is part of what a target claims. A copy of the same file
    at the sprite root is a different file, and a stale one — this is the shape
    of the residue left when `entities` was fixed to install where the loader
    actually reads.

    PROBE: dropping `install_subdir` from the claim path turns this red both
    ways at once — the top-level stale copy stops being reported and the live
    `entities/spike.png` starts being reported.
    """
    _install(tmp_path, "entities/spike.png", "spike.png")
    target = _target(
        "entities", sheet_files=("spike.png",), install_subdir="entities"
    )
    result = audit(tmp_path, report=_report(target))
    assert result.orphans == ["spike.png"]
    assert "entities/spike.png" in result.claimed_by


def test_a_warning_from_discovery_refuses_the_whole_report(tmp_path: Path) -> None:
    """A module that failed to register claims nothing, so its installed files
    read as unclaimed — the `generated/` mistake one level up, and how a partial
    regen makes every unrendered target look stale.

    PROBE: changing the guard to `if len(result.registry_warnings) > 99` turns
    this red — the audit reports `live_spritesheet.png` as an orphan on the
    strength of a registry that just told it a producer is missing.
    """
    _install(tmp_path, "live_spritesheet.png")
    result = audit(tmp_path, report=_report(warnings=["props/live: no `render()`"]))
    assert result.refused
    assert result.orphans == []
    assert "props/live: no `render()`" in format_report(result)


def test_a_failed_discovery_refuses_rather_than_reporting_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discovery raising must not read as "nothing claims anything".

    PROBE: removing the `try` and letting the exception escape turns this into
    an error rather than a refusal; catching it and returning an empty registry
    instead turns it red with every installed file reported as an orphan.
    """
    _install(tmp_path, "live_spritesheet.png")

    def boom() -> DiscoveryReport:
        raise ImportError("targets/props/live.py: cannot import name 'gone'")

    monkeypatch.setattr(
        "ambition_sprite2d_renderer.devtools.installed_audit.discover_all_targets",
        boom,
    )
    result = audit(tmp_path)
    assert result.refused
    assert result.orphans == []
    assert "ImportError" in (result.refusal_reason or "")


def test_standalone_command_output_is_not_an_orphan(tmp_path: Path) -> None:
    """Producer class 3: files a CLI command emits that no target claims.
    `ldtk-manifest` writes `ldtk_sprite_manifest.json`; an audit that knows only
    the target registry reports it as stale.

    PROBE: emptying `COMMAND_PRODUCED` turns this red.
    """
    _install(tmp_path, *COMMAND_PRODUCED)
    result = audit(tmp_path, report=_report())
    assert result.orphans == []


def test_the_audit_never_writes(tmp_path: Path) -> None:
    """REPORT ONLY is the whole design. Nothing this module exports may remove
    or rewrite a file, and no flag may ask it to.

    PROBE: adding an `unlink` to the orphan loop turns this red.
    """
    _install(tmp_path, "glider_spritesheet.png", "retired_v1_spritesheet.png")
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    result = audit(tmp_path, report=_report(_target("glider")))
    format_report(result, verbose=True)
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before

    import ambition_sprite2d_renderer.devtools.installed_audit as module

    source = Path(module.__file__).read_text()
    for forbidden in ("unlink", "rmtree", "shutil.move", "os.remove", "write_text"):
        assert forbidden not in source, f"the audit must not {forbidden}"


def test_result_shape_is_stable_for_json_consumers(tmp_path: Path) -> None:
    result = audit(tmp_path, report=_report())
    assert isinstance(result, AuditResult)
    assert result.scanned == 0
    assert result.orphans == []
