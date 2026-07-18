"""Portrait-sheet authoring shared by independent sprite-generator families.

A portrait is a separately rendered presentation asset, never a crop enlarged
from a published gameplay sprite sheet.  This module owns only the common
*output* vocabulary (named clips, frame rectangles, RON manifest) and a useful
head-and-shoulders compositor for scalable renderers.  Targets remain free to
produce the source image with procedural Python, a rig, SVG parts, or any other
appropriate authoring method.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image

DEFAULT_PORTRAIT_SIZE = (256, 320)
DEFAULT_PORTRAIT_SUPERSAMPLE = 4


@dataclass(frozen=True)
class FaceGuide:
    """Logical face region used to compose a default portrait.

    Coordinates live in the target's authored source canvas, not in a packed
    sheet and not in the newly rendered source image's raster coordinates.
    This makes the guide reusable at any native render resolution.
    """

    center_x: float
    center_y: float
    width: float
    height: float
    source_width: float = 128.0
    source_height: float = 128.0


@dataclass(frozen=True)
class PortraitClip:
    """Rendered frames and playback metadata for one named portrait clip."""

    frames: tuple[Image.Image, ...]
    duration_ms: int = 0
    looping: bool = False

    @classmethod
    def still(cls, image: Image.Image) -> "PortraitClip":
        return cls((image,), duration_ms=0, looping=False)


@dataclass(frozen=True)
class PortraitPose:
    """Author-time request for a generator-backed portrait frame."""

    animation: str
    frame_index: int = 0
    duration_ms: int = 0
    looping: bool = False


def portrait_files(target: str) -> tuple[str, str]:
    """Canonical published filenames for a target's portrait product."""

    return (f"{target}_portraits.png", f"{target}_portraits.ron")


def _xy(value: Any) -> tuple[float, float] | None:
    if isinstance(value, Mapping):
        if "x" in value and "y" in value:
            return (float(value["x"]), float(value["y"]))
        if "width" in value and "height" in value:
            return (float(value["width"]), float(value["height"]))
        if "w" in value and "h" in value:
            return (float(value["w"]), float(value["h"]))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) >= 2:
            return (float(value[0]), float(value[1]))
    return None


def face_guide_from_metadata(
    *,
    visual: Mapping[str, Any] | None = None,
    sockets: Mapping[str, Any] | None = None,
    spec: Any = None,
    source_size: tuple[int, int] = (128, 128),
) -> FaceGuide:
    """Resolve an explicit or naturally derived face guide.

    Resolution order:

    1. ``visual.portrait.face_guide`` or ``visual.face_guide``;
    2. the target's ``head`` socket plus ``head_w`` / ``head_h`` spec fields;
    3. a conservative centered humanoid default.

    The metadata is intentionally independent of rigs.  Any generator family
    may provide the same logical guide.
    """

    visual = dict(visual or {})
    portrait = visual.get("portrait")
    portrait = dict(portrait) if isinstance(portrait, Mapping) else {}
    raw = portrait.get("face_guide", visual.get("face_guide"))
    if isinstance(raw, Mapping):
        center = _xy(raw.get("center"))
        if center is None and "center_x" in raw and "center_y" in raw:
            center = (float(raw["center_x"]), float(raw["center_y"]))
        extent = _xy(raw.get("size") or raw.get("extent"))
        if extent is None and "width" in raw and "height" in raw:
            extent = (float(raw["width"]), float(raw["height"]))
        raw_source = _xy(raw.get("source_size")) or (
            float(source_size[0]),
            float(source_size[1]),
        )
        if center is not None and extent is not None:
            return FaceGuide(
                center_x=center[0],
                center_y=center[1],
                width=max(1.0, extent[0]),
                height=max(1.0, extent[1]),
                source_width=max(1.0, raw_source[0]),
                source_height=max(1.0, raw_source[1]),
            )

    head_point: tuple[float, float] | None = None
    head = dict(sockets or {}).get("head")
    if isinstance(head, Mapping):
        head_point = _xy(head.get("point", head))

    sw, sh = float(source_size[0]), float(source_size[1])
    head_w = float(getattr(spec, "head_w", sw * 0.22))
    head_h = float(getattr(spec, "head_h", sh * 0.24))
    if head_point is None:
        head_point = (sw * 0.5, sh * 0.23)
    return FaceGuide(
        center_x=head_point[0],
        center_y=head_point[1],
        width=max(1.0, head_w),
        height=max(1.0, head_h),
        source_width=sw,
        source_height=sh,
    )


def default_portrait_poses(generator: Any, job: Any) -> dict[str, PortraitPose]:
    """Resolve named portrait poses for a config-backed generator.

    ``visual.portraits`` is an optional mapping whose values may specify
    ``animation``, ``frame``, ``duration_ms``, and ``looping``.  Overlay 1 uses
    the required static ``default`` clip, while the shape deliberately supports
    later expression and animation work without changing the product manifest.
    """

    default_animation, default_frame = generator.canonical_pose()
    visual = dict(getattr(job, "visual", {}) or {})
    configured = visual.get("portraits")
    poses: dict[str, PortraitPose] = {}
    if isinstance(configured, Mapping):
        for name, raw in configured.items():
            if not isinstance(raw, Mapping):
                continue
            poses[str(name)] = PortraitPose(
                animation=str(raw.get("animation", default_animation)),
                frame_index=int(raw.get("frame", raw.get("frame_index", default_frame))),
                duration_ms=max(0, int(raw.get("duration_ms", 0))),
                looping=bool(raw.get("looping", False)),
            )
    if "default" not in poses:
        portrait = visual.get("portrait")
        portrait = dict(portrait) if isinstance(portrait, Mapping) else {}
        poses["default"] = PortraitPose(
            animation=str(
                portrait.get(
                    "animation",
                    visual.get("default_pose", default_animation),
                )
            ),
            frame_index=int(
                portrait.get("frame", portrait.get("frame_index", default_frame))
            ),
        )
    return poses


def render_framed_portrait(
    source: Image.Image,
    face: FaceGuide,
    *,
    output_size: tuple[int, int] = DEFAULT_PORTRAIT_SIZE,
    view_width: float | None = None,
    center_y: float | None = None,
) -> Image.Image:
    """Compose a native source render into a portrait-sized transparent frame.

    ``source`` must be a fresh render of the authored character.  The function
    maps the logical guide into that raster, crops a head-and-shoulders viewport,
    and downsamples to the published portrait size.  It never reads gameplay
    sheet pixels.
    """

    if source.mode != "RGBA":
        source = source.convert("RGBA")
    out_w, out_h = (int(output_size[0]), int(output_size[1]))
    if out_w <= 0 or out_h <= 0:
        raise ValueError(f"portrait output size must be positive, got {output_size!r}")

    logical_width = float(
        view_width
        if view_width is not None
        else max(face.width * 2.6, face.source_width * 0.50)
    )
    logical_height = logical_width * out_h / out_w
    logical_center_y = float(
        center_y if center_y is not None else face.center_y + face.height * 0.55
    )
    left = face.center_x - logical_width * 0.5
    top = logical_center_y - logical_height * 0.5
    right = left + logical_width
    bottom = top + logical_height

    sx = source.width / face.source_width
    sy = source.height / face.source_height
    raster_box = (
        int(math.floor(left * sx)),
        int(math.floor(top * sy)),
        int(math.ceil(right * sx)),
        int(math.ceil(bottom * sy)),
    )
    crop = source.crop(raster_box)
    if crop.size != (out_w, out_h):
        crop = crop.resize((out_w, out_h), Image.Resampling.LANCZOS)
    return crop


def render_generator_portraits(
    generator: Any,
    spec: Any,
    job: Any,
    *,
    target: str,
    out_dir: str | Path,
    output_size: tuple[int, int] = DEFAULT_PORTRAIT_SIZE,
) -> list[Path]:
    """Render and write portraits for a scalable ``CharacterGenerator``."""

    source_size = (int(job.render.frame_width), int(job.render.frame_height))
    face = face_guide_from_metadata(
        visual=getattr(job, "visual", None),
        sockets=getattr(job, "sockets", None),
        spec=spec,
        source_size=source_size,
    )
    clips: dict[str, PortraitClip] = {}
    for name, pose in default_portrait_poses(generator, job).items():
        native_size = (
            source_size[0] * DEFAULT_PORTRAIT_SUPERSAMPLE,
            source_size[1] * DEFAULT_PORTRAIT_SUPERSAMPLE,
        )
        source = generator.render_frame(
            spec,
            pose.animation,
            pose.frame_index,
            native_size,
            job,
        )
        frame = render_framed_portrait(source, face, output_size=output_size)
        clips[name] = PortraitClip(
            frames=(frame,),
            duration_ms=pose.duration_ms,
            looping=pose.looping,
        )
    return write_portrait_sheet(target, clips, out_dir)


def _ron_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _manifest_to_ron(
    *,
    target: str,
    image_name: str,
    frame_size: tuple[int, int],
    clips: Mapping[str, tuple[PortraitClip, list[tuple[int, int, int, int]]]],
) -> str:
    lines = [
        "// Generated by ambition_sprite2d_renderer. Do not edit by hand.",
        "(",
        f"    target: {_ron_string(target)},",
        f"    image: {_ron_string(image_name)},",
        f"    frame_width: {int(frame_size[0])},",
        f"    frame_height: {int(frame_size[1])},",
        '    default_clip: "default",',
        "    clips: {",
    ]
    for name, (clip, rects) in clips.items():
        lines.extend(
            [
                f"        {_ron_string(name)}: (",
                f"            duration_ms: {int(clip.duration_ms)},",
                f"            looping: {'true' if clip.looping else 'false'},",
                "            frames: [",
            ]
        )
        for x, y, w, h in rects:
            lines.append(f"                (x: {x}, y: {y}, w: {w}, h: {h}),")
        lines.extend(["            ],", "        ),"])
    lines.extend(["    },", ")", ""])
    return "\n".join(lines)


def write_portrait_sheet(
    target: str,
    clips: Mapping[str, PortraitClip],
    out_dir: str | Path,
    *,
    max_columns: int = 8,
) -> list[Path]:
    """Pack named portrait clips and emit canonical PNG + RON products."""

    if "default" not in clips:
        raise ValueError(f"portrait target {target!r} must define a 'default' clip")
    if not clips:
        raise ValueError(f"portrait target {target!r} has no clips")

    normalized: dict[str, PortraitClip] = {}
    frame_size: tuple[int, int] | None = None
    for name, clip in clips.items():
        if not name or not str(name).strip():
            raise ValueError("portrait clip names must be non-empty")
        if not clip.frames:
            raise ValueError(f"portrait clip {name!r} has no frames")
        frames: list[Image.Image] = []
        for frame in clip.frames:
            image = frame.convert("RGBA") if frame.mode != "RGBA" else frame.copy()
            if frame_size is None:
                frame_size = image.size
            elif image.size != frame_size:
                raise ValueError(
                    f"portrait frame size mismatch for {target}/{name}: "
                    f"expected {frame_size}, got {image.size}"
                )
            frames.append(image)
        normalized[str(name)] = PortraitClip(
            frames=tuple(frames),
            duration_ms=max(0, int(clip.duration_ms)),
            looping=bool(clip.looping),
        )
    assert frame_size is not None

    frame_count = sum(len(clip.frames) for clip in normalized.values())
    columns = max(1, min(max_columns, frame_count))
    rows = math.ceil(frame_count / columns)
    fw, fh = frame_size
    sheet = Image.new("RGBA", (columns * fw, rows * fh), (0, 0, 0, 0))
    clip_rects: dict[str, tuple[PortraitClip, list[tuple[int, int, int, int]]]] = {}
    index = 0
    for name, clip in normalized.items():
        rects: list[tuple[int, int, int, int]] = []
        for frame in clip.frames:
            column = index % columns
            row = index // columns
            x, y = column * fw, row * fh
            sheet.alpha_composite(frame, (x, y))
            rects.append((x, y, fw, fh))
            index += 1
        clip_rects[name] = (clip, rects)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image_name, manifest_name = portrait_files(target)
    image_out = out_dir / image_name
    manifest_out = out_dir / manifest_name
    sheet.save(image_out)
    manifest_out.write_text(
        _manifest_to_ron(
            target=target,
            image_name=image_name,
            frame_size=frame_size,
            clips=clip_rects,
        ),
        encoding="utf8",
    )
    return [image_out, manifest_out]


__all__ = [
    "DEFAULT_PORTRAIT_SIZE",
    "FaceGuide",
    "PortraitClip",
    "PortraitPose",
    "default_portrait_poses",
    "face_guide_from_metadata",
    "portrait_files",
    "render_framed_portrait",
    "render_generator_portraits",
    "write_portrait_sheet",
]
