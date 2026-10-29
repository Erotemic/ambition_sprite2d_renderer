"""Plan, build, validate, and publish registered sprite bundles."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from . import artifacts
from .publication_store import Store, TIERS, MANAGED_ROOTS, digest, identity, write_json

RENDERER = Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return Path(os.environ.get("AMBITION_REPO_ROOT", RENDERER.parents[1]))


from .content_library import manifest_path as library_path, read as library, publication_root


def store_root() -> Path:
    return Path(os.environ.get("AMBITION_ART_STORE", publication_root()))


def policy() -> dict:
    from .yaml_io import safe_load
    path = library_path().parent / library()["producers"]["sprites"]["policy"]
    return safe_load(path.read_text())


def discover():
    from .registry import discover_all_targets
    return discover_all_targets()


def names_in(scope: str | None, requested=()) -> tuple[list[str], object]:
    scope = scope or library()["producers"]["sprites"]["collection"]
    report = discover()
    names = list(dict.fromkeys(requested)) if requested else sorted(report.targets) if scope == "all" else policy()["collections"][scope]
    missing = sorted(set(names) - report.targets.keys())
    if missing:
        raise ValueError(f"Unregistered publication targets: {', '.join(missing)}. {report.failures}")
    return names, report


def definition(target) -> dict:
    from .provenance import target_generator
    required = []
    output_root = getattr(target, "publication_root", "sprites")
    for name in artifacts.required_names(target):
        prefix = target.portrait_install_subdir if name in target.portrait_files else target.install_subdir
        required.append((Path(output_root) / (prefix or "") / name).as_posix())
    static = policy()["static_props"].get(target.name)
    if static:
        required.append(f"sprites/props/{static}.png")
    source_state = "missing" if any(not Path(path).is_file() for path in target.data_sources) else "available"
    inspection = getattr(target, "_inspection", None)
    if isinstance(inspection, dict) and inspection.get("state") == "invalid":
        source_state = "invalid"
    return {"id": "target:" + target.name, "source_state": source_state, "target": target.name, "kind": target.category,
            "generator": target_generator(target), "required": sorted(set(required)),
            "dynamic_members": any(name.endswith("_spritesheet.ron") for name in required),
            "static_prop": static, "root": output_root, "tiers": getattr(target, "publication_tiers", list(TIERS)),
            "repair": f"./scripts/regen/sprites.sh --target {target.name}"}


def plan(scope=None, requested=()) -> dict:
    scope = scope or library()["producers"]["sprites"]["collection"]
    names, report = names_in(scope, requested)
    return {"schema": "ambition.art_plan.v1", "scope": scope, "complete": not report.failures,
            "warnings": report.warnings, "failures": report.failures,
            "units": {"target:" + name: definition(report.targets[name]) for name in names},
            "exact": False, "unresolved": [name for name in names if any(p.endswith("_spritesheet.ron") for p in artifacts.required_names(report.targets[name]))]}


def source_files() -> dict[str, Path]:
    root = repo_root()
    files = {}
    for directory in (RENDERER / "ambition_sprite2d_renderer", RENDERER / "assets", RENDERER / "scripts", *[library_path().parent / path for path in library()["producers"]["sprites"].get("sources", [])]):
        for path in directory.rglob("*"):
            if path.is_file() and not any(part in ("__pycache__", ".cache", ".venv", "build", ".profiles") for part in path.parts) and path.suffix != ".pyc":
                files[path.relative_to(root).as_posix()] = path
    files[library_path().relative_to(root).as_posix()] = library_path()
    for name in ("pyproject.toml", "uv.lock"):
        path = RENDERER / name
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def toolchain() -> dict:
    fonts = {}
    for directory in (Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"):
        for path in directory.rglob("*") if directory.is_dir() else []:
            if path.is_file():
                fonts[str(path)] = digest(path)
    return {"python": platform.python_version(), "machine": platform.machine(),
            "packages": sorted([d.metadata["Name"], d.version] for d in importlib.metadata.distributions()),
            "fonts": fonts}


def recipe_state(recipe: dict | None, files: dict[str, Path], chain: dict, hashes=None) -> tuple[str, list[dict]]:
    if recipe is None:
        return "unknown", [{"code": "unknown-inputs"}]
    changed = []
    if recipe["toolchain"] != chain:
        changed.append({"code": "changed-toolchain"})
    if recipe["membership"] != identity(sorted(files)):
        changed.append({"code": "changed-source-membership"})
    for name, expected in recipe["inputs"].items():
        path = files.get(name)
        actual = hashes.file(path) if hashes is not None and path else digest(path) if path else None
        if actual != expected:
            changed.append({"code": "changed-input", "path": name})
    return ("stale", changed) if changed else ("current", [])


@contextmanager
def source_snapshot(files: dict[str, Path]):
    with tempfile.TemporaryDirectory(prefix="ambition-art-source-") as temporary:
        root = Path(temporary)
        hashes = {}
        for name, source in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            hashes[name] = digest(target)
        yield root, hashes


def _spec(target, root: Path) -> dict:
    return {"name": target.name, "kind": target.kind, "category": target.category,
            "module_path": target.module_path, "lineup_row": getattr(target, "_lineup_row", False),
            "config_path": str(root / target._config_path.relative_to(repo_root())) if target._config_path else None}


def _worker(spec: dict) -> int:
    from . import read_record
    root, work = Path(spec["root"]), Path(spec["work"])
    read_record.start(root, [work, root / "tools/ambition_sprite2d_renderer/generated"])
    target = read_record._one_target(spec["target"])
    rendered = work / "render"
    target.render_sheet(rendered)
    if target.supports_portraits:
        target.render_portraits(rendered)
    members = artifacts.collect(target, rendered)
    from PIL import Image
    from .image_io import configure_generated_image_reads
    configure_generated_image_reads()
    for path in set(members.values()):
        if path.suffix == ".png":
            with Image.open(path) as image:
                image.verify()
    output_root = spec.get("output_root", "sprites")
    files = {output_root + "/" + name: [str(path), "runtime", "full"] for name, path in members.items()}
    if spec.get("static_prop"):
        canonical = rendered / f"{target.name}_canonical_transparent.png"
        if not canonical.is_file():
            raise ValueError(f"Missing static prop product: {canonical}")
        files[f"sprites/props/{spec['static_prop']}.png"] = [str(canonical), "runtime", "full"]
    runtime_sources = {Path(row[0]).resolve() for row in files.values()}
    for path in rendered.rglob("*"):
        if path.is_file() and path.resolve() not in runtime_sources:
            files[f"review/{path.relative_to(rendered).as_posix()}"] = [str(path), "review", "full"]
    if output_root == "sprites" and any(tier != "full" for tier in spec["tiers"]):
        from .quality import (VARIANTS, SheetSource, build_sheet_variant,
            build_parts_variant, build_portrait_variant, resize_png, portrait_claims, sheet_page_claims,
            part_flipbook_claims, publish_source_quality_target)
        full = work / "assets/sprites"
        for logical, row in files.items():
            if row[1] != "runtime":
                continue
            dest = work / "assets" / logical
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(row[0], dest)
        sheets = sheet_page_claims(full)
        parts = part_flipbook_claims(full)
        portraits = portrait_claims(full)
        claimed = {page.resolve() for pages in sheets.values() for page in pages}
        claimed |= {page.resolve() for pages in parts.values() for page in pages}
        claimed |= {page.resolve() for page in portraits.values()}
        for variant in VARIANTS:
            tier = {"0_5x": "half", "0_25x": "quarter", "potato": "potato"}[variant.suffix]
            if tier not in spec["tiers"]:
                continue
            dest = work / "assets" / TIERS[tier]
            if target.kind == "config":
                publish_source_quality_target(target, variant, dest)
            else:
                for ron in sheets:
                    sheet = SheetSource.load(ron)
                    try:
                        build_sheet_variant(sheet, dest / ron.relative_to(full), variant)
                    finally:
                        sheet.close()
            for ron in parts:
                build_parts_variant(ron, dest / ron.relative_to(full), variant)
            for ron, png in portraits.items():
                build_portrait_variant(ron, png, dest / ron.relative_to(full), variant)
            for png in full.rglob("*.png"):
                if png.resolve() not in claimed:
                    resize_png(png, dest / png.relative_to(full), variant.nominal_scale, min_px=variant.min_frame_px)
            for metadata in set(sheets) | set(parts) | set(portraits):
                if not (dest / metadata.relative_to(full)).is_file():
                    raise ValueError(f"Missing quality metadata: {tier}: {metadata.name}")
            for path in dest.rglob("*"):
                if path.is_file():
                    for page in artifacts.references(path):
                        if not (path.parent / page).is_file():
                            raise ValueError(f"Missing quality page: {path}: {page}")
                    logical = f"{TIERS[tier]}/{path.relative_to(dest).as_posix()}"
                    files[logical] = [str(path), "runtime", tier]
    reads = read_record.recorded() or []
    write_json(work / "result.json", {"files": files, "reads": [Path(p).relative_to(root).as_posix() for p in reads]})
    return 0


def validate_metadata(files: dict) -> None:
    roots = sorted({str(Path(row[0]).parent) for logical, row in files.items()
                    if row[1] == "runtime" and logical.endswith("_spritesheet.ron")})
    if not roots:
        return
    binary = Path(os.environ.get("AMBITION_ART_CONTENT_BIN", repo_root() / "target/debug/ambition_content"))
    if not binary.is_file():
        raise ValueError("Build the metadata validator first: cargo build -p ambition_content_cli --bin ambition_content")
    command = [str(binary), "--inspect-art"]
    for root in roots:
        command += ["--sheet-root", root]
    done = subprocess.run(command, capture_output=True, text=True)
    if done.returncode:
        raise ValueError(f"Metadata validation failed: {done.stderr[-2000:]}")
    report = json.loads(done.stdout)
    if report.get("failures"):
        raise ValueError(f"Invalid sheet metadata: {report['failures']}")
    for path, records in report.get("sheets", {}).items():
        for record in records:
            if any(not row["valid"] for row in record["rows"]) or any(not page["exists"] for page in record["pages"]):
                raise ValueError(f"Invalid sheet rows or pages: {path}")


def pack_parents(report) -> dict[str, str]:
    from .yaml_io import safe_load
    value = safe_load((RENDERER / "ambition_sprite2d_renderer/data/pack_plan.yaml").read_text())
    stems = {stem for group in value["runtime_groups"] for stem in value["groups"][group]}
    paths = {f"sprites/{stem}_spritesheet.yaml" for stem in stems}
    owners = {}
    for name, target in report.targets.items():
        for logical in definition(target)["required"]:
            if logical in paths:
                owners[logical] = "target:" + name
    if paths - owners.keys():
        raise ValueError(f"Atlas inputs have no producer: {sorted(paths - owners.keys())}")
    return owners


def build_packs(store: Store, bundles: dict, report, sources: dict, chain: dict, *, force=False) -> dict:
    owners = pack_parents(report)
    parents = {unit: bundles[unit] for unit in set(owners.values()) if unit in bundles}
    if not parents:
        return {}
    if set(parents) != set(owners.values()):
        raise ValueError(f"Missing atlas dependencies: {sorted(set(owners.values()) - parents.keys())}")
    inputs = {name: digest(path) for name, path in sources.items() if name.endswith(("/authoring/ultrapack.py", "/authoring/packer.py", "/data/pack_plan.yaml", "/publication.py", "/publication_store.py"))}
    recipe = {"inputs": inputs, "membership": identity(sorted(sources)), "toolchain": chain, "quality": True}
    required = [tier for tier in TIERS if force or "atlas:"+tier not in bundles
                or store.bundle(bundles["atlas:"+tier])["parents"] != parents
                or recipe_state(store.bundle(bundles["atlas:"+tier])["recipe"], sources, chain)[0] != "current"
                or store.integrity(bundles["atlas:"+tier])]
    result = {"atlas:"+tier: bundles["atlas:"+tier] for tier in TIERS if tier not in required}
    if not required:
        return result
    with source_snapshot(sources) as (snapshot, _original), tempfile.TemporaryDirectory(prefix="ambition-art-pack-") as temporary:
        work = Path(temporary)
        recipe["inputs"] = {name: _original[name] for name in recipe["inputs"]}
        for unit, key in parents.items():
            for logical, member in store.bundle(key)["files"].items():
                if logical.startswith("sprites/"):
                    dest = work / logical
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(store.root / "bundles" / key / member["path"], dest)
        renderer = snapshot / RENDERER.relative_to(repo_root())
        settings = {"full": (1,1,2048), "half": (.5,1,1024), "quarter": (.25,1,512), "potato": (.0625,8,256)}
        for tier in required:
            scale, minimum, page_size = settings[tier]
            out = work / "packs" / tier
            command = [sys.executable, "-m", "ambition_sprite2d_renderer.authoring.ultrapack", "--from-rendered", str(work / "sprites"),
                "--out", str(out), "--state", str(work / (tier+".state.json")), "--runtime-only", "--scale", str(scale),
                "--min-frame-px", str(minimum), "--page-size", str(page_size), "--pack-plan", "ambition_sprite2d_renderer/data/pack_plan.yaml", "--jobs", "1"]
            done = subprocess.run(command, cwd=renderer, capture_output=True, text=True,
                                  env=dict(os.environ, PYTHONPATH=str(renderer), AMBITION_REPO_ROOT=str(snapshot),
                                           AMBITION_CONTENT_LIBRARY=library_path().relative_to(repo_root()).as_posix()))
            if done.returncode:
                raise ValueError(f"Atlas {tier}: {done.stderr[-3000:]}")
            catalog = out / "ultrapack.json"
            files = {f"sprite_packs/{tier}/{path.name}": (path, "runtime", tier)
                     for path in [catalog] + [out / page for page in json.loads(catalog.read_text())["pages"]]}
            result["atlas:"+tier] = store.accept("atlas:"+tier, files, recipe, parents=parents)
            print(f"art: atlas {tier}", file=sys.stderr, flush=True)
    return result


def build(scope=None, requested=(), *, force=False, jobs=1, publish=True) -> dict:
    names, report = names_in(scope, requested)
    if report.failures:
        raise ValueError(f"Target discovery failed: {report.failures}")
    store = Store(store_root())
    selected = store.selected()
    atlas_owners = set(pack_parents(report).values())
    if any("target:"+name in atlas_owners for name in names):
        names = list(dict.fromkeys(names + [unit.removeprefix("target:") for unit in atlas_owners if unit not in selected["bundles"]]))
    sources, chain = source_files(), toolchain()
    from .products import Digests
    hashes = Digests(RENDERER / ".cache/publication-inputs.json")
    accepted = {}
    directory = store.root / "bundles"
    for path in sorted(directory.iterdir()) if directory.is_dir() else ():
        if path.name.startswith("."):
            continue
        try:
            manifest = store.bundle(path.name)
            if manifest["recipe"] is not None:
                accepted.setdefault(manifest["unit"], []).append((path.name, manifest))
        except (ValueError, OSError):
            continue
    replacements = {}
    pending = []
    for name in names:
        unit = "target:" + name
        candidates = accepted.get(unit, [])
        candidates.sort(key=lambda row: row[0] != selected["bundles"].get(unit))
        reusable = next((key for key, manifest in candidates if not force
            and manifest["recipe"].get("quality") is True
            and recipe_state(manifest["recipe"], sources, chain, hashes)[0] == "current"
            and not store.integrity(key, hashes=hashes)), None)
        if reusable:
            replacements[unit] = reusable
        else:
            pending.append(name)
    hashes.save()
    sizes = {unit: sum(member["bytes"] for member in store.bundle(key)["files"].values())
             for unit, key in selected["bundles"].items()}
    pending.sort(key=lambda name: -sizes.get("target:" + name, 0))
    print(f"art: {len(names)} targets, {len(pending)} builds, {len(replacements)} current", file=sys.stderr, flush=True)
    if pending:
        with source_snapshot(sources) as (snapshot, original):
            snapshot_renderer = snapshot / RENDERER.relative_to(repo_root())
            def render(name):
                target = report.targets[name]
                with tempfile.TemporaryDirectory(prefix="ambition-art-build-") as temporary:
                    work = Path(temporary)
                    spec = {"target": _spec(target, snapshot), "root": str(snapshot), "work": str(work),
                            "static_prop": policy()["static_props"].get(name), "tiers": getattr(target, "publication_tiers", list(TIERS)),
                            "output_root": getattr(target, "publication_root", "sprites")}
                    command = [sys.executable, "-m", "ambition_sprite2d_renderer.publication", "--worker", json.dumps(spec)]
                    profile = os.environ.get("AMBITION_ART_PROFILE_DIR")
                    if profile:
                        Path(profile).mkdir(parents=True, exist_ok=True)
                        command = [sys.executable, "-m", "kernprof", "-l", "-o", str(Path(profile) / (name + ".lprof")),
                                   "-m", "ambition_sprite2d_renderer.publication", "--worker", json.dumps(spec)]
                    done = subprocess.run(command,
                        cwd=snapshot_renderer, env=dict(os.environ, PYTHONPATH=str(snapshot_renderer), AMBITION_REPO_ROOT=str(snapshot)),
                        capture_output=True, text=True)
                    if done.returncode:
                        raise ValueError(f"{name}: {done.stderr[-4000:]}\n{done.stdout[-1000:]}")
                    result = json.loads((work / "result.json").read_text())
                    validate_metadata(result["files"])
                    inputs = {path: original[path] for path in result["reads"] if path in original}
                    # The recipe owner and collection policy affect every build.
                    for path, sha in original.items():
                        if path.endswith(("/publication.py", "/artifacts.py", "/publication_store.py", "/sprites.yaml", "/library.json", "/quality.py")):
                            inputs[path] = sha
                    recipe = {"inputs": inputs, "membership": identity(sorted(original)), "toolchain": chain, "quality": True, "tiers": getattr(target, "publication_tiers", list(TIERS))}
                    key = store.accept("target:" + name, {k: (Path(v[0]), v[1], v[2]) for k,v in result["files"].items()}, recipe)
                    return name, key
            failures = []
            with ThreadPoolExecutor(max_workers=min(6, max(1, jobs))) as pool:
                futures = {pool.submit(render, name): name for name in pending}
                try:
                    for index, future in enumerate(as_completed(futures), 1):
                        try:
                            name, key = future.result()
                            replacements["target:" + name] = key
                            print(f"art: [{index}/{len(pending)}] {name}", file=sys.stderr, flush=True)
                        except (ValueError, OSError) as error:
                            failures.append(str(error))
                            print(f"art: [{index}/{len(pending)}] FAILED {futures[future]}: {error}", file=sys.stderr, flush=True)
                except BaseException:
                    for future in futures:
                        future.cancel()
                    raise
            if failures:
                raise ValueError(f"{len(failures)} target builds failed. The published selection was kept.\n" + "\n".join(failures))
            now = source_files()
            used = {name: sha for key in replacements.values() for name, sha in (store.bundle(key)["recipe"] or {}).get("inputs", {}).items()}
            if identity(sorted(now)) != identity(sorted(original)) or any(name not in now or digest(now[name]) != expected for name, expected in used.items()):
                raise ValueError("Authored sources changed during generation. The published selection was kept.")
            if toolchain() != chain:
                raise ValueError("The rendering toolchain changed during generation.")
    candidate = selected["bundles"] | replacements
    replacements.update(build_packs(store, candidate, report, sources, chain, force=force))
    used = {name: sha for key in replacements.values() for name, sha in (store.bundle(key)["recipe"] or {}).get("inputs", {}).items()}
    latest = source_files()
    if set(latest) != set(sources) or any(name not in latest or digest(latest[name]) != sha for name, sha in used.items()):
        raise ValueError("Authored sources changed before publication. The previous selection was kept.")
    if toolchain() != chain:
        raise ValueError("The rendering toolchain changed before publication.")
    if not publish:
        return {"exact": True, "bundles": replacements,
                "files": sorted({logical for key in replacements.values() for logical in store.bundle(key)["files"]})}
    return store.publish(replacements, selected["generation"], replace=not requested)


def inventory(*, deep=False, requested=None) -> dict:
    from .products import Digests
    report = discover()
    sources, chain = source_files(), toolchain()
    hashes = Digests(RENDERER / ".cache/publication-inputs.json", deep=deep)
    store = Store(store_root())
    selected = store.selected()
    units = {}
    for name, target in report.targets.items():
        if requested is not None and name not in requested:
            continue
        unit = definition(target)
        key = selected["bundles"].get(unit["id"])
        manifest = store.bundle(key) if key else None
        state, reasons = recipe_state(manifest["recipe"] if manifest else None, sources, chain, hashes)
        defects = store.integrity(key, hashes=hashes) if key else [{"code": "missing-bundle"}]
        if defects:
            state = "missing" if not manifest else "partial" if any(r["code"] == "missing" for r in defects) else "stale"
        output_root = unit["root"]
        unit["kind"] = {"characters": "actor", "props": "prop", "tiles": "tile", "icons": "icon", "projectiles": "projectile"}.get(target.category, target.category)
        unit["required"] = [p.removeprefix(output_root + "/") for p in unit["required"]]
        unit["optional"] = []
        unit["metadata"] = {}
        unit["source"] = None
        try:
            unit["metadata"] = dict(target._actor_metadata)
            source = target._inspection
            unit["source"] = source() if callable(source) else source
        except Exception as error:
            unit["source"] = {"state": "unavailable", "errors": [str(error)]}
        unit["receipt"] = None
        unit["bundle"] = key
        unit["publication"] = {"selected": bool(key), "files": manifest["files"] if manifest else {}}
        if manifest:
            unit["required"] = [p.removeprefix(output_root + "/") for p,v in manifest["files"].items() if p.startswith(output_root + "/") and v["role"] == "runtime"]
        unit["status"] = {"state": state, "reasons": reasons + defects, "evidence_complete": bool(manifest and manifest["recipe"]),
                          "required": unit["required"], "tiers": {}, "repair": unit["repair"]}
        for tier in (t for t in unit["tiers"] if t != "full"):
            members = [p for p in (manifest or {}).get("files", {}) if p.startswith(TIERS[tier] + "/")]
            unit["status"]["tiers"][tier] = {"state": state if members else "missing", "missing": [], "components": {}}
        units[unit["id"]] = unit
    for tier in TIERS:
        uid = "atlas:"+tier
        key = selected["bundles"].get(uid)
        manifest = store.bundle(key) if key else None
        state, reasons = recipe_state(manifest["recipe"] if manifest else None, sources, chain, hashes)
        defects = store.integrity(key, hashes=hashes) if key else [{"code": "missing-bundle"}]
        if defects:
            state = "missing" if not key else "stale"
        units[uid] = {"id":uid,"kind":"atlas","root":"sprite_packs/"+tier,"generator":{"id":"ultrapack","family":"ultrapack"},
            "required":[Path(p).name for p in (manifest or {}).get("files",{})],"optional":[],"metadata":{},"source":None,"tiers":[],
            "repair":"./scripts/regen/sprites.sh","bundle":key,"publication":{"files":manifest["files"] if manifest else {}},
            "status":{"state":state,"reasons":reasons+defects,"evidence_complete":bool(manifest and manifest["recipe"]),"tiers":{},"repair":"./scripts/regen/sprites.sh"}}
    hashes.save()
    return {"schema": "ambition.art_products.v1", "complete": not report.failures, "warnings": list(report.warnings),
            "units": units, "receipts": [], "publication": selected, "store": str(store.root)}


def audit(asset_root: Path | None = None) -> dict:
    store = Store(store_root())
    selected = store.selected()
    asset_root = asset_root or repo_root() / "game/ambition_content_library/generated/runtime"
    unmanaged = []
    for root in selected.get("roots", MANAGED_ROOTS):
        for path in (asset_root / root).rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                logical = path.relative_to(asset_root).as_posix()
                current = selected["files"].get(logical)
                unmanaged.append({"path": str(path), "logical_path": logical,
                                  "published_owner": current.get("unit") if current else None,
                                  "matches_published_bytes": digest(path) == current["sha256"] if current else None})
    active = set(selected["bundles"].values())
    historical = [path.name for path in (store.root / "bundles").iterdir()
                  if path.is_dir() and not path.name.startswith(".") and path.name not in active] if (store.root / "bundles").is_dir() else []
    registered = {"target:" + name for name in discover().targets} | {"atlas:" + tier for tier in TIERS}
    return {"schema":"ambition.art_audit.v1", "generation":selected["generation"],
            "unmanaged_files":unmanaged, "historical_bundles":sorted(historical),
            "unregistered_units": sorted(set(selected["bundles"]) - registered)}


def adopt_existing(asset_root: Path, *, scope="runtime") -> dict:
    """Import existing bytes with unknown recipe evidence. Rendered evidence is not inferred."""
    names, report = names_in(scope)
    store = Store(store_root())
    selected = store.selected()
    replacements = {}
    for name in names:
        target = report.targets[name]
        uid = "target:" + name
        previous = selected["bundles"].get(uid)
        if previous and store.bundle(previous)["recipe"] is not None:
            replacements[uid] = previous
            continue
        found = {}
        declared = definition(target)
        for logical in declared["required"]:
            path = asset_root / logical
            if path.is_file():
                found[logical] = (path, "runtime", "full")
                for page in artifacts.references(path):
                    source = path.parent / page
                    if source.is_file():
                        found[(Path(logical).parent / page).as_posix()] = (source, "runtime", "full")
        for logical in list(found):
            if logical.endswith("_spritesheet.ron"):
                stem = logical.removesuffix("_spritesheet.ron")
                for suffix in ("_parts.ron", "_actor.ron", "_body_rig.ron"):
                    path = asset_root / (stem + suffix)
                    if path.is_file():
                        found[stem + suffix] = (path, "runtime", "full")
                        for page in artifacts.references(path):
                            found[(Path(stem).parent / page).as_posix()] = (path.parent / page, "runtime", "full")
        for tier in ("half", "quarter", "potato"):
            for logical in list(found):
                if not logical.startswith("sprites/"):
                    continue
                other = TIERS[tier] + logical[len("sprites"):]
                path = asset_root / other
                if path.is_file():
                    found[other] = (path, "runtime", tier)
                    for page in artifacts.references(path):
                        found[(Path(other).parent / page).as_posix()] = (path.parent / page, "runtime", tier)
        if found:
            replacements["target:" + name] = store.accept("target:" + name, found, None)
    owners = pack_parents(report)
    parents = {unit: replacements[unit] for unit in set(owners.values()) if unit in replacements}
    for tier in TIERS:
        catalog = asset_root / "sprite_packs" / tier / "ultrapack.json"
        if catalog.is_file():
            files = {f"sprite_packs/{tier}/{path.name}":(path,"runtime",tier) for path in [catalog]+[catalog.parent/page for page in json.loads(catalog.read_text())["pages"]]}
            replacements["atlas:"+tier] = store.accept("atlas:"+tier,files,None,parents=parents)
    return store.publish(replacements, selected["generation"], replace=True)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--worker")
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--scope", help="declared collection, or all registered targets")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--list-outputs", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--resolve-layout", action="store_true")
    parser.add_argument("--adopt-existing", type=Path)
    parser.add_argument("--jobs", type=int, default=min(6, max(1, (os.cpu_count() or 2)//2)))
    args = parser.parse_args(argv)
    if args.library:
        os.environ["AMBITION_CONTENT_LIBRARY"] = (repo_root() / args.library).resolve().relative_to(repo_root()).as_posix()
    if args.worker:
        return _worker(json.loads(args.worker))
    try:
        if args.audit:
            result = audit()
        elif args.adopt_existing:
            result = adopt_existing(args.adopt_existing, scope=args.scope)
        elif args.check:
            names, _ = names_in(args.scope, args.target)
            result = inventory(deep=args.deep, requested=set(names))
            if not args.json:
                for uid, unit in result["units"].items():
                    print(f"{uid}: {unit['status']['state']}")
                return int(not result["complete"] or any(u["status"]["state"] != "current" for u in result["units"].values()))
        elif args.plan or args.list or args.list_outputs:
            result = plan(args.scope, args.target)
            if args.list:
                print("\n".join(u["target"] for u in result["units"].values()))
                return int(not result["complete"])
            if args.list_outputs:
                print("\n".join(sorted({p.removeprefix("sprites/") for u in result["units"].values() for p in u["required"]})))
                return int(not result["complete"])
        else:
            result = build(args.scope, args.target, force=args.force, jobs=args.jobs,
                           publish=not args.resolve_layout)
        if not args.json and not any((args.audit, args.adopt_existing, args.check, args.plan, args.resolve_layout)):
            print(f"Published {result['generation']}: {len(result['bundles'])} bundles, {len(result['files'])} runtime files.")
        else:
            print(json.dumps(result, sort_keys=True, indent=1))
        return int(args.check and (not result["complete"] or any(unit["status"]["state"] != "current" for unit in result["units"].values())))
    except (ValueError, OSError) as error:
        print(f"art publication: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
