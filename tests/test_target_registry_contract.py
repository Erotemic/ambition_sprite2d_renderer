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
        # A manifest can be the renderer's intermediate YAML/JSON or the RON
        # sheet manifest the engine actually loads; a target that emits only the
        # `.ron` (e.g. the gnu_ton boss, which skips the YAML intermediate) still
        # declares a manifest.
        if target.portrait_files:
            if not target.supports_portraits:
                problems.append(f"{name}: portrait files declared without renderer")
            for fname in target.portrait_files:
                path = Path(fname)
                if path.is_absolute() or ".." in path.parts:
                    problems.append(f"{name}: non-local portrait file {fname!r}")
            if not any(fname.endswith(".png") for fname in target.portrait_files):
                problems.append(f"{name}: portrait product has no png")
            if not any(fname.endswith(".ron") for fname in target.portrait_files):
                problems.append(f"{name}: portrait product has no ron manifest")
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


def test_noether_dedicated_module_outranks_legacy_loose_rig():
    report = discover_module_targets()
    target = report.targets["noether"]
    assert target.module_path == "ambition_sprite2d_renderer.targets.characters.noether"


def test_polygon_reference_fighters_are_module_authored_targets():
    report = discover_all_targets()

    for name in ("pointed_polygon", "pugnacious_polygon"):
        target = report.targets[name]
        assert target.kind == "module"
        assert target.module_path == (
            f"ambition_sprite2d_renderer.targets.characters.{name}"
        )


def test_entity_target_does_not_claim_authoring_diagnostics():
    target = discover_all_targets().targets["entities"]
    claims = set(target.claimed_install_names())

    assert "entities/entity_contact_sheet.png" not in claims
    assert "entities/entity_manifest.yaml" not in claims
    assert any(name.startswith("entities/") and name.endswith(".png") for name in claims)


def test_a_portrait_function_a_module_writes_is_the_one_its_target_publishes():
    """A module that writes ``render_portraits`` publishes those portraits.

    A module with a ``TARGETS`` table names its hooks in the table. Eleven
    characters had the function and not the key (2026-10-13): each published
    the default crop of its body with one clip, and a conversation that named
    another clip got the default with no error."""
    import importlib

    report = discover_module_targets()
    problems: list[str] = []
    for name, target in sorted(report.targets.items()):
        module_path = getattr(target, "module_path", None)
        if not module_path:
            continue
        module = importlib.import_module(module_path)
        own = getattr(module, "render_portraits", None)
        table = getattr(module, "TARGETS", None)
        if callable(own) and isinstance(table, dict) and len(table) == 1 and target._render_portraits_fn is None:
            problems.append(f"{name}: {module_path}.render_portraits is not what the target publishes")
    assert problems == []


def test_a_faction_lineup_row_is_built_by_the_publish_worker_as_discovery_builds_it():
    """The batch publish builds each target again in a worker interpreter
    (`read_record._one_target`). A lineup row cannot be rebuilt from its file
    alone, which holds many jobs: the worker reads the lineup and takes the row
    by its name."""
    from pathlib import Path

    from ambition_sprite2d_renderer import read_record

    discovered = discover_all_targets().targets["goblin_cantina_chieftain"]
    spec = {
        "name": discovered.name,
        "kind": discovered.kind,
        "category": discovered.category,
        "module_path": discovered.module_path,
        "config_path": str(discovered._config_path),
        "lineup_row": discovered._lineup_row,
    }
    rebuilt = read_record._one_target(spec)
    assert rebuilt.name == discovered.name
    assert rebuilt._job == discovered._job
    assert Path(rebuilt._config_path).name == "music_factions.yaml"
