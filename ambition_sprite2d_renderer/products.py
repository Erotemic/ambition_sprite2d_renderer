"""Product plans and accepted generation evidence. This owner decides freshness."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
from functools import lru_cache
from pathlib import Path

VERSION = "ambition.art_generation.v1"
TIERS = {"half": "_0_5x", "quarter": "_0_25x", "potato": "_potato"}
REVIEW = ("_canonical.png", "_canonical_transparent.png", "_preview_labeled.png", "_parts_debug.png", "_debug.png")




class Digests:
    """Hash shared inputs once. A persistent cache uses file identity and change times."""

    def __init__(self, path: Path | None = None, *, deep: bool = False):
        self.path, self.deep = path, deep
        try:
            self.cache = json.loads(path.read_text()) if path else {}
        except (OSError, ValueError):
            self.cache = {}
        self.seen = {}

    def file(self, path: Path) -> str | None:
        path = path.resolve()
        try:
            st = path.stat()
            signature = [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
            key = str(path)
            if key in self.seen:
                return self.seen[key]
            old = self.cache.get(key)
            if not self.deep and old and old[0] == signature:
                digest = old[1]
            else:
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
            self.cache[key] = [signature, digest]
            self.seen[key] = digest
            return digest
        except OSError:
            return None

    def save(self):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".partial")
            temp.write_text(json.dumps(self.cache, separators=(",", ":")))
            temp.replace(self.path)


@lru_cache(maxsize=1)
def toolchain() -> dict:
    versions = {"python": platform.python_version()}
    for name in ("Pillow", "PyYAML", "numpy", "resvg-py"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def key(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def generation(inputs: list[dict], directories: list[dict], parameters: dict, *, complete: bool) -> dict:
    value = {"version": VERSION, "inputs": inputs, "directories": directories,
             "parameters": parameters, "toolchain": toolchain()}
    return {**value, "complete": complete, "key": key(value)}




def describe(targets: dict) -> tuple[dict, list[str]]:
    """Use the same plans as sprite, background and terrain publication. Draw nothing."""
    from .provenance import asset_root

    from .content_library import read
    producers = read().get("producers", {})
    units = {}
    if "sprites" in producers:
        from .authoring.ultrapack import product_plans
        units.update(product_plans())
    warnings = [f"{uid}: {unit['source']['errors']}" for uid, unit in units.items() if (unit.get("source") or {}).get("errors")]
    if "backgrounds" not in producers:
        return units, warnings
    try:
        from .backgrounds.__main__ import plan, parts_plan
        from .terrain.__main__ import plan as terrain_plan
        root = asset_root()
        for book, prefix, kind, subdir, tiers in (
            (plan(root / "backgrounds/parallax_layers", []), "theme", "background", "backgrounds/parallax_layers", list(TIERS)),
            (parts_plan(root / "backgrounds/sky_parts"), "sky", "background", "backgrounds/sky_parts", []),
            (terrain_plan(root / "room_dressing", []), "skin", "terrain", "room_dressing", []),
        ):
            for name, products in book.units.items():
                uid = f"{prefix}:{name}"
                units[uid] = {"id": uid, "kind": kind, "root": subdir,
                    "generator": {"family": book.family, "id": name},
                    "required": [path.relative_to(book.dest).as_posix() for path, _ in products],
                    "optional": [], "metadata": {}, "source": None, "tiers": tiers,
                    "repair": book.command.format(unit=name)}
    except Exception as error:
        warnings.append(f"background or terrain discovery failed: {error}")
    return units, warnings


def evaluate(plan: dict, record: dict | None, root: Path, repo: Path, hashes: Digests,
             *, tiers: bool = True, publication: dict | None = None) -> dict:
    """Decide missing members, source changes and byte changes from one accepted receipt."""
    reasons = []
    members = set(plan["required"])
    if record:
        members.update(row["path"] for row in record.get("outputs", [])
                       if row.get("path"))
    missing = sorted(rel for rel in members if not (root / rel).is_file())
    if missing:
        reasons.append({"code": "missing", "members": missing})
    evidence = record.get("generation") if record else None
    if not evidence or not evidence.get("complete"):
        reasons.append({"code": "unknown-inputs", "message": "No complete generation receipt. Publish this bundle to record its inputs."})
    if record:
        known = evidence or record
        changed = [item["path"] for item in known.get("inputs", []) if item.get("sha256") and hashes.file(repo / item["path"]) != item["sha256"]]
        for item in known.get("directories", []):
            path = repo / item["path"]
            now = sorted(os.listdir(path)) if path.is_dir() else None
            if now != item.get("members"):
                changed.append(item["path"])
        if changed:
            reasons.append({"code": "stale-inputs", "members": changed})
        if evidence and (evidence.get("toolchain") != toolchain() or evidence.get("version") != VERSION):
            reasons.append({"code": "stale-toolchain"})
        from .provenance import read_record, provenance_root
        changed_parents = []
        for parent in known.get("parameters", {}).get("parents", []):
            accepted = read_record(provenance_root() / parent["path"], publication) or {}
            if accepted.get("generation", {}).get("key") != parent["key"] or output_key(accepted) != parent["outputs"]:
                changed_parents.append(parent["path"])
        if changed_parents:
            reasons.append({"code": "stale-parent-bundle", "members": changed_parents})
        published_parents = known.get("parameters", {}).get("published_parents", {})
        if published_parents:
            from .content_library import publication_root
            from .publication_store import Store
            selected = publication if publication is not None else Store(publication_root()).selected()
            retired = [unit for unit, key in published_parents.items() if selected["bundles"].get(unit) != key]
            if retired:
                reasons.append({"code": "stale-parent-bundle", "members": retired})
        changed_outputs = [item["path"] for item in record.get("outputs", [])
                           if item["path"] in members and item["path"] not in missing and hashes.file(root / item["path"]) != item.get("sha256")]
        if changed_outputs:
            reasons.append({"code": "changed-outputs", "members": changed_outputs})
        if set(plan["required"]) - {row["path"] for row in record.get("outputs", [])}:
            reasons.append({"code": "changed-plan"})
    full_state = ("missing" if missing and len(missing) == len(members) else "partial") if missing else (
        "stale" if any(r["code"] != "unknown-inputs" for r in reasons) else "unknown" if reasons else "current")
    tier_rows = {}
    if tiers:
        for tier in plan.get("tiers", []):
            suffix = TIERS[tier]
            from .content_library import runtime_root, quality_root
            try:
                relative = root.resolve().relative_to(runtime_root().resolve())
            except ValueError:
                tier_root = root.with_name(root.name + suffix)
            else:
                tier_root = quality_root(suffix.removeprefix("_")) / relative.parent / (root.name + suffix)
            absent = [rel for rel in plan["required"] if not rel.endswith((".yaml", ".yml")) and not (tier_root / rel).is_file()]
            components = set()
            for rel in plan["required"]:
                if rel.endswith((".yaml", ".yml")):
                    continue
                stem = Path(rel).stem
                if "_spritesheet" in stem:
                    stem = stem.split("_spritesheet")[0] + "_spritesheet"
                components.add((Path(rel).parent.as_posix(), stem))
            checks = {f"{folder}/{stem}": conversion_status(tier_root / folder, stem, hashes) for folder, stem in components}
            states = {check["state"] for check in checks.values()}
            state = "missing" if absent else "stale" if states & {"stale", "partial", "missing"} else "unknown" if "unknown" in states else "current"
            tier_rows[tier] = {"state": state, "missing": absent, "components": checks}
    return {"state": full_state, "reasons": reasons, "evidence_complete": bool(evidence and evidence.get("complete")),
            "required": sorted(members), "tiers": tier_rows, "repair": plan["repair"]}


def inventory(repo: Path, *, deep: bool = False) -> dict:
    from . import publication
    from .content_library import read, publication_root
    from .publication_store import Store
    from .provenance import provenance_root, read_record
    store = Store(publication_root())
    selected = store.selected()
    report = publication.inventory(deep=deep) if "sprites" in read().get("producers", {}) else {
        "schema": "ambition.art_products.v1", "complete": True, "warnings": [], "units": {},
        "receipts": [], "publication": selected, "store": str(store.root)}
    selected = report["publication"]
    files = {logical: store.root / member["path"] for logical, member in selected["files"].items()}
    other, warnings = describe({})
    hashes = Digests(Path(__file__).resolve().parents[1] / ".cache/art_inputs.json", deep=deep)
    for uid, unit in other.items():
        if unit["kind"] == "atlas":
            continue
        record = read_record(provenance_root() / unit["root"] / f"{unit['generator']['id']}.json", selected)
        sample = next(((rel, files[unit["root"] + "/" + rel]) for rel in unit["required"] if unit["root"] + "/" + rel in files), None)
        if sample is None:
            unit["status"] = {"state": "missing", "reasons": [{"code": "missing-publication"}], "tiers": {}, "required": unit["required"], "repair": unit["repair"]}
        else:
            rel, physical = sample
            root = physical.parents[len(Path(rel).parts) - 1]
            unit["status"] = evaluate(unit, record, root, repo, hashes, tiers=False, publication=selected)
            for tier in unit.get("tiers", []):
                logical_root = unit["root"] + TIERS[tier]
                checks = {}
                for rel in unit["required"]:
                    logical = logical_root + "/" + rel
                    path = files.get(logical)
                    if path is None:
                        checks[rel] = {"state": "missing"}
                        continue
                    receipt = read_record(provenance_root() / logical_root / (Path(rel).stem + ".quality.json"), selected)
                    checks[rel] = evaluate({"root": logical_root, "required": [path.name], "repair": unit["repair"]}, receipt, path.parent, repo, hashes, tiers=False, publication=selected)
                states = {check["state"] for check in checks.values()}
                state = "missing" if "missing" in states else "stale" if states & {"stale", "partial"} else "unknown" if "unknown" in states else "current"
                unit["status"]["tiers"][tier] = {"state": state, "components": checks, "missing": [rel for rel, status in checks.items() if status["state"] == "missing"]}
        unit["receipt"] = record
        report["units"][uid] = unit
    report["warnings"] += warnings
    report["complete"] = report["complete"] and not warnings
    hashes.save()
    return report


def main() -> int:
    import argparse
    from .provenance import repo_root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--check-sprites", action="store_true", help="check full sprite receipts for the publisher")
    args = parser.parse_args()
    report = inventory(repo_root(), deep=args.deep)
    if args.check_sprites:
        return int(not report["complete"] or any(unit["status"]["state"] != "current" for unit in report["units"].values() if unit["root"] == "sprites"))
    print(json.dumps(report, sort_keys=True))
    return 0




def output_key(record: dict) -> str:
    return key({row["path"]: row.get("sha256") for row in record.get("outputs", [])})


@lru_cache(maxsize=4)
def _parent_index(records_root: str, pixels_root: str) -> dict:
    from .provenance import read_record
    index = {}
    for path in (Path(records_root) / "sprites").glob("*.json"):
        record = read_record(path)
        if not record or record.get("generator", {}).get("family") != "sprite_target":
            continue
        parent = {"path": path.relative_to(records_root).as_posix(), "key": record.get("generation", {}).get("key"), "outputs": output_key(record)}
        for item in record.get("outputs", []):
            index[str((Path(pixels_root) / "sprites" / item["path"]).resolve())] = parent
    return index


def parents_of(inputs: list[Path]) -> list[dict]:
    from .provenance import provenance_root, asset_root
    index = _parent_index(str(provenance_root()), str(asset_root()))
    found = {row["path"]: row for path in inputs if (row := index.get(str(Path(path).resolve()))) is not None}
    return [found[path] for path in sorted(found)]


def conversion_directory(root: Path) -> Path:
    from .provenance import record_dir
    directory = record_dir(root)
    if directory is not None:
        return directory
    for tier_root in (root, *root.parents):
        if tier_root.name.startswith(("sprites_", "parallax_layers_")):
            base = tier_root.parent.parent if tier_root.parent.name == "backgrounds" else tier_root.parent
            return base.parent / (base.name + ".art_provenance") / root.relative_to(base)
    return root.parent / "asset_provenance" / root.name


def conversion_status(root: Path, stem: str, hashes: Digests) -> dict:
    from .provenance import read_record, repo_root
    record = read_record(conversion_directory(root) / f"{stem}.quality.json")
    if not record:
        return {"state": "unknown", "reasons": [{"code": "unknown-conversion"}]}
    return evaluate(record["plan"], record, root, repo_root(), hashes, tiers=False)


def conversion_evidence(inputs: list[Path], parameters: dict, *, complete=True) -> dict:
    from .provenance import _inputs
    return generation(_inputs(inputs), [], parameters, complete=complete)


def conversion_current(root: Path, stem: str, evidence: dict) -> bool:
    from .provenance import read_record
    record = read_record(conversion_directory(root) / f"{stem}.quality.json")
    return bool(record and record.get("generation", {}).get("key") == evidence["key"]
                and conversion_status(root, stem, Digests()).get("state") == "current")


def accept_conversion(root: Path, stem: str, evidence: dict, outputs: list[Path]) -> None:
    from .provenance import write_record
    if not outputs or any(not path.is_file() for path in outputs):
        raise ValueError(f"Incomplete conversion: {stem}")
    plan = {"root": root.name, "required": [p.relative_to(root).as_posix() for p in outputs],
            "repair": "./scripts/regen/quality_variants.sh", "tiers": []}
    write_record(conversion_directory(root), stem + ".quality", generator={"family": "quality_variants", "id": stem},
                 dest=root, outputs=[(p, None) for p in outputs], inputs=evidence["inputs"],
                 extra={"generation": evidence, "plan": plan})


if __name__ == "__main__":
    raise SystemExit(main())
