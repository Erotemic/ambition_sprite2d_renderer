"""Published-asset equivalence comparator (Pillow + stdlib only).

Two rendered sprite targets are *equivalent* when a game that consumes them
cannot tell them apart. The published contract — not a character's internal
drawing code — is what matters, so this module compares two **rendered output
directories** across the dimensions the runtime actually reads:

  * layout      — frame_width/height, label_width, page count, canvas sizes;
  * animations  — animation names, frame counts, durations, per-frame rects;
  * geometry    — body_metrics bbox, feet anchor, collision/hurtbox boxes;
  * metadata    — sockets, capabilities, animation bindings, tags;
  * pixels      — decoded RGBA of every animation frame, cropped from the sheet;
  * portraits   — portrait products and their named clips.

The comparator is **authority-agnostic**: it does not care whether a reference
render came from a legacy Pillow path, a second render authority, or a blessed
baseline of the same SVG target. That is deliberate. The SVG migration
(docs/planning/engine/svg-component-character-migration.md) is *not* a
faithful-pixel port for every character — a redesign like Oiler will never
match dead legacy pixels and is not meant to. So a pixel mismatch is **not** a
failure by itself: the report separates the pixel dimension (quantified, so a
port can watch the numbers converge) from the structure/metadata dimensions
(where a redesign is still expected to publish a valid, stable contract).

Overall verdicts, best → worst:

  * ``exact-pixels``          — every decoded RGBA frame is byte-identical;
  * ``raster-equivalent``     — pixels differ only within a small antialiased
                                edge tolerance; all structure/metadata match;
  * ``contract-match``        — pixels differ materially, but layout,
                                animations, geometry and metadata all match
                                (the normal "redesign, valid contract" result);
  * ``differs``               — a structural/geometry/metadata dimension differs.

Only Pillow + stdlib here (guarded by ``test_core_minimal_deps``): rendering
targets to compare is the caller's job (see ``equivalence_harness.py``).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Tolerant RON reader
# ---------------------------------------------------------------------------
#
# The manifests we parse are *emitted* by this package's own RON writer, so we
# only need the subset it produces: structs ``(k: v, ...)``, tuples ``(v, v)``,
# lists ``[...]``, maps ``{ "k": v, ... }``, ``Some(x)`` / ``None``, strings,
# numbers, and bools. Anything the parser cannot handle raises ``RonError`` so
# the caller can fall back to a textual comparison rather than silently
# mis-reporting a match.


class RonError(ValueError):
    """The RON text is outside the emitted subset this reader supports."""


class _RonReader:
    def __init__(self, text: str) -> None:
        self.s = self._strip_comments(text)
        self.i = 0
        self.n = len(self.s)

    @staticmethod
    def _strip_comments(text: str) -> str:
        out: List[str] = []
        for line in text.splitlines():
            # `//` only starts a comment outside a string. The emitted manifests
            # never put `//` inside a string, but guard anyway.
            in_str = False
            cut = len(line)
            k = 0
            while k < len(line) - 1:
                c = line[k]
                if c == '"' and (k == 0 or line[k - 1] != "\\"):
                    in_str = not in_str
                elif not in_str and c == "/" and line[k + 1] == "/":
                    cut = k
                    break
                k += 1
            out.append(line[:cut])
        return "\n".join(out)

    def parse(self) -> Any:
        self._ws()
        val = self._value()
        self._ws()
        if self.i != self.n:
            raise RonError(f"trailing content at offset {self.i}: {self.s[self.i:self.i+40]!r}")
        return val

    # -- scanning helpers --
    def _ws(self) -> None:
        while self.i < self.n and self.s[self.i] in " \t\r\n":
            self.i += 1

    def _peek(self) -> str:
        return self.s[self.i] if self.i < self.n else ""

    def _expect(self, ch: str) -> None:
        if self._peek() != ch:
            raise RonError(f"expected {ch!r} at offset {self.i}, got {self._peek()!r}")
        self.i += 1

    # -- grammar --
    def _value(self) -> Any:
        self._ws()
        c = self._peek()
        if c == '"':
            return self._string()
        if c == "(":
            return self._paren()
        if c == "[":
            return self._seq("[", "]")
        if c == "{":
            return self._map()
        if c == "-" or c.isdigit():
            return self._number()
        if c.isalpha() or c == "_":
            return self._ident_value()
        raise RonError(f"unexpected char {c!r} at offset {self.i}")

    def _string(self) -> str:
        self._expect('"')
        out: List[str] = []
        while self.i < self.n:
            c = self.s[self.i]
            self.i += 1
            if c == "\\":
                nxt = self.s[self.i] if self.i < self.n else ""
                self.i += 1
                out.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
            elif c == '"':
                return "".join(out)
            else:
                out.append(c)
        raise RonError("unterminated string")

    def _number(self) -> Any:
        start = self.i
        if self._peek() == "-":
            self.i += 1
        seen_dot = False
        while self.i < self.n and (self.s[self.i].isdigit() or self.s[self.i] in ".eE+-"):
            if self.s[self.i] == ".":
                seen_dot = True
            self.i += 1
        tok = self.s[start:self.i]
        try:
            return float(tok) if (seen_dot or "e" in tok or "E" in tok) else int(tok)
        except ValueError as exc:  # pragma: no cover - defensive
            raise RonError(f"bad number {tok!r}") from exc

    def _ident(self) -> str:
        start = self.i
        while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] == "_"):
            self.i += 1
        if self.i == start:
            raise RonError(f"expected identifier at offset {self.i}")
        return self.s[start:self.i]

    def _ident_value(self) -> Any:
        name = self._ident()
        if name == "None":
            return None
        if name == "true":
            return True
        if name == "false":
            return False
        self._ws()
        if self._peek() == "(":
            if name == "Some":
                # ``Some(X)`` wraps exactly one value — unwrap to X directly so
                # ``Some((x: 1))`` reads as the struct ``{x: 1}``, not ``[{x:1}]``.
                self._expect("(")
                inner = self._value()
                self._ws()
                self._expect(")")
                return inner
            # A tagged enum variant carrying data — keep the tag so a diff can
            # see it, but this is rare in the emitted manifests.
            return {"__variant__": name, "__data__": self._paren()}
        # A bare enum variant with no data.
        return name

    def _paren(self) -> Any:
        """``(k: v, ...)`` -> dict (struct); ``(v, v, ...)`` -> list (tuple)."""
        self._expect("(")
        self._ws()
        if self._peek() == ")":
            self.i += 1
            return {}
        # Decide struct vs tuple by looking for ``ident :`` on the first field.
        save = self.i
        is_struct = False
        if self._peek().isalpha() or self._peek() == "_":
            self._ident()
            self._ws()
            is_struct = self._peek() == ":"
        self.i = save
        if is_struct:
            return self._struct_body()
        return self._seq_body(")")

    def _struct_body(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        while True:
            self._ws()
            if self._peek() == ")":
                self.i += 1
                return out
            key = self._string() if self._peek() == '"' else self._ident()
            self._ws()
            self._expect(":")
            out[key] = self._value()
            self._ws()
            if self._peek() == ",":
                self.i += 1
            elif self._peek() == ")":
                self.i += 1
                return out
            else:
                raise RonError(f"expected ',' or ')' at offset {self.i}")

    def _seq(self, open_ch: str, close_ch: str) -> List[Any]:
        self._expect(open_ch)
        return self._seq_body(close_ch)

    def _seq_body(self, close_ch: str) -> List[Any]:
        out: List[Any] = []
        while True:
            self._ws()
            if self._peek() == close_ch:
                self.i += 1
                return out
            out.append(self._value())
            self._ws()
            if self._peek() == ",":
                self.i += 1
            elif self._peek() == close_ch:
                self.i += 1
                return out
            else:
                raise RonError(f"expected ',' or {close_ch!r} at offset {self.i}")

    def _map(self) -> Dict[Any, Any]:
        self._expect("{")
        out: Dict[Any, Any] = {}
        while True:
            self._ws()
            if self._peek() == "}":
                self.i += 1
                return out
            key = self._string() if self._peek() == '"' else self._ident()
            self._ws()
            self._expect(":")
            out[key] = self._value()
            self._ws()
            if self._peek() == ",":
                self.i += 1
            elif self._peek() == "}":
                self.i += 1
                return out
            else:
                raise RonError(f"expected ',' or '}}' at offset {self.i}")


def parse_ron(text: str) -> Any:
    """Parse the emitted-RON subset into nested dict/list/scalar values."""
    return _RonReader(text).parse()


# ---------------------------------------------------------------------------
# Loading a rendered target directory
# ---------------------------------------------------------------------------


@dataclass
class SheetView:
    """One ``*_spritesheet.ron`` manifest plus its decoded page pixels."""

    stem: str
    manifest: Any
    pages: Dict[int, Any]  # page index -> PIL.Image (RGBA), lazily filled

    def sheet(self) -> Dict[str, Any]:
        """The single sheet struct (manifests are a 1-element list)."""
        m = self.manifest
        if isinstance(m, list):
            if len(m) != 1:
                # multi-sheet manifests are uncommon; expose the first + a note.
                pass
            return m[0] if m else {}
        return m


@dataclass
class RenderOutput:
    """Everything a target published into one directory."""

    root: Path
    sheets: Dict[str, SheetView] = field(default_factory=dict)
    actors: Dict[str, Any] = field(default_factory=dict)
    portrait_manifests: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, int] = field(default_factory=dict)  # relpath -> size
    parse_errors: Dict[str, str] = field(default_factory=dict)


def _load_image(path: Path):
    from PIL import Image

    return Image.open(path).convert("RGBA")


def load_render(root: Path) -> RenderOutput:
    """Load every published product under ``root`` for comparison."""
    root = Path(root)
    out = RenderOutput(root=root)
    for f in sorted(root.rglob("*")):
        if f.is_file():
            out.files[str(f.relative_to(root))] = f.stat().st_size

    for ron in sorted(root.rglob("*_spritesheet.ron")):
        stem = ron.name[: -len("_spritesheet.ron")]
        try:
            manifest = parse_ron(ron.read_text())
        except RonError as exc:
            out.parse_errors[ron.name] = str(exc)
            continue
        pages: Dict[int, Any] = {}
        # page 0 is `<stem>_spritesheet.png`; page N is `<stem>_spritesheet.N.png`.
        p0 = ron.with_name(f"{stem}_spritesheet.png")
        if p0.exists():
            pages[0] = _load_image(p0)
        for extra in sorted(root.glob(f"{stem}_spritesheet.*.png")):
            digits = extra.name[len(f"{stem}_spritesheet.") : -len(".png")]
            if digits.isdigit():
                pages[int(digits)] = _load_image(extra)
        out.sheets[stem] = SheetView(stem=stem, manifest=manifest, pages=pages)

    for actor in sorted(root.rglob("*_actor.ron")):
        stem = actor.name[: -len("_actor.ron")]
        try:
            out.actors[stem] = parse_ron(actor.read_text())
        except RonError as exc:
            out.parse_errors[actor.name] = str(exc)

    for portrait in sorted(root.rglob("*_portraits.ron")):
        stem = portrait.name[: -len("_portraits.ron")]
        try:
            out.portrait_manifests[stem] = parse_ron(portrait.read_text())
        except RonError as exc:
            out.parse_errors[portrait.name] = str(exc)
    return out


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

EXACT = "exact-pixels"
RASTER = "raster-equivalent"
CONTRACT = "contract-match"
DIFFERS = "differs"
_ORDER = {EXACT: 0, RASTER: 1, CONTRACT: 2, DIFFERS: 3}


@dataclass
class DimensionResult:
    name: str
    ok: bool
    detail: str
    diffs: List[str] = field(default_factory=list)


@dataclass
class PixelStat:
    animation: str
    frame: int
    status: str            # exact | raster-equivalent | differs | size-mismatch
    max_channel_delta: int
    frac_changed: float
    note: str = ""


@dataclass
class EquivalenceReport:
    verdict: str
    dimensions: List[DimensionResult] = field(default_factory=list)
    pixels: List[PixelStat] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def structural_ok(self) -> bool:
        """True when every non-pixel dimension matches (a valid contract)."""
        return all(d.ok for d in self.dimensions if d.name != "pixels")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "structural_ok": self.structural_ok,
            "dimensions": [
                {"name": d.name, "ok": d.ok, "detail": d.detail, "diffs": d.diffs}
                for d in self.dimensions
            ],
            "pixels": [
                {
                    "animation": p.animation,
                    "frame": p.frame,
                    "status": p.status,
                    "max_channel_delta": p.max_channel_delta,
                    "frac_changed": round(p.frac_changed, 6),
                    "note": p.note,
                }
                for p in self.pixels
            ],
            "notes": self.notes,
        }


def _rows_by_anim(sheet: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row.get("animation"): row for row in sheet.get("rows", [])}


def _deep_diffs(ref: Any, cand: Any, path: str, out: List[str], *, float_tol: float = 0.0) -> None:
    if isinstance(ref, dict) and isinstance(cand, dict):
        for k in sorted(set(ref) | set(cand)):
            if k not in ref:
                out.append(f"{path}.{k}: added ({cand[k]!r})")
            elif k not in cand:
                out.append(f"{path}.{k}: removed (was {ref[k]!r})")
            else:
                _deep_diffs(ref[k], cand[k], f"{path}.{k}", out, float_tol=float_tol)
    elif isinstance(ref, list) and isinstance(cand, list):
        if len(ref) != len(cand):
            out.append(f"{path}: length {len(ref)} -> {len(cand)}")
        for idx, (a, b) in enumerate(zip(ref, cand)):
            _deep_diffs(a, b, f"{path}[{idx}]", out, float_tol=float_tol)
    elif isinstance(ref, (int, float)) and isinstance(cand, (int, float)):
        if abs(float(ref) - float(cand)) > float_tol:
            out.append(f"{path}: {ref!r} -> {cand!r}")
    else:
        if ref != cand:
            out.append(f"{path}: {ref!r} -> {cand!r}")


def _compare_layout(ref: Dict[str, Any], cand: Dict[str, Any]) -> DimensionResult:
    keys = ["frame_width", "frame_height", "label_width", "tuning"]
    diffs: List[str] = []
    for k in keys:
        _deep_diffs(ref.get(k), cand.get(k), k, diffs)
    return DimensionResult("layout", not diffs, "sheet frame geometry + tuning", diffs)


def _compare_animations(ref: Dict[str, Any], cand: Dict[str, Any]) -> DimensionResult:
    ra, ca = _rows_by_anim(ref), _rows_by_anim(cand)
    diffs: List[str] = []
    if set(ra) != set(ca):
        only_ref = sorted(set(ra) - set(ca))
        only_cand = sorted(set(ca) - set(ra))
        if only_ref:
            diffs.append(f"animations only in reference: {only_ref}")
        if only_cand:
            diffs.append(f"animations only in candidate: {only_cand}")
    for name in sorted(set(ra) & set(ca)):
        for k in ("frame_count", "duration_ms", "row_index"):
            if ra[name].get(k) != ca[name].get(k):
                diffs.append(f"{name}.{k}: {ra[name].get(k)} -> {ca[name].get(k)}")
        # page assignment per frame (rect geometry itself is a pixel-layout
        # concern, but a frame jumping pages breaks addressing).
        rp = [r.get("page") for r in ra[name].get("rects", [])]
        cp = [r.get("page") for r in ca[name].get("rects", [])]
        if rp != cp:
            diffs.append(f"{name}.rect page assignment differs")
    return DimensionResult("animations", not diffs, "names, frame counts, durations", diffs)


def _compare_geometry(ref: RenderOutput, cand: RenderOutput, stem: str) -> DimensionResult:
    diffs: List[str] = []
    rs = ref.sheets[stem].sheet()
    cs = cand.sheets[stem].sheet()
    _deep_diffs(rs.get("body_metrics"), cs.get("body_metrics"), "body_metrics", diffs, float_tol=0.5)
    ra = ref.actors.get(stem, {})
    ca = cand.actors.get(stem, {})
    for k in ("body",):
        _deep_diffs(_get(ra, k), _get(ca, k), f"actor.{k}", diffs, float_tol=0.5)
    return DimensionResult("geometry", not diffs, "body bbox, feet, collision/hurtbox", diffs)


def _get(obj: Any, key: str) -> Any:
    return obj.get(key) if isinstance(obj, dict) else None


def _compare_metadata(ref: RenderOutput, cand: RenderOutput, stem: str) -> DimensionResult:
    diffs: List[str] = []
    ra = ref.actors.get(stem, {})
    ca = cand.actors.get(stem, {})
    for k in ("sockets", "capabilities", "animation_bindings", "tags", "brain", "actions"):
        _deep_diffs(_get(ra, k), _get(ca, k), f"actor.{k}", diffs, float_tol=0.5)
    return DimensionResult("metadata", not diffs, "sockets, capabilities, bindings, tags", diffs)


def _compare_portraits(ref: RenderOutput, cand: RenderOutput) -> DimensionResult:
    diffs: List[str] = []
    if set(ref.portrait_manifests) != set(cand.portrait_manifests):
        diffs.append(
            f"portrait manifests: {sorted(ref.portrait_manifests)} -> "
            f"{sorted(cand.portrait_manifests)}"
        )
    for stem in sorted(set(ref.portrait_manifests) & set(cand.portrait_manifests)):
        rc = _clip_names(ref.portrait_manifests[stem])
        cc = _clip_names(cand.portrait_manifests[stem])
        if rc != cc:
            diffs.append(f"{stem} portrait clips: {sorted(rc)} -> {sorted(cc)}")
    return DimensionResult("portraits", not diffs, "portrait products + named clips", diffs)


def _clip_names(manifest: Any) -> set:
    """Best-effort extraction of portrait clip names from a portrait manifest."""
    names: set = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            clips = node.get("clips")
            if isinstance(clips, dict):
                names.update(clips.keys())
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(manifest)
    return names


def _crop(sheetview: SheetView, rect: Dict[str, Any]):
    page = sheetview.pages.get(rect.get("page", 0))
    if page is None:
        return None
    x, y, w, h = rect.get("x"), rect.get("y"), rect.get("w"), rect.get("h")
    return page.crop((x, y, x + w, y + h))


def _compare_pixels(
    ref: RenderOutput,
    cand: RenderOutput,
    stem: str,
    *,
    edge_tol: int,
    area_tol: float,
) -> Tuple[DimensionResult, List[PixelStat]]:
    stats: List[PixelStat] = []
    rs = ref.sheets[stem]
    cs = cand.sheets[stem]
    ra = _rows_by_anim(rs.sheet())
    ca = _rows_by_anim(cs.sheet())
    for name in sorted(set(ra) & set(ca)):
        r_rects = ra[name].get("rects", [])
        c_rects = ca[name].get("rects", [])
        for idx in range(min(len(r_rects), len(c_rects))):
            ri = _crop(rs, r_rects[idx])
            ci = _crop(cs, c_rects[idx])
            if ri is None or ci is None:
                stats.append(PixelStat(name, idx, "differs", 255, 1.0, "missing page"))
                continue
            if ri.size != ci.size:
                stats.append(PixelStat(name, idx, "size-mismatch", 255, 1.0,
                                       f"{ri.size} vs {ci.size}"))
                continue
            max_delta, frac = _pixel_delta(ri, ci)
            if max_delta == 0:
                status = "exact"
            elif max_delta <= edge_tol and frac <= area_tol:
                status = "raster-equivalent"
            else:
                status = "differs"
            stats.append(PixelStat(name, idx, status, max_delta, frac))

    if not stats:
        return DimensionResult("pixels", True, "no comparable frames", []), stats
    worst = max((_pixel_rank(p.status) for p in stats), default=0)
    n_diff = sum(1 for p in stats if p.status in ("differs", "size-mismatch"))
    n_raster = sum(1 for p in stats if p.status == "raster-equivalent")
    detail = f"{len(stats)} frames: {len(stats)-n_diff-n_raster} exact, " \
             f"{n_raster} raster-equiv, {n_diff} differ"
    ok = worst == 0  # only "ok" (byte-exact) when every frame is exact
    return DimensionResult("pixels", ok, detail, []), stats


def _pixel_rank(status: str) -> int:
    return {"exact": 0, "raster-equivalent": 1, "differs": 2, "size-mismatch": 2}.get(status, 2)


def _pixel_delta(a, b) -> Tuple[int, float]:
    """Return (max per-channel delta, fraction of pixels that changed at all).

    Works band-by-band on purpose: ``Image.getbbox()`` defaults to
    ``alpha_only=True`` on RGBA and would ignore pure colour changes, and an
    ``L`` conversion drops the alpha band — so a translucency-only or
    colour-only change must be caught by inspecting every band directly.
    """
    from PIL import ImageChops

    diff = ImageChops.difference(a, b)
    bands = diff.split()
    max_delta = max((band.getextrema()[1] for band in bands), default=0)
    if max_delta == 0:
        return 0, 0.0
    # Per-pixel max across all bands, so any changed channel marks the pixel.
    merged = bands[0]
    for band in bands[1:]:
        merged = ImageChops.lighter(merged, band)
    changed = sum(merged.histogram()[1:])
    total = a.size[0] * a.size[1]
    return int(max_delta), (changed / total if total else 0.0)


def compare_renders(
    ref: RenderOutput,
    cand: RenderOutput,
    *,
    edge_tol: int = 6,
    area_tol: float = 0.02,
) -> EquivalenceReport:
    """Compare two loaded renders across every published dimension.

    ``edge_tol`` is the max per-channel RGBA delta still considered an
    antialiasing edge difference; ``area_tol`` is the fraction of a frame's
    pixels allowed to change while still calling it raster-equivalent.
    """
    report = EquivalenceReport(verdict=DIFFERS)

    ref_stems = set(ref.sheets)
    cand_stems = set(cand.sheets)
    if ref.parse_errors or cand.parse_errors:
        for src, err in {**ref.parse_errors, **cand.parse_errors}.items():
            report.notes.append(f"parse error in {src}: {err}")
    if ref_stems != cand_stems:
        report.dimensions.append(DimensionResult(
            "targets", False, "sheet set differs",
            [f"reference sheets {sorted(ref_stems)} != candidate {sorted(cand_stems)}"]))
        report.verdict = DIFFERS
        return report

    if not ref_stems:
        report.notes.append("no *_spritesheet.ron found in either render")
        report.verdict = DIFFERS
        return report

    # Compare the primary sheet (single-target case) and fold any extra sheets
    # into the same dimension buckets.
    all_pixels: List[PixelStat] = []
    dims_by_name: Dict[str, DimensionResult] = {}

    def merge(dim: DimensionResult) -> None:
        existing = dims_by_name.get(dim.name)
        if existing is None:
            dims_by_name[dim.name] = dim
        else:
            existing.ok = existing.ok and dim.ok
            existing.diffs.extend(dim.diffs)

    for stem in sorted(ref_stems):
        rs = ref.sheets[stem].sheet()
        cs = cand.sheets[stem].sheet()
        merge(_compare_layout(rs, cs))
        merge(_compare_animations(rs, cs))
        merge(_compare_geometry(ref, cand, stem))
        merge(_compare_metadata(ref, cand, stem))
        pix_dim, stats = _compare_pixels(ref, cand, stem, edge_tol=edge_tol, area_tol=area_tol)
        merge(pix_dim)
        all_pixels.extend(stats)

    merge(_compare_portraits(ref, cand))

    report.dimensions = [dims_by_name[k] for k in
                         ("layout", "animations", "geometry", "metadata", "portraits", "pixels")
                         if k in dims_by_name]
    report.pixels = all_pixels
    report.verdict = _verdict(report, all_pixels)
    return report


def _verdict(report: EquivalenceReport, pixels: List[PixelStat]) -> str:
    if not report.structural_ok:
        return DIFFERS
    if pixels and all(p.status == "exact" for p in pixels):
        return EXACT
    if pixels and all(p.status in ("exact", "raster-equivalent") for p in pixels):
        return RASTER
    # Structure/metadata/geometry all match; pixels differ materially. This is
    # the expected outcome for a redesign that still honours the contract.
    return CONTRACT


# ---------------------------------------------------------------------------
# Human-readable formatting
# ---------------------------------------------------------------------------

def format_report(report: EquivalenceReport, *, ref_label: str, cand_label: str) -> str:
    lines: List[str] = []
    lines.append(f"equivalence: {ref_label}  ->  {cand_label}")
    lines.append(f"  VERDICT: {report.verdict}"
                 f"   (contract {'OK' if report.structural_ok else 'BROKEN'})")
    for d in report.dimensions:
        mark = "ok " if d.ok else "XX "
        lines.append(f"  [{mark}] {d.name:<11} {d.detail}")
        for diff in d.diffs[:20]:
            lines.append(f"           - {diff}")
        if len(d.diffs) > 20:
            lines.append(f"           … +{len(d.diffs) - 20} more")
    if report.pixels:
        worst = [p for p in report.pixels if p.status in ("differs", "size-mismatch")]
        worst.sort(key=lambda p: (-p.max_channel_delta, -p.frac_changed))
        for p in worst[:12]:
            lines.append(f"    pixel {p.animation}#{p.frame}: {p.status} "
                         f"(Δmax={p.max_channel_delta}, changed={p.frac_changed:.1%}) {p.note}")
    for note in report.notes:
        lines.append(f"  note: {note}")
    return "\n".join(lines)


def write_report(report: EquivalenceReport, dest_dir: Path, *,
                 ref_label: str, cand_label: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "equivalence.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True))
    (dest_dir / "equivalence.txt").write_text(
        format_report(report, ref_label=ref_label, cand_label=cand_label))
