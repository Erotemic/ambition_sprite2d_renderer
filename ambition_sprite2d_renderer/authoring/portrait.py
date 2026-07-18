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
import re
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


def render_canonical_portrait(
    source: Image.Image,
    *,
    actor_metadata: Mapping[str, Any] | None = None,
    output_size: tuple[int, int] = DEFAULT_PORTRAIT_SIZE,
) -> Image.Image:
    """Compose a default portrait from a freshly authored canonical render.

    This is the module-target coverage fallback. ``source`` must come from the
    target's current authoring code during this invocation; callers must never
    pass an installed gameplay sheet or a frame extracted from one. Bespoke and
    scalable families should override this fallback when they can rerender a
    more detailed face or pose.

    Humanoid canonicals are framed to their upper body. Other body plans keep
    the complete visible subject so beasts, props, swarms, and unusual bosses
    receive a useful default without pretending that they share humanoid face
    geometry.
    """

    image = source.convert("RGBA") if source.mode != "RGBA" else source.copy()
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return Image.new("RGBA", output_size, (0, 0, 0, 0))

    x1, y1, x2, y2 = (float(v) for v in bbox)
    subject_w = max(1.0, x2 - x1)
    subject_h = max(1.0, y2 - y1)
    metadata = dict(actor_metadata or {})
    body = metadata.get("body")
    body = dict(body) if isinstance(body, Mapping) else {}
    body_plan = str(body.get("body_plan", ""))

    if body_plan == "HumanoidBiped":
        # Head, torso, and enough upper arms to preserve silhouette. The
        # canonical source is already alpha-trimmed, so proportional framing
        # remains valid across procedural, rigged, SVG, and part-based families.
        crop_x1 = x1 - subject_w * 0.08
        crop_x2 = x2 + subject_w * 0.08
        crop_y1 = y1 - subject_h * 0.04
        crop_y2 = y1 + subject_h * 0.64
    else:
        crop_x1 = x1 - subject_w * 0.08
        crop_x2 = x2 + subject_w * 0.08
        crop_y1 = y1 - subject_h * 0.08
        crop_y2 = y2 + subject_h * 0.08

    out_w, out_h = output_size
    crop_w = max(1.0, crop_x2 - crop_x1)
    crop_h = max(1.0, crop_y2 - crop_y1)
    target_aspect = out_w / out_h
    current_aspect = crop_w / crop_h
    if current_aspect < target_aspect:
        wanted_w = crop_h * target_aspect
        extra = (wanted_w - crop_w) * 0.5
        crop_x1 -= extra
        crop_x2 += extra
    else:
        wanted_h = crop_w / target_aspect
        extra = (wanted_h - crop_h) * 0.5
        crop_y1 -= extra
        crop_y2 += extra

    crop = image.crop(
        (
            int(math.floor(crop_x1)),
            int(math.floor(crop_y1)),
            int(math.ceil(crop_x2)),
            int(math.ceil(crop_y2)),
        )
    )
    if crop.size != output_size:
        crop = crop.resize(output_size, Image.Resampling.LANCZOS)
    return crop


def write_default_portrait_from_canonical(
    target: str,
    canonical_path: str | Path,
    out_dir: str | Path,
    *,
    actor_metadata: Mapping[str, Any] | None = None,
    output_size: tuple[int, int] = DEFAULT_PORTRAIT_SIZE,
) -> list[Path]:
    """Publish a one-frame ``default`` clip from a fresh canonical render."""

    with Image.open(canonical_path) as source:
        portrait = render_canonical_portrait(
            source, actor_metadata=actor_metadata, output_size=output_size
        )
    return write_portrait_sheet(
        target, {"default": PortraitClip.still(portrait)}, out_dir
    )


@dataclass(frozen=True)
class PortraitProduct:
    """One installed portrait sheet discovered for visual review."""

    target: str
    image_path: Path
    manifest_path: Path
    frame_width: int
    frame_height: int
    default_clip: str
    default_rect: tuple[int, int, int, int]


def _ron_field(text: str, name: str) -> str:
    match = re.search(rf"\b{name}:\s*\"([^\"]+)\"", text)
    if match is None:
        raise ValueError(f"portrait manifest missing string field {name!r}")
    return match.group(1)


def _ron_int_field(text: str, name: str) -> int:
    match = re.search(rf"\b{name}:\s*(\d+)", text)
    if match is None:
        raise ValueError(f"portrait manifest missing integer field {name!r}")
    return int(match.group(1))


def read_portrait_product(manifest_path: str | Path) -> PortraitProduct:
    """Read the controlled portrait-manifest subset needed by review tools.

    The runtime owns the complete RON schema. This lightweight reader is
    intentionally limited to manifests emitted by :func:`write_portrait_sheet`
    and avoids making the renderer depend on a general-purpose RON parser.
    """

    manifest_path = Path(manifest_path)
    text = manifest_path.read_text(encoding="utf8")
    target = _ron_field(text, "target")
    image_name = _ron_field(text, "image")
    frame_width = _ron_int_field(text, "frame_width")
    frame_height = _ron_int_field(text, "frame_height")
    default_clip = _ron_field(text, "default_clip")
    marker = f'{_ron_string(default_clip)}: ('
    clip_start = text.find(marker)
    if clip_start < 0:
        raise ValueError(
            f"portrait manifest {manifest_path} has no default clip {default_clip!r}"
        )
    rect_match = re.search(
        r"\(x:\s*(\d+),\s*y:\s*(\d+),\s*w:\s*(\d+),\s*h:\s*(\d+)\)",
        text[clip_start:],
    )
    if rect_match is None:
        raise ValueError(
            f"portrait manifest {manifest_path} default clip has no frame rect"
        )
    rect = tuple(int(value) for value in rect_match.groups())
    return PortraitProduct(
        target=target,
        image_path=manifest_path.parent / image_name,
        manifest_path=manifest_path,
        frame_width=frame_width,
        frame_height=frame_height,
        default_clip=default_clip,
        default_rect=rect,
    )


def discover_portrait_products(source_dir: str | Path) -> tuple[list[PortraitProduct], list[str]]:
    """Discover installed portrait products recursively for gallery review."""

    source_dir = Path(source_dir)
    products: list[PortraitProduct] = []
    warnings: list[str] = []
    for manifest in sorted(source_dir.rglob("*_portraits.ron")):
        try:
            product = read_portrait_product(manifest)
            if not product.image_path.exists():
                raise FileNotFoundError(product.image_path)
        except Exception as ex:  # noqa: BLE001 - report every malformed product
            warnings.append(f"{manifest}: {ex}")
            continue
        products.append(product)
    return products, warnings


def load_default_portrait_frame(product: PortraitProduct) -> Image.Image:
    """Load one product's named default frame as an independent RGBA image."""

    x, y, w, h = product.default_rect
    with Image.open(product.image_path) as sheet:
        return sheet.convert("RGBA").crop((x, y, x + w, y + h))


def write_portrait_gallery(
    source_dir: str | Path,
    out_path: str | Path,
    *,
    columns: int = 8,
) -> tuple[Path, list[str]]:
    """Write a labeled contact sheet of every installed default portrait."""

    from ..core.draw import font as load_font
    from PIL import ImageDraw

    products, warnings = discover_portrait_products(source_dir)
    if not products:
        raise ValueError(f"no portrait products found under {Path(source_dir)}")
    columns = max(1, min(int(columns), len(products)))
    image_w, image_h = 176, 220
    card_w, card_h = 208, 270
    rows = math.ceil(len(products) / columns)
    gallery = Image.new(
        "RGBA", (columns * card_w, rows * card_h), (24, 25, 31, 255)
    )
    draw = ImageDraw.Draw(gallery)
    label_font = load_font(12)
    small_font = load_font(10)
    for index, product in enumerate(products):
        col, row = index % columns, index // columns
        x, y = col * card_w, row * card_h
        draw.rounded_rectangle(
            (x + 5, y + 5, x + card_w - 5, y + card_h - 5),
            radius=10,
            fill=(36, 38, 48, 255),
            outline=(76, 80, 100, 255),
            width=1,
        )
        frame = load_default_portrait_frame(product)
        scale = min(image_w / frame.width, image_h / frame.height)
        shown = frame.resize(
            (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
            Image.Resampling.LANCZOS,
        )
        gallery.alpha_composite(
            shown,
            (x + (card_w - shown.width) // 2, y + 14 + (image_h - shown.height) // 2),
        )
        draw.text(
            (x + 10, y + 238),
            product.target,
            font=label_font,
            fill=(245, 246, 252, 255),
        )
        rel = product.manifest_path.relative_to(Path(source_dir))
        draw.text(
            (x + 10, y + 254),
            str(rel.parent),
            font=small_font,
            fill=(172, 178, 198, 255),
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(out_path)
    return out_path, warnings


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
    "render_canonical_portrait",
    "render_framed_portrait",
    "render_generator_portraits",
    "write_default_portrait_from_canonical",
    "PortraitProduct",
    "discover_portrait_products",
    "load_default_portrait_frame",
    "read_portrait_product",
    "write_portrait_gallery",
    "write_portrait_sheet",
]
