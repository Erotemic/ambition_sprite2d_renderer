from __future__ import annotations

import argparse
import copy
import io
import math
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont, ImageOps

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, sample_channel_spec
from ambition_sprite2d_renderer.authoring.skeleton import BoneWorld, two_bone_ik
from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as player_robot_v3_target

AUTHOR_RIG_PATH = ROOT / "assets" / "rigs" / "author_vanity" / "author_vanity.rig.json"
ROBOT_RIG_PATH = player_robot_v3_target.RIG_PATH
GAMEPAD_SVG_PATH = ROOT / "assets" / "gamepad-draft.svg"
DEFAULT_OUT_DIR = ROOT / "agent-scratch" / "author_vanity_dialog"

CANVAS_SIZE = (640, 360)
CARD_MARGIN = 8
CARD_FILL = (246, 247, 251, 255)
CARD_OUTLINE = (210, 216, 228, 255)
TEXT_RGBA = (32, 36, 46, 255)
BUBBLE_FILL = (255, 255, 255, 255)
BUBBLE_OUTLINE = (168, 178, 198, 255)
RENDER_SCALE = 2
SUPERSAMPLE = 2
FLOOR_Y = 326
ROBOT_X_END = 330.0
AUTHOR_X = 450.0
ROBOT_TARGET_HEIGHT = 190.0
AUTHOR_TARGET_HEIGHT = 264.0
ANIMATION_FRAMES = 80
FRAME_DURATION_MS = 95


@dataclass(frozen=True)
class ActorStyle:
    effective_scale: float
    render_scale: int
    frame_width: float
    frame_height: float
    center_x: float
    ground_y: float


@dataclass(frozen=True)
class ActorLayer:
    image: Image.Image
    paste_xy: Tuple[int, int]


@dataclass(frozen=True)
class ActorPlacement:
    name: str
    style: ActorStyle
    x_center: float
    baseline_y: float
    world: Dict[str, BoneWorld]
    params: Dict[str, float]
    full_origin: Tuple[float, float]
    mirrored: bool
    full_layer: ActorLayer
    hand_layer: ActorLayer

    def point_for_bone(self, bone_name: str, *, use_tip: bool = False) -> Tuple[float, float]:
        bone = self.world[bone_name]
        point = bone.tip if use_tip else bone.origin
        x = point[0] * self.style.effective_scale
        y = point[1] * self.style.effective_scale
        if self.mirrored:
            x = self.style.frame_width - x
        return (self.full_origin[0] + x, self.full_origin[1] + y)

    def hand_point(self, side: str) -> Tuple[float, float]:
        return self.point_for_bone(f"{side}_arm_hand", use_tip=True)

    def head_anchor(self) -> Tuple[float, float]:
        x, y = self.point_for_bone("head")
        return (x, y - 28.0)

    def screen_to_doc(self, point: Tuple[float, float]) -> Tuple[float, float]:
        x = point[0] - self.full_origin[0]
        y = point[1] - self.full_origin[1]
        if self.mirrored:
            x = self.style.frame_width - x
        return (x / self.style.effective_scale, y / self.style.effective_scale)


@dataclass(frozen=True)
class TimelineState:
    frame_index: int
    robot_x: float
    author_x: float
    robot_clip: str
    robot_t: float
    author_clip: str
    author_t: float
    gamepad_center: Tuple[float, float]
    gamepad_angle: float
    robot_holds: bool
    author_holds: bool
    robot_arm_strength: float
    author_reach_strength: float
    author_body_lean: float
    author_head_tilt: float
    robot_head_tilt: float
    bubble_speaker: Optional[str]
    bubble_text: Optional[str]
    blink_closed: bool


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _smoothstep(value: float) -> float:
    value = _clamp(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_point(a: Tuple[float, float], b: Tuple[float, float], t: float) -> Tuple[float, float]:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def _phase(frame_index: int, start: int, end: int) -> float:
    if end <= start:
        return 1.0
    return _clamp((frame_index - start) / float(end - start), 0.0, 1.0)


def ensure_rigs_exist() -> None:
    checks = [
        (
            AUTHOR_RIG_PATH,
            [sys.executable, str(ROOT / "scripts" / "build_author_vanity_rig.py"), "build"],
        ),
        (
            ROBOT_RIG_PATH,
            [sys.executable, str(ROOT / "scripts" / "build_player_robot_v3_svg.py"), "build"],
        ),
    ]
    for path, command in checks:
        if not path.exists():
            subprocess.run(command, check=True, cwd=ROOT)


def parts_include_doc(doc: RigDocument, names: Sequence[str]) -> RigDocument:
    wanted = set(names)
    data = copy.deepcopy(doc.data)
    data["parts"] = [part for part in data.get("parts", []) if str(part.get("name", "")) in wanted]
    return RigDocument(data, source_path=doc.source_path)


def parts_exclude_doc(doc: RigDocument, names: Sequence[str]) -> RigDocument:
    blocked = set(names)
    data = copy.deepcopy(doc.data)
    data["parts"] = [part for part in data.get("parts", []) if str(part.get("name", "")) not in blocked]
    return RigDocument(data, source_path=doc.source_path)


def hand_only_doc(doc: RigDocument) -> RigDocument:
    data = copy.deepcopy(doc.data)
    data["parts"] = [part for part in data.get("parts", []) if "hand" in str(part.get("name", ""))]
    return RigDocument(data, source_path=doc.source_path)


def pick_clip(doc: RigDocument, requested: str, fallback: str) -> str:
    if requested in doc.clips:
        return requested
    if fallback in doc.clips:
        return fallback
    if doc.clips:
        return next(iter(doc.clips))
    raise ValueError(f"rig {doc.name!r} has no clips")


def sample_params(doc: RigDocument, clip_name: str, t: float) -> Dict[str, float]:
    clip = doc.clips.get(clip_name) or {"channels": {}}
    loop = bool(clip.get("loop", True))
    return {
        name: sample_channel_spec(spec, t, loop)
        for name, spec in clip.get("channels", {}).items()
    }


def solve_doc(
    doc: RigDocument,
    clip_name: str,
    t: float,
    *,
    channel_overrides: Optional[Dict[str, float]] = None,
    pose_overrides: Optional[Dict[str, float]] = None,
    param_overrides: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, BoneWorld], Dict[str, float]]:
    params = sample_params(doc, clip_name, t)
    if channel_overrides:
        params.update(channel_overrides)
    if param_overrides:
        params.update(param_overrides)

    frame = doc.frame
    cx = float(frame.get("center_x", frame["width"] / 2))
    gy = float(frame.get("ground_y", frame["height"] - 2))
    ankle_h = float(frame.get("ankle_h", 0.0))
    root = (cx + params.get("root_x", 0.0), gy + params.get("root_y", 0.0))
    skeleton = doc.build_skeleton()
    angles = {name: value for name, value in params.items() if name in skeleton.bones}
    if pose_overrides:
        angles.update(pose_overrides)
    initial_world = skeleton.world(angles, root=root)

    def solve_chain(chain: dict, target: Tuple[float, float], pitch: Optional[float], bend: float) -> None:
        upper_name = str(chain["upper"])
        lower_name = str(chain["lower"])
        end_name = chain.get("end") or chain.get("foot")
        if upper_name not in skeleton.bones or lower_name not in skeleton.bones:
            return
        origin = initial_world[upper_name].origin
        upper_world, lower_world = two_bone_ik(
            origin,
            target,
            skeleton.bones[upper_name].length,
            skeleton.bones[lower_name].length,
            bend=bend,
        )
        parent_name = skeleton.bones[upper_name].parent
        parent_angle = initial_world[parent_name].angle if parent_name else 0.0
        angles[upper_name] = upper_world - parent_angle - skeleton.bones[upper_name].rest_angle
        angles[lower_name] = lower_world - upper_world - skeleton.bones[lower_name].rest_angle
        if end_name and end_name in skeleton.bones and pitch is not None:
            angles[end_name] = pitch - lower_world - skeleton.bones[end_name].rest_angle

    for leg in doc.ik_legs:
        prefix = str(leg.get("channel_prefix", "foot"))
        x = params.get(f"{prefix}_x", float(leg.get("rest_x", 0.0)))
        lift = params.get(f"{prefix}_lift", float(leg.get("rest_lift", 0.0)))
        pitch = params.get(f"{prefix}_pitch", float(leg.get("rest_pitch", 0.0)))
        bend = params.get(f"{prefix}_bend", float(leg.get("bend", 1.0)))
        solve_chain(leg, (cx + x, gy - ankle_h - lift), pitch, float(bend))

    for chain in doc.ik_chains:
        prefix = str(chain.get("channel_prefix", "target"))
        x = params.get(f"{prefix}_x", float(chain.get("rest_x", 0.0)))
        y = params.get(f"{prefix}_y", float(chain.get("rest_y", 0.0)))
        pitch = params.get(f"{prefix}_pitch", float(chain.get("rest_pitch", 0.0)))
        bend = params.get(f"{prefix}_bend", float(chain.get("bend", 1.0)))
        solve_chain(chain, (cx + x, gy + y), pitch, float(bend))

    return skeleton.world(angles, root=root), params


def calculate_style(doc: RigDocument, clip_name: str, target_height: float) -> ActorStyle:
    world, params = solve_doc(doc, clip_name, 0.0)
    image = doc.render_at(clip_name, 0.0, supersample=SUPERSAMPLE, scale=RENDER_SCALE, solved=(world, params))
    bbox = image.getbbox()
    if bbox is None:
        raise RuntimeError(f"empty reference pose for {doc.name}")
    source_height = (bbox[3] - bbox[1]) / float(RENDER_SCALE)
    effective_scale = target_height / max(1.0, source_height)
    frame = doc.frame
    return ActorStyle(
        effective_scale=effective_scale,
        render_scale=RENDER_SCALE,
        frame_width=float(frame["width"]) * effective_scale,
        frame_height=float(frame["height"]) * effective_scale,
        center_x=float(frame.get("center_x", frame["width"] / 2)),
        ground_y=float(frame.get("ground_y", frame["height"] - 2)),
    )


def render_layer(
    doc: RigDocument,
    clip_name: str,
    t: float,
    world: Dict[str, BoneWorld],
    params: Dict[str, float],
    style: ActorStyle,
    x_center: float,
    baseline_y: float,
    *,
    mirrored: bool,
) -> Tuple[ActorLayer, Tuple[float, float]]:
    raw = doc.render_at(clip_name, t, supersample=SUPERSAMPLE, scale=style.render_scale, solved=(world, params))
    display_width = max(1, int(round(float(doc.frame["width"]) * style.effective_scale)))
    display_height = max(1, int(round(float(doc.frame["height"]) * style.effective_scale)))
    displayed = raw.resize((display_width, display_height), Image.Resampling.LANCZOS)
    if mirrored:
        displayed = ImageOps.mirror(displayed)
    full_origin = (
        x_center - style.center_x * style.effective_scale,
        baseline_y - style.ground_y * style.effective_scale,
    )
    bbox = displayed.getbbox()
    if bbox is None:
        return ActorLayer(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), (0, 0)), full_origin
    cropped = displayed.crop(bbox)
    paste = (int(round(full_origin[0] + bbox[0])), int(round(full_origin[1] + bbox[1])))
    return ActorLayer(cropped, paste), full_origin


def build_actor(
    doc: RigDocument,
    hands_doc: RigDocument,
    style: ActorStyle,
    *,
    name: str,
    clip_name: str,
    t: float,
    x_center: float,
    baseline_y: float,
    channel_overrides: Optional[Dict[str, float]] = None,
    pose_overrides: Optional[Dict[str, float]] = None,
    param_overrides: Optional[Dict[str, float]] = None,
    mirrored: bool = False,
) -> ActorPlacement:
    world, params = solve_doc(
        doc,
        clip_name,
        t,
        channel_overrides=channel_overrides,
        pose_overrides=pose_overrides,
        param_overrides=param_overrides,
    )
    full_layer, full_origin = render_layer(
        doc, clip_name, t, world, params, style, x_center, baseline_y, mirrored=mirrored
    )
    hand_layer, _ = render_layer(
        hands_doc, clip_name, t, world, params, style, x_center, baseline_y, mirrored=mirrored
    )
    return ActorPlacement(
        name=name,
        style=style,
        x_center=x_center,
        baseline_y=baseline_y,
        world=world,
        params=params,
        full_origin=full_origin,
        mirrored=mirrored,
        full_layer=full_layer,
        hand_layer=hand_layer,
    )


def arm_pose_for_targets(
    doc: RigDocument,
    base_world: Dict[str, BoneWorld],
    targets: Dict[str, Tuple[float, float]],
    *,
    pitches: Optional[Dict[str, float]] = None,
    bends: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    skeleton = doc.build_skeleton()
    result: Dict[str, float] = {}
    pitches = pitches or {}
    bends = bends or {}
    for side, target in targets.items():
        upper_name = f"{side}_arm_u"
        lower_name = f"{side}_arm_l"
        hand_name = f"{side}_arm_hand"
        origin = base_world[upper_name].origin
        upper_world, lower_world = two_bone_ik(
            origin,
            target,
            skeleton.bones[upper_name].length,
            skeleton.bones[lower_name].length,
            bend=float(bends.get(side, 1.0)),
        )
        parent_name = skeleton.bones[upper_name].parent
        parent_angle = base_world[parent_name].angle if parent_name else 0.0
        result[upper_name] = upper_world - parent_angle - skeleton.bones[upper_name].rest_angle
        result[lower_name] = lower_world - upper_world - skeleton.bones[lower_name].rest_angle
        pitch = float(pitches.get(side, lower_world))
        result[hand_name] = pitch - lower_world - skeleton.bones[hand_name].rest_angle
    return result


def timeline_state(frame_index: int) -> TimelineState:
    # 00-11: robot walks in carrying the gamepad.
    if frame_index <= 11:
        t = _smoothstep(_phase(frame_index, 0, 11))
        robot_x = _lerp(72.0, ROBOT_X_END, t)
        gamepad = (robot_x + 30.0, 265.0 - 2.0 * math.sin(frame_index * math.pi / 2.0))
        return TimelineState(
            frame_index, robot_x, AUTHOR_X,
            "walk", (frame_index * 0.23) % 1.0,
            "vanity_idle", (frame_index / ANIMATION_FRAMES) % 1.0,
            gamepad, -2.0, True, False,
            1.0, 0.0, 0.0, 0.0, 0.0,
            None, None, False,
        )

    # 12-23: robot presents the controller and holds the line long enough to read.
    if frame_index <= 23:
        t = _smoothstep(_phase(frame_index, 12, 16))
        hold = _phase(frame_index, 12, 23)
        gamepad = _lerp_point((ROBOT_X_END + 30.0, 265.0), (368.0, 228.0), t)
        return TimelineState(
            frame_index, ROBOT_X_END, AUTHOR_X,
            "idle", (0.22 + 0.12 * hold) % 1.0,
            "vanity_idle", (0.24 + 0.08 * hold) % 1.0,
            gamepad, -5.0, True, False,
            1.0, 0.0, 0.0, 0.0, 0.0,
            "robot", "I made this.", False,
        )

    # 24-35: author reacts, leaning down slightly, with enough pause for the beat.
    if frame_index <= 35:
        t = _smoothstep(_phase(frame_index, 24, 28))
        hold = _phase(frame_index, 24, 35)
        gamepad = (368.0, 228.0)
        reach = 0.35 * min(1.0, t)
        lean = 0.22 * min(1.0, t)
        head = 8.0 * min(1.0, t)
        return TimelineState(
            frame_index, ROBOT_X_END, AUTHOR_X,
            "idle", (0.34 + 0.10 * hold) % 1.0,
            "vanity_receive", 0.10 + 0.16 * min(1.0, t),
            gamepad, -5.0, True, False,
            1.0, reach, lean, head, 0.0,
            "author", "You made this?", False,
        )

    # 36-43: handoff and take.
    if frame_index <= 43:
        t = _smoothstep(_phase(frame_index, 36, 43))
        gamepad = _lerp_point((368.0, 228.0), (388.0, 214.0), t)
        return TimelineState(
            frame_index, ROBOT_X_END, AUTHOR_X,
            "idle", (0.40 + 0.10 * t) % 1.0,
            "vanity_receive", 0.28 + 0.40 * t,
            gamepad, -4.0 + 10.0 * t, True, True,
            1.0 - 0.55 * t, 0.42 + 0.55 * t, 0.45 + 0.30 * t, 10.0 + 4.0 * t, 0.0,
            None, None, False,
        )

    # 44-49: author straightens and lifts the gamepad up closer to inspect it.
    if frame_index <= 49:
        t = _smoothstep(_phase(frame_index, 44, 49))
        gamepad = _lerp_point((388.0, 214.0), (418.0, 182.0), t)
        return TimelineState(
            frame_index, ROBOT_X_END - 4.0 * t, AUTHOR_X,
            "idle", (0.52 + 0.06 * t) % 1.0,
            "vanity_receive", 0.70 + 0.20 * t,
            gamepad, 8.0 + 12.0 * t, False, True,
            0.18 * (1.0 - t), 0.34, 0.04 * (1.0 - t), 12.0 + 4.0 * t, 0.0,
            None, None, False,
        )

    # 50-57: contemplative inspection pause while holding the gamepad up.
    if frame_index <= 57:
        hold = _phase(frame_index, 50, 57)
        bob = math.sin(hold * math.pi)
        return TimelineState(
            frame_index, ROBOT_X_END - 4.0, AUTHOR_X,
            "idle", (0.56 + 0.08 * hold) % 1.0,
            "vanity_receive", 0.90 + 0.04 * hold,
            (418.0, 182.0 - 1.5 * bob), 20.0, False, True,
            0.0, 0.34, 0.0, 16.0, 0.0,
            None, None, False,
        )

    # 58-61: author delivers the line after the inspect beat.
    if frame_index <= 61:
        hold = _phase(frame_index, 58, 61)
        return TimelineState(
            frame_index, ROBOT_X_END - 4.0, AUTHOR_X,
            "idle", (0.60 + 0.05 * hold) % 1.0,
            "vanity_receive", 0.92 + 0.02 * hold,
            (418.0, 182.0), 20.0, False, True,
            0.0, 0.34, 0.0, 16.0, 0.0,
            "author", "I made this.", False,
        )

    # 62-79: robot closes its eyes, tips its head down, and the shot lingers.
    linger = _phase(frame_index, 62, 79)
    author_bob = math.sin(linger * 2.0 * math.pi)
    return TimelineState(
        frame_index, ROBOT_X_END - 4.0, AUTHOR_X,
        "idle", (0.64 + 0.10 * linger) % 1.0,
        "vanity_receive", 0.90 + 0.04 * linger,
        (418.0, 182.0 - 1.2 * author_bob), 20.0, False, True,
        0.0, 0.34, 0.0, 16.0, 10.0,
        "author", "I made this.", True,
    )


def render_gamepad(width: int = 72) -> Image.Image:
    if not GAMEPAD_SVG_PATH.exists():
        raise FileNotFoundError(f"required prop SVG is missing: {GAMEPAD_SVG_PATH}")
    errors: List[str] = []
    try:
        import resvg_py

        png = resvg_py.svg_to_bytes(
            svg_string=GAMEPAD_SVG_PATH.read_text(encoding="utf-8"), dpi=96.0
        )
        image = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    except Exception as ex:
        errors.append(f"resvg_py: {ex}")
        try:
            import cairosvg

            png = cairosvg.svg2png(url=str(GAMEPAD_SVG_PATH))
            image = Image.open(io.BytesIO(png)).convert("RGBA")
        except Exception as ex2:
            errors.append(f"cairosvg: {ex2}")
            raise RuntimeError("could not rasterize gamepad-draft.svg: " + "; ".join(errors))
    bbox = image.getbbox()
    if bbox is None:
        raise RuntimeError("gamepad-draft.svg rendered empty")
    image = image.crop(bbox)
    height = max(1, int(round(image.height * width / image.width)))
    return image.resize((width, height), Image.Resampling.LANCZOS)


_FONT_CACHE: Dict[int, ImageFont.ImageFont] = {}


def load_font(size: int) -> ImageFont.ImageFont:
    if size not in _FONT_CACHE:
        try:
            _FONT_CACHE[size] = ImageFont.truetype("DejaVuSans.ttf", size)
        except Exception:
            _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=3)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    scratch = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scratch)
    lines: List[str] = []
    current: List[str] = []
    for word in text.split():
        candidate = " ".join(current + [word])
        if current and measure_text(draw, candidate, font)[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def draw_speech_bubble(
    canvas: Image.Image,
    text: str,
    tail: Tuple[float, float],
    box_xy: Tuple[int, int],
    *,
    max_width: int = 160,
) -> None:
    font = load_font(18)
    wrapped = wrap_text(text, font, max_width)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    text_w, text_h = measure_text(draw, wrapped, font)
    pad_x, pad_y = 13, 9
    x0, y0 = box_xy
    x1 = x0 + text_w + pad_x * 2
    y1 = y0 + text_h + pad_y * 2
    x0 = int(_clamp(x0, 12, canvas.width - (x1 - x0) - 12))
    y0 = int(_clamp(y0, 12, canvas.height - (y1 - y0) - 12))
    x1 = x0 + text_w + pad_x * 2
    y1 = y0 + text_h + pad_y * 2
    attach_x = int(_clamp(tail[0], x0 + 20, x1 - 20))
    triangle = [(attach_x - 10, y1 - 2), (attach_x + 8, y1 - 2), (int(tail[0]), int(tail[1]))]
    draw.polygon(triangle, fill=BUBBLE_FILL, outline=BUBBLE_OUTLINE)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=13, fill=BUBBLE_FILL, outline=BUBBLE_OUTLINE, width=1)
    draw.multiline_text((x0 + pad_x, y0 + pad_y), wrapped, font=font, fill=TEXT_RGBA, spacing=3)
    canvas.alpha_composite(layer)


def draw_background(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (CARD_MARGIN, CARD_MARGIN, canvas.width - CARD_MARGIN, canvas.height - CARD_MARGIN),
        radius=22,
        fill=CARD_FILL,
        outline=CARD_OUTLINE,
        width=2,
    )


def draw_rotated_prop(canvas: Image.Image, prop: Image.Image, center: Tuple[float, float], angle: float) -> None:
    rotated = prop.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(
        rotated,
        (int(round(center[0] - rotated.width / 2)), int(round(center[1] - rotated.height / 2))),
    )


def make_actor_for_state(
    doc: RigDocument,
    hands_doc: RigDocument,
    style: ActorStyle,
    *,
    name: str,
    clip_name: str,
    t: float,
    x_center: float,
    arm_targets_screen: Optional[Dict[str, Tuple[float, float]]] = None,
    arm_pitches: Optional[Dict[str, float]] = None,
    arm_bends: Optional[Dict[str, float]] = None,
    param_overrides: Optional[Dict[str, float]] = None,
    body_pose: Optional[Dict[str, float]] = None,
) -> ActorPlacement:
    clip_name = pick_clip(doc, clip_name, "idle" if name == "robot" else "vanity_idle")
    base_world, _ = solve_doc(doc, clip_name, t, pose_overrides=body_pose, param_overrides=param_overrides)
    temporary = build_actor(
        doc,
        hands_doc,
        style,
        name=name,
        clip_name=clip_name,
        t=t,
        x_center=x_center,
        baseline_y=FLOOR_Y,
        pose_overrides=body_pose,
        param_overrides=param_overrides,
    )
    pose_overrides: Dict[str, float] = dict(body_pose or {})
    channel_overrides: Dict[str, float] = {}
    if arm_targets_screen:
        targets_doc = {
            side: temporary.screen_to_doc(point)
            for side, point in arm_targets_screen.items()
        }
        if doc.ik_chains:
            cx = float(doc.frame.get("center_x", doc.frame["width"] / 2))
            gy = float(doc.frame.get("ground_y", doc.frame["height"] - 2))
            for side, target in targets_doc.items():
                prefix = f"{side}_hand"
                channel_overrides[f"{prefix}_x"] = target[0] - cx
                channel_overrides[f"{prefix}_y"] = target[1] - gy
                channel_overrides[f"{prefix}_pitch"] = float((arm_pitches or {}).get(side, 170.0))
                channel_overrides[f"{prefix}_bend"] = float((arm_bends or {}).get(side, 1.0))
        else:
            pose_overrides = arm_pose_for_targets(
                doc,
                base_world,
                targets_doc,
                pitches=arm_pitches,
                bends=arm_bends,
            )
    return build_actor(
        doc,
        hands_doc,
        style,
        name=name,
        clip_name=clip_name,
        t=t,
        x_center=x_center,
        baseline_y=FLOOR_Y,
        channel_overrides=channel_overrides,
        pose_overrides=pose_overrides,
        param_overrides=param_overrides,
    )


def compose_actors(
    state: TimelineState,
    author_doc: RigDocument,
    author_hands_doc: RigDocument,
    author_style: ActorStyle,
    robot_doc: RigDocument,
    robot_hands_doc: RigDocument,
    robot_style: ActorStyle,
    prop_width: int,
) -> Tuple[ActorPlacement, ActorPlacement]:
    """Solve both actors for one frame — the IK, the reach, the head tilts.

    Split out of :func:`render_frame` so the ENGINE EXPORT and the GIF share one
    definition of where everybody is. Exporting baked placements from a second
    copy of this arithmetic would produce a card that agrees with itself and
    with nothing else; when the choreography is retuned here, both outputs move
    together or neither does.
    """
    prop_half = prop_width * 0.32
    robot_targets = None
    if state.robot_arm_strength > 0.02:
        lower_y = state.gamepad_center[1] + 5.0
        robot_targets = {
            "near": (state.gamepad_center[0] - prop_half, lower_y + 1.0),
            "far": (state.gamepad_center[0] + prop_half, lower_y - 2.0),
        }
    robot_face = {
        "face_open_vis": 0.0 if state.blink_closed else 1.0,
        "blink_vis": 1.0 if state.blink_closed else 0.0,
    }
    robot = make_actor_for_state(
        robot_doc,
        robot_hands_doc,
        robot_style,
        name="robot",
        clip_name=state.robot_clip,
        t=state.robot_t,
        x_center=state.robot_x,
        arm_targets_screen=robot_targets,
        arm_pitches={"far": 2.0, "near": -2.0},
        arm_bends={"far": 1.0, "near": -1.0},
        body_pose={"head": state.robot_head_tilt},
        param_overrides=robot_face,
    )

    author_targets = None
    if state.author_reach_strength > 0.02:
        author_targets = {
            "far": (state.gamepad_center[0] - prop_half * 0.72, state.gamepad_center[1] + 6.0),
            "near": (state.gamepad_center[0] + prop_half * 0.80, state.gamepad_center[1] + 3.0),
        }
    author = make_actor_for_state(
        author_doc,
        author_hands_doc,
        author_style,
        name="author",
        clip_name=state.author_clip,
        t=state.author_t,
        x_center=state.author_x,
        arm_targets_screen=author_targets,
        arm_pitches={"far": 166.0, "near": 174.0},
        arm_bends={"far": -1.0, "near": 1.0},
        body_pose={
            "torso": -18.0 * state.author_body_lean,
            "head": state.author_head_tilt,
            "pelvis": 1.5 * state.author_body_lean,
        },
    )
    return robot, author


def render_frame(
    state: TimelineState,
    author_doc: RigDocument,
    author_hands_doc: RigDocument,
    author_body_doc: RigDocument,
    author_near_arm_doc: RigDocument,
    author_style: ActorStyle,
    robot_doc: RigDocument,
    robot_hands_doc: RigDocument,
    robot_style: ActorStyle,
    prop: Image.Image,
) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw_background(canvas)

    robot, author = compose_actors(
        state,
        author_doc,
        author_hands_doc,
        author_style,
        robot_doc,
        robot_hands_doc,
        robot_style,
        prop.width,
    )

    author_body_layer, _ = render_layer(
        author_body_doc, state.author_clip, state.author_t, author.world, author.params,
        author_style, state.author_x, FLOOR_Y, mirrored=False
    )
    author_near_arm_layer, _ = render_layer(
        author_near_arm_doc, state.author_clip, state.author_t, author.world, author.params,
        author_style, state.author_x, FLOOR_Y, mirrored=False
    )

    canvas.alpha_composite(robot.full_layer.image, robot.full_layer.paste_xy)
    canvas.alpha_composite(author_body_layer.image, author_body_layer.paste_xy)
    draw_rotated_prop(canvas, prop, state.gamepad_center, state.gamepad_angle)

    # Keep the gamepad between the author's far and near limbs: the body layer
    # already contains the far-side arm and hand, while the near-side arm is
    # always composited above the prop. This also avoids the early-frame bug
    # where the author's near arm vanished entirely.
    canvas.alpha_composite(author_near_arm_layer.image, author_near_arm_layer.paste_xy)

    if state.bubble_speaker == "robot" and state.bubble_text:
        draw_speech_bubble(
            canvas,
            state.bubble_text,
            robot.head_anchor(),
            (155, 52),
        )
    elif state.bubble_speaker == "author" and state.bubble_text:
        draw_speech_bubble(
            canvas,
            state.bubble_text,
            author.head_anchor(),
            (388, 24),
        )
    return canvas


def gif_frame_from_rgba(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = Image.new("RGB", rgba.size, (255, 255, 255))
    rgb.paste(rgba, mask=alpha)
    pal = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    palette = pal.getpalette() or []
    palette = [0, 0, 0] + palette[: 255 * 3]
    palette += [0] * (768 - len(palette))
    shifted = pal.point(lambda value: min(255, value + 1))
    shifted.putpalette(palette)
    mask = alpha.point(lambda value: 255 if value == 0 else 0)
    shifted.paste(0, mask=mask)
    shifted.info["transparency"] = 0
    shifted.info["disposal"] = 2
    return shifted


def save_storyboards(frames: Sequence[Image.Image], out_dir: Path) -> List[Path]:
    key_indices = [0, 14, 26, 39, 47, 54, 60, 74]
    labels = [
        "walk in",
        "robot claim",
        "author reaction",
        "take it",
        "lift up",
        "inspect",
        "author claim",
        "linger",
    ]
    key_frames = [frames[index] for index in key_indices]
    strip = Image.new("RGBA", (CANVAS_SIZE[0] * len(key_frames), CANVAS_SIZE[1] + 28), (0, 0, 0, 0))
    draw = ImageDraw.Draw(strip)
    font = load_font(14)
    for index, (frame, label) in enumerate(zip(key_frames, labels)):
        x = index * CANVAS_SIZE[0]
        strip.alpha_composite(frame, (x, 0))
        width, _ = measure_text(draw, label, font)
        draw.text((x + (CANVAS_SIZE[0] - width) / 2, CANVAS_SIZE[1] + 5), label, font=font, fill=(90, 98, 118, 255))
    strip_path = out_dir / "author_vanity_dialog_strip.png"
    strip.save(strip_path)

    tile_w, tile_h = 480, 270
    cols = 3
    rows = (len(key_frames) + cols - 1) // cols
    board = Image.new("RGBA", (tile_w * cols, (tile_h + 24) * rows), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(board)
    for index, (frame, label) in enumerate(zip(key_frames, labels)):
        shown = frame.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        x = (index % 3) * tile_w
        y = (index // 3) * (tile_h + 24)
        board.alpha_composite(shown, (x, y))
        width, _ = measure_text(bdraw, label, font)
        bdraw.text((x + (tile_w - width) / 2, y + tile_h + 4), label, font=font, fill=(90, 98, 118, 255))
    board_path = out_dir / "author_vanity_dialog_storyboard.png"
    board.save(board_path)
    return [strip_path, board_path]


def build_dialog_sequence(out_dir: Path) -> List[Path]:
    ensure_rigs_exist()
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    author_doc = RigDocument.load(AUTHOR_RIG_PATH)
    robot_doc = player_robot_v3_target.load_doc()
    author_hands_doc = hand_only_doc(author_doc)
    robot_hands_doc = hand_only_doc(robot_doc)
    author_near_arm_doc = parts_include_doc(author_doc, ["near_arm_u", "near_arm_l", "near_sleeve", "near_hand"])
    author_body_doc = parts_exclude_doc(author_doc, ["near_arm_u", "near_arm_l", "near_sleeve", "near_hand"])
    author_style = calculate_style(author_doc, "vanity_idle", AUTHOR_TARGET_HEIGHT)
    robot_style = calculate_style(robot_doc, "idle", ROBOT_TARGET_HEIGHT)
    prop = render_gamepad()

    frames: List[Image.Image] = []
    outputs: List[Path] = []
    for frame_index in range(ANIMATION_FRAMES):
        state = timeline_state(frame_index)
        frame = render_frame(
            state,
            author_doc,
            author_hands_doc,
            author_body_doc,
            author_near_arm_doc,
            author_style,
            robot_doc,
            robot_hands_doc,
            robot_style,
            prop,
        )
        path = frames_dir / f"frame_{frame_index:03d}.png"
        frame.save(path)
        outputs.append(path)
        frames.append(frame)

    outputs.extend(save_storyboards(frames, out_dir))

    gif_path = out_dir / "author_vanity_dialog.gif"
    gif_frames = [gif_frame_from_rgba(frame) for frame in frames]
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=False,
        disposal=2,
        transparency=0,
    )
    outputs.append(gif_path)

    webp_path = out_dir / "author_vanity_dialog.webp"
    frames[0].save(
        webp_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        lossless=True,
    )
    outputs.append(webp_path)

    manifest_path = out_dir / "author_vanity_dialog_manifest.txt"
    manifest_path.write_text(
        "\n".join(
            [
                "Author vanity dialog animation",
                f"frames={ANIMATION_FRAMES}",
                f"duration_ms={FRAME_DURATION_MS}",
                f"author_rig={AUTHOR_RIG_PATH.relative_to(ROOT)}",
                f"robot_rig={ROBOT_RIG_PATH.relative_to(ROOT)}",
                f"prop={GAMEPAD_SVG_PATH.relative_to(ROOT)}",
                "robot path: walk in -> stop -> lift prop -> handoff -> relax",
                "author path: idle -> look/question -> IK reach down -> take -> hold",
                "blink: discrete open/closed visibility only; no opacity tween",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    outputs.append(manifest_path)
    return outputs


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the polished Author vanity-card animation.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    outputs = build_dialog_sequence(args.out_dir)
    print("Wrote:")
    for path in outputs:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
