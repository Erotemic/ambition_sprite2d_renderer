#!/usr/bin/env python3
"""Generate Madam LeBlanc's rigged SVG art and refresh her rig documents.

This is a code-first redesign that moves the character onto the same direct-SVG
multiview pipeline used by Oiler/PCA-style rigs.  The editable source of truth
is still an SVG, but this script *builds* that SVG from structured Python so we
can iterate on silhouette, dress construction, and rig layering without any
image-generation tooling.

Usage::

    uv run python scripts/build_m_leblanc_rig.py build
    uv run python scripts/build_m_leblanc_rig.py build --fresh
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
    merge_generated_geometry,
)

SVG = ROOT / "ambition_sprite2d_renderer/data/characters/m_leblanc/m_leblanc-multiview.svg"
RIG_DIR = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/m_leblanc"

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INK_NS)
ET.register_namespace("sodipodi", SODIPODI_NS)

OUTLINE = "#17120e"
DRESS = "#f6f1e8"
DRESS_SHADE = "#e7ddd0"
RIBBON = "#4f8f60"
RIBBON_DARK = "#356042"
HAIR = "#5c4336"
HAIR_DARK = "#3d2a20"
SKIN = "#efc9ae"
CHEEK = "#d89a90"
STOCKING = "#ece7df"
SHOE = "#293238"
HAT_SHADOW = "#c9c0b4"

VIEWS = {
    "three_quarter": HumanoidViewSpec(
        view="Madam LeBlanc - Three Quarter",
        name="m_leblanc_three_quarter",
        target_height=105.0,
        collision_scale=1.70,
    ),
}


def fmt(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def pts(points: Sequence[tuple[float, float]]) -> str:
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)


def el(parent: ET.Element, tag: str, **attrs) -> ET.Element:
    return ET.SubElement(parent, f"{{{SVG_NS}}}{tag}", {k: str(v) for k, v in attrs.items() if v is not None})


def g(parent: ET.Element, gid: str, label: str | None = None, **attrs) -> ET.Element:
    attrib = {"id": gid, **{k: str(v) for k, v in attrs.items() if v is not None}}
    if label is not None:
        attrib[f"{{{INK_NS}}}label"] = label
    return el(parent, "g", **attrib)


def layer(parent: ET.Element, gid: str, label: str) -> ET.Element:
    return g(parent, gid, label=label, **{f"{{{INK_NS}}}groupmode": "layer"})


def path(parent: ET.Element, gid: str, d: str, *, fill: str = "none", stroke: str | None = None,
         stroke_width: float | None = None, linecap: str | None = None,
         linejoin: str | None = None, opacity: float | None = None) -> ET.Element:
    return el(
        parent,
        "path",
        id=gid,
        d=d,
        fill=fill,
        stroke=stroke,
        **({"stroke-width": fmt(stroke_width)} if stroke_width is not None else {}),
        **({"stroke-linecap": linecap} if linecap else {}),
        **({"stroke-linejoin": linejoin} if linejoin else {}),
        **({"opacity": fmt(opacity)} if opacity is not None else {}),
    )


def poly(parent: ET.Element, gid: str, points: Sequence[tuple[float, float]], *, fill: str,
         stroke: str | None = None, stroke_width: float | None = None,
         linejoin: str = "round") -> ET.Element:
    return el(
        parent,
        "polygon",
        id=gid,
        points=pts(points),
        fill=fill,
        stroke=stroke,
        **({"stroke-width": fmt(stroke_width)} if stroke_width is not None else {}),
        **({"stroke-linejoin": linejoin} if stroke else {}),
    )


def circle(parent: ET.Element, gid: str, cx: float, cy: float, r: float, *, fill: str,
           stroke: str | None = None, stroke_width: float | None = None,
           opacity: float | None = None) -> ET.Element:
    return el(
        parent,
        "circle",
        id=gid,
        cx=fmt(cx),
        cy=fmt(cy),
        r=fmt(r),
        fill=fill,
        stroke=stroke,
        **({"stroke-width": fmt(stroke_width)} if stroke_width is not None else {}),
        **({"opacity": fmt(opacity)} if opacity is not None else {}),
    )


def ellipse(parent: ET.Element, gid: str, cx: float, cy: float, rx: float, ry: float, *, fill: str,
            stroke: str | None = None, stroke_width: float | None = None,
            opacity: float | None = None) -> ET.Element:
    return el(
        parent,
        "ellipse",
        id=gid,
        cx=fmt(cx),
        cy=fmt(cy),
        rx=fmt(rx),
        ry=fmt(ry),
        fill=fill,
        stroke=stroke,
        **({"stroke-width": fmt(stroke_width)} if stroke_width is not None else {}),
        **({"opacity": fmt(opacity)} if opacity is not None else {}),
    )


def line(parent: ET.Element, gid: str, x1: float, y1: float, x2: float, y2: float, *, stroke: str,
         stroke_width: float, linecap: str = "round", opacity: float | None = None) -> ET.Element:
    return el(
        parent,
        "line",
        id=gid,
        x1=fmt(x1),
        y1=fmt(y1),
        x2=fmt(x2),
        y2=fmt(y2),
        fill="none",
        stroke=stroke,
        **({"stroke-width": fmt(stroke_width)}),
        **({"stroke-linecap": linecap}),
        **({"opacity": fmt(opacity)} if opacity is not None else {}),
    )


def part(parent: ET.Element, gid: str, label: str, part_name: str, bone: str, z: float,
         opacity_channel: str | None = None) -> ET.Element:
    attrs = {
        "data-rig-part": part_name,
        "data-rig-bone": bone,
        "data-rig-z": fmt(z),
    }
    if opacity_channel:
        attrs["data-rig-opacity"] = opacity_channel
    return g(parent, gid, label=label, **attrs)


def joint(parent: ET.Element, gid: str, name: str, x: float, y: float, *, r: float = 2.8) -> None:
    circle(
        parent,
        gid,
        x,
        y,
        r,
        fill="#ff3eb5",
        stroke=OUTLINE,
        stroke_width=1.1,
        opacity=0.28,
    ).set("data-rig-joint", name)


def qpath(p0: tuple[float, float], p1: tuple[float, float], bend: float = 0.0) -> str:
    x0, y0 = p0
    x1, y1 = p1
    mx = (x0 + x1) / 2.0 + bend
    my = (y0 + y1) / 2.0
    return f"M {fmt(x0)} {fmt(y0)} Q {fmt(mx)} {fmt(my)} {fmt(x1)} {fmt(y1)}"


def stroked_limb(parent: ET.Element, prefix: str, p0: tuple[float, float], p1: tuple[float, float], *,
                 outer_w: float, inner_w: float, color: str, bend: float = 0.0,
                 cuff: bool = False) -> None:
    d = qpath(p0, p1, bend=bend)
    path(parent, f"{prefix}-outline", d, fill="none", stroke=OUTLINE, stroke_width=outer_w, linecap="round")
    path(parent, f"{prefix}-fill", d, fill="none", stroke=color, stroke_width=inner_w, linecap="round")
    if cuff:
        line(parent, f"{prefix}-cuff", p1[0] - 4, p1[1] - 1, p1[0] + 4, p1[1] + 1, stroke=RIBBON_DARK, stroke_width=2.3)


def boot(parent: ET.Element, prefix: str, ankle: tuple[float, float], toe: tuple[float, float], *, facing: int = 1) -> None:
    ax, ay = ankle
    tx, ty = toe
    poly(
        parent,
        f"{prefix}-boot",
        [
            (ax - 5, ay - 1),
            (ax + 4, ay - 2),
            (tx + 7 * facing, ty - 3),
            (tx + 9 * facing, ty + 3),
            (ax - 4, ay + 4),
        ],
        fill=SHOE,
        stroke=OUTLINE,
        stroke_width=2.0,
    )
    line(parent, f"{prefix}-sole", tx - 1 * facing, ty + 2, tx + 8 * facing, ty + 2, stroke=OUTLINE, stroke_width=1.8)


def draw_eye(
    parent: ET.Element,
    prefix: str,
    x: float,
    y: float,
    *,
    width: float = 5.2,
    height: float = 1.7,
    pupil_shift: float = 0.0,
) -> None:
    """Draw a small readable eye that survives the final sprite downsample.

    A full dark outline and large circular iris collapse into a black rectangle
    at 128 px.  Use a pale almond, one fine upper lid, and a sub-pixel brown
    iris instead.
    """
    rx = width / 2.0
    ry = height / 2.0
    almond = (
        f"M {fmt(x-rx)} {fmt(y)} "
        f"Q {fmt(x)} {fmt(y-ry)} {fmt(x+rx)} {fmt(y)} "
        f"Q {fmt(x)} {fmt(y+ry)} {fmt(x-rx)} {fmt(y)} Z"
    )
    path(parent, f"{prefix}-white", almond, fill="#fbf4e8")
    path(
        parent,
        f"{prefix}-upper-lid",
        f"M {fmt(x-rx)} {fmt(y)} Q {fmt(x)} {fmt(y-ry-0.35)} {fmt(x+rx)} {fmt(y)}",
        fill="none",
        stroke="#5b4033",
        stroke_width=0.72,
        linecap="round",
    )
    ellipse(
        parent,
        f"{prefix}-iris",
        x + pupil_shift,
        y + 0.08,
        0.62,
        0.88,
        fill="#5c4638",
    )
    circle(parent, f"{prefix}-pupil", x + pupil_shift + 0.05, y + 0.12, 0.26, fill="#251c18")


def dress_panel(parent: ET.Element, gid: str, points: Sequence[tuple[float, float]], *, band_y: float | None = None,
                pleats: Iterable[tuple[tuple[float, float], tuple[float, float]]] = ()) -> None:
    poly(parent, f"{gid}-body", points, fill=DRESS, stroke=OUTLINE, stroke_width=2.3)
    if band_y is not None:
        xs = [p[0] for p in points]
        line(parent, f"{gid}-band", min(xs) + 2, band_y, max(xs) - 2, band_y, stroke=RIBBON, stroke_width=2.6)
    for idx, (a, b) in enumerate(pleats):
        line(parent, f"{gid}-pleat-{idx}", a[0], a[1], b[0], b[1], stroke=DRESS_SHADE, stroke_width=1.6, opacity=0.95)


def torso_piece(parent: ET.Element, gid: str, points: Sequence[tuple[float, float]]) -> None:
    poly(parent, f"{gid}-bodice", points, fill=DRESS, stroke=OUTLINE, stroke_width=2.5)


def ribbon_bow(parent: ET.Element, prefix: str, cx: float, cy: float, *, scale: float = 1.0) -> None:
    poly(parent, f"{prefix}-left", [(cx - 9*scale, cy), (cx - 2*scale, cy - 4*scale), (cx - 1*scale, cy + 4*scale)], fill=RIBBON, stroke=OUTLINE, stroke_width=1.8)
    poly(parent, f"{prefix}-right", [(cx + 9*scale, cy), (cx + 2*scale, cy - 4*scale), (cx + 1*scale, cy + 4*scale)], fill=RIBBON, stroke=OUTLINE, stroke_width=1.8)
    circle(parent, f"{prefix}-knot", cx, cy, 2.5*scale, fill=RIBBON_DARK, stroke=OUTLINE, stroke_width=1.6)
    line(parent, f"{prefix}-tail-l", cx - 1.0*scale, cy + 2.8*scale, cx - 4.5*scale, cy + 11.0*scale, stroke=RIBBON_DARK, stroke_width=1.7)
    line(parent, f"{prefix}-tail-r", cx + 1.0*scale, cy + 2.8*scale, cx + 2.0*scale, cy + 12.0*scale, stroke=RIBBON_DARK, stroke_width=1.7)


def hair_ribbon(parent: ET.Element, prefix: str, cx: float, cy: float) -> None:
    ribbon_bow(parent, prefix, cx, cy, scale=0.75)


def eyebrow(parent: ET.Element, gid: str, x1: float, y1: float, x2: float, y2: float) -> None:
    path(
        parent,
        gid,
        f"M {fmt(x1)} {fmt(y1)} Q {fmt((x1+x2)/2.0)} {fmt(min(y1,y2)-0.7)} {fmt(x2)} {fmt(y2)}",
        fill="none",
        stroke="#684a3a",
        stroke_width=0.82,
        linecap="round",
    )


def add_head(view: ET.Element, prefix: str, base_x: float, eye_mode: str) -> None:
    head = part(view, f"{prefix}-head", "Head", "head", "head", 14)
    ellipse(head, f"{prefix}-hair-back", base_x, 95, 24, 29, fill=HAIR, stroke=OUTLINE, stroke_width=2.6)
    ellipse(head, f"{prefix}-face", base_x, 99, 19, 23, fill=SKIN, stroke=OUTLINE, stroke_width=2.2)
    path(head, f"{prefix}-hair-front", f"M {fmt(base_x-21)} 89 C {fmt(base_x-11)} 72, {fmt(base_x+17)} 72, {fmt(base_x+19)} 94 C {fmt(base_x+11)} 88, {fmt(base_x+5)} 84, {fmt(base_x-1)} 83 C {fmt(base_x-8)} 83, {fmt(base_x-15)} 86, {fmt(base_x-21)} 89 Z", fill=HAIR, stroke=OUTLINE, stroke_width=2.0, linejoin="round")
    path(head, f"{prefix}-curl-left", f"M {fmt(base_x-18)} 106 C {fmt(base_x-26)} 112, {fmt(base_x-25)} 122, {fmt(base_x-15)} 126", fill="none", stroke=HAIR_DARK, stroke_width=4.2, linecap="round")
    path(head, f"{prefix}-curl-right", f"M {fmt(base_x+18)} 106 C {fmt(base_x+26)} 112, {fmt(base_x+25)} 122, {fmt(base_x+15)} 126", fill="none", stroke=HAIR_DARK, stroke_width=4.2, linecap="round")
    circle(head, f"{prefix}-cheek-l", base_x - 8.5, 104, 2.0, fill=CHEEK, opacity=0.55)
    circle(head, f"{prefix}-cheek-r", base_x + 8.5, 104, 2.0, fill=CHEEK, opacity=0.45)
    if eye_mode == "front":
        draw_eye(head, f"{prefix}-eye-l", base_x - 7.5, 97.5)
        draw_eye(head, f"{prefix}-eye-r", base_x + 7.5, 97.5)
        line(head, f"{prefix}-mouth", base_x - 4, 110.5, base_x + 4, 110.5, stroke=OUTLINE, stroke_width=1.8)
        line(head, f"{prefix}-nose", base_x, 98.5, base_x - 1.0, 104.5, stroke=OUTLINE, stroke_width=1.3)
        ribbon_bow(head, f"{prefix}-neck-bow", base_x, 120, scale=0.82)
        hair_ribbon(head, f"{prefix}-hair-ribbon", base_x + 16, 84)
        blink = part(view, f"{prefix}-blink", "Blink", "blink", "head", 15, opacity_channel="blink_vis")
        line(blink, f"{prefix}-blink-l", base_x - 11, 97.2, base_x - 4, 97.2, stroke=OUTLINE, stroke_width=2.2)
        line(blink, f"{prefix}-blink-r", base_x + 4, 97.2, base_x + 11, 97.2, stroke=OUTLINE, stroke_width=2.2)
        talk = part(view, f"{prefix}-talk", "Talk Mouth", "talk_mouth", "head", 15, opacity_channel="talk_vis")
        ellipse(talk, f"{prefix}-talk-mouth", base_x, 110.8, 4.2, 3.0, fill="#b66e63", stroke=OUTLINE, stroke_width=1.5)
    elif eye_mode == "three_quarter":
        eyebrow(head, f"{prefix}-brow-main", base_x + 0.9, 92.4, base_x + 7.0, 92.1)
        eyebrow(head, f"{prefix}-brow-far", base_x - 10.7, 94.0, base_x - 6.5, 93.7)
        draw_eye(
            head,
            f"{prefix}-eye-main",
            base_x + 4.0,
            97.7,
            width=5.2,
            height=1.65,
            pupil_shift=0.12,
        )
        draw_eye(
            head,
            f"{prefix}-eye-far",
            base_x - 8.6,
            98.25,
            width=3.25,
            height=1.35,
            pupil_shift=0.0,
        )
        path(head, f"{prefix}-nose", f"M {fmt(base_x+0.8)} 98.7 Q {fmt(base_x+3.6)} 103.5 {fmt(base_x+1.0)} 107.0", fill="none", stroke=OUTLINE, stroke_width=1.4, linecap="round")
        path(head, f"{prefix}-mouth", f"M {fmt(base_x-1.7)} 110.0 Q {fmt(base_x+2.0)} 112.4 {fmt(base_x+5.7)} 109.9", fill="none", stroke=OUTLINE, stroke_width=1.5, linecap="round")
        line(head, f"{prefix}-lip-shadow", base_x + 0.5, 111.4, base_x + 4.6, 111.0, stroke="#a87067", stroke_width=0.8, opacity=0.65)
        ribbon_bow(head, f"{prefix}-neck-bow", base_x + 1, 120, scale=0.82)
        hair_ribbon(head, f"{prefix}-hair-ribbon", base_x + 17, 86)
        blink = part(view, f"{prefix}-blink", "Blink", "blink", "head", 15, opacity_channel="blink_vis")
        line(blink, f"{prefix}-blink-main", base_x + 1.0, 97.7, base_x + 8.1, 97.7, stroke=OUTLINE, stroke_width=2.0)
        line(blink, f"{prefix}-blink-far", base_x - 10.4, 98.3, base_x - 6.7, 98.3, stroke=OUTLINE, stroke_width=1.7)
        talk = part(view, f"{prefix}-talk", "Talk Mouth", "talk_mouth", "head", 15, opacity_channel="talk_vis")
        ellipse(talk, f"{prefix}-talk-mouth", base_x + 1.9, 110.7, 2.6, 1.8, fill="#b66e63", stroke=OUTLINE, stroke_width=1.2)
    else:
        path(head, f"{prefix}-profile-face", f"M {fmt(base_x-10)} 85 C {fmt(base_x+2)} 80, {fmt(base_x+15)} 91, {fmt(base_x+12)} 99 C {fmt(base_x+16)} 101, {fmt(base_x+15)} 106, {fmt(base_x+10)} 108 C {fmt(base_x+10)} 117, {fmt(base_x+1)} 122, {fmt(base_x-8)} 121 C {fmt(base_x-12)} 116, {fmt(base_x-13)} 108, {fmt(base_x-12)} 96 C {fmt(base_x-12)} 91, {fmt(base_x-11)} 87, {fmt(base_x-10)} 85 Z", fill=SKIN, stroke=OUTLINE, stroke_width=2.1, linejoin="round")
        path(head, f"{prefix}-profile-hair", f"M {fmt(base_x-19)} 88 C {fmt(base_x-10)} 74, {fmt(base_x+9)} 75, {fmt(base_x+12)} 91 C {fmt(base_x+8)} 85, {fmt(base_x+1)} 82, {fmt(base_x-6)} 82 C {fmt(base_x-11)} 82, {fmt(base_x-16)} 84, {fmt(base_x-19)} 88 Z", fill=HAIR, stroke=OUTLINE, stroke_width=2.0, linejoin="round")
        path(head, f"{prefix}-curl-back", f"M {fmt(base_x-14)} 109 C {fmt(base_x-24)} 114, {fmt(base_x-22)} 125, {fmt(base_x-10)} 128", fill="none", stroke=HAIR_DARK, stroke_width=4.1, linecap="round")
        line(head, f"{prefix}-eye", base_x + 4, 97.7, base_x + 9.2, 97.7, stroke=OUTLINE, stroke_width=1.8)
        line(head, f"{prefix}-mouth", base_x + 4.3, 110.7, base_x + 8.5, 109.7, stroke=OUTLINE, stroke_width=1.7)
        ribbon_bow(head, f"{prefix}-neck-bow", base_x + 1.5, 120, scale=0.8)
        hair_ribbon(head, f"{prefix}-hair-ribbon", base_x - 8, 84.5)
        blink = part(view, f"{prefix}-blink", "Blink", "blink", "head", 15, opacity_channel="blink_vis")
        line(blink, f"{prefix}-blink-main", base_x + 3.7, 97.5, base_x + 9.4, 97.5, stroke=OUTLINE, stroke_width=2.0)
        talk = part(view, f"{prefix}-talk", "Talk Mouth", "talk_mouth", "head", 15, opacity_channel="talk_vis")
        ellipse(talk, f"{prefix}-talk-mouth", base_x + 7.1, 110.2, 2.6, 2.1, fill="#b66e63", stroke=OUTLINE, stroke_width=1.3)


def build_three_quarter(root: ET.Element) -> None:
    ox = 150.0
    view = layer(root, "view-mleblanc-tq", "Madam LeBlanc - Three Quarter")
    joints = {
        "waist": (ox + 0, 145),
        "neck": (ox + 0, 120),
        "far_shoulder": (ox - 15, 124),
        "far_elbow": (ox - 25, 153),
        "far_wrist": (ox - 24, 181),
        "far_handtip": (ox - 22, 191),
        "near_shoulder": (ox + 18, 123),
        "near_elbow": (ox + 31, 151),
        "near_wrist": (ox + 32, 179),
        "near_handtip": (ox + 33, 189),
        "far_hip": (ox - 10, 148),
        "far_knee": (ox - 15, 185),
        "far_ankle": (ox - 18, 226),
        "far_toe": (ox - 11, 237),
        "near_hip": (ox + 12, 149),
        "near_knee": (ox + 19, 186),
        "near_ankle": (ox + 23, 227),
        "near_toe": (ox + 31, 238),
    }
    far_arm_u = part(view, "tq-far-arm-u", "Far Upper Arm", "far_arm_u", "far_arm_u", 5.5)
    stroked_limb(far_arm_u, "tq-far-arm-u-shape", joints["far_shoulder"], joints["far_elbow"], outer_w=15, inner_w=11, color=DRESS, bend=-3.5, cuff=False)
    far_arm_l = part(view, "tq-far-arm-l", "Far Lower Arm", "far_arm_l", "far_arm_l", 6.1)
    stroked_limb(far_arm_l, "tq-far-arm-l-shape", joints["far_elbow"], joints["far_wrist"], outer_w=14, inner_w=10, color=DRESS, bend=-2.2, cuff=True)
    far_hand = part(view, "tq-far-hand", "Far Hand", "far_hand", "far_arm_l", 6.6)
    ellipse(far_hand, "tq-far-hand-shape", joints["far_handtip"][0], joints["far_handtip"][1], 5.4, 4.4, fill=SKIN, stroke=OUTLINE, stroke_width=1.8)

    far_leg_u = part(view, "tq-far-leg-u", "Far Upper Leg", "far_leg_u", "far_leg_u", 1.8)
    stroked_limb(far_leg_u, "tq-far-leg-u-shape", joints["far_hip"], joints["far_knee"], outer_w=16, inner_w=12, color=STOCKING, bend=-1.6)
    far_leg_l = part(view, "tq-far-leg-l", "Far Lower Leg", "far_leg_l", "far_leg_l", 1.9)
    stroked_limb(far_leg_l, "tq-far-leg-l-shape", joints["far_knee"], joints["far_ankle"], outer_w=15, inner_w=11, color=STOCKING, bend=-1.0)
    far_foot = part(view, "tq-far-foot", "Far Foot", "far_leg_foot", "far_leg_foot", 1.0)
    boot(far_foot, "tq-far-foot-shape", joints["far_ankle"], joints["far_toe"], facing=1)

    near_leg_u = part(view, "tq-near-leg-u", "Near Upper Leg", "near_leg_u", "near_leg_u", 2.4)
    stroked_limb(near_leg_u, "tq-near-leg-u-shape", joints["near_hip"], joints["near_knee"], outer_w=18, inner_w=14, color=STOCKING, bend=1.8)
    near_leg_l = part(view, "tq-near-leg-l", "Near Lower Leg", "near_leg_l", "near_leg_l", 2.5)
    stroked_limb(near_leg_l, "tq-near-leg-l-shape", joints["near_knee"], joints["near_ankle"], outer_w=15, inner_w=11, color=STOCKING, bend=0.8)
    near_foot = part(view, "tq-near-foot", "Near Foot", "near_leg_foot", "near_leg_foot", 1.2)
    boot(near_foot, "tq-near-foot-shape", joints["near_ankle"], joints["near_toe"], facing=1)

    skirt_far = part(view, "tq-skirt-far", "Far Skirt Panel", "skirt_far", "far_leg_u", 3.3)
    dress_panel(
        skirt_far,
        "tq-skirt-far",
        [(ox - 10, 145), (ox - 27, 163), (ox - 31, 218), (ox - 10, 221), (ox + 1, 151)],
        pleats=[((ox - 17, 157), (ox - 18, 214)), ((ox - 24, 166), (ox - 25, 216))],
    )
    skirt_center = part(view, "tq-skirt-center", "Center Skirt", "skirt_center", "pelvis", 4.0)
    dress_panel(
        skirt_center,
        "tq-skirt-center",
        [(ox - 15, 145), (ox + 14, 145), (ox + 20, 220), (ox - 6, 222)],
        band_y=208,
        pleats=[((ox - 7, 154), (ox - 4, 219)), ((ox + 1, 152), (ox + 5, 220)), ((ox + 9, 153), (ox + 13, 218))],
    )
    skirt_near = part(view, "tq-skirt-near", "Near Skirt Panel", "skirt_near", "near_leg_u", 4.7)
    dress_panel(
        skirt_near,
        "tq-skirt-near",
        [(ox + 8, 145), (ox + 31, 152), (ox + 39, 217), (ox + 14, 221), (ox + 2, 149)],
        pleats=[((ox + 18, 154), (ox + 24, 218)), ((ox + 28, 158), (ox + 33, 216))],
    )
    pelvis = part(view, "tq-pelvis", "Pelvis Yoke", "pelvis_yoke", "pelvis", 4.9)
    poly(pelvis, "tq-waist-band", [(ox - 14, 139), (ox + 18, 141), (ox + 14, 152), (ox - 18, 149)], fill=RIBBON, stroke=OUTLINE, stroke_width=2.0)
    ribbon_bow(pelvis, "tq-waist-bow", ox + 15, 145, scale=0.88)

    torso = part(view, "tq-torso", "Torso", "torso", "torso", 8.4)
    torso_piece(torso, "tq-torso", [(ox - 17, 116), (ox + 9, 114), (ox + 20, 126), (ox + 15, 145), (ox - 14, 145), (ox - 22, 126)])
    poly(torso, "tq-collar", [(ox - 7, 115), (ox + 7, 115), (ox + 2, 123), (ox - 5, 123)], fill=HAT_SHADOW, stroke=OUTLINE, stroke_width=1.8)
    line(torso, "tq-bodice-line", ox - 1, 123, ox + 2, 144, stroke=DRESS_SHADE, stroke_width=1.8)

    near_arm_u = part(view, "tq-near-arm-u", "Near Upper Arm", "near_arm_u", "near_arm_u", 9.8)
    stroked_limb(near_arm_u, "tq-near-arm-u-shape", joints["near_shoulder"], joints["near_elbow"], outer_w=16, inner_w=12, color=DRESS, bend=4.2)
    near_arm_l = part(view, "tq-near-arm-l", "Near Lower Arm", "near_arm_l", "near_arm_l", 10.8)
    stroked_limb(near_arm_l, "tq-near-arm-l-shape", joints["near_elbow"], joints["near_wrist"], outer_w=14, inner_w=10, color=DRESS, bend=2.5, cuff=True)
    near_hand = part(view, "tq-near-hand", "Near Hand", "near_hand", "near_arm_l", 11.3)
    ellipse(near_hand, "tq-near-hand-shape", joints["near_handtip"][0], joints["near_handtip"][1], 5.6, 4.5, fill=SKIN, stroke=OUTLINE, stroke_width=1.8)

    add_head(view, "tq", ox + 0.5, "three_quarter")

    j = g(view, "tq-joints", label="Joints")
    for name, (x, y) in joints.items():
        joint(j, f"tq-joint-{name}", name, x, y)


def build_front(root: ET.Element) -> None:
    ox = 450.0
    view = layer(root, "view-mleblanc-front", "Madam LeBlanc - Front")
    joints = {
        "waist": (ox + 0, 145),
        "neck": (ox + 0, 120),
        "far_shoulder": (ox - 19, 124),
        "far_elbow": (ox - 27, 153),
        "far_wrist": (ox - 25, 181),
        "far_handtip": (ox - 22, 191),
        "near_shoulder": (ox + 19, 124),
        "near_elbow": (ox + 27, 153),
        "near_wrist": (ox + 25, 181),
        "near_handtip": (ox + 22, 191),
        "far_hip": (ox - 11, 148),
        "far_knee": (ox - 13, 186),
        "far_ankle": (ox - 14, 228),
        "far_toe": (ox - 10, 238),
        "near_hip": (ox + 11, 148),
        "near_knee": (ox + 13, 186),
        "near_ankle": (ox + 14, 228),
        "near_toe": (ox + 10, 238),
    }

    far_leg_u = part(view, "front-far-leg-u", "Far Upper Leg", "far_leg_u", "far_leg_u", 2.0)
    stroked_limb(far_leg_u, "front-far-leg-u-shape", joints["far_hip"], joints["far_knee"], outer_w=16, inner_w=12, color=STOCKING)
    far_leg_l = part(view, "front-far-leg-l", "Far Lower Leg", "far_leg_l", "far_leg_l", 2.1)
    stroked_limb(far_leg_l, "front-far-leg-l-shape", joints["far_knee"], joints["far_ankle"], outer_w=15, inner_w=11, color=STOCKING)
    far_foot = part(view, "front-far-foot", "Far Foot", "far_leg_foot", "far_leg_foot", 1.0)
    boot(far_foot, "front-far-foot-shape", joints["far_ankle"], joints["far_toe"], facing=1)

    near_leg_u = part(view, "front-near-leg-u", "Near Upper Leg", "near_leg_u", "near_leg_u", 2.2)
    stroked_limb(near_leg_u, "front-near-leg-u-shape", joints["near_hip"], joints["near_knee"], outer_w=16, inner_w=12, color=STOCKING)
    near_leg_l = part(view, "front-near-leg-l", "Near Lower Leg", "near_leg_l", "near_leg_l", 2.3)
    stroked_limb(near_leg_l, "front-near-leg-l-shape", joints["near_knee"], joints["near_ankle"], outer_w=15, inner_w=11, color=STOCKING)
    near_foot = part(view, "front-near-foot", "Near Foot", "near_leg_foot", "near_leg_foot", 1.1)
    boot(near_foot, "front-near-foot-shape", joints["near_ankle"], joints["near_toe"], facing=1)

    skirt_far = part(view, "front-skirt-far", "Far Skirt Panel", "skirt_far", "far_leg_u", 3.2)
    dress_panel(front_sk := skirt_far, "front-skirt-far", [(ox - 11, 145), (ox - 27, 151), (ox - 31, 220), (ox - 8, 221)], pleats=[((ox - 18, 153), (ox - 20, 219)), ((ox - 24, 157), (ox - 26, 218))])
    skirt_center = part(view, "front-skirt-center", "Center Skirt", "skirt_center", "pelvis", 3.9)
    dress_panel(skirt_center, "front-skirt-center", [(ox - 18, 145), (ox + 18, 145), (ox + 16, 221), (ox - 16, 221)], band_y=208, pleats=[((ox - 10, 151), (ox - 10, 219)), ((ox, 151), (ox, 219)), ((ox + 10, 151), (ox + 10, 219))])
    skirt_near = part(view, "front-skirt-near", "Near Skirt Panel", "skirt_near", "near_leg_u", 4.5)
    dress_panel(skirt_near, "front-skirt-near", [(ox + 11, 145), (ox + 27, 151), (ox + 31, 220), (ox + 8, 221)], pleats=[((ox + 18, 153), (ox + 20, 219)), ((ox + 24, 157), (ox + 26, 218))])

    pelvis = part(view, "front-pelvis", "Pelvis Yoke", "pelvis_yoke", "pelvis", 4.8)
    poly(pelvis, "front-waist-band", [(ox - 18, 141), (ox + 18, 141), (ox + 15, 151), (ox - 15, 151)], fill=RIBBON, stroke=OUTLINE, stroke_width=2.0)
    ribbon_bow(pelvis, "front-waist-bow", ox, 145, scale=0.92)

    far_arm_u = part(view, "front-far-arm-u", "Far Upper Arm", "far_arm_u", "far_arm_u", 6.8)
    stroked_limb(far_arm_u, "front-far-arm-u-shape", joints["far_shoulder"], joints["far_elbow"], outer_w=15, inner_w=11, color=DRESS, bend=-2.0)
    far_arm_l = part(view, "front-far-arm-l", "Far Lower Arm", "far_arm_l", "far_arm_l", 7.0)
    stroked_limb(far_arm_l, "front-far-arm-l-shape", joints["far_elbow"], joints["far_wrist"], outer_w=14, inner_w=10, color=DRESS, bend=-1.8, cuff=True)
    far_hand = part(view, "front-far-hand", "Far Hand", "far_hand", "far_arm_l", 7.1)
    ellipse(far_hand, "front-far-hand-shape", joints["far_handtip"][0], joints["far_handtip"][1], 5.2, 4.2, fill=SKIN, stroke=OUTLINE, stroke_width=1.8)

    torso = part(view, "front-torso", "Torso", "torso", "torso", 8.2)
    torso_piece(torso, "front-torso", [(ox - 20, 115), (ox + 20, 115), (ox + 18, 145), (ox - 18, 145)])
    poly(torso, "front-collar", [(ox - 8, 115), (ox + 8, 115), (ox + 3, 123), (ox - 3, 123)], fill=HAT_SHADOW, stroke=OUTLINE, stroke_width=1.8)
    line(torso, "front-bodice-line", ox, 123, ox, 144, stroke=DRESS_SHADE, stroke_width=1.8)

    near_arm_u = part(view, "front-near-arm-u", "Near Upper Arm", "near_arm_u", "near_arm_u", 8.8)
    stroked_limb(near_arm_u, "front-near-arm-u-shape", joints["near_shoulder"], joints["near_elbow"], outer_w=15, inner_w=11, color=DRESS, bend=2.0)
    near_arm_l = part(view, "front-near-arm-l", "Near Lower Arm", "near_arm_l", "near_arm_l", 9.0)
    stroked_limb(near_arm_l, "front-near-arm-l-shape", joints["near_elbow"], joints["near_wrist"], outer_w=14, inner_w=10, color=DRESS, bend=1.8, cuff=True)
    near_hand = part(view, "front-near-hand", "Near Hand", "near_hand", "near_arm_l", 9.1)
    ellipse(near_hand, "front-near-hand-shape", joints["near_handtip"][0], joints["near_handtip"][1], 5.2, 4.2, fill=SKIN, stroke=OUTLINE, stroke_width=1.8)

    add_head(view, "front", ox, "front")

    j = g(view, "front-joints", label="Joints")
    for name, (x, y) in joints.items():
        joint(j, f"front-joint-{name}", name, x, y)


def build_side(root: ET.Element) -> None:
    ox = 740.0
    view = layer(root, "view-mleblanc-side", "Madam LeBlanc - Side Right")
    joints = {
        "waist": (ox + 2, 145),
        "neck": (ox + 5, 120),
        "far_shoulder": (ox + 1, 124),
        "far_elbow": (ox - 4, 152),
        "far_wrist": (ox - 3, 180),
        "far_handtip": (ox - 1, 190),
        "near_shoulder": (ox + 10, 124),
        "near_elbow": (ox + 20, 153),
        "near_wrist": (ox + 20, 181),
        "near_handtip": (ox + 18, 191),
        "far_hip": (ox - 1, 148),
        "far_knee": (ox - 4, 186),
        "far_ankle": (ox - 2, 228),
        "far_toe": (ox + 7, 238),
        "near_hip": (ox + 7, 149),
        "near_knee": (ox + 10, 186),
        "near_ankle": (ox + 12, 228),
        "near_toe": (ox + 23, 238),
    }

    far_arm_u = part(view, "side-far-arm-u", "Far Upper Arm", "far_arm_u", "far_arm_u", 5.5)
    stroked_limb(far_arm_u, "side-far-arm-u-shape", joints["far_shoulder"], joints["far_elbow"], outer_w=14.5, inner_w=10.5, color=DRESS, bend=-2.5)
    far_arm_l = part(view, "side-far-arm-l", "Far Lower Arm", "far_arm_l", "far_arm_l", 5.7)
    stroked_limb(far_arm_l, "side-far-arm-l-shape", joints["far_elbow"], joints["far_wrist"], outer_w=13.5, inner_w=9.6, color=DRESS, bend=-1.0, cuff=True)
    far_hand = part(view, "side-far-hand", "Far Hand", "far_hand", "far_arm_l", 5.8)
    ellipse(far_hand, "side-far-hand-shape", joints["far_handtip"][0], joints["far_handtip"][1], 4.8, 4.0, fill=SKIN, stroke=OUTLINE, stroke_width=1.7)

    far_leg_u = part(view, "side-far-leg-u", "Far Upper Leg", "far_leg_u", "far_leg_u", 1.8)
    stroked_limb(far_leg_u, "side-far-leg-u-shape", joints["far_hip"], joints["far_knee"], outer_w=15, inner_w=11, color=STOCKING, bend=-0.8)
    far_leg_l = part(view, "side-far-leg-l", "Far Lower Leg", "far_leg_l", "far_leg_l", 1.9)
    stroked_limb(far_leg_l, "side-far-leg-l-shape", joints["far_knee"], joints["far_ankle"], outer_w=14, inner_w=10, color=STOCKING, bend=0.2)
    far_foot = part(view, "side-far-foot", "Far Foot", "far_leg_foot", "far_leg_foot", 1.0)
    boot(far_foot, "side-far-foot-shape", joints["far_ankle"], joints["far_toe"], facing=1)

    near_leg_u = part(view, "side-near-leg-u", "Near Upper Leg", "near_leg_u", "near_leg_u", 2.2)
    stroked_limb(near_leg_u, "side-near-leg-u-shape", joints["near_hip"], joints["near_knee"], outer_w=16, inner_w=12, color=STOCKING, bend=0.8)
    near_leg_l = part(view, "side-near-leg-l", "Near Lower Leg", "near_leg_l", "near_leg_l", 2.3)
    stroked_limb(near_leg_l, "side-near-leg-l-shape", joints["near_knee"], joints["near_ankle"], outer_w=14, inner_w=10, color=STOCKING, bend=0.4)
    near_foot = part(view, "side-near-foot", "Near Foot", "near_leg_foot", "near_leg_foot", 1.1)
    boot(near_foot, "side-near-foot-shape", joints["near_ankle"], joints["near_toe"], facing=1)

    skirt_far = part(view, "side-skirt-far", "Far Skirt Panel", "skirt_far", "far_leg_u", 3.3)
    dress_panel(skirt_far, "side-skirt-far", [(ox - 4, 145), (ox - 16, 149), (ox - 20, 220), (ox - 2, 222)], pleats=[((ox - 9, 151), (ox - 11, 218)), ((ox - 14, 154), (ox - 16, 216))])
    skirt_center = part(view, "side-skirt-center", "Center Skirt", "skirt_center", "pelvis", 4.0)
    dress_panel(skirt_center, "side-skirt-center", [(ox + 1, 144), (ox + 20, 146), (ox + 23, 221), (ox + 2, 222)], band_y=209, pleats=[((ox + 8, 150), (ox + 11, 220)), ((ox + 15, 151), (ox + 18, 219))])
    skirt_near = part(view, "side-skirt-near", "Near Skirt Panel", "skirt_near", "near_leg_u", 4.8)
    dress_panel(skirt_near, "side-skirt-near", [(ox + 8, 145), (ox + 28, 148), (ox + 33, 219), (ox + 10, 221)], pleats=[((ox + 17, 149), (ox + 22, 218)), ((ox + 25, 151), (ox + 28, 216))])

    pelvis = part(view, "side-pelvis", "Pelvis Yoke", "pelvis_yoke", "pelvis", 4.9)
    poly(pelvis, "side-waist-band", [(ox - 3, 141), (ox + 18, 142), (ox + 16, 152), (ox - 5, 150)], fill=RIBBON, stroke=OUTLINE, stroke_width=2.0)
    ribbon_bow(pelvis, "side-waist-bow", ox + 16, 145.5, scale=0.82)

    torso = part(view, "side-torso", "Torso", "torso", "torso", 8.2)
    torso_piece(torso, "side-torso", [(ox - 8, 115), (ox + 10, 114), (ox + 18, 126), (ox + 16, 145), (ox - 2, 145), (ox - 10, 126)])
    poly(torso, "side-collar", [(ox + 2, 115), (ox + 12, 116), (ox + 5, 124), (ox + 1, 123)], fill=HAT_SHADOW, stroke=OUTLINE, stroke_width=1.8)
    line(torso, "side-bodice-line", ox + 8, 123, ox + 9, 144, stroke=DRESS_SHADE, stroke_width=1.6)

    near_arm_u = part(view, "side-near-arm-u", "Near Upper Arm", "near_arm_u", "near_arm_u", 9.6)
    stroked_limb(near_arm_u, "side-near-arm-u-shape", joints["near_shoulder"], joints["near_elbow"], outer_w=15.5, inner_w=11.4, color=DRESS, bend=2.8)
    near_arm_l = part(view, "side-near-arm-l", "Near Lower Arm", "near_arm_l", "near_arm_l", 10.2)
    stroked_limb(near_arm_l, "side-near-arm-l-shape", joints["near_elbow"], joints["near_wrist"], outer_w=14, inner_w=10, color=DRESS, bend=1.3, cuff=True)
    near_hand = part(view, "side-near-hand", "Near Hand", "near_hand", "near_arm_l", 10.4)
    ellipse(near_hand, "side-near-hand-shape", joints["near_handtip"][0], joints["near_handtip"][1], 5.2, 4.3, fill=SKIN, stroke=OUTLINE, stroke_width=1.8)

    add_head(view, "side", ox + 4, "side")

    j = g(view, "side-joints", label="Joints")
    for name, (x, y) in joints.items():
        joint(j, f"side-joint-{name}", name, x, y)


def build_svg() -> None:
    svg = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "id": "m-leblanc-multiview",
            "version": "1.1",
            "viewBox": "0 0 900 300",
            "width": "900",
            "height": "300",
            f"{{{SODIPODI_NS}}}docname": "m_leblanc-multiview.svg",
        },
    )
    defs = el(svg, "defs", id="defs")
    del defs
    build_three_quarter(svg)
    SVG.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(svg)
    ET.indent(tree, space="  ")
    tree.write(SVG, encoding="utf-8", xml_declaration=True)


def _leg_rest_channels(doc: dict) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for leg in doc.get("ik_legs", []):
        prefix = leg["channel_prefix"]
        result[prefix] = {
            "x": float(leg.get("rest_x", 0.0)),
            "lift": float(leg.get("rest_lift", 0.0)),
            "pitch": float(leg.get("rest_pitch", 0.0)),
        }
    return result


def make_idle_clip() -> dict:
    return {
        "name": "idle",
        "loop": True,
        "frames": 8,
        "duration_ms": 110,
        "channels": {
            "root_y": [0.0, -0.8, -1.2, -0.6, 0.2, 0.8, 0.4, -0.2],
            "torso": [0.0, 0.2, 0.35, 0.2, 0.0, -0.2, -0.15, 0.0],
            "head": [0.0, -0.1, -0.2, -0.1, 0.0, 0.1, 0.1, 0.0],
            "pelvis": [0.0, -0.4, -0.6, -0.2, 0.2, 0.5, 0.4, 0.1],
            "near_arm_u": [10.0, 9.0, 8.0, 8.5, 9.5, 10.5, 11.0, 10.5],
            "near_arm_l": [14.0, 13.0, 12.0, 12.5, 13.5, 14.0, 14.5, 14.0],
            "far_arm_u": [-14.0, -15.0, -15.5, -15.0, -14.0, -13.0, -13.0, -13.5],
            "far_arm_l": [-10.0, -9.5, -9.0, -9.5, -10.0, -10.5, -10.5, -10.0],
            "blink_vis": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        },
    }


def make_interact_clip() -> dict:
    return {
        "name": "interact",
        "loop": True,
        "frames": 6,
        "duration_ms": 120,
        "channels": {
            "root_y": [0.0, -0.6, -1.0, -0.2, 0.4, 0.0],
            "torso": [0.0, 0.4, 0.8, 0.5, -0.2, 0.0],
            "head": [0.0, -0.3, -0.5, -0.3, 0.2, 0.0],
            "pelvis": [0.0, -1.5, -2.0, -1.0, 0.0, 0.0],
            "near_arm_u": [18.0, 8.0, -6.0, -10.0, 0.0, 14.0],
            "near_arm_l": [26.0, 16.0, 4.0, -4.0, 8.0, 22.0],
            "far_arm_u": [-12.0, -10.0, -8.0, -10.0, -12.0, -12.0],
            "far_arm_l": [-12.0, -9.0, -7.0, -8.0, -10.0, -11.0],
            "blink_vis": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        },
    }


def make_talk_clip() -> dict:
    return {
        "name": "talk",
        "loop": True,
        "frames": 6,
        "duration_ms": 100,
        "channels": {
            "root_y": [0.0, -0.6, 0.0, 0.6, 0.0, -0.4],
            "torso": [0.0, -0.2, 0.15, 0.25, 0.0, -0.15],
            "head": [0.0, 0.3, -0.2, 0.35, 0.0, -0.2],
            "near_arm_u": [12.0, 10.0, 7.0, 5.0, 8.0, 12.0],
            "near_arm_l": [12.0, 2.0, -6.0, -2.0, 6.0, 12.0],
            "far_arm_u": [-12.0, -10.0, -8.0, -7.0, -9.0, -12.0],
            "far_arm_l": [-10.0, -6.0, 0.0, -2.0, -7.0, -10.0],
            "talk_vis": [0.0, 1.0, 0.0, 1.0, 0.0, 0.0],
            "blink_vis": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        },
    }


def make_curtsy_clip() -> dict:
    return {
        "name": "curtsy",
        "loop": True,
        "frames": 8,
        "duration_ms": 110,
        "channels": {
            "root_y": [0.0, -0.8, -1.5, -2.5, -1.0, 0.2, 0.8, 0.0],
            "pelvis": [0.0, -1.5, -3.0, -5.0, -2.0, 0.0, 1.0, 0.0],
            "torso": [0.0, 0.2, 0.5, 0.8, 0.5, 0.2, 0.0, 0.0],
            "head": [0.0, -0.1, -0.2, -0.3, -0.2, 0.0, 0.1, 0.0],
            "near_arm_u": [14.0, 12.0, 8.0, 4.0, 2.0, 5.0, 10.0, 14.0],
            "near_arm_l": [18.0, 12.0, 4.0, -4.0, -6.0, 0.0, 10.0, 18.0],
            "far_arm_u": [-16.0, -18.0, -22.0, -26.0, -24.0, -20.0, -18.0, -16.0],
            "far_arm_l": [-10.0, -14.0, -20.0, -24.0, -20.0, -14.0, -10.0, -10.0],
            "near_leg_u": [0.0, 1.0, 3.0, 6.0, 4.0, 1.0, 0.0, 0.0],
            "near_leg_l": [0.0, -2.0, -5.0, -8.0, -5.0, -2.0, 0.0, 0.0],
            "far_leg_u": [0.0, -1.0, -3.0, -6.0, -4.0, -1.0, 0.0, 0.0],
            "far_leg_l": [0.0, 2.0, 5.0, 8.0, 5.0, 2.0, 0.0, 0.0],
            "blink_vis": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        },
    }


def seed_clips(doc: dict, view_key: str) -> dict[str, dict]:
    del doc, view_key
    return {
        "idle": make_idle_clip(),
        "interact": make_interact_clip(),
        "talk": make_talk_clip(),
        "curtsy": make_curtsy_clip(),
    }


def build_rig_docs(*, fresh: bool = False) -> list[Path]:
    outputs: list[Path] = []
    RIG_DIR.mkdir(parents=True, exist_ok=True)
    for view_key, spec in VIEWS.items():
        output = RIG_DIR / f"{spec.name}.rig.json"
        generated = build_humanoid_view_document(SVG, RIG_DIR, spec)
        doc = generated
        if output.exists() and not fresh:
            existing = json.loads(output.read_text())
            doc = merge_generated_geometry(existing, generated)
        doc["clips"] = seed_clips(doc, view_key)
        output.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        outputs.append(output)
    return outputs


def build(*, fresh: bool = False) -> list[Path]:
    build_svg()
    outputs = [SVG]
    outputs.extend(build_rig_docs(fresh=fresh))
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_build = sub.add_parser("build", help="Build Madam LeBlanc SVG and rig documents")
    p_build.add_argument("--fresh", action="store_true", help="Ignore any existing manual edits in rig docs")
    args = parser.parse_args(argv)
    if args.cmd == "build":
        for path in build(fresh=args.fresh):
            print(path)
        return 0
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
