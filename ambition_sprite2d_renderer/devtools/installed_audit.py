"""Report installed sprite files that no registered producer claims.

This audit is intentionally read-only. Claims come from the same target registry
used by normal discovery plus known standalone producer commands. Any discovery
warning makes orphan reporting unreliable, so the audit reports the warning and
refuses to classify files instead of deleting or guessing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from ..registry import DiscoveryReport, discover_all_targets
from ..yaml_io import safe_load


#: Producer class 3: files written by a standalone command rather than by any
#: registered target. Each entry names the command that writes it, so a reader
#: can re-run the producer instead of guessing whether the file is stale.
#: Keep this list SHORT and each entry justified — it is an escape hatch from
#: the registry oracle, and every unjustified entry hides a real orphan.
COMMAND_PRODUCED: Mapping[str, str] = {
    "ldtk_sprite_manifest.json": (
        "python3 -m ambition_sprite2d_renderer ldtk-manifest"
    ),
    "editor_icons.png": (
        "python3 -m ambition_ldtk_tools visual-manifest generate-icons "
        "(tools/ambition_ldtk_tools — a different tool, same install root)"
    ),
    ".gitignore": "repository infrastructure, not a rendered asset",
}


def faction_claims() -> Dict[str, str]:
    """Producer class 3, resolved from data rather than from a copied list.

    ``draw-factions`` renders every character declared in
    ``configs/factions/music_factions.yaml``; ``regen_sprites.sh`` then copies a
    subset into the install root. The config is the declaration, so read it
    instead of restating three filenames here — a hand-copied list is a fresh
    drift source, and the drift it causes is "the audit calls a live sheet
    stale".
    """
    from ..cli.commands import DEFAULT_FACTION_CONFIG

    config_path = Path(DEFAULT_FACTION_CONFIG)
    if not config_path.is_file():
        return {}
    spec = safe_load(config_path.read_text())
    if not isinstance(spec, Mapping):
        return {}
    producer = "command:python3 -m ambition_sprite2d_renderer draw-factions"
    claims: Dict[str, str] = {}
    for faction in spec.get("factions") or ():
        if not isinstance(faction, Mapping):
            continue
        for character in faction.get("characters") or ():
            if not isinstance(character, Mapping):
                continue
            stem = character.get("id")
            if not stem:
                continue
            for name in (
                f"{stem}_spritesheet.png",
                f"{stem}_spritesheet.yaml",
                f"{stem}_spritesheet.ron",
                f"{stem}_actor.ron",
                f"{stem}_portraits.png",
                f"{stem}_portraits.ron",
            ):
                claims[name] = producer
    return claims

#: Directories under the install root that no producer in THIS tool installs
#: into, and whose contents are therefore outside what the registry can speak
#: for. They are reported as unaudited, never as orphans: calling a file
#: unclaimed because this tool cannot see its producer is precisely the mistake
#: the module docstring exists to prevent.
UNAUDITED_SUBDIRS: Mapping[str, str] = {
    "backgrounds": "written by regen_backgrounds.sh, not by a sprite target",
    "props": (
        "written by regen_sprites.sh, which copies selected targets' "
        "`*_canonical_transparent.png` in under runtime basenames"
    ),
}


@dataclass
class AuditResult:
    """Outcome of one audit pass. ``refused`` short-circuits everything else."""

    install_root: Path
    refused: bool = False
    registry_warnings: List[str] = field(default_factory=list)
    registry_error: str | None = None
    scanned: int = 0
    claimed_by: Dict[str, str] = field(default_factory=dict)
    orphans: List[str] = field(default_factory=list)
    unaudited: List[str] = field(default_factory=list)
    claimed_but_absent: List[str] = field(default_factory=list)

    @property
    def refusal_reason(self) -> str | None:
        if not self.refused:
            return None
        if self.registry_error is not None:
            return f"target discovery failed: {self.registry_error}"
        return (
            f"target discovery emitted {len(self.registry_warnings)} warning(s); "
            "an unregistered producer's files read as unclaimed"
        )


def _page_siblings(manifest_path: Path) -> List[str]:
    """Page PNGs a sheet manifest declares beyond its page-0 image.

    A split sheet emits ``<stem>_spritesheet.png`` plus ``.1.png``, ``.2.png``,
    …; the INSTALLER discovers those by globbing its render dir, so they are not
    in any ``SHEET_FILES``. The installed manifest lists them under ``images``,
    which makes the claim readable from the install tree itself rather than from
    whatever pages this machine last rendered. That distinction is the whole
    point: a sheet whose page count SHRANK leaves the extra page behind, and the
    manifest is the only record of how many pages are current.
    """
    try:
        manifest = safe_load(manifest_path.read_text())
    except Exception:  # noqa: BLE001 - an unreadable manifest claims nothing
        return []
    if not isinstance(manifest, Mapping):
        return []
    images = manifest.get("images")
    if not isinstance(images, Sequence) or isinstance(images, (str, bytes)):
        return []
    return [str(name) for name in images]


def _scan(install_root: Path) -> List[str]:
    return sorted(
        path.relative_to(install_root).as_posix()
        for path in install_root.rglob("*")
        if path.is_file()
    )


def audit(
    install_root: Path,
    *,
    report: DiscoveryReport | None = None,
) -> AuditResult:
    """Classify every file under ``install_root``. Reads only; writes nothing.

    ``report`` is injectable so a test can hand in a registry with a warning, or
    a registry missing a target, and watch the refusal and the orphan verdict
    change. Production callers omit it and get the same discovery pass
    ``list-targets`` performs.
    """
    install_root = Path(install_root)
    result = AuditResult(install_root=install_root)

    if report is None:
        try:
            report = discover_all_targets()
        except Exception as ex:  # noqa: BLE001
            result.refused = True
            result.registry_error = f"{type(ex).__name__}: {ex}"
            return result

    result.registry_warnings = list(report.warnings)
    if result.registry_warnings:
        result.refused = True
        return result

    claimed: Dict[str, str] = {}
    for name, target in sorted(report.targets.items()):
        for rel in target.claimed_install_names():
            claimed.setdefault(rel, f"target:{name}")

    # Page siblings are claimed by the manifest that a target already claims, so
    # resolve them only after the registry pass has established that manifest.
    for rel in list(claimed):
        if not rel.endswith("_spritesheet.yaml"):
            continue
        manifest_path = install_root / rel
        if not manifest_path.is_file():
            continue
        parent = Path(rel).parent
        owner = claimed[rel]
        for image in _page_siblings(manifest_path):
            sibling = (parent / image).as_posix() if str(parent) != "." else image
            claimed.setdefault(sibling, f"{owner} (page of {Path(rel).name})")

    for rel, command in COMMAND_PRODUCED.items():
        claimed.setdefault(rel, f"command:{command}")
    for rel, producer in faction_claims().items():
        claimed.setdefault(rel, producer)

    installed = _scan(install_root)
    result.scanned = len(installed)
    for rel in installed:
        top = rel.split("/", 1)[0] if "/" in rel else None
        if top in UNAUDITED_SUBDIRS:
            result.unaudited.append(rel)
        elif rel in claimed:
            result.claimed_by[rel] = claimed[rel]
        else:
            result.orphans.append(rel)

    installed_set = set(installed)
    result.claimed_but_absent = sorted(
        rel for rel in claimed if rel not in installed_set
    )
    return result


def format_report(result: AuditResult, *, verbose: bool = False) -> str:
    lines: List[str] = []
    lines.append(f"# install audit: {result.install_root}")
    if result.refused:
        lines.append("")
        lines.append(f"REFUSED — {result.refusal_reason}")
        lines.append("")
        if result.registry_error is not None:
            lines.append(
                "  Fix target discovery (`python3 -m ambition_sprite2d_renderer "
                "list-targets`) and re-run."
            )
        else:
            for warning in result.registry_warnings:
                lines.append(f"  discovery warning: {warning}")
            lines.append("")
            lines.append(
                "  A module that failed to register claims nothing, so its "
                "installed files would be reported as orphans. Register it (or "
                "add a generator-only module to `GENERATOR_MODULE_STEMS`) and "
                "re-run."
            )
        return "\n".join(lines)

    lines.append(f"  scanned:  {result.scanned} files")
    lines.append(f"  claimed:  {len(result.claimed_by)}")
    lines.append(
        f"  unaudited:{len(result.unaudited):>4}  "
        f"({', '.join(sorted(UNAUDITED_SUBDIRS)) or 'none'})"
    )
    lines.append(f"  ORPHANS:  {len(result.orphans)}")
    lines.append("")
    if result.orphans:
        lines.append("# claimed by no producer (report only — nothing is deleted):")
        for rel in result.orphans:
            lines.append(f"  {rel}")
    else:
        lines.append("# no orphans: every audited file is claimed by a producer.")
    if verbose:
        lines.append("")
        lines.append(
            "# claimed but NOT installed here "
            f"({len(result.claimed_but_absent)}) — a partial or never-run regen, "
            "not stale files:"
        )
        for rel in result.claimed_but_absent:
            lines.append(f"  {rel}")
        lines.append("")
        lines.append(f"# unaudited ({len(result.unaudited)}):")
        for name, why in sorted(UNAUDITED_SUBDIRS.items()):
            lines.append(f"  {name}/ — {why}")
    return "\n".join(lines)


def format_json(result: AuditResult) -> str:
    return json.dumps(
        {
            "install_root": str(result.install_root),
            "refused": result.refused,
            "refusal_reason": result.refusal_reason,
            "registry_warnings": result.registry_warnings,
            "registry_error": result.registry_error,
            "scanned": result.scanned,
            "claimed": len(result.claimed_by),
            "orphans": result.orphans,
            "unaudited": result.unaudited,
            "claimed_but_absent": result.claimed_but_absent,
        },
        indent=2,
        sort_keys=True,
    )


__all__ = [
    "COMMAND_PRODUCED",
    "UNAUDITED_SUBDIRS",
    "AuditResult",
    "audit",
    "format_json",
    "format_report",
]
