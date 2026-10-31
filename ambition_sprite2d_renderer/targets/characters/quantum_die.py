"""The Quantum Die: an enemy of the haunted floors of Hylbert's Hotel (the
Math dimension; Jon, 2026-10-31: "a quantum dice enemy that does spooky
action at a distance").

A floating die of violet-teal spectral glass, in SUPERPOSITION: faint ghost
copies of it tumble round it, each showing other faces, as if it were
several states at once. Its attack is SPOOKY ACTION AT A DISTANCE: an
ENTANGLED TWIN of it materializes ahead (a ghost die tied to it by a
shimmering thread), and then the die COLLAPSES into its twin, blinking
across the gap in a burst of light; it sits dim and decohered after.

Drawn as a real cube: its eight corners turned in 3D (yaw, pitch, roll),
projected, its faces lit by their facing and drawn back to front, the pips
of each face placed on the face in 3D, so it tumbles properly.

Parts: the SUPERPOSITION GHOSTS (faint tumbling copies), the CUBE (glass
faces, glowing edges, pips), the ENTANGLEMENT THREAD and the TWIN (the
attack), the COLLAPSE burst, motes and an aura.

Rows: ``idle`` 8 (it tumbles slowly, its ghosts round it), ``walk`` 8 (it
drifts, tumbling faster), ``attack_side`` 12 (the twin forms ahead and the
thread draws taut (0-4), the collapse: it is the twin, a burst (5-7), dim
and still after (8-11)), ``hurt`` 3 (its faces scramble), ``death`` 8
(the wavefunction collapses: it splits into its pips, which wink out).

Facing right; it floats, its lowest corner near the canvas foot. No drop
shadow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "quantum_die"
FRAME_SIZE = (208, 144)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("attack_side", 12, 65),
    ("hurt", 3, 90),
    ("death", 8, 110),
]

OUTLINE: RGBA = (26, 14, 46, 255)
GLASS_LIGHT = np.array([196, 170, 255], np.float32)
GLASS_DARK = np.array([60, 30, 120], np.float32)
EDGE: RGBA = (150, 255, 236, 255)
PIP: RGBA = (240, 252, 255, 255)
TEAL: RGBA = (110, 240, 220, 255)
VIOLET: RGBA = (176, 120, 255, 255)
WHITE: RGBA = (250, 252, 255, 255)

#: The die's half size (frame pixels) and where it floats.
HALF = 15.0
CENTRE = (58.0, 74.0)
#: Where its entangled twin forms, ahead of it.
TWIN_AHEAD = 96.0
#: The light: from the upper left, toward the viewer.
LIGHT = np.array([-0.45, -0.6, 0.66])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

#: The cube's six faces: (corner indices, pip count, its outward normal).
CORNERS = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], np.float32)
FACES = [
    ((0, 1, 3, 2), 1, (-1, 0, 0)),
    ((4, 6, 7, 5), 6, (1, 0, 0)),
    ((0, 4, 5, 1), 2, (0, -1, 0)),
    ((2, 3, 7, 6), 5, (0, 1, 0)),
    ((0, 2, 6, 4), 3, (0, 0, -1)),
    ((1, 5, 7, 3), 4, (0, 0, 1)),
]
#: Pip positions on a face, in its own (u, v) from -1 to 1.
PIPS = {
    1: [(0, 0)],
    2: [(-0.5, -0.5), (0.5, 0.5)],
    3: [(-0.5, -0.5), (0, 0), (0.5, 0.5)],
    4: [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)],
    5: [(-0.5, -0.5), (0.5, -0.5), (0, 0), (-0.5, 0.5), (0.5, 0.5)],
    6: [(-0.5, -0.55), (0.5, -0.55), (-0.5, 0), (0.5, 0), (-0.5, 0.55), (0.5, 0.55)],
}


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


def _rotation(yaw: float, pitch: float, roll: float) -> np.ndarray:
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return rz @ rx @ ry


@dataclass(frozen=True)
class Pose:
    """One frame: where the die is, how it is turned (radians), how bright,
    and the attack's state."""

    centre: Point = CENTRE
    yaw: float = 0.6
    pitch: float = -0.45
    roll: float = 0.15
    scale: float = 1.0
    glow: float = 0.7
    alpha: float = 1.0
    ghosts: float = 1.0
    twin: float = 0.0
    thread: float = 0.0
    burst: float = -1.0
    shatter: float = 0.0


# --- parts ------------------------------------------------------------------------


def draw_cube(layer: Image.Image, centre: Point, rot: np.ndarray, half: float, alpha: float, glow: float, scramble: int = 0) -> None:
    """The CUBE: its faces of spectral glass lit by their facing (light
    toward the upper left), drawn back to front; glowing teal edges; the
    pips of each face placed on it in 3D. ``scramble`` swaps the faces'
    pips about (a die whose state will not hold)."""
    pts3 = (CORNERS * half) @ rot.T
    proj = [(centre[0] + p[0], centre[1] + p[1]) for p in pts3]
    faces = []
    for k, (idx, pips, normal) in enumerate(FACES):
        n = rot @ np.array(normal, np.float32)
        if n[2] >= -0.02:  # facing away (z toward the viewer is negative)
            continue
        depth = float(np.mean([pts3[i][2] for i in idx]))
        faces.append((depth, idx, FACES[(k + scramble) % 6][1], n))
    faces.sort(key=lambda f: -f[0])
    d = blending_draw(layer)
    for depth, idx, pips, n in faces:
        shade = float(np.clip(np.dot(-n, -LIGHT * np.array([1, 1, -1])), 0.0, 1.0))
        colour = GLASS_DARK + (GLASS_LIGHT - GLASS_DARK) * (0.25 + 0.75 * shade)
        poly = [_s(proj[i]) for i in idx]
        d.polygon(poly, fill=(int(colour[0]), int(colour[1]), int(colour[2]), int(205 * alpha)))
        # The face's pips, on it in 3D: its corners' frame (u along 0->1,
        # v along 0->3).
        p0, p1, p3 = (np.array(proj[idx[0]]), np.array(proj[idx[1]]), np.array(proj[idx[3]]))
        mid = (np.array(proj[idx[0]]) + np.array(proj[idx[2]])) / 2
        u_axis, v_axis = (p1 - p0) / 2, (p3 - p0) / 2
        for u, v in PIPS[pips]:
            c = mid + u_axis * u * 0.9 + v_axis * v * 0.9
            r = 0.16
            ring = [tuple(c + u_axis * r * math.cos(t) + v_axis * r * math.sin(t)) for t in np.linspace(0, math.tau, 12, endpoint=False)]
            d.polygon([_s(q) for q in ring], fill=_a(PIP, alpha))
    # Edges glowing teal, and the outline.
    edges = set()
    for _, idx, _, _ in faces:
        for a, b in zip(idx, idx[1:] + idx[:1]):
            edges.add(tuple(sorted((a, b))))
    _glow(layer, lambda g: [g.line([_s(proj[a]), _s(proj[b])], fill=_a(TEAL, 0.8 * glow * alpha), width=int(2.4 * SUPER)) for a, b in edges], 1.4)
    d = blending_draw(layer)
    for a, b in edges:
        d.line([_s(proj[a]), _s(proj[b])], fill=_a(EDGE, alpha), width=int(0.9 * SUPER))


def draw_superposition(layer: Image.Image, pose: Pose, phase: float) -> None:
    """SUPERPOSITION GHOSTS: faint copies of the die round it, each turned
    to another state, drifting in and out."""
    if pose.ghosts <= 0:
        return
    for k in range(3):
        a = phase + k * 2.1
        off = (math.cos(a) * 9.0, math.sin(a * 1.3) * 6.0)
        rot = _rotation(pose.yaw + 1.2 * (k + 1), pose.pitch + 0.5 * k, pose.roll - 0.7 * k)
        alpha = pose.ghosts * pose.alpha * (0.18 + 0.1 * math.sin(phase * 2 + k))
        draw_cube(layer, (pose.centre[0] + off[0], pose.centre[1] + off[1]), rot, HALF * pose.scale * 0.95, alpha, 0.4, scramble=k + 1)


def draw_entanglement(layer: Image.Image, pose: Pose, phase: float) -> None:
    """The ENTANGLED TWIN, forming ahead, and the THREAD between them: a
    shimmering double strand, twisting, drawn taut as the attack comes."""
    if pose.twin <= 0 and pose.thread <= 0:
        return
    c = pose.centre
    twin_at = (c[0] + TWIN_AHEAD, c[1])
    if pose.thread > 0:
        def strand(g, sign):
            pts = []
            for k in range(25):
                t = k / 24.0
                sag = math.sin(t * math.pi) * 8.0 * (1.0 - pose.thread)
                twist = math.sin(t * math.tau * 2 + phase * 3) * 2.2 * sign
                pts.append(_s((c[0] + (twin_at[0] - c[0]) * t, c[1] + sag + twist)))
            g.line(pts, fill=_a(VIOLET if sign > 0 else TEAL, 0.85 * pose.thread), width=int(1.4 * SUPER), joint="curve")
        _glow(layer, lambda g: (strand(g, 1), strand(g, -1)), 1.2)
        d = blending_draw(layer)
        strand(d, 1)
        strand(d, -1)
    if pose.twin > 0:
        rot = _rotation(-pose.yaw, pose.pitch, -pose.roll)  # its twin: the mirror state
        draw_cube(layer, twin_at, rot, HALF * pose.scale * (0.6 + 0.4 * pose.twin), 0.55 * pose.twin, 1.0, scramble=3)


def draw_collapse(layer: Image.Image, at: Point, u: float) -> None:
    """The COLLAPSE: a burst where the die lands in its twin: a flash, a
    ring, rays of light."""
    if u < 0:
        return
    fade = 1.0 - u
    r = 8.0 + 34.0 * u

    def burst(g):
        g.ellipse((*_s((at[0] - r, at[1] - r)), *_s((at[0] + r, at[1] + r))), outline=_a(TEAL, fade), width=int(2.4 * SUPER))
        g.ellipse((*_s((at[0] - 10 * fade, at[1] - 10 * fade)), *_s((at[0] + 10 * fade, at[1] + 10 * fade))), fill=_a(WHITE, fade))
        for k in range(8):
            a = k * math.tau / 8 + 0.3
            g.line([_s((at[0] + math.cos(a) * r * 0.6, at[1] + math.sin(a) * r * 0.6)), _s((at[0] + math.cos(a) * r * 1.1, at[1] + math.sin(a) * r * 1.1))],
                   fill=_a(VIOLET, fade), width=int(1.4 * SUPER))

    _glow(layer, burst, 2.0)
    burst(blending_draw(layer))


def draw_die(pose: Pose, phase: float, scramble: int = 0) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    c = pose.centre
    _glow(img, lambda g: g.ellipse((*_s((c[0] - 30, c[1] - 30)), *_s((c[0] + 30, c[1] + 30))), fill=_a(VIOLET, 0.22 * pose.alpha * (0.5 + 0.5 * pose.glow))), 8.0)
    draw_superposition(img, pose, phase)
    draw_entanglement(img, pose, phase)
    if pose.shatter > 0:
        # The wavefunction collapses: the die splits into its pips, which
        # fly apart and wink out.
        rng = np.random.default_rng(9)
        d = blending_draw(img)
        for k in range(21):
            a = rng.random() * math.tau
            dist = pose.shatter * (14 + rng.random() * 34)
            p = (c[0] + math.cos(a) * dist, c[1] + math.sin(a) * dist - pose.shatter * 6)
            al = (1.0 - pose.shatter) * (0.6 + 0.4 * rng.random())
            _glow(img, lambda g, p=p, al=al: g.ellipse((*_s((p[0] - 2.4, p[1] - 2.4)), *_s((p[0] + 2.4, p[1] + 2.4))), fill=_a(TEAL, al)), 1.0)
            blending_draw(img).ellipse((*_s((p[0] - 1.3, p[1] - 1.3)), *_s((p[0] + 1.3, p[1] + 1.3))), fill=_a(PIP, al))
    if pose.alpha > 0.02:
        draw_cube(img, c, _rotation(pose.yaw, pose.pitch, pose.roll), HALF * pose.scale, pose.alpha, pose.glow, scramble)
    draw_collapse(img, c, pose.burst)
    # Motes.
    rng = np.random.default_rng(4)
    d = blending_draw(img)
    for _ in range(8):
        x, y, ph = c[0] - 30 + rng.random() * 60, c[1] - 30 + rng.random() * 60, rng.random()
        yy = y - ((phase / math.tau + ph) % 1.0) * 14
        d.ellipse((*_s((x - 0.8, yy - 0.8)), *_s((x + 0.8, yy + 0.8))), fill=_a(PIP, 0.6 * pose.alpha))
    return img


def _pose_for(animation: str, i: int, n: int) -> Tuple[Pose, float, int]:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    # A quarter turn a loop on each axis: a die's quarter turn shows a die
    # again, so the tumble loops without a seam.
    base = Pose(centre=(CENTRE[0], CENTRE[1] + 3 * w), yaw=0.6 + t * math.pi / 2, pitch=-0.45 + 0.1 * w, roll=0.15, glow=0.6 + 0.25 * w)
    if animation == "idle":
        return base, t * math.tau, 0
    if animation == "walk":
        return replace(base, yaw=0.6 + t * math.pi, roll=0.15 + t * math.pi / 2, centre=(CENTRE[0] + 2 * w, CENTRE[1])), t * math.tau * 2, 0
    if animation == "attack_side":
        if i <= 4:  # the twin forms ahead, the thread draws taut
            k = i / 4.0
            return replace(base, twin=k, thread=k, glow=0.7 + 0.3 * k, ghosts=1.0 - 0.6 * k, scale=1.0 + 0.08 * k), t * math.tau, 0
        if i <= 7:  # the collapse: it is the twin now
            k = (i - 5) / 2.0
            return replace(base, centre=(CENTRE[0] + TWIN_AHEAD * 0.0, CENTRE[1]), twin=0.0, thread=0.0, burst=0.1 + 0.85 * k,
                           ghosts=0.0, glow=1.0, scale=1.0 + 0.1 * (1 - k)), t * math.tau, 0
        k = (i - 8) / 3.0  # decohered: dim and still, ghosts slowly back
        return replace(base, yaw=0.6, glow=0.3 + 0.3 * k, ghosts=0.4 * k, scale=0.95), 0.0, 0
    if animation == "hurt":
        return replace(base, glow=1.0, ghosts=1.4, roll=0.15 + 0.5 * (1 - u)), t * math.tau, i + 1
    if animation == "death":
        return replace(base, shatter=u, alpha=max(0.0, 1.0 - u * 2.5), ghosts=max(0.0, 1.0 - u * 3), glow=1.0), t * math.tau, 0
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    pose, phase, scramble = _pose_for(animation, frame_index, nframes)
    return draw_die(pose, phase, scramble).resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Quantum Die"},
    "body": {
        "body_plan": "Amorphous",
        "body_kind": "Entity",
        "mass_class": "Light",
        "traits": ["spectral", "quantum", "die", "math", "floating"],
        "locomotion_hint": "Float",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["math", "spectral", "enemy", "hylberts_hotel"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
