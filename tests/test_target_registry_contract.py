"""Cheap structural checks for target discovery.

These tests validate the target protocol without rendering every authored asset.
Full visual review belongs in manual render commands; pytest should only protect
installable target contracts that tooling/runtime code depends on.
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.registry import discover_all_targets, discover_module_targets


def test_registered_targets_have_installable_sheet_contracts():
    report = discover_all_targets()
    assert report.targets

    problems: list[str] = []
    for name, target in sorted(report.targets.items()):
        if not target.sheet_files:
            problems.append(f"{name}: no sheet_files")
            continue
        if len(target.sheet_files) != len(set(target.sheet_files)):
            problems.append(f"{name}: duplicate sheet_files")
        for fname in target.sheet_files:
            path = Path(fname)
            if path.is_absolute() or ".." in path.parts:
                problems.append(f"{name}: non-local sheet file {fname!r}")
        if not any(fname.endswith(".png") for fname in target.sheet_files):
            problems.append(f"{name}: no png output declared")
        if not any(fname.endswith((".yaml", ".json")) for fname in target.sheet_files):
            problems.append(f"{name}: no manifest output declared")
    assert problems == []


def test_module_targets_expose_callable_renderers():
    report = discover_module_targets()
    missing = []
    for name, target in sorted(report.targets.items()):
        if not callable(getattr(target, "_render_fn", None)):
            missing.append(name)
    assert missing == []


def test_target_names_are_unique_after_discovery():
    report = discover_all_targets()
    names = list(report.targets)
    assert len(names) == len(set(names))
