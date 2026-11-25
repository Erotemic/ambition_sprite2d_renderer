"""Fia, the town mechanic, and Fia embraced by the void: one woman, two looks.

Faith "Fia" Knoss works under Oiler (``docs/storylines/cannon.md``; her arc:
``docs/brainstorms/the_fia_arc.md``; concept art:
``assets/concept_art/character-concepts/Fia``). The void draws her toward it
and changes her; at its fullest she is its form for a while. The game shows
that as two catalog rows, ``npc_fia`` and ``npc_fia_void``, worn by one body
(``CharacterForm``; ``<<transform>>`` in a conversation).

* Her specs: ``data/characters/fia/fia.chargen.yaml`` and
  ``fia_void.chargen.yaml``: the same base, seed and body numbers, so the same
  rig and poses. The void's look is the chargen family ``void`` (white ink on
  black).
* Her hand-drawn overlays: ``data/overlays/fia.overlay.svg`` (her hair, the
  white streak and the red bandana, freckles and the plaster, the belt over
  her duster with the pouch and the wrench, rolled sleeves and wrist cuffs)
  and ``fia_void.overlay.svg`` (the same in black and white, her hair loose
  and rising like flame, a white diamond where the plaster was, the hem of
  the coat coming apart, white diamonds about her).

Each look's sheet has a ``transform`` row: the change INTO that look (the
sheet of the look a body arrives at plays it, ``body::wear``). It is drawn
from one rig that holds both looks' parts (:func:`hybrid_rig`): each frame
shows each body region in the look it has reached. The void takes her from
the hands (the arm first, as the concept sheets have it), then the arms, the
legs, the body and last the head; leaving, it lets go of the head first and
the hands last.
"""

from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml

from ...chargen.overlay import path_of as overlay_path
from ...chargen.rig import write_character
from ...chargen.sheets import PUBLISH_ROWS, RiggedCharacter, actor_metadata
from ...chargen.spec import CharacterSpec, complete

DATA = Path(__file__).resolve().parents[2] / "data" / "characters" / "fia"

#: The two looks: target -> (spec file, catalog id, the other look).
LOOKS: Dict[str, Tuple[str, str, str]] = {
    "fia": ("fia.chargen.yaml", "npc_fia", "fia_void"),
    "fia_void": ("fia_void.chargen.yaml", "npc_fia_void", "fia"),
}

#: The body regions in the order the void takes them; it gives them back in
#: the reverse order.
REGIONS = ("hands", "arms", "legs", "body", "head")
#: How many regions have changed, frame by frame: a beat as she was, one
#: region a frame, and a hold on the look she arrives at.
TRANSFORM_STAGES = (0, 1, 2, 3, 4, 5, 5, 5)
TRANSFORM_FRAME_MS = 100
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


class FiaSheet(RiggedCharacter):
    """Her rigs as sheet rows, and the ``transform`` row from the hybrid rig."""

    def __init__(self, rigs: Dict[str, Path], rows: Sequence[str], transform_rig: Path, order: Sequence[str]) -> None:
        super().__init__(rigs, rows)
        from ...authoring.rigdoc import RigDocument

        self.transform = RigDocument.load(transform_rig)
        self.order = tuple(order)

    def rows(self) -> List[Tuple[str, int, int]]:
        return super().rows() + [("transform", len(TRANSFORM_STAGES), TRANSFORM_FRAME_MS)]

    def render_frame(self, animation: str, frame_idx: int, frame_count: int):
        if animation != "transform":
            return super().render_frame(animation, frame_idx, frame_count)
        self.transform.data["features"] = stage_features(TRANSFORM_STAGES[frame_idx % len(TRANSFORM_STAGES)], self.order)
        pose = self.transform.clips[TRANSFORM_POSE]
        return self.transform.render_frame(TRANSFORM_POSE, 0, int(pose["frames"]))


def _metadata(target: str) -> dict:
    spec = load_spec(target)
    character_id = LOOKS[target][1]
    meta = actor_metadata(spec, character_id=character_id, description=DESCRIPTIONS[target])
    meta["actor"]["display_name"] = "Fia" if target == "fia" else "Fia (void)"
    meta["body"]["traits"] = ["humanoid", "story", "generated"] + (["void"] if target == "fia_void" else [])
    meta["tags"] = meta["body"]["traits"] + ["svg_rigged"]
    meta["visual"]["canonical_source"] = f"ambition_sprite2d_renderer/data/characters/fia/{LOOKS[target][0]}"
    meta["animation_bindings"]["ability.transform"] = {"animation": "transform", "events": []}
    return meta


DESCRIPTIONS = {
    "fia": ("Faith \"Fia\" Knoss, the town mechanic who works under Oiler: freckled, a plaster on her cheek, dark hair "
            "with one white streak in a messy high ponytail under a red bandana, a canvas duster with its sleeves rolled "
            "to the elbow, a belt over it with a tool pouch and a wrench whose slot glows. No goggles. One of the first "
            "people to treat the player with kindness."),
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
        order = REGIONS if target == "fia_void" else tuple(reversed(REGIONS))
        sheet = FiaSheet(rigs, PUBLISH_ROWS, transform_rig, order)
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

__all__ = ["LOOKS", "REGIONS", "TARGETS", "TRANSFORM_STAGES", "FiaSheet", "hybrid_rig", "load_spec", "region_of", "stage_features"]
