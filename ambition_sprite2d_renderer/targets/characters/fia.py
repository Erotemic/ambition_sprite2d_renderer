"""Fia, the town mechanic, touched by the void and embraced by it: one woman,
three looks.

Fia Knoss works under Oiler (``docs/storylines/cannon.md``; her arc:
``docs/brainstorms/the_fia_arc.md``; concept art:
``assets/concept_art/character-concepts/Fia``). The void draws her toward it
and changes her; at its fullest she is its form for a while. The game shows
that as three catalog rows, ``npc_fia``, ``npc_fia_touched`` and
``npc_fia_void``, worn by one body (``CharacterForm``; ``<<transform>>`` in a
conversation).

* Her specs: ``data/characters/fia/fia.chargen.yaml``,
  ``fia_touched.chargen.yaml`` and ``fia_void.chargen.yaml``: the same base,
  seed and body numbers, so the same rig and poses. Her clothes are the
  generator's: fingerless gloves, baggy trousers into chunky boots, a duster
  whose skirt flares. The void's look is the chargen family ``void`` (white
  ink on black).
* Her hand-drawn overlays (``scripts/draw_fia_overlays.py`` draws all three):
  ``fia.overlay.svg`` (the high ponytail that rises and sweeps back in spiky
  locks, the red bandana, freckles and the plaster, the belt over her duster
  with the pouch and the wrench, rolled sleeves); ``fia_touched`` (the void's
  first traces: a white streak in her hair, her hands black and the black
  creeping up her forearms, two of its diamonds); ``fia_void`` (the same in
  black and white, her hair loosed into a white flame bigger than the
  ponytail was, a white diamond where the plaster was, the coat's hem coming
  apart, white diamonds about her).

Each look's sheet has a ``transform`` row: the change INTO that look (the
sheet of the look a body arrives at plays it, ``body::wear``) from the look
before it: Fia to touched, touched to the void, the void back to Fia. It is
drawn from one rig that holds both looks' parts (:func:`hybrid_rig`): each
frame shows each body region in the look it has reached. The void takes her
from the hands (the arm first, as the concept sheets have it), then the
arms, the legs, the body and last the head; leaving, it lets go of the head
first and the hands last.

The change happens inside a swirl of the void (Jon, 2026-11-25: "more like
jeff hinter's transform where it wraps around her, or maybe it sort of
'wooshes' around her like a swirl, almost like cosmic maryo"). Black ribbons
edged in white spiral up from her feet and close on her outline, as Jeff
Hinter's surface does. At their tightest she is all void (:func:`shroud`, as
he is all light at his lock), and her regions change under it. Then the
ribbons unwind up and off her, flinging the void's diamonds, and she stands
in the new look. The swirl is effect layers composited around the hybrid
rig's frame (``rigdoc.composite_layer``): behind her, the shroud over her,
and in front of her.
"""

from __future__ import annotations

import copy
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml
from PIL import Image, ImageDraw, ImageFilter

from ...authoring import rigdoc
from ...chargen.overlay import path_of as overlay_path
from ...chargen.rig import write_character
from ...chargen.sheets import PUBLISH_ROWS, RiggedCharacter, actor_metadata
from ...chargen.spec import CharacterSpec, complete

DATA = Path(__file__).resolve().parents[2] / "data" / "characters" / "fia"

#: The looks: target -> (spec file, catalog id, the look its transform row
#: changes from).
LOOKS: Dict[str, Tuple[str, str, str]] = {
    "fia": ("fia.chargen.yaml", "npc_fia", "fia_void"),
    "fia_touched": ("fia_touched.chargen.yaml", "npc_fia_touched", "fia"),
    "fia_void": ("fia_void.chargen.yaml", "npc_fia_void", "fia_touched"),
}
NAMES = {"fia": "Fia", "fia_touched": "Fia (touched)", "fia_void": "Fia (void)"}

#: The body regions in the order the void takes them; it gives them back in
#: the reverse order.
REGIONS = ("hands", "arms", "legs", "body", "head")
TRANSFORM_FRAMES = 18
TRANSFORM_FRAME_MS = 75
#: The span of the row (0..1) over which her regions change, one after
#: another, under the swirl at its tightest.
CHANGE_SPAN = (0.3, 0.62)
#: How much swirl each change has: the void's first touch is a gust, its
#: embrace a whirlwind, and its letting go between the two.
SWIRL_STRENGTH = {"fia_touched": 0.6, "fia_void": 1.0, "fia": 0.85}
#: The view and pose the change is drawn in: her idle's.
TRANSFORM_VIEW = "front_3q"
TRANSFORM_POSE = "idle"

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SOURCE_PREFIX = "src-"


def load_spec(target: str) -> CharacterSpec:
    return complete(yaml.safe_load((DATA / LOOKS[target][0]).read_text(encoding="utf8")))


def region_of(part: str) -> str:
    """The body region a rig part belongs to (:data:`REGIONS`)."""
    if part.startswith(("hair", "head", "face", "neck_upper")):
        return "head"
    if "_hand" in part or "_arm_l" in part or "_grip" in part:
        return "hands"
    if "_arm_u" in part:
        return "arms"
    if "_leg" in part or "_foot" in part or "_skirt" in part:
        return "legs"
    return "body"


def _merged_svg(dst_svg: Path, src_svg: Path, view: str, out: Path) -> Path:
    """``dst_svg`` with the source look's parts of ``view`` added to the same
    view cell, their ids prefixed :data:`SOURCE_PREFIX`. Both looks lay their
    cells out alike (the same views, the same cell width), so a source part
    lands where it is drawn in its own file."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("inkscape", INKSCAPE_NS)
    dst, src = ET.parse(dst_svg), ET.parse(src_svg)
    cell_id = f"view-{view}"
    dst_cell = next(el for el in dst.iter(f"{{{SVG_NS}}}g") if el.get("id") == cell_id)
    src_cell = next(el for el in src.iter(f"{{{SVG_NS}}}g") if el.get("id") == cell_id)
    for child in list(src_cell):
        child = copy.deepcopy(child)
        for el in child.iter():
            if el.get("id"):
                el.set("id", SOURCE_PREFIX + el.get("id"))
        dst_cell.append(child)
    dst.write(out, encoding="utf-8", xml_declaration=True)
    return out


def hybrid_rig(src_rig: Path, dst_rig: Path, view_key: str, out_dir: Path) -> Path:
    """One rig of a view with both looks' parts: the arriving look's parts
    tagged ``to:<region>``, the leaving look's tagged ``from:<region>`` (and
    named ``src__<part>``). A frame chooses, region by region, which shows
    (the rig's ``features``). Both rigs come from specs with the same body,
    so their bones, pivots and clips are one."""
    src, dst = json.loads(src_rig.read_text()), json.loads(dst_rig.read_text())
    if [b["name"] for b in src["bones"]] != [b["name"] for b in dst["bones"]]:
        raise ValueError(f"{src_rig.name} and {dst_rig.name} have different bones: the looks must share a body")
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = _merged_svg(dst_rig.parent / dst["svg_source"]["path"], src_rig.parent / src["svg_source"]["path"], view_key,
                      out_dir / f"{dst_rig.stem}.transform.svg")
    doc = copy.deepcopy(dst)
    doc["svg_source"] = dict(dst["svg_source"], path=svg.name)
    parts = []
    for part in dst["parts"]:
        parts.append(dict(part, feature=f"to:{region_of(part['name'])}"))
    for part in src["parts"]:
        parts.append(dict(part, name=f"src__{part['name']}", include=[SOURCE_PREFIX + i for i in part.get("include", [])],
                          feature=f"from:{region_of(part['name'])}"))
    doc["parts"] = parts
    doc["features"] = {}
    path = out_dir / f"{dst_rig.stem}.transform.rig.json"
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    return path


def stage_features(changed: int, order: Sequence[str]) -> Dict[str, bool]:
    """The rig features of a transform frame in which the first ``changed``
    regions of ``order`` show the arriving look."""
    done = set(order[:changed])
    out = {}
    for region in REGIONS:
        out[f"to:{region}"] = region in done
        out[f"from:{region}"] = region not in done
    return out


def _ramp(u: float, a: float, b: float) -> float:
    """0 before ``a``, 1 after ``b``, smooth between."""
    t = max(0.0, min(1.0, (u - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def changed_regions(u: float) -> int:
    """How many regions show the arriving look at ``u`` of the row."""
    return round(5 * _ramp(u, *CHANGE_SPAN))


#: Swirl colours: the void's black, edged in its white.
SWIRL_CORE = (14, 14, 17, 255)
SWIRL_RIM = (244, 244, 244, 255)
#: The swirl is painted this many times larger and reduced, for clean edges.
SUPERSAMPLE = 3


class Silhouette:
    """Her outline in a frame: the middle of her and her half width at each
    row, so the swirl can wrap her shape (Jeff Hinter's surface is fitted to
    his outline the same way)."""

    def __init__(self, frame: Image.Image) -> None:
        alpha = frame.getchannel("A").point(lambda a: 255 if a > 40 else 0)
        self.mask = alpha
        x0, y0, x1, y1 = alpha.getbbox()
        self.top, self.bottom, self.height = y0, y1, y1 - y0
        w = alpha.width
        data = alpha.tobytes()
        cols = [x for y in range(y0, y1) for x in range(x0, x1) if data[y * w + x]]
        cols.sort()
        self.cx = cols[len(cols) // 2]
        half = []
        for y in range(y0, y1):
            row = data[y * w + x0:y * w + x1]
            xs = [x0 + i for i, a in enumerate(row) if a]
            half.append(max(abs(xs[0] - self.cx), abs(xs[-1] - self.cx)) if xs else 0)
        # The widest of the rows near each row: a ribbon passes outside a
        # hand or a hem as well as the waist beside it.
        win = max(1, self.height // 20)
        self.half = [max(half[max(0, i - win):i + win + 1]) for i in range(len(half))]

    def half_at(self, y: float) -> float:
        i = int(round(y - self.top))
        return float(self.half[max(0, min(len(self.half) - 1, i))])


def _ribbon_runs(sil: Silhouette, u: float, strength: float, phase: float):
    """One ribbon of the swirl at ``u``: runs of (points, widths, in front)
    along a helix that rises up her, closes on her outline, spins, and at the
    end unwinds outward and up and is gone."""
    H = sil.height
    rise = _ramp(u, 0.02, 0.42)  # how far up her the ribbon has climbed
    close = _ramp(u, 0.05, 0.4)  # how near her outline it is
    leave = _ramp(u, 0.62, 0.9)  # it lets go of her and flies off, from her feet up
    spin = 2.0 * math.pi * (3.4 * u + 2.2 * u * u)
    turns = 1.7
    appear = _ramp(u, 0.0, 0.16)  # the first frame is her as she was
    thick = H * (0.022 + 0.022 * strength) * (1.0 - leave) * appear
    pad = H * (0.16 * (1.0 - close) + 0.015 + 0.12 * leave)
    lift = H * 0.3 * leave
    span = 0.25 + 0.75 * rise
    points, widths, fronts = [], [], []
    m = 72
    for j in range(m + 1):
        s = j / m
        # The ribbon runs from its tail low on her to its head up at its reach.
        h = span * (leave + (1.0 - leave) * s)
        y = sil.bottom - h * H * 1.02 - lift
        theta = phase + spin + turns * 2.0 * math.pi * s
        r = sil.half_at(y) + pad
        x = sil.cx + r * math.sin(theta)
        y += r * 0.24 * math.cos(theta)
        taper = math.sin(math.pi * min(1.0, s * 1.15)) ** 0.7 if s * 1.15 < 1.0 else max(0.0, 1.0 - (s * 1.15 - 1.0) * 6)
        points.append((x, y))
        widths.append(thick * max(0.0, taper))
        fronts.append(math.cos(theta) > 0.0)
    runs, cur = [], [0]
    for j in range(1, m + 1):
        if fronts[j] != fronts[cur[-1]]:
            cur.append(j)  # the run ends where it turns, overlapping by one
            runs.append(cur)
            cur = [j]
        else:
            cur.append(j)
    runs.append(cur)
    return [([points[j] for j in run], [widths[j] for j in run], fronts[run[len(run) // 2]]) for run in runs if len(run) > 1]


def _band(points, widths, grow: float, k: float):
    """The outline of a ribbon of ``widths`` along ``points``, ``grow`` wider
    each side, scaled ``k``."""
    left, right = [], []
    for j, (x, y) in enumerate(points):
        a, b = points[max(0, j - 1)], points[min(len(points) - 1, j + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        w = widths[j] / 2 + min(grow, widths[j] * 0.35)
        left.append(((x + nx * w) * k, (y + ny * w) * k))
        right.append(((x - nx * w) * k, (y - ny * w) * k))
    return left + right[::-1]


def _diamond(draw, x: float, y: float, r: float, k: float, fill) -> None:
    draw.polygon([((x) * k, (y - r) * k), ((x + r * 0.62) * k, y * k), (x * k, (y + r) * k), ((x - r * 0.62) * k, y * k)], fill=fill)


def swirl_layers(sil: Silhouette, size: Tuple[int, int], u: float, strength: float) -> Tuple[Image.Image, Image.Image]:
    """The swirl at ``u``: what passes behind her and what passes in front."""
    k = SUPERSAMPLE
    big = (size[0] * k, size[1] * k)
    back, front = Image.new("RGBA", big, (0, 0, 0, 0)), Image.new("RGBA", big, (0, 0, 0, 0))
    db, df = ImageDraw.Draw(back), ImageDraw.Draw(front)
    rim = max(1.0, sil.height * 0.006)
    ribbons = 3 if strength >= 0.8 else 2
    runs = []
    for r in range(ribbons):
        runs += _ribbon_runs(sil, u, strength, 2.0 * math.pi * r / ribbons)
    # A ribbon thinner than a pixel is gone (an empty band still rasterizes
    # as a hairline).
    runs = [run for run in runs if max(run[1]) >= 0.5]
    # Rims first, then cores, layer by layer: a ribbon crossing another in
    # the same layer reads as one band of black edged in white.
    for draw, front_layer in ((db, False), (df, True)):
        for pts, ws, f in runs:
            if f == front_layer:
                draw.polygon(_band(pts, ws, rim, k), fill=SWIRL_RIM)
        for pts, ws, f in runs:
            if f == front_layer:
                draw.polygon(_band(pts, ws, 0.0, k), fill=SWIRL_CORE)
    # The void's diamonds ride the heads of the ribbons, and are flung off
    # when it lets go.
    leave = _ramp(u, 0.62, 0.9)
    if 0.08 < u < 0.9:
        n_d = 4 + int(4 * strength)
        for i in range(n_d):
            a = 2.0 * math.pi * (i / n_d) + 2.0 * math.pi * 2.6 * u
            h = sil.top + sil.height * (0.15 + 0.7 * ((i * 0.618) % 1.0))
            r = sil.half_at(h) + sil.height * (0.06 + 0.25 * leave + 0.12 * (1.0 - _ramp(u, 0.05, 0.4)))
            x, y = sil.cx + r * math.sin(a), h + r * 0.24 * math.cos(a) - sil.height * 0.3 * leave
            size_d = sil.height * (0.018 + 0.01 * ((i * 0.37) % 1.0)) * (1.0 - leave)
            _diamond(df if math.cos(a) > 0 else db, x, y, size_d + rim, k, SWIRL_CORE)
            _diamond(df if math.cos(a) > 0 else db, x, y, size_d, k, SWIRL_RIM)
    return back.resize(size, Image.LANCZOS), front.resize(size, Image.LANCZOS)


def shroud(sil: Silhouette, frame: Image.Image, amount: float) -> Image.Image:
    """Her outline filled with the void's black and edged in white, at
    ``amount``: at the swirl's tightest she is all of it, as Jeff Hinter is
    all light at his lock, and her look changes under it."""
    rim = max(2, int(sil.height * 0.01) | 1)
    alpha = frame.getchannel("A")
    grown = alpha.filter(ImageFilter.MaxFilter(rim))
    out = Image.new("RGBA", frame.size, SWIRL_RIM[:3] + (0,))
    out.putalpha(grown.point(lambda a: int(a * amount)))
    core = Image.new("RGBA", frame.size, SWIRL_CORE[:3] + (0,))
    core.putalpha(alpha.filter(ImageFilter.MinFilter(rim)).point(lambda a: int(a * amount)))
    out.alpha_composite(core)
    return out


class FiaSheet(RiggedCharacter):
    """Her rigs as sheet rows, and the ``transform`` row: the hybrid rig
    under a swirl of the void (:func:`swirl_layers`)."""

    def __init__(self, rigs: Dict[str, Path], rows: Sequence[str], transform_rig: Path, order: Sequence[str],
                 target: str = "fia_void") -> None:
        super().__init__(rigs, rows)
        from ...authoring.rigdoc import RigDocument

        self.transform = RigDocument.load(transform_rig)
        self.order = tuple(order)
        self.strength = SWIRL_STRENGTH.get(target, 1.0)
        self._sil: Dict[int, Silhouette] = {}

    def rows(self) -> List[Tuple[str, int, int]]:
        return super().rows() + [("transform", TRANSFORM_FRAMES, TRANSFORM_FRAME_MS)]

    def _body(self, changed: int) -> Image.Image:
        self.transform.data["features"] = stage_features(changed, self.order)
        pose = self.transform.clips[TRANSFORM_POSE]
        return self.transform.render_frame(TRANSFORM_POSE, 0, int(pose["frames"]))

    def render_frame(self, animation: str, frame_idx: int, frame_count: int):
        if animation != "transform":
            return super().render_frame(animation, frame_idx, frame_count)
        u = (frame_idx % TRANSFORM_FRAMES) / (TRANSFORM_FRAMES - 1)
        changed = changed_regions(u)
        body = self._body(changed)
        if changed not in self._sil:
            self._sil[changed] = Silhouette(body)
        sil = self._sil[changed]
        back, front = swirl_layers(sil, body.size, u, self.strength)
        canvas = Image.new("RGBA", body.size, (0, 0, 0, 0))
        rigdoc.composite_layer(canvas, back, (0, 0), name="swirl_back")
        rigdoc.composite_canvas(canvas, body, (0, 0))
        amount = self.strength * 0.92 * min(_ramp(u, 0.26, 0.4), 1.0 - _ramp(u, 0.56, 0.7))
        if amount > 0.01:
            rigdoc.composite_layer(canvas, shroud(sil, body, amount), (0, 0), name="swirl_shroud")
        rigdoc.composite_layer(canvas, front, (0, 0), name="swirl_front")
        return canvas


def _metadata(target: str) -> dict:
    spec = load_spec(target)
    character_id = LOOKS[target][1]
    meta = actor_metadata(spec, character_id=character_id, description=DESCRIPTIONS[target])
    meta["actor"]["display_name"] = NAMES[target]
    meta["body"]["traits"] = ["humanoid", "story", "generated"] + (["void"] if target != "fia" else [])
    meta["tags"] = meta["body"]["traits"] + ["svg_rigged"]
    meta["visual"]["canonical_source"] = f"ambition_sprite2d_renderer/data/characters/fia/{LOOKS[target][0]}"
    meta["animation_bindings"]["ability.transform"] = {"animation": "transform", "events": []}
    return meta


DESCRIPTIONS = {
    "fia": ("Fia Knoss, the town mechanic who works under Oiler: freckled, a plaster on her cheek, dark hair "
            "in a big high ponytail that sweeps back in spiky locks, under a red bandana; a canvas duster with its sleeves "
            "rolled to the elbow and its skirt flaring, a belt over it with a tool pouch and a wrench whose slot glows, "
            "fingerless leather gloves, baggy trousers into chunky work boots. No goggles. One of the first people to "
            "treat the player with kindness."),
    "fia_touched": ("Fia with the void's first traces on her: a white streak in her hair, her hands gone black and the "
                    "black creeping up her forearms, two small white diamonds near her. More power, subtle changes."),
    "fia_void": ("Fia embraced by the void: the same woman drawn in the void's black and white. Her skin and clothes "
                 "are black edged in white, her hair is white with one black streak and rises like flame, her eyes are "
                 "white, a white diamond marks her cheek, her coat comes apart at the hem, and white diamonds drift about "
                 "her. A temporary, dangerous state of great power."),
}


#: The rigs written in this process, by look and output directory.
_RIGS: Dict[Tuple[str, str], Dict[str, Path]] = {}


def _rigs(target: str, out_dir: Path) -> Dict[str, Path]:
    key = (target, str(out_dir))
    rigs = _RIGS.get(key)
    if rigs is None or not all(Path(p).is_file() for p in rigs.values()):
        rigs = write_character(load_spec(target), out_dir).rigs
        _RIGS[key] = rigs
    return rigs


def _make(target: str):
    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        from ...authoring.part_flipbook import publish_rig_flipbook
        from ...authoring.sheet_build import build_sheet

        out_dir = Path(out_dir)
        other = LOOKS[target][2]
        rigs = _rigs(target, out_dir)
        other_rigs = _rigs(other, out_dir / f"_{other}_rigs")
        transform_rig = hybrid_rig(other_rigs[TRANSFORM_VIEW], rigs[TRANSFORM_VIEW], TRANSFORM_VIEW, out_dir / "_transform")
        # The void takes her from the hands; giving her back, it lets go of the head first.
        order = tuple(reversed(REGIONS)) if target == "fia" else REGIONS
        sheet = FiaSheet(rigs, PUBLISH_ROWS, transform_rig, order, target)
        frame_transform: dict = {}
        outputs = build_sheet(
            parts=True,
            frame_transform_out=frame_transform,
            target=target,
            rows=sheet.rows(),
            render_fn=sheet.render_frame,
            out_dir=out_dir,
            frame_size=sheet.frame_size(),
            auto_crop=True,
            crop_margin=4,
            actor_metadata=_metadata(target),
            sheet_tuning={"collision_scale": 1.7},
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        parts = publish_rig_flipbook(target, sheet.rows(), sheet.render_frame, outputs, frame_transform, out_dir)
        return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())

    def render_canonical(out_dir: str | Path, **opts) -> Path:
        from ...authoring.sheet_build import canonical_render_only

        out_dir = Path(out_dir)
        with canonical_render_only():
            render(out_dir, **opts)
        for name in (f"{target}_canonical_transparent.png", f"{target}_canonical.png"):
            if (out_dir / name).is_file():
                return out_dir / name
        raise FileNotFoundError(f"{target}: the canonical render wrote no canonical image in {out_dir}")

    return {"render": render, "render_canonical": render_canonical, "actor_metadata": lambda: _metadata(target),
            "data": [DATA / LOOKS[t][0] for t in LOOKS] + [overlay_path(t) for t in LOOKS]}


TARGETS = {target: _make(target) for target in LOOKS}

__all__ = ["LOOKS", "REGIONS", "TARGETS", "TRANSFORM_FRAMES", "FiaSheet", "hybrid_rig", "load_spec", "region_of", "stage_features"]
