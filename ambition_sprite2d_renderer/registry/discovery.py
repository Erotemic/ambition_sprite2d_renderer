"""Unified discovery for every sprite target.

One concept — [`Target`] — covers every renderable thing in the package. A
Target is built one of two ways (see :meth:`Target.from_module` /
:meth:`Target.from_config`), and consumers treat them identically:

- **Module-authored** targets: a Python module under ``targets/<category>/``
  (a single ``.py`` file or a package directory) that exposes a module-level
  ``render(out_dir, **opts)`` function. Character modules may additionally
  expose ``render_portraits(out_dir, **opts)`` for an independent native
  portrait product.
- **Config-authored** targets: a YAML config in ``configs/*.yaml`` (or
  ``configs/review/*.yaml``) that drives one of the ``CharacterGenerator``s
  registered in ``registry/character_generators.py``. Character generators
  receive a default native portrait implementation that families may override.

The registry unifies discovery and published outputs, not drawing or posing
internals. Consumers (CLI, gallery, publish) iterate the returned dict without
caring which authoring family produced a target.
"""

from __future__ import annotations

import importlib
import copy
import shutil
import sys
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from ..authoring.actor_profiles import merge_actor_metadata
from ..profiling import profile

CATEGORIES: Tuple[str, ...] = (
    # Tack-on categories — Python authoring under `targets/<category>/`.
    "characters",
    "props",
    "tiles",
    "icons",
    "projectiles",
)
# Note: there used to be a separate `review_npcs` category for YAML-
# config-driven characters that lived in `configs/review/*.yaml`. As
# of the Phase 6 character-catalog cleanup (2026-05-24) those targets
# merge into `characters` — the split was an internal authoring
# detail that didn't map to runtime behavior (many "review NPCs"
# ship to the runtime via the same sprite registry as everyone else).
# The `configs/review/` directory still exists for backwards-
# compat authoring, but its contents now register under `characters`.

# Modules under `targets/characters/` that define a `CharacterGenerator` (or a
# helper for one) and are driven by YAML configs through `registry/character_generators.py`
# rather than a top-level `render()` function. Discovery silently skips these so
# they don't show up as "doesn't conform to the Target API" warnings under
# `list-targets`. (`sandbag` is deliberately absent: it exposes both a generator
# AND a tackon `render()`, so it is discovered as a normal target.)
GENERATOR_MODULE_STEMS: frozenset[str] = frozenset(
    {
        "alice_cryptographer",
        "bob_engineer",
        "boss_side",
        "goblin_side",
        "ninja_side",
        "oiler_mechanic",
        "robot25d",
        "robot_side",
        "toon_side",
        "trent_elder",
    }
)


# ---- Shared install helpers --------------------------------------------------


def _copy_sheet_files(
    sheet_files: "Sequence[str]",
    render_dir: Path,
    dest_root: Path,
) -> List[Path]:
    """Copy every listed sheet file plus optional generated sidecars.

    Runtime-compatible sheets have long shipped ``*_spritesheet.ron`` next to
    their YAML manifests. The renderer now also emits optional
    ``*_actor.ron`` contracts; copy them opportunistically so old targets and
    old manifests keep working while new metadata can ride along.
    """
    copied: List[Path] = []
    copied_names: set[str] = set()
    listed = set(sheet_files)

    def copy_if_exists(fname: str) -> None:
        if fname in copied_names:
            return
        src = render_dir / fname
        if not src.exists():
            return
        dst = dest_root / fname
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)
        copied_names.add(fname)

    def companions_for(fname: str) -> List[str]:
        out: List[str] = []
        if fname.endswith(".yaml"):
            out.append(fname[:-5] + ".ron")
        stem = None
        for suffix in ("_spritesheet.yaml", "_spritesheet.ron", "_spritesheet.png"):
            if fname.endswith(suffix):
                stem = fname[: -len(suffix)]
                break
        if stem:
            out.append(f"{stem}_actor.ron")
        return out

    def page_siblings_for(fname: str) -> List[str]:
        """Extra page PNGs for a split sheet: `<stem>_spritesheet.1.png`,
        `.2.png`, … emitted next to `<stem>_spritesheet.png` when the sheet was
        too tall for one texture. Empty for the common single-page case."""
        suffix = "_spritesheet.png"
        if not fname.endswith(suffix):
            return []
        stem = fname[: -len(suffix)]
        out: List[str] = []
        for src in render_dir.glob(f"{stem}_spritesheet.*.png"):
            middle = src.name[len(stem) + len("_spritesheet.") : -len(".png")]
            if middle.isdigit():
                out.append(src.name)
        return sorted(out)

    for fname in sheet_files:
        copy_if_exists(fname)
        for companion in companions_for(fname):
            if companion not in listed:
                copy_if_exists(companion)
        for page in page_siblings_for(fname):
            copy_if_exists(page)
    return copied


# ---- Target ------------------------------------------------------------------
# The unified `Target` class is defined below; there is one concrete target type
# with two constructors (module-authored / config-authored).


# ---- Optional actor-contract sidecar hook -----------------------------------


def _ensure_actor_sidecars(
    *,
    target_name: str,
    render_dir: Path,
    paths: Sequence[Path],
    actor_metadata: Mapping[str, Any] | None = None,
) -> List[Path]:
    """Ensure every rendered ``*_spritesheet.yaml`` has ``*_actor.ron``.

    Most modern targets already emit the sidecar from ``sheet_build``. This
    post-render hook covers older/custom tack-ons and lets module-level
    ``ACTOR_METADATA`` enrich the inferred contract without forcing every
    bespoke renderer through the generic sheet builder immediately. It also
    handles multi-file boss targets that emit ``*_spritesheet_manifest.json``
    instead of the standard YAML/RON sheet manifest.
    """
    from ..authoring.actor_contract import write_actor_contract_for_tackon
    import json
    from ..yaml_io import safe_load

    extras: List[Path] = []
    declared_paths = {Path(path) for path in paths}

    def maybe_emit(
        *,
        manifest_path: Path,
        manifest: Mapping[str, Any],
        image_name: str,
        sheet_manifest_name: str,
    ) -> None:
        actor_path = manifest_path.with_name(f"{target_name}_actor.ron")
        if actor_path.exists() and not actor_metadata:
            return
        write_actor_contract_for_tackon(
            target=target_name,
            image_out=manifest_path.with_name(image_name),
            sheet_ron_out=manifest_path.with_name(sheet_manifest_name),
            manifest=manifest,
            actor_metadata=actor_metadata or {},
        )
        if actor_path.exists() and actor_path not in extras:
            extras.append(actor_path)

    for path in list(paths):
        path = Path(path)
        if path.suffix == ".yaml" and path.name.endswith("_spritesheet.yaml"):
            # Generic sheet builders already emitted and returned this sidecar.
            # Do not parse the just-written YAML and regenerate identical RON.
            declared_actor = path.with_name(
                path.name.replace("_spritesheet.yaml", "_actor.ron")
            )
            if declared_actor in declared_paths and declared_actor.exists():
                continue
            try:
                manifest = safe_load(path.read_text(encoding="utf8")) or {}
            except Exception:
                continue
            if not isinstance(manifest, dict):
                continue
            image_name = str(
                manifest.get("image") or path.name.replace(".yaml", ".png")
            )
            maybe_emit(
                manifest_path=path,
                manifest=manifest,
                image_name=image_name,
                sheet_manifest_name=path.with_suffix(".ron").name,
            )
        elif path.suffix == ".json" and path.name.endswith(
            "_spritesheet_manifest.json"
        ):
            try:
                manifest = json.loads(path.read_text(encoding="utf8")) or {}
            except Exception:
                continue
            if not isinstance(manifest, dict):
                continue
            image_name = str(manifest.get("image") or f"{target_name}_spritesheet.png")
            maybe_emit(
                manifest_path=path,
                manifest=manifest,
                image_name=image_name,
                sheet_manifest_name=path.name,
            )
    return extras


# ---- Target ------------------------------------------------------------------


class Target:
    """One renderable sprite target.

    Two authoring paths construct a Target, and consumers (CLI, gallery, install)
    treat them identically — neither knows nor cares which path a target came
    from:

    * :meth:`from_module` — a Python module under ``targets/<category>/`` that
      exposes a ``render(out_dir, **opts)`` function (and optionally
      ``render_canonical`` / ``render_portraits`` / ``install`` /
      ``ACTOR_METADATA``). The module may use any authoring family internally.
    * :meth:`from_config` — a YAML config in ``configs/`` that drives a
      :class:`~ambition_sprite2d_renderer.authoring.generator.CharacterGenerator`.
      The generator may be procedural, rigged, part-based, or hybrid.

    ``kind`` (``"module"`` / ``"config"``) records which path built it, for the
    rare consumer that needs to know (e.g. listing only module-authored props).
    """

    def __init__(
        self,
        *,
        name: str,
        category: str,
        sheet_files: Tuple[str, ...],
        portrait_files: Tuple[str, ...] = (),
        portrait_install_subdir: str | None = None,
        kind: str,
    ) -> None:
        self.name = name
        self.category = category
        self.sheet_files = sheet_files
        self.portrait_files = portrait_files
        self.portrait_install_subdir = portrait_install_subdir
        self.kind = kind
        # Module-authored fields.
        self.module_path: Optional[str] = None
        self._render_fn: Optional[Callable] = None
        self._render_canonical_fn: Optional[Callable] = None
        self._render_portraits_fn: Optional[Callable] = None
        self._install_fn: Optional[Callable] = None
        self._actor_metadata: Dict[str, Any] = {}
        # Config-authored fields.
        self._config_path: Optional[Path] = None
        self._job: Any = None

    # -- constructors -----------------------------------------------------

    @classmethod
    def from_module(
        cls,
        *,
        name: str,
        category: str,
        module_path: str,
        render: Callable,
        sheet_files: Tuple[str, ...],
        install: Optional[Callable] = None,
        render_canonical: Optional[Callable] = None,
        render_portraits: Optional[Callable] = None,
        portrait_files: Tuple[str, ...] = (),
        portrait_install_subdir: str | None = None,
        actor_metadata: Mapping[str, Any] | None = None,
    ) -> "Target":
        self = cls(
            name=name,
            category=category,
            sheet_files=sheet_files,
            portrait_files=portrait_files,
            portrait_install_subdir=portrait_install_subdir,
            kind="module",
        )
        self.module_path = module_path
        self._render_fn = render
        self._install_fn = install
        self._render_canonical_fn = render_canonical
        self._render_portraits_fn = render_portraits
        self._actor_metadata = dict(actor_metadata or {})
        return self

    @classmethod
    def from_config(cls, *, config_path: Path, category: str) -> "Target":
        # Local import — the generator pipeline pulls in Pillow; keep
        # registry/discovery.py importable without it by deferring.
        from .config import CharacterJob

        config_path = Path(config_path)
        job = CharacterJob.load(config_path)
        name = job.output_stem(config_path)
        self = cls(
            name=name,
            category=category,
            kind="config",
            sheet_files=(
                f"{name}_spritesheet.png",
                f"{name}_spritesheet.yaml",
                f"{name}_spritesheet.ron",
                f"{name}_actor.ron",
            ),
            portrait_files=(
                f"{name}_portraits.png",
                f"{name}_portraits.ron",
            ),
        )
        self._config_path = config_path
        self._job = job
        return self

    # -- render / install (dispatch by authoring kind) --------------------

    @profile
    def render_sheet(self, out_dir: Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.kind == "module":
            return self._render_sheet_module(out_dir, **opts)
        return self._render_sheet_config(out_dir, **opts)

    @profile
    def render_canonical(self, out_dir: Path, **opts) -> Path:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.kind == "module":
            return self._render_canonical_module(out_dir, **opts)
        return self._render_canonical_config(out_dir, **opts)

    @property
    def supports_portraits(self) -> bool:
        """Whether this target publishes the standard portrait product.

        Every registered character has a default portrait path. Authoring
        families may provide a native ``render_portraits`` hook; otherwise a
        module target receives the conservative freshly-rendered canonical
        fallback. Non-character targets do not acquire portrait products.
        """
        return self.category == "characters" or self._render_portraits_fn is not None

    @profile
    def render_portraits(self, out_dir: Path, **opts) -> List[Path]:
        """Render the target's independent portrait-sheet product.

        Portrait support is a publishing capability, not an authoring-style
        requirement. Config generators receive the scalable default. Module
        targets may override it with a native hook; otherwise the target's
        authoring code is invoked afresh for a canonical render and the common
        compositor derives a conservative default portrait from that source.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if not self.supports_portraits:
            return []
        if self.kind == "module":
            if self._render_portraits_fn is not None:
                return list(self._render_portraits_fn(out_dir, **opts))
            from tempfile import TemporaryDirectory

            from ..authoring.portrait import write_default_portrait_from_canonical

            # Use a clean staging directory so the portrait path must invoke
            # the authoring code again. It cannot accidentally reuse a
            # canonical or gameplay raster left by render_sheet().
            with TemporaryDirectory(prefix=f"{self.name}-portrait-") as temp_dir:
                from ..authoring.sheet_build import canonical_render_only

                with canonical_render_only():
                    canonical = self._render_canonical_module(Path(temp_dir), **opts)
                return write_default_portrait_from_canonical(
                    self.name,
                    canonical,
                    out_dir,
                    actor_metadata=self._actor_metadata,
                )
        return self._render_portraits_config(out_dir, **opts)

    @profile
    def install(self, render_dir: Path, dest_root: Path) -> List[Path]:
        """Install every declared gameplay and portrait product.

        Module targets may override gameplay installation with a module-level
        ``install`` (for example, a multipart boss that ships a subdirectory).
        Declared portrait files are still copied by the common target contract.
        """
        render_dir = Path(render_dir)
        dest_root = Path(dest_root)
        dest_root.mkdir(parents=True, exist_ok=True)
        portrait_dest = (
            dest_root / self.portrait_install_subdir
            if self.portrait_install_subdir
            else dest_root
        )
        if self._install_fn is not None:
            copied = list(self._install_fn(render_dir, dest_root))
            copied.extend(
                _copy_sheet_files(self.portrait_files, render_dir, portrait_dest)
            )
            return copied
        copied = _copy_sheet_files(self.sheet_files, render_dir, dest_root)
        copied.extend(_copy_sheet_files(self.portrait_files, render_dir, portrait_dest))
        return copied

    # -- module-authored strategy -----------------------------------------

    @profile
    def _render_sheet_module(self, out_dir: Path, **opts) -> List[Path]:
        paths = list(self._render_fn(out_dir, **opts))
        paths.extend(
            _ensure_actor_sidecars(
                target_name=self.name,
                render_dir=out_dir,
                paths=paths,
                actor_metadata=self._actor_metadata,
            )
        )
        return paths

    @profile
    def _render_canonical_module(self, out_dir: Path, **opts) -> Path:
        # Reuse a canonical emitted earlier in the same publish invocation.
        # This is authored source output, not a gameplay-sheet crop.
        candidates = (
            out_dir / f"{self.name}_canonical_transparent.png",
            out_dir / f"{self.name}_canonical.png",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Fast path: a target-provided canonical hook. Otherwise run the full
        # target authoring path and locate its canonical output.
        if self._render_canonical_fn is not None:
            return Path(self._render_canonical_fn(out_dir, **opts))
        self._render_fn(out_dir, **opts)
        for candidate in candidates:
            if candidate.exists():
                return candidate
        expected = " or ".join(candidate.name for candidate in candidates)
        raise FileNotFoundError(
            f"{self.category}/{self.name}: full render completed but {expected} "
            "is missing — add a `render_canonical` or `render_portraits` hook "
            "for this authoring family."
        )

    # -- config-authored strategy -----------------------------------------

    @profile
    def _render_sheet_config(self, out_dir: Path, **opts) -> List[Path]:
        from ..authoring.sheet import write_spritesheet

        quality_scale = opts.pop("quality_scale", None)
        downsample = opts.pop("downsample", None)
        if opts:
            unknown = ", ".join(sorted(opts))
            raise TypeError(f"config target render_sheet got unknown option(s): {unknown}")
        job = copy.deepcopy(self._job)
        if quality_scale is not None:
            job.render.render_scale = max(
                1.0 / 64.0, float(job.render.render_scale) * float(quality_scale)
            )
        if downsample is not None:
            job.render.downsample = str(downsample)
        image_out = out_dir / f"{self.name}_spritesheet.png"
        manifest_out = out_dir / f"{self.name}_spritesheet.yaml"
        paths = list(
            write_spritesheet(job, image_out, manifest_out, source_config=self._config_path)
        )
        actor_out = out_dir / f"{self.name}_actor.ron"
        if actor_out.exists():
            paths.append(actor_out)
        return paths

    @profile
    def _render_canonical_config(self, out_dir: Path, **opts) -> Path:
        from .character_generators import get_generator

        del opts  # generator pipeline ignores module-target **opts
        generator = get_generator(self._job.target)
        spec = generator.sample_spec(self._job)
        img = generator.render_canonical(spec, self._job)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        out = out_dir / f"{self.name}_canonical_transparent.png"
        img.save(out)
        return out

    @profile
    def _render_portraits_config(self, out_dir: Path, **opts) -> List[Path]:
        from .character_generators import get_generator

        # Gameplay quality flags tune the gameplay sheet. Portraits have their
        # own native render resolution and must not be post-scaled from it.
        opts.pop("quality_scale", None)
        opts.pop("downsample", None)
        if opts:
            unknown = ", ".join(sorted(opts))
            raise TypeError(
                f"config target render_portraits got unknown option(s): {unknown}"
            )
        generator = get_generator(self._job.target)
        spec = generator.sample_spec(self._job)
        return list(
            generator.render_portraits(
                spec, self._job, target=self.name, out_dir=str(out_dir)
            )
        )


# ---- Discovery ---------------------------------------------------------------


class DiscoveryReport(NamedTuple):
    """Outcome of one discovery pass."""

    targets: Dict[str, Target]
    warnings: List[str]


def _targets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "targets"


def _configs_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "configs"


def _walk_category(category: str) -> Iterator[Tuple[str, str]]:
    """Yield ``(stem, dotted_module_path)`` for each candidate under
    ``targets/<category>/`` — both single-file modules and packages."""
    cat_dir = _targets_dir() / category
    if not cat_dir.is_dir():
        return
    for path in sorted(cat_dir.iterdir()):
        name = path.name
        if name.startswith("_"):
            continue  # __init__, __main__, private helpers
        if path.is_file() and path.suffix == ".py":
            stem = path.stem
            yield stem, f"ambition_sprite2d_renderer.targets.{category}.{stem}"
        elif path.is_dir() and (path / "__init__.py").exists():
            yield name, f"ambition_sprite2d_renderer.targets.{category}.{name}"
        elif (
            path.is_dir()
            and any(path.glob("*.py"))
            and not (cat_dir / f"{name}.py").exists()
        ):
            # A would-be multi-file target missing its __init__.py must not
            # vanish silently (contrast: a module missing render() warns).
            # Dirs paired with a sibling module of the same name (e.g.
            # rigged.py + rigged/ holding data + loose scripts) stay quiet.
            print(
                f"warning: targets/{category}/{name}/ has .py files but no "
                f"__init__.py — not a package, so it cannot register",
                file=sys.stderr,
            )


def _with_actor_sidecar(stem: str, sheet_files: Sequence[str]) -> Tuple[str, ...]:
    """Return install file list with the optional actor sidecar included."""
    out = list(sheet_files)
    actor = f"{stem}_actor.ron"
    if actor not in out:
        out.append(actor)
    return tuple(out)


def default_sheet_files(stem: str) -> List[str]:
    """Default install set for tack-on targets that don't declare ``SHEET_FILES``."""
    return [
        f"{stem}_spritesheet.png",
        f"{stem}_spritesheet.yaml",
        f"{stem}_spritesheet.ron",
        f"{stem}_actor.ron",
    ]


def _build_module_target(
    mod,
    stem: str,
    category: str,
    dotted: str,
    render: Callable,
) -> Target:
    sheet_files = _with_actor_sidecar(
        stem, getattr(mod, "SHEET_FILES", default_sheet_files(stem))
    )
    install_fn = getattr(mod, "install", None)
    if not callable(install_fn):
        install_fn = None
    render_canonical_fn = getattr(mod, "render_canonical", None)
    if not callable(render_canonical_fn):
        render_canonical_fn = None
    render_portraits_fn = getattr(mod, "render_portraits", None)
    if not callable(render_portraits_fn):
        render_portraits_fn = None
    portrait_files = tuple(
        getattr(
            mod,
            "PORTRAIT_FILES",
            (f"{stem}_portraits.png", f"{stem}_portraits.ron")
            if category == "characters" or render_portraits_fn is not None
            else (),
        )
    )
    portrait_install_subdir = getattr(mod, "PORTRAIT_INSTALL_SUBDIR", None)
    return Target.from_module(
        name=stem,
        category=category,
        module_path=dotted,
        render=render,
        sheet_files=sheet_files,
        install=install_fn,
        render_canonical=render_canonical_fn,
        render_portraits=render_portraits_fn,
        portrait_files=portrait_files,
        portrait_install_subdir=portrait_install_subdir,
        actor_metadata=getattr(mod, "ACTOR_METADATA", None),
    )


def _build_module_targets(
    mod,
    stem: str,
    category: str,
    dotted: str,
    warnings: List[str],
) -> List[Target]:
    """A module exposing ``TARGETS = {name: {...}}`` registers many."""
    results: List[Target] = []
    for sub_name, spec in mod.TARGETS.items():
        render = spec.get("render")
        if not callable(render):
            warnings.append(
                f"{category}/{stem}: TARGETS[{sub_name!r}] missing `render`; skipped"
            )
            continue
        sheet_files = _with_actor_sidecar(
            sub_name, spec.get("sheet_files", default_sheet_files(sub_name))
        )
        install_fn = spec.get("install")
        if install_fn is not None and not callable(install_fn):
            install_fn = None
        render_canonical_fn = spec.get("render_canonical")
        if render_canonical_fn is not None and not callable(render_canonical_fn):
            render_canonical_fn = None
        render_portraits_fn = spec.get("render_portraits")
        if render_portraits_fn is not None and not callable(render_portraits_fn):
            render_portraits_fn = None
        portrait_files = tuple(
            spec.get(
                "portrait_files",
                (f"{sub_name}_portraits.png", f"{sub_name}_portraits.ron")
                if category == "characters" or render_portraits_fn is not None
                else (),
            )
        )
        portrait_install_subdir = spec.get(
            "portrait_install_subdir",
            getattr(mod, "PORTRAIT_INSTALL_SUBDIR", None),
        )
        results.append(
            Target.from_module(
                name=sub_name,
                category=category,
                module_path=dotted,
                render=render,
                sheet_files=sheet_files,
                install=install_fn,
                render_canonical=render_canonical_fn,
                render_portraits=render_portraits_fn,
                portrait_files=portrait_files,
                portrait_install_subdir=portrait_install_subdir,
                actor_metadata=merge_actor_metadata(
                    getattr(mod, "ACTOR_METADATA", None), spec.get("actor_metadata")
                ),
            )
        )
    return results


@profile
def discover_module_targets() -> DiscoveryReport:
    """Walk ``targets/<category>/`` and register every conformant module.

    Module-authored targets only; for the unified surface that also covers
    config-authored (YAML) targets, see [`discover_all_targets`].
    """
    targets: Dict[str, Target] = {}
    warnings: List[str] = []
    module_categories = ("characters", "props", "tiles", "icons", "projectiles")
    for category in module_categories:
        for stem, dotted in _walk_category(category):
            if category == "characters" and stem in GENERATOR_MODULE_STEMS:
                continue
            try:
                mod = importlib.import_module(dotted)
            except Exception as ex:  # noqa: BLE001 - record + continue
                warnings.append(
                    f"{category}/{stem}: import failed ({type(ex).__name__}: {ex})"
                )
                continue
            multi = getattr(mod, "TARGETS", None)
            if isinstance(multi, dict):
                for tgt in _build_module_targets(mod, stem, category, dotted, warnings):
                    if tgt.name in targets:
                        warnings.append(
                            f"{category}/{stem}: TARGETS entry {tgt.name!r} shadows "
                            f"an earlier target of the same name"
                        )
                    targets[tgt.name] = tgt
                continue
            render = getattr(mod, "render", None)
            if not callable(render):
                warnings.append(
                    f"{category}/{stem}: no `render(out_dir, **opts) -> Iterable[Path]` "
                    f"function (and no `TARGETS` dict) — add one to register as a "
                    f"module target, or move shared helpers to the package root."
                )
                continue
            if stem in targets:
                warnings.append(
                    f"{category}/{stem}: shadows an earlier target of the same name"
                )
            targets[stem] = _build_module_target(mod, stem, category, dotted, render)
    return DiscoveryReport(targets=targets, warnings=warnings)


def _discover_yaml_configs(
    config_dir: Path, category: str
) -> Tuple[Dict[str, Target], List[str]]:
    """Walk ``config_dir/*.yaml`` and wrap each as a config-authored Target."""
    targets: Dict[str, Target] = {}
    warnings: List[str] = []
    if not config_dir.is_dir():
        return targets, warnings
    for path in sorted(config_dir.glob("*.yaml")):
        stem = path.stem
        try:
            target = Target.from_config(config_path=path, category=category)
        except Exception as ex:  # noqa: BLE001
            warnings.append(
                f"{category}/{stem}: load failed ({type(ex).__name__}: {ex})"
            )
            continue
        targets[target.name] = target
    return targets, warnings


@profile
def discover_all_targets() -> DiscoveryReport:
    """Walk every surface (module- + config-authored) into one Target dict.

    Sources, in precedence order (later overrides earlier on name collision):

    1. ``configs/review/*.yaml`` — config-authored, category ``"characters"``
    2. ``configs/*.yaml`` (main) — config-authored, category ``"characters"``
    3. Module-authored Python targets under ``targets/<category>/``

    So a module character with the same name as a config (e.g. `sandbag` ships
    both) gets the module target. The config pipeline is still reachable via
    `draw-character <config>` for one-off use.
    """
    module_report = discover_module_targets()
    # `configs/review/*.yaml` joins `characters` (Phase 6 cleanup — the split
    # was internal renderer-bookkeeping). Config- and module-authored targets
    # both surface under one category.
    review_targets, review_warnings = _discover_yaml_configs(
        _configs_dir() / "review",
        "characters",
    )
    main_targets, main_warnings = _discover_yaml_configs(
        _configs_dir(),
        "characters",
    )
    targets: Dict[str, Target] = {}
    # Precedence (later overrides earlier).
    targets.update(review_targets)
    targets.update(main_targets)
    targets.update(module_report.targets)
    return DiscoveryReport(
        targets=targets,
        warnings=module_report.warnings + main_warnings + review_warnings,
    )


__all__ = [
    "GENERATOR_MODULE_STEMS",
    "CATEGORIES",
    "DiscoveryReport",
    "Target",
    "default_sheet_files",
    "discover_all_targets",
    "discover_module_targets",
]
