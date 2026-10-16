"""Ultrapacking: repack every target's frames into shared, uniformly-sized pages.

At publish time a single-frame static prop is no longer its own PNG file — its
frame is packed into whatever shared atlas page it fits in, alongside frames
from every other target. Every page is the same size (``page_size``). This is
the cross-target counterpart to per-target sheet building: one frame pool, one
MaxRects packer, N uniform pages.

First pass = general packing (best-fit across the whole pool). Memory-locality
grouping (keep a target's or a zone's frames co-resident on a page) can be
layered on later via pack groups; this pass deliberately packs everything into
the tightest set of uniform pages.

Frames enter the pool two ways:

* ``ultrapack(targets)`` renders each target's sheet fresh, reads the manifest,
  and reconstructs each logical frame (trimmed crop pasted back at its offset).
* ``ultrapack_rendered(sheet_dir)`` reads the *already-published* per-target
  sheets in a directory — no re-render. This is the efficient regen path: the
  main regen renders every sheet once, then the pool is packed straight from
  those sheets.

Quality tiers. A pack is produced at a ``scale`` (1.0 = authored, 0.5, 0.25,
1/16 potato). Each *isolated* logical frame is downsampled to the tier budget
*before* it enters the packer, then packed into fresh tier-local pages. This is
the sanctioned quality path (see
``docs/planning/engine/data-driven-sprites-and-characters.md`` and
``scripts/generate_visual_quality_variants.py``): never resize an
already-packed atlas page — packed neighbours bleed across frame edges — but a
lone frame may be downsampled and repacked freely. ``min_frame_px`` floors each
scaled frame so potato atlases stay loadable.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw
from ..profiling import profile
from ..yaml_io import safe_load

from .packer import FrameInput, _trim, pack_frames
from ambition_sprite2d_renderer.core.draw import blending_draw


@dataclass
class PackedFrame:
    """One frame's placement in the shared atlas, plus what it needs to be
    addressed at runtime (source target/animation/index + trim + logical size)."""

    target: str
    animation: str
    index: int
    duration_ms: int
    page: int
    x: int
    y: int
    w: int
    h: int
    off_x: int
    off_y: int
    src_w: int
    src_h: int


@dataclass
class UltraPack:
    page_size: int
    pages: List[Image.Image]
    scale: float = 1.0
    frames: List[PackedFrame] = field(default_factory=list)
    #: Locality group of each page (parallel to ``pages``). Every frame of a
    #: pack-plan group lands only on that group's pages, so a zone can keep
    #: its visuals co-resident and load/unload them as a unit. The general
    #: pool uses group ``"shared"``.
    page_groups: List[str] = field(default_factory=list)

    def fill_fraction(self) -> float:
        """Packed pixel area / total page area — how tightly the pool packed."""
        if not self.pages:
            return 0.0
        used = sum(f.w * f.h for f in self.frames)
        total = self.page_size * self.page_size * len(self.pages)
        return used / total if total else 0.0

    def catalog(self, page_names: List[str]) -> dict:
        """A plain-dict catalog: uniform page list + every frame's placement,
        grouped by target -> animation -> [frames]."""
        by_target: Dict[str, Dict[str, list]] = {}
        for f in self.frames:
            anim = by_target.setdefault(f.target, {}).setdefault(f.animation, [])
            anim.append(
                {
                    "index": f.index,
                    "page": f.page,
                    "x": f.x,
                    "y": f.y,
                    "w": f.w,
                    "h": f.h,
                    "off": [f.off_x, f.off_y],
                    "src": [f.src_w, f.src_h],
                    "duration_ms": f.duration_ms,
                }
            )
        return {
            "page_size": self.page_size,
            "scale": self.scale,
            "pages": page_names,
            "page_groups": self.page_groups or ["shared"] * len(page_names),
            "targets": by_target,
        }


@dataclass
class PackPlan:
    """Locality policy for ultrapacking: which targets pack co-resident.

    ``groups`` maps a group name to the target stems that must share a page
    sequence (a zone's cast, the always-loaded set). Targets in no group land
    in the ``"shared"`` pool. This is quality-independent policy — the same
    plan applies to every tier — matching the PackPlan artifact in
    ``docs/planning/engine/data-driven-sprites-and-characters.md``.

    Authored as YAML::

        groups:
          intro: [intro_cart, creator, interdimensional_gate_ring]
          always: [player_robot_v3, robot]
        runtime_groups: [intro]

    ``runtime_groups`` are the groups a runtime reader loads: their pages are
    the pack's runtime product (:func:`write_runtime_product`). The rest of
    the pack is a source that nothing in the game reads.
    """

    SHARED = "shared"

    groups: Dict[str, List[str]] = field(default_factory=dict)
    runtime_groups: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._stem_to_group: Dict[str, str] = {}
        for group, stems in self.groups.items():
            if group == self.SHARED:
                raise ValueError('pack-plan group name "shared" is reserved for the default pool')
            for stem in stems:
                prior = self._stem_to_group.setdefault(stem, group)
                if prior != group:
                    raise ValueError(
                        f"pack-plan target {stem!r} is in two groups ({prior!r}, {group!r})"
                    )
        for group in self.runtime_groups:
            if group not in self.groups:
                raise ValueError(f"pack-plan runtime group {group!r} is not a group of the plan")

    @classmethod
    def load(cls, path: Path) -> "PackPlan":
        doc = safe_load(Path(path).read_text()) or {}
        return cls(
            groups={str(g): [str(s) for s in stems] for g, stems in (doc.get("groups") or {}).items()},
            runtime_groups=[str(g) for g in (doc.get("runtime_groups") or [])],
        )

    def group_of(self, stem: str) -> str:
        return self._stem_to_group.get(stem, self.SHARED)

    def group_names(self) -> List[str]:
        return list(self.groups)


@profile
def _reconstruct_logical(page: Image.Image, rect: dict, src_w: int, src_h: int) -> Image.Image:
    """Rebuild a frame's logical (untrimmed) image from a sheet: crop the packed
    rect and paste it back at its trim offset in a transparent logical canvas."""
    x, y, w, h = int(rect["x"]), int(rect["y"]), int(rect["w"]), int(rect["h"])
    crop = page.crop((x, y, x + w, y + h))
    off = rect.get("off") or (0, 0)
    logical = Image.new("RGBA", (src_w, src_h), (0, 0, 0, 0))
    logical.paste(crop, (int(off[0]), int(off[1])))
    return logical


@profile
def _scale_logical(
    logical: Image.Image, scale: float, min_px: int
) -> Tuple[Image.Image, Tuple[int, int]]:
    """Downsample an *isolated* logical frame to a quality tier.

    Returns ``(image, (w, h))`` at the tier size. ``scale >= 1.0`` is a no-op.
    Below the potato threshold we use nearest-neighbour for deliberate crunchy
    pixels; otherwise LANCZOS for a clean reduction. Every side is floored at
    ``min_px`` so a frame never collapses to nothing.
    """
    if scale >= 1.0:
        return logical, logical.size
    w, h = logical.size
    nw = max(min_px, round(w * scale))
    nh = max(min_px, round(h * scale))
    resample = Image.NEAREST if scale <= 0.125 else Image.LANCZOS
    return logical.resize((nw, nh), resample), (nw, nh)


@profile
def _read_sheet_frames(
    sheet_dir: Path, stem: str, *, scale: float, min_px: int
) -> List[Tuple[FrameInput, dict]]:
    """Read one published sheet (``{stem}_spritesheet.yaml`` + its page PNGs) in
    ``sheet_dir`` and reconstruct every logical frame (scaled to the tier).

    Returns ``(FrameInput, meta)`` pairs where meta carries the source
    animation/index/duration for the catalog. Empty for a bespoke/multi-file
    target without a standard single-sheet manifest.
    """
    manifest_path = sheet_dir / f"{stem}_spritesheet.yaml"
    if not manifest_path.exists():
        return []
    manifest = safe_load(manifest_path.read_text()) or {}
    fw = int(manifest.get("frame_width", 0))
    fh = int(manifest.get("frame_height", 0))
    if fw <= 0 or fh <= 0:
        return []
    # Page filenames: the config manifest omits `image`/`images` (only the RON
    # carries them), so fall back to the conventional page-0 name.
    page_names = manifest.get("images") or [
        manifest.get("image") or f"{stem}_spritesheet.png"
    ]
    pages = [Image.open(sheet_dir / n).convert("RGBA") for n in page_names if n]
    out: List[Tuple[FrameInput, dict]] = []
    for row in manifest.get("rows", []):
        anim = row.get("animation", "")
        duration_ms = int(row.get("duration_ms", 0))
        row_page = int(row.get("page", 0))
        for idx, rect in enumerate(row.get("rects", [])):
            page_idx = int(rect.get("fpage", rect.get("page", row_page)))
            if page_idx >= len(pages):
                continue
            logical = _reconstruct_logical(pages[page_idx], rect, fw, fh)
            image, logical_size = _scale_logical(logical, scale, min_px)
            key = (stem, anim, idx)
            out.append(
                (
                    FrameInput(key=key, image=image, logical_size=logical_size),
                    {"target": stem, "animation": anim, "index": idx, "duration_ms": duration_ms},
                )
            )
    return out


@profile
def _frames_from_target(
    target, tmp: Path, *, scale: float, min_px: int
) -> List[Tuple[FrameInput, dict]]:
    """Render one target's sheet into ``tmp`` then read its logical frames."""
    target.render_sheet(tmp)
    return _read_sheet_frames(tmp, target.name, scale=scale, min_px=min_px)


@profile
def _pack_pool(
    pairs: Sequence[Tuple[FrameInput, dict]],
    *,
    scale: float,
    page_size: int,
    max_dim: int,
    plan: Optional["PackPlan"] = None,
) -> UltraPack:
    """Pack a pool of ``(FrameInput, meta)`` pairs into uniform shared pages.

    With a ``plan``, the pool is partitioned by locality group and each group
    packs into its OWN page sequence (concatenated into one global page list,
    each page tagged with its group). Frames of one group never share a page
    with another group — that is the locality guarantee — at the cost of some
    fill on each group's last page.
    """
    plan = plan or PackPlan()
    by_group: Dict[str, List[Tuple[FrameInput, dict]]] = {}
    for fi, m in pairs:
        by_group.setdefault(plan.group_of(m["target"]), []).append((fi, m))

    packed = UltraPack(page_size=page_size, pages=[], scale=scale)
    # Deterministic group order: named plan groups first (plan order), then
    # the shared pool.
    ordered = [g for g in plan.group_names() if g in by_group]
    if PackPlan.SHARED in by_group and PackPlan.SHARED not in ordered:
        ordered.append(PackPlan.SHARED)
    for group in ordered:
        group_pairs = by_group[group]
        inputs = [fi for fi, _m in group_pairs]
        meta = {fi.key: m for fi, m in group_pairs}
        result = pack_frames(inputs, max_dim=max_dim, page_size=page_size, padding=1, trim=True)
        page_base = len(packed.pages)
        packed.pages.extend(result.pages)
        packed.page_groups.extend([group] * len(result.pages))
        for key, pl in result.placements.items():
            m = meta[key]
            packed.frames.append(
                PackedFrame(
                    target=m["target"],
                    animation=m["animation"],
                    index=m["index"],
                    duration_ms=m["duration_ms"],
                    page=page_base + pl.page,
                    x=pl.x,
                    y=pl.y,
                    w=pl.w,
                    h=pl.h,
                    off_x=pl.off_x,
                    off_y=pl.off_y,
                    src_w=pl.src_w,
                    src_h=pl.src_h,
                )
            )
    return packed


@profile
def ultrapack(
    targets,
    *,
    scale: float = 1.0,
    min_frame_px: int = 1,
    page_size: int = 2048,
    max_dim: int = 16384,
    plan: Optional[PackPlan] = None,
) -> UltraPack:
    """Render every target fresh and pool its frames into uniform pages.

    Same no-silent-coverage-caps rule as :func:`ultrapack_rendered`: a target
    whose render/read raises is reported loudly on stderr, never dropped
    without a trace.
    """
    pairs: List[Tuple[FrameInput, dict]] = []
    with tempfile.TemporaryDirectory() as td:
        for target in targets:
            tdir = Path(td) / target.name
            tdir.mkdir(parents=True, exist_ok=True)
            try:
                pairs.extend(
                    _frames_from_target(target, tdir, scale=scale, min_px=min_frame_px)
                )
            except Exception as ex:  # noqa: BLE001 — report, then keep packing the rest
                print(
                    f"warning: ultrapack failed to render/read '{target.name}' "
                    f"({ex!r}) — target DROPPED from this pack",
                    file=sys.stderr,
                )
                continue
    return _pack_pool(pairs, scale=scale, page_size=page_size, max_dim=max_dim, plan=plan)


@profile
def ultrapack_rendered(
    sheet_dir: Path,
    *,
    stems: Optional[Sequence[str]] = None,
    scale: float = 1.0,
    min_frame_px: int = 1,
    page_size: int = 2048,
    max_dim: int = 16384,
    plan: Optional[PackPlan] = None,
    jobs: int = 1,
) -> UltraPack:
    """Pool frames from the *already-published* per-target sheets in ``sheet_dir``
    (no re-render). ``stems`` limits which sheets to include; ``None`` packs
    every ``*_spritesheet.yaml`` found at the top level of ``sheet_dir``.

    No silent coverage caps: a sheet whose read RAISES is reported loudly on
    stderr (a transient IO flake here once dropped 59 targets from one tier
    with no trace). A sheet that reads to zero frames (bespoke manifest with
    no standard rows) is reported once as skipped — that set should match the
    known bespoke targets, not vary run to run.
    """
    sheet_dir = Path(sheet_dir)
    if stems is None:
        stems = sorted(
            p.name[: -len("_spritesheet.yaml")]
            for p in sheet_dir.glob("*_spritesheet.yaml")
        )
    pairs: List[Tuple[FrameInput, dict]] = []
    no_frames: List[str] = []

    def read(stem: str):
        try:
            return _read_sheet_frames(sheet_dir, stem, scale=scale, min_px=min_frame_px), None
        except Exception as ex:  # noqa: BLE001 — report, then keep packing the rest
            return None, ex

    for stem, (frames, ex) in zip(stems, _ordered_map(read, stems, jobs)):
        if ex is not None:
            print(
                f"warning: ultrapack failed to read '{stem}' ({ex!r}) — "
                f"target DROPPED from this pack",
                file=sys.stderr,
            )
            continue
        if not frames:
            no_frames.append(stem)
            continue
        pairs.extend(frames)
    if no_frames:
        print(
            f"ultrapack: {len(no_frames)} sheet(s) had no standard frame rows "
            f"(bespoke targets, not packed): {', '.join(no_frames)}",
            file=sys.stderr,
        )
    return _pack_pool(pairs, scale=scale, page_size=page_size, max_dim=max_dim, plan=plan)


def _ordered_map(fn, items, jobs: int) -> list:
    """``[fn(item) for item in items]``, on ``jobs`` threads, in item order.

    Pillow releases the GIL while it decodes, scales and encodes, so the
    threads run at once: the encode of 48 full-tier pages was 20.7 s on one
    thread and 7.2 s on three, the same bytes (measured 2026-10-15). The
    results keep the order of the items, so the pack is the same for each
    number of threads."""
    items = list(items)
    if jobs <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(fn, items))


def _holds_pixels(path: Path, img: Image.Image) -> bool:
    """True when ``path`` is an image with exactly the pixels of ``img``."""
    if not path.is_file():
        return False
    try:
        with Image.open(path) as existing:
            return (
                existing.size == img.size
                and existing.mode == img.mode
                and existing.tobytes() == img.tobytes()
            )
    except OSError:
        return False


def _pixel_digest(img: Image.Image) -> str:
    digest = hashlib.sha1(f"{img.mode}:{img.size}:".encode())
    digest.update(img.tobytes())
    return digest.hexdigest()


def _keep_or_write(path: Path, img: Image.Image, ledger: Optional[Dict[str, list]]) -> list:
    """Write ``img`` to ``path`` unless the file already holds its pixels, and
    return the file's record, ``[size, mtime_ns, pixel digest]``.

    ``ledger`` is those records from the last run. A file whose size and
    mtime did not change is known by its digest, and is not decoded: the
    decode of every page was 17 s of an 87 s full-tier pack (measured
    2026-10-15)."""
    digest = _pixel_digest(img)
    known = (ledger or {}).get(path.name)
    stat = path.stat() if path.is_file() else None
    if stat is not None and known and known[0] == stat.st_size and known[1] == stat.st_mtime_ns:
        same = known[2] == digest
    else:
        same = _holds_pixels(path, img)
    if not same:
        img.save(path)
        stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns, digest]


@profile
def write_pack(
    pack: UltraPack,
    out_dir: Path,
    *,
    name: str = "ultrapack",
    ledger: Optional[Dict[str, list]] = None,
    records: Optional[Dict[str, list]] = None,
    jobs: int = 1,
) -> List[Path]:
    """Write the shared page PNGs + a catalog JSON (runtime artifacts only).

    Diagnostics are NOT written here — see ``write_debug_views`` for the
    opt-in labeled/overlay sheets, which land under ``diagnostics/`` so the
    publish output stays clean by default."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page_names = [f"{name}_{i}.png" for i in range(len(pack.pages))]
    written: List[Path] = [out_dir / pname for pname in page_names]
    # A page whose file already holds these pixels is kept: encoding a
    # page costs about 5 times its decode, and an edit to one sheet
    # leaves most pages as they were (1 of 61 changed for a recolour,
    # 30 of 61 for a frame that changed size; measured 2026-10-15).
    kept = _ordered_map(lambda pair: _keep_or_write(pair[1], pair[0], ledger), list(zip(pack.pages, written)), jobs)
    if records is not None:
        for path, record in zip(written, kept):
            records[path.name] = record
    # A pack with fewer pages than the last one: the extra pages are stale.
    for stale in out_dir.glob(f"{name}_*.png"):
        suffix = stale.stem[len(name) + 1 :]
        if suffix.isdigit() and int(suffix) >= len(pack.pages):
            stale.unlink()
    catalog_path = out_dir / f"{name}.json"
    catalog_path.write_text(json.dumps(pack.catalog(page_names), indent=1, sort_keys=True))
    written.append(catalog_path)
    return written


def write_runtime_product(source_dir: Path, out_dir: Path, *, name: str = "ultrapack", groups: Sequence[str]) -> List[Path]:
    """Write the runtime product of the pack in ``source_dir`` to ``out_dir``:
    the pages of ``groups``, renumbered from 0, and a catalog of the targets on
    them.

    The packager ships every file under the runtime roots, and the game reads
    a pack only through the targets a prop row names (one, ``intro_cart``):
    695 MB of pack pages shipped for 5.4 MB that a reader can reach (measured
    2026-10-15). The source pack stays whole, outside the runtime roots. A
    page is copied byte for byte and only when it differs, so an unchanged
    group keeps its files."""
    source_dir, out_dir = Path(source_dir), Path(out_dir)
    catalog = json.loads((source_dir / f"{name}.json").read_text())
    wanted = set(groups)
    kept = [index for index, group in enumerate(catalog["page_groups"]) if group in wanted]
    renumber = {old: new for new, old in enumerate(kept)}
    targets: Dict[str, Dict[str, list]] = {}
    for target, animations in catalog["targets"].items():
        pages = {frame["page"] for frames in animations.values() for frame in frames}
        if not pages & set(renumber):
            continue
        if not pages <= set(renumber):
            raise ValueError(f"target {target!r} has frames on pages of a group that is not shipped")
        targets[target] = {
            animation: [dict(frame, page=renumber[frame["page"]]) for frame in frames]
            for animation, frames in animations.items()
        }
    out_dir.mkdir(parents=True, exist_ok=True)
    page_names = [f"{name}_{index}.png" for index in range(len(kept))]
    written: List[Path] = []
    for old, page_name in zip(kept, page_names):
        source = (source_dir / catalog["pages"][old]).read_bytes()
        path = out_dir / page_name
        if not path.is_file() or path.read_bytes() != source:
            path.write_bytes(source)
        written.append(path)
    for stale in out_dir.glob(f"{name}_*.png"):
        suffix = stale.stem[len(name) + 1 :]
        if suffix.isdigit() and int(suffix) >= len(kept):
            stale.unlink()
    runtime = dict(catalog, pages=page_names, page_groups=[catalog["page_groups"][old] for old in kept], targets=targets)
    catalog_path = out_dir / f"{name}.json"
    catalog_path.write_text(json.dumps(runtime, indent=1, sort_keys=True))
    written.append(catalog_path)
    return written


#: The version of a tier's state file. A change to the file's shape makes
#: every state file stale, so the next pack is a full pack.
_STATE_VERSION = 1


def _code_key() -> str:
    """A digest of the code that lays out a tier. A layout from other code
    must not be patched."""
    here = Path(__file__).resolve().parent
    digest = hashlib.sha1()
    for module in ("packer.py", "ultrapack.py"):
        digest.update((here / module).read_bytes())
    return digest.hexdigest()


def _sheet_digests(sheet_dir: Path, memo: Dict[str, list]) -> Tuple[Dict[str, str], Dict[str, list]]:
    """The content digest of each published sheet in ``sheet_dir``: its
    manifest and each page PNG, by stem.

    ``memo`` maps a file name to ``[size, mtime_ns, digest]`` from the last
    run. A file whose size and mtime did not change keeps its digest and is
    not read. A copy with new mtimes (the publish's staging root) is read
    once, and its digest is the same, so the copy alone moves no sheet."""
    names = sorted(p.name for p in sheet_dir.iterdir() if p.is_file())
    stems = [n[: -len("_spritesheet.yaml")] for n in names if n.endswith("_spritesheet.yaml")]
    files: Dict[str, List[str]] = {stem: [f"{stem}_spritesheet.yaml"] for stem in stems}
    page = re.compile(r"^(.+)_spritesheet(?:\.\d+)?\.png$")
    for name in names:
        match = page.match(name)
        if match and match.group(1) in files:
            files[match.group(1)].append(name)
    new_memo: Dict[str, list] = {}
    digests: Dict[str, str] = {}
    for stem, stem_files in files.items():
        sheet = hashlib.sha1()
        for name in stem_files:
            stat = (sheet_dir / name).stat()
            known = memo.get(name)
            if known and known[0] == stat.st_size and known[1] == stat.st_mtime_ns:
                file_digest = known[2]
            else:
                file_digest = hashlib.sha1((sheet_dir / name).read_bytes()).hexdigest()
            new_memo[name] = [stat.st_size, stat.st_mtime_ns, file_digest]
            sheet.update(f"{name}:{file_digest};".encode())
        digests[stem] = sheet.hexdigest()
    return digests, new_memo


def _signature(pack: UltraPack) -> Dict[str, list]:
    """Each target's frames in pool order, with their trimmed sizes. The
    packer places frames by these sizes in this order and by nothing else, so
    two pools with one signature have one layout."""
    out: Dict[str, list] = {}
    for f in pack.frames:
        out.setdefault(f.target, []).append([f.animation, f.index, f.w, f.h])
    return out


def _load_state(state_path: Path) -> Optional[dict]:
    try:
        state = json.loads(Path(state_path).read_text())
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) and state.get("version") == _STATE_VERSION else None


def _plan_patch(
    state: dict,
    params: dict,
    sheets: Dict[str, str],
    sheet_dir: Path,
    out_dir: Path,
    name: str,
    *,
    scale: float,
    min_px: int,
) -> Optional[Dict[str, list]]:
    """The new frames of each changed sheet, when the tier can be patched;
    ``None`` when it must be packed again.

    It can be patched when the inputs are the same as the last pack's except
    for the pixels of some sheets, and each changed sheet's frames have the
    same trimmed sizes in the same order. Then a full pack gives the same
    layout, so the old pages with the changed frames drawn again are what a
    full pack writes."""
    if state.get("params") != params or set(state.get("sheets", {})) != set(sheets):
        return None
    catalog_path = out_dir / f"{name}.json"
    try:
        catalog_text = catalog_path.read_text()
    except OSError:
        return None
    if hashlib.sha1(catalog_text.encode()).hexdigest() != state.get("catalog"):
        return None
    pages = json.loads(catalog_text).get("pages", [])
    if not all((out_dir / page).is_file() for page in pages):
        return None
    changes: Dict[str, list] = {}
    for stem in sorted(stem for stem in sheets if sheets[stem] != state["sheets"][stem]):
        try:
            pairs = _read_sheet_frames(sheet_dir, stem, scale=scale, min_px=min_px)
        except Exception:  # noqa: BLE001 — the full pack reports it, by name
            return None
        frames = []
        for fi, meta in pairs:
            image, off_x, off_y = _trim(fi.image, fi.logical_size, True)
            frames.append((meta, image, off_x, off_y, fi.logical_size))
        signature = [[m["animation"], m["index"], *image.size] for m, image, _x, _y, _s in frames]
        if signature != state.get("signature", {}).get(stem, []):
            return None
        changes[stem] = frames
    return changes


def _apply_patch(
    changes: Dict[str, list], out_dir: Path, name: str, ledger: Dict[str, list], records: Dict[str, list]
) -> List[Path]:
    """Draw each changed frame again on its page, at its place, and write the
    catalog with the frames' new offsets, sizes and durations."""
    catalog_path = out_dir / f"{name}.json"
    catalog = json.loads(catalog_path.read_text())
    by_page: Dict[int, list] = {}
    for stem, frames in changes.items():
        for meta, image, off_x, off_y, (src_w, src_h) in frames:
            entry = next(
                e for e in catalog["targets"][stem][meta["animation"]] if e["index"] == meta["index"]
            )
            entry["off"] = [off_x, off_y]
            entry["src"] = [src_w, src_h]
            entry["duration_ms"] = meta["duration_ms"]
            by_page.setdefault(entry["page"], []).append((entry, image))
    written: List[Path] = []
    for page_index, drawn in sorted(by_page.items()):
        path = out_dir / catalog["pages"][page_index]
        with Image.open(path) as opened:
            page = opened.convert("RGBA")
        for entry, image in drawn:
            x, y = entry["x"], entry["y"]
            # Clear the rect first: a pixel the new frame leaves transparent
            # must not keep the old frame's colour.
            page.paste((0, 0, 0, 0), (x, y, x + entry["w"], y + entry["h"]))
            page.alpha_composite(image, (x, y))
        records[path.name] = _keep_or_write(path, page, ledger)
        written.append(path)
    catalog_path.write_text(json.dumps(catalog, indent=1, sort_keys=True))
    written.append(catalog_path)
    return written


@profile
def pack_tier(
    sheet_dir: Path,
    out_dir: Path,
    state_path: Path,
    *,
    name: str = "ultrapack",
    scale: float = 1.0,
    min_frame_px: int = 1,
    page_size: int = 2048,
    max_dim: int = 16384,
    plan: Optional[PackPlan] = None,
    jobs: int = 1,
) -> Tuple[str, List[Path]]:
    """Bring the tier in ``out_dir`` up to date with the sheets in
    ``sheet_dir``, at a cost in proportion to what changed.

    ``state_path`` records the last pack's inputs (each sheet's digest, the
    frames' trimmed sizes, the catalog's digest). When only the pixels of
    some sheets changed and their frames kept their trimmed sizes (a
    recolour, a shading pass), the layout is the same, and only the pages
    that hold those frames are drawn again. Otherwise the tier is packed
    again. Both roads write the same bytes. Returns how the tier was brought
    up to date, and the files written.

    The state file is removed before anything is written and written last,
    so a run cut short leaves no state, and the next run packs in full."""
    sheet_dir, out_dir, state_path = Path(sheet_dir), Path(out_dir), Path(state_path)
    plan = plan or PackPlan()
    params = {
        "code": _code_key(),
        "name": name,
        "scale": scale,
        "min_frame_px": min_frame_px,
        "page_size": page_size,
        "max_dim": max_dim,
        "groups": plan.groups,
    }
    state = _load_state(state_path)
    sheets, memo = _sheet_digests(sheet_dir, state.get("digests", {}) if state else {})
    changes = None
    if state is not None:
        changes = _plan_patch(
            state, params, sheets, sheet_dir, out_dir, name, scale=scale, min_px=min_frame_px
        )
    state_path.unlink(missing_ok=True)
    if changes is not None:
        signature = state["signature"]
        pages = dict(state.get("pages", {}))
        written = _apply_patch(changes, out_dir, name, state.get("pages", {}), pages)
        how = f"patched {len(changes)} sheet(s) on {len(written) - 1} page(s): {', '.join(changes) or 'none'}"
    else:
        pack = ultrapack_rendered(
            sheet_dir, scale=scale, min_frame_px=min_frame_px, page_size=page_size, max_dim=max_dim, plan=plan,
            jobs=jobs,
        )
        signature = _signature(pack)
        pages: Dict[str, list] = {}
        written = write_pack(
            pack, out_dir, name=name, ledger=state.get("pages") if state else None, records=pages, jobs=jobs
        )
        how = (
            f"packed {len(pack.frames)} frames from {len(signature)} targets -> "
            f"{len(pack.pages)} pages ({pack.fill_fraction() * 100:.1f}% fill)"
        )
    catalog_digest = hashlib.sha1((out_dir / f"{name}.json").read_bytes()).hexdigest()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "version": _STATE_VERSION,
                "params": params,
                "sheets": sheets,
                "signature": signature,
                "catalog": catalog_digest,
                "digests": memo,
                "pages": pages,
            }
        )
    )
    return how, written


def _checkerboard(size: Tuple[int, int], cell: int = 16) -> Image.Image:
    """Opaque grey checkerboard so packed transparency reads in a debug view."""
    w, h = size
    board = Image.new("RGBA", size, (52, 52, 60, 255))
    draw = blending_draw(board)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(70, 70, 80, 255))
    return board


@profile
def write_debug_views(
    pack: UltraPack,
    out_dir: Path,
    *,
    name: str = "ultrapack",
    debug_dir: Optional[Path] = None,
) -> List[Path]:
    """Opt-in diagnostics: each page over a checkerboard with per-frame rect
    outlines, plus a text pack report. Written under ``debug_dir`` when given
    (regen passes the STAGING diagnostics dir so a runtime pack root never
    holds debug views), else under ``out_dir/diagnostics/`` — either way,
    never mixed in with the runtime pages + catalog."""
    diag_dir = Path(debug_dir) if debug_dir is not None else Path(out_dir) / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for i, page in enumerate(pack.pages):
        view = _checkerboard(page.size)
        view.alpha_composite(page)
        draw = blending_draw(view)
        for f in pack.frames:
            if f.page != i:
                continue
            draw.rectangle([f.x, f.y, f.x + f.w - 1, f.y + f.h - 1], outline=(0, 255, 170, 200))
        p = diag_dir / f"{name}_{i}_debug.png"
        view.convert("RGB").save(p)
        written.append(p)

    by_target: Dict[str, int] = {}
    for f in pack.frames:
        by_target[f.target] = by_target.get(f.target, 0) + 1
    lines = [
        f"ultrapack '{name}'",
        f"scale        : {pack.scale:g}",
        f"page_size    : {pack.page_size}",
        f"pages        : {len(pack.pages)}",
        f"frames       : {len(pack.frames)}",
        f"targets      : {len(by_target)}",
        f"fill         : {pack.fill_fraction() * 100:.1f}%",
    ]
    if pack.page_groups:
        lines.append("")
        lines.append("page residency per group:")
        group_pages: Dict[str, int] = {}
        for g in pack.page_groups:
            group_pages[g] = group_pages.get(g, 0) + 1
        group_frames: Dict[str, int] = {}
        for f in pack.frames:
            g = pack.page_groups[f.page]
            group_frames[g] = group_frames.get(g, 0) + 1
        for g in sorted(group_pages):
            lines.append(f"  {g}: {group_pages[g]} page(s), {group_frames.get(g, 0)} frame(s)")
    lines += [
        "",
        "frames per target:",
    ]
    for stem in sorted(by_target):
        lines.append(f"  {stem}: {by_target[stem]}")
    report = diag_dir / f"{name}_report.txt"
    report.write_text("\n".join(lines) + "\n")
    written.append(report)
    return written


def main(argv: Optional[Sequence[str]] = None) -> int:
    """The publish's road to one tier: ``python -m
    ambition_sprite2d_renderer.authoring.ultrapack``.

    It is here and not in the ``ultrapack`` command because an edit to the
    CLI moves the renderer's shared core key, and that makes every published
    sheet stale (a full re-render, about 56 minutes); this module is outside
    that key. The ``ultrapack`` command packs in full, with no state."""
    import argparse

    parser = argparse.ArgumentParser(description=pack_tier.__doc__.split("\n\n")[0])
    parser.add_argument("--from-rendered", type=Path, required=True, metavar="DIR")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True, metavar="FILE")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--min-frame-px", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=2048)
    parser.add_argument("--name", default="ultrapack")
    parser.add_argument("--pack-plan", type=Path, default=None)
    parser.add_argument("--debug-views", action="store_true")
    parser.add_argument("--debug-dir", type=Path, default=None)
    parser.add_argument("--jobs", type=int, default=1, help="threads that read sheets and encode pages")
    parser.add_argument(
        "--runtime-out", type=Path, default=None, metavar="DIR",
        help="also write the runtime product (the plan's runtime groups) to DIR",
    )
    args = parser.parse_args(argv)
    plan = PackPlan.load(args.pack_plan) if args.pack_plan else None
    if args.debug_views:
        # The views need the whole pack, so this is a full pack. It writes
        # no state, and the next run packs in full.
        args.state.unlink(missing_ok=True)
        pack = ultrapack_rendered(
            args.from_rendered,
            scale=args.scale,
            min_frame_px=args.min_frame_px,
            page_size=args.page_size,
            plan=plan,
        )
        written = write_pack(pack, args.out, name=args.name)
        written += write_debug_views(pack, args.out, name=args.name, debug_dir=args.debug_dir)
        how = f"packed {len(pack.frames)} frames -> {len(pack.pages)} pages, with debug views"
    else:
        how, written = pack_tier(
            args.from_rendered,
            args.out,
            args.state,
            name=args.name,
            scale=args.scale,
            min_frame_px=args.min_frame_px,
            page_size=args.page_size,
            plan=plan,
            jobs=args.jobs,
        )
    if args.runtime_out is not None:
        groups = plan.runtime_groups if plan else []
        runtime = write_runtime_product(args.out, args.runtime_out, name=args.name, groups=groups)
        how += f"; runtime product: {len(runtime) - 1} page(s) of {', '.join(groups) or 'no group'}"
        written += runtime
    print(f"ultrapack '{args.name}' @ scale {args.scale:g}: {how}")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
