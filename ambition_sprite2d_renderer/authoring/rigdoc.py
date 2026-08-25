"""Serializable rig documents — data-defined characters for the bone toolkit.

A rig document is plain JSON describing a complete character: bones,
drawable parts, palette, IK leg bindings, and animation clips whose
channels are keyframes, math expressions, or constants. This module turns
documents into rendered frames and spritesheets using the same
``skeleton`` + ``sheet_build`` machinery as the Python-coded targets.

Consumers:

- ``ambition_sprite2d_renderer.gui`` — the PySide6 character editor;
  documents are its file format.
- ``targets/characters/rigged.py`` — auto-registers every document under
  ``targets/characters/rigged/`` as a sheet target, so GUI-authored
  characters publish through ``./regen_sprites.sh --target <name>`` like
  everything else.

Document shape (all geometry in base-frame pixels, y down, facing +x)::

    {
      "name": "my_bot",
      "frame": {"width": 128, "height": 128, "supersample": 4,
                "ground_y": 101.0, "center_x": 64.0, "ankle_h": 2.6},
      "palette": {"shell": "#FDFDFB", ...},
      "bones": [{"name": "pelvis", "parent": null, "offset": [0, -20.5],
                 "length": 0.0, "rest_angle": 0.0}, ...],
      "parts": [
        {"name": "torso", "bone": "torso", "z": 40, "kind": "polygon",
         "points": [[-9.8, -13.5], ...], "radius": 3.6,
         "fill": "shell", "outline": "outline", "outline_w": 1.15},
        {"kind": "capsule", "a": [0, 0], "b": null, "radius": 2.3, ...},
        {"kind": "circle", "center": [8, 0], "radius": 3.2, ...},
        ... optional "opacity_channel": "slash_vis" on any part ...
        ... optional "feature": "hairpin" tags a part as an optional accessory ...
      ],
      "features": {"hairpin": false, "glasses": true},  # toggle optional parts
      "gameplay_geometry": {  # authoring-only; ignored by publication for now
        "version": 1, "space": "rig_frame_pixels",
        "collision": null, "hurtboxes": {"clips": {}},
        "hitboxes": {"clips": {}}
      },
      "animation_constraints": {
        "version": 2,
        "clips": {"idle": {"pins": [
          {"bone": "near_foot", "anchor_local": [0.0, 0.0],
           "target": [69.0, 96.9], "rotation": 0.0,
           "lock_rotation": true, "scope": "clip",
           "solver": {"upper": "near_leg_u", "lower": "near_leg_l",
                      "bend": 1.0}, "role": "foot"}
        ]}}
      },

      "ik_legs": [{"upper": "near_leg_u", "lower": "near_leg_l",
                   "foot": "near_foot", "channel_prefix": "near_foot",
                   "rest_x": 5.0, "bend": 1.0}],
      "ik_chains": [{"upper": "near_arm_u", "lower": "near_arm_l",
                     "end": "near_hand", "channel_prefix": "near_hand",
                     "rest_x": 18.0, "rest_y": -34.0, "bend": -1.0}],
      "clips": {
        "idle": {"loop": true, "frames": 8, "duration_ms": 120,
                 "channels": {
                   "torso": {"expr": "2.8*sin(tau*t)"},
                   "near_arm_u": {"keys": [[0, 8, "smooth"], [0.5, -4]]},
                   "near_foot_x": {"const": 5.0}}}}
    }

Channel conventions match the Python targets: names that are bones become
pose angles (degrees); ``bone.<name>.x`` / ``bone.<name>.y`` add a translation
to that bone's authored local attachment; ``root_x``/``root_y`` offset the root
from ``(center_x, ground_y)``; ``<prefix>_x`` / ``_lift`` / ``_pitch`` drive IK
feet (x is offset from ``center_x`` in WORLD space so planted feet stay
put); generic two-bone chains use ``<prefix>_x`` / ``_y`` / ``_pitch``.
Both IK forms may animate ``<prefix>_bend`` to choose the joint side per
pose instead of being locked to the document's static ``bend`` value.
Anything else is a free parameter (e.g. an ``opacity_channel``).

Colors are palette keys, ``#RRGGBB``, or ``#RRGGBBAA``. Translucent parts
are painted on a scratch layer and alpha-composited (the gnu_ton rule).
"""

from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from PIL import Image, ImageDraw

from .animation_constraints import (
    constraints_root,
    pin_active,
    transform_pins,
)
from .common_draw import draw_capsule
from .rig import clamp, lerp, smoothstep
from .skeleton import (
    BoneWorld,
    Channel,
    Skeleton,
    draw_polygon,
    rounded_polygon,
    two_bone_ik,
)
from ambition_sprite2d_renderer.core.draw import (
    RESAMPLING,
    blending_draw,
    resize_transparent_sprite,
    rotate_transparent_sprite,
)

try:
    from line_profiler import profile
except ImportError:  # Optional developer dependency.
    from ..profiling import profile

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]

RenderPadding = Union[int, Tuple[int, int], Tuple[int, int, int, int]]


def normalize_render_padding(value: Optional[RenderPadding]) -> Tuple[int, int, int, int]:
    """Normalize rig render overscan to ``(left, top, right, bottom)``.

    Rig animation coordinates stay in the original logical frame. Padding only
    enlarges the temporary/output raster and translates world-space painting,
    so rotations can leave the logical frame without losing pixels.
    """
    if value is None:
        return (0, 0, 0, 0)
    if isinstance(value, int):
        n = max(0, int(value))
        return (n, n, n, n)
    values = tuple(int(v) for v in value)
    if len(values) == 2:
        x, y = values
        return (max(0, x), max(0, y), max(0, x), max(0, y))
    if len(values) == 4:
        left, top, right, bottom = values
        return tuple(max(0, v) for v in (left, top, right, bottom))
    raise ValueError(
        "render padding must be an int, (x, y), or (left, top, right, bottom)"
    )


def translate_bone_worlds(
    world: Dict[str, BoneWorld], dx: float, dy: float
) -> Dict[str, BoneWorld]:
    """Translate solved bone origins without changing pose angles/lengths."""
    if dx == 0.0 and dy == 0.0:
        return world
    return {
        name: BoneWorld((bone.origin[0] + dx, bone.origin[1] + dy), bone.angle, bone.length)
        for name, bone in world.items()
    }


PART_KINDS = ("polygon", "capsule", "circle", "sprite")
EASE_NAMES = ("linear", "smooth", "out", "in", "sine", "hold")
DEFAULT_SPRITE_TRANSFORM_CACHE_MB = 128
DEFAULT_SPRITE_TRANSFORM_WORKERS = min(4, max(1, os.cpu_count() or 1))


def _sprite_transform_cache_bytes() -> int:
    value = os.environ.get(
        "AMBITION_SPRITE_TRANSFORM_CACHE_MB",
        str(DEFAULT_SPRITE_TRANSFORM_CACHE_MB),
    )
    try:
        megabytes = int(value)
    except ValueError as ex:
        raise ValueError(
            "AMBITION_SPRITE_TRANSFORM_CACHE_MB must be an integer number of MiB"
        ) from ex
    return max(0, megabytes) * 1024 * 1024


def _sprite_transform_workers() -> int:
    value = os.environ.get(
        "AMBITION_SPRITE_ROTATE_WORKERS",
        str(DEFAULT_SPRITE_TRANSFORM_WORKERS),
    )
    try:
        workers = int(value)
    except ValueError as ex:
        raise ValueError(
            "AMBITION_SPRITE_ROTATE_WORKERS must be an integer"
        ) from ex
    return max(1, workers)

# Restricted namespace for local expression channels: math only, with no
# builtins.
_EXPR_GLOBALS = {
    "__builtins__": {},
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "atan2": math.atan2,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "floor": math.floor,
    "pi": math.pi,
    "tau": math.tau,
    "abs": abs,
    "min": min,
    "max": max,
    "clamp": clamp,
    "lerp": lerp,
    "smoothstep": smoothstep,
}
_EXPR_CACHE: Dict[str, object] = {}


def normalize_degrees(value: float) -> float:
    """Canonicalize equivalent rotations while preserving exact pose values."""
    angle = (float(value) + 180.0) % 360.0 - 180.0
    # Avoid separate cache entries for -0.0 and 0.0.
    return 0.0 if angle == 0.0 else angle


@dataclass(frozen=True)
class SpriteRaster:
    """One SVG part raster prepared for cheap repeated pose composition.

    ``image`` remains cropped for the zero-rotation fast path. ``padded`` keeps
    the historical all-angle representation for standalone compatibility.
    ``premultiplied`` is the immutable cropped source in Pillow's ``RGBa`` mode;
    the shared transform cache can place it directly into each tight rotation
    canvas instead of repeating RGBA -> RGBa conversion on every cache miss.
    ``cache_key`` identifies the source subset, pivot, and raster scale.
    """

    image: Image.Image
    pivot: Point
    padded: Image.Image
    radius: int
    cache_key: tuple
    # Effective source pixels per authored logical pixel. High-resolution rig
    # publication already provides its own antialiasing budget, so rotations at
    # >=3x can use Pillow's substantially cheaper bilinear kernel and still be
    # filtered again at the publication boundary.
    working_scale: float = 1.0
    premultiplied: Optional[Image.Image] = None


class SpriteTransformCache:
    """Byte-bounded LRU of full-opacity rotated part rasters.

    Rig frames ask for many independent SVG-part transforms before any of those
    parts need to be composited. ``rotated_many`` resolves resident cache hits
    first, computes the remaining Pillow rotations concurrently, then admits
    results and composites later in authoritative SVG z-order. Rendering stays
    deterministic because only the independent transforms are parallel; paint
    order is unchanged.

    The cache budget defaults to 128 MiB and is configurable with
    ``AMBITION_SPRITE_TRANSFORM_CACHE_MB``. Rotation parallelism defaults to at
    most four workers and is configurable with ``AMBITION_SPRITE_ROTATE_WORKERS``.
    Set the latter to 1 for a strictly sequential diagnostic run.

    Once the byte budget is full, a one-off transform is not allowed to evict a
    useful resident immediately. It enters a small probation set instead; only
    a second observation earns admission. This keeps animation streams with many
    unique angles from turning the LRU into an eviction conveyor belt while
    preserving first-hit caching when there is still free capacity.
    """

    def __init__(
        self,
        max_bytes: Optional[int] = None,
        *,
        max_probation_keys: int = 8192,
        max_workers: Optional[int] = None,
    ) -> None:
        self.max_bytes = max(
            0,
            int(_sprite_transform_cache_bytes() if max_bytes is None else max_bytes),
        )
        self.max_probation_keys = max(0, int(max_probation_keys))
        self.max_workers = max(
            1,
            int(_sprite_transform_workers() if max_workers is None else max_workers),
        )
        self._items: OrderedDict[tuple, Image.Image] = OrderedDict()
        self._probation: OrderedDict[tuple, None] = OrderedDict()
        self._bytes = 0
        self._executor: Optional[ThreadPoolExecutor] = None

    def clear(self) -> None:
        self._items.clear()
        self._probation.clear()
        self._bytes = 0

    def _remember_probation(self, key: tuple) -> None:
        if self.max_probation_keys <= 0:
            return
        self._probation[key] = None
        self._probation.move_to_end(key)
        while len(self._probation) > self.max_probation_keys:
            self._probation.popitem(last=False)

    @staticmethod
    def _key(sprite: SpriteRaster, angle: float) -> tuple:
        return (id(sprite.image), sprite.cache_key, angle)

    @staticmethod
    @profile
    def _rotate_uncached(sprite: SpriteRaster, angle: float) -> Image.Image:
        # Bicubic is useful when a rig is rendered near its final pixel size.
        # At >=3 source pixels per logical pixel, however, the part is already
        # supersampled. Bilinear rotation is ~2-3x cheaper in Pillow and the
        # later whole-frame reduction (or native 3x publication) supplies the
        # final antialiasing pass. Keep the low-resolution/editor path bicubic.
        resample = (
            RESAMPLING.BILINEAR
            if sprite.working_scale >= 3.0
            else RESAMPLING.BICUBIC
        )

        # Rotate the smallest pivot-centered canvas that can contain this angle
        # instead of the all-angles circumscribed square. Work directly in
        # premultiplied-alpha space: SVG source rasters are immutable, so the
        # RGBA -> RGBa conversion can be paid once in ``sprite_raster`` rather
        # than once per animation angle.
        pivot_x = int(round(sprite.pivot[0]))
        pivot_y = int(round(sprite.pivot[1]))
        base_half_w = max(pivot_x, sprite.image.width - pivot_x) + 2
        base_half_h = max(pivot_y, sprite.image.height - pivot_y) + 2
        radians = math.radians(angle)
        cos_a = abs(math.cos(radians))
        sin_a = abs(math.sin(radians))
        rotated_half_w = int(
            math.ceil(cos_a * base_half_w + sin_a * base_half_h)
        ) + 1
        rotated_half_h = int(
            math.ceil(sin_a * base_half_w + cos_a * base_half_h)
        ) + 1
        # The source is pasted *before* it is rotated.  A canvas sized only for
        # the post-rotation bounds can therefore be smaller than the unrotated
        # source in one axis (the classic case is a tall sword rotated ~90deg).
        # Pillow clips the paste silently; a separately bound child such as a
        # hand then survives while the forearm/weapon appears mysteriously cut.
        # The working canvas must contain BOTH the source-centered rectangle and
        # its rotated rectangle.  Keeping the pivot at the canvas center preserves
        # the existing blit contract and still avoids the old all-angle square.
        half_w = max(base_half_w, rotated_half_w)
        half_h = max(base_half_h, rotated_half_h)
        pad = Image.new("RGBa", (2 * half_w, 2 * half_h), (0, 0, 0, 0))
        premultiplied = sprite.premultiplied
        if premultiplied is None:
            premultiplied = sprite.image.convert("RGBa")
        pad.paste(
            premultiplied,
            (half_w - pivot_x, half_h - pivot_y),
        )
        rot = rotate_transparent_sprite(
            pad,
            -angle,
            center=(half_w, half_h),
            resample=resample,
        )
        return rot.convert("RGBA") if rot.mode != "RGBA" else rot

    def _admit(self, key: tuple, rot: Image.Image) -> Image.Image:
        """Apply the existing probation/LRU policy to one computed transform."""
        cached = self._items.get(key)
        if cached is not None:
            self._items.move_to_end(key)
            return cached

        size_bytes = rot.width * rot.height * 4
        if self.max_bytes <= 0 or size_bytes > self.max_bytes:
            return rot

        would_evict = self._bytes + size_bytes > self.max_bytes
        repeated = key in self._probation
        if would_evict and not repeated:
            self._remember_probation(key)
            return rot

        self._probation.pop(key, None)
        while self._items and self._bytes + size_bytes > self.max_bytes:
            _old_key, old = self._items.popitem(last=False)
            self._bytes -= old.width * old.height * 4
        self._items[key] = rot
        self._bytes += size_bytes
        return rot

    def _pool(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="ambition-sprite-rotate",
            )
        return self._executor

    @profile
    def rotated(self, sprite: SpriteRaster, delta_deg: float) -> Image.Image:
        # Preserve exact render semantics. The normalized angle only aliases
        # equivalent full turns; it does not quantize animation values.
        angle = normalize_degrees(delta_deg)
        key = self._key(sprite, angle)
        cached = self._items.get(key)
        if cached is not None:
            self._items.move_to_end(key)
            return cached
        return self._admit(key, self._rotate_uncached(sprite, angle))

    @profile
    def rotated_many(
        self,
        requests: List[Tuple[SpriteRaster, float]],
    ) -> List[Image.Image]:
        """Resolve independent non-zero transforms while preserving cache semantics.

        Cache inspection/admission remains on the calling thread. Only expensive
        Pillow rotations run concurrently, and results are consumed in request
        order. The caller still composites those images sequentially in SVG z-order.
        """
        if not requests:
            return []

        normalized = [
            (sprite, normalize_degrees(angle)) for sprite, angle in requests
        ]
        missing: OrderedDict[tuple, Tuple[SpriteRaster, float]] = OrderedDict()
        for sprite, angle in normalized:
            key = self._key(sprite, angle)
            if key not in self._items and key not in missing:
                missing[key] = (sprite, angle)

        computed: Dict[tuple, Image.Image] = {}
        if missing:
            items = list(missing.items())
            if self.max_workers > 1 and len(items) > 1:
                rotations = self._pool().map(
                    lambda item: self._rotate_uncached(item[1][0], item[1][1]),
                    items,
                )
                computed = {
                    key: rotation for (key, _request), rotation in zip(items, rotations)
                }
            else:
                computed = {
                    key: self._rotate_uncached(sprite, angle)
                    for key, (sprite, angle) in items
                }

        results: List[Image.Image] = []
        for sprite, angle in normalized:
            key = self._key(sprite, angle)
            cached = self._items.get(key)
            if cached is not None:
                self._items.move_to_end(key)
                results.append(cached)
                continue
            rot = computed.get(key)
            # An initially resident transform can be evicted by an earlier
            # request in the same batch. Match sequential semantics by rebuilding
            # that rare case rather than changing the cache's admission policy.
            if rot is None:
                rot = self._rotate_uncached(sprite, angle)
            results.append(self._admit(key, rot))
        return results


def eval_expr(expr: str, t: float) -> float:
    code = _EXPR_CACHE.get(expr)
    if code is None:
        code = compile(expr, "<channel expr>", "eval")
        _EXPR_CACHE[expr] = code
    return float(eval(code, _EXPR_GLOBALS, {"t": t}))


def sample_channel_spec(spec: dict, t: float, loop: bool) -> float:
    """Sample one channel spec ({"const"} | {"expr"} | {"keys"}) at t."""
    if "const" in spec:
        return float(spec["const"])
    if "expr" in spec:
        return eval_expr(spec["expr"], t % 1.0 if loop else clamp(t, 0.0, 1.0))
    keys = spec.get("keys") or []
    if not keys:
        return 0.0
    ch = Channel(*[tuple(k) for k in keys])
    return ch.sample(t, loop)


def part_visible(part: dict, features: Dict[str, bool]) -> bool:
    """Whether a part renders under the document's ``features`` toggles.

    A part with no ``feature`` tag always renders. A part tagged
    ``"feature": "hairpin"`` renders unless ``features["hairpin"]`` is set
    false — so a character can carry optional accessories (hairpin, glasses,
    hat, …) and toggle each one on/off without editing the parts list. An
    unlisted feature defaults to visible, so existing rigs are unaffected.
    """
    feature = part.get("feature")
    if feature is None:
        return True
    return bool(features.get(feature, True))


def visible_parts(parts: List[dict], features: Dict[str, bool]) -> List[dict]:
    """Parts to paint, back-to-front by ``z``, with disabled features dropped."""
    ordered = sorted(parts, key=lambda p: float(p.get("z", 0.0)))
    return [p for p in ordered if part_visible(p, features)]


def parse_color(value, palette: Dict[str, str], opacity: float = 1.0) -> Optional[Color]:
    """Resolve a palette key / #RRGGBB / #RRGGBBAA into RGBA ints."""
    if value is None:
        return None
    s = palette.get(value, value)
    s = str(s).lstrip("#")
    if len(s) == 8:
        r, g, b, a = (int(s[i : i + 2], 16) for i in (0, 2, 4, 6))
    else:
        r, g, b = (int(s[i : i + 2], 16) for i in (0, 2, 4))
        a = 255
    return (r, g, b, int(a * clamp(opacity, 0.0, 1.0)))


class RigDocument:
    """A mutable rig document: thin helpers over the plain ``data`` dict.

    The GUI edits ``data`` in place. Expensive immutable derivations are
    cached behind content signatures so repeated editor paints do not rebuild
    the same skeleton while direct dictionary mutation remains safe."""

    def __init__(self, data: dict, source_path=None) -> None:
        self.data = data
        # Where this document was loaded from. ``sprite`` parts resolve their
        # SVG relative to this, and the per-resolution sprite raster cache is
        # keyed per instance (so a sheet rasterizes each part once).
        self.source_path = Path(source_path) if source_path is not None else None
        self._sprite_cache: Dict[tuple, SpriteRaster] = {}
        self._sprite_transform_cache = SpriteTransformCache()
        self._svg_path_cache_key: Optional[tuple] = None
        self._svg_path_cache: Optional[Path] = None
        self._skeleton_cache_key: Optional[tuple] = None
        self._skeleton_cache: Optional[Skeleton] = None

    # ---- I/O -------------------------------------------------------------

    @classmethod
    def load(cls, path) -> "RigDocument":
        return cls(
            json.loads(Path(path).read_text(encoding="utf8")), source_path=path
        )

    def save(self, path) -> None:
        Path(path).write_text(
            json.dumps(self.data, indent=1) + "\n", encoding="utf8"
        )

    @classmethod
    def new_empty(cls, name: str = "new_character") -> "RigDocument":
        return cls(
            {
                "name": name,
                "frame": {
                    "width": 128,
                    "height": 128,
                    "supersample": 4,
                    "ground_y": 101.0,
                    "center_x": 64.0,
                    "ankle_h": 2.6,
                },
                "palette": {
                    "shell": "#FDFDFB",
                    "outline": "#17191F",
                    "glow": "#0CEBFF",
                    "accent": "#C58AFF",
                },
                "bones": [
                    {"name": "pelvis", "parent": None, "offset": [0.0, -20.5], "length": 0.0, "rest_angle": 0.0},
                    {"name": "torso", "parent": "pelvis", "offset": [0.0, -4.0], "length": 0.0, "rest_angle": 0.0},
                ],
                "parts": [
                    {"name": "torso", "bone": "torso", "z": 40, "kind": "polygon",
                     "points": [[-10, -14], [10, -14], [9, 2], [-9, 2]], "radius": 3.5,
                     "fill": "shell", "outline": "outline", "outline_w": 1.15},
                ],
                "ik_legs": [],
                "ik_chains": [],
                "clips": {
                    "idle": {"loop": True, "frames": 8, "duration_ms": 120, "channels": {}},
                },
            }
        )

    # ---- Accessors ---------------------------------------------------------

    @property
    def name(self) -> str:
        return str(self.data.get("name", "unnamed"))

    @property
    def frame(self) -> dict:
        return self.data["frame"]

    @property
    def palette(self) -> Dict[str, str]:
        return self.data.setdefault("palette", {})

    @property
    def bones(self) -> List[dict]:
        return self.data.setdefault("bones", [])

    @property
    def parts(self) -> List[dict]:
        return self.data.setdefault("parts", [])

    @property
    def clips(self) -> Dict[str, dict]:
        return self.data.setdefault("clips", {})

    @property
    def ik_legs(self) -> List[dict]:
        return self.data.setdefault("ik_legs", [])

    @property
    def ik_chains(self) -> List[dict]:
        """Generic two-bone IK chains (typically arms).

        A chain targets ``(center_x + <prefix>_x, ground_y + <prefix>_y)`` in
        frame/world space. ``rest_x`` / ``rest_y`` reproduce the authored rest
        pose when a clip does not drive the channels. ``end`` is optional; when
        present, ``<prefix>_pitch`` controls its world angle.
        """
        return self.data.setdefault("ik_chains", [])

    @property
    def features(self) -> Dict[str, bool]:
        """Optional-part toggles: ``{feature_name: enabled}``. A part tagged
        with a ``feature`` only renders when its entry here is truthy (or
        absent — features default to on)."""
        return self.data.setdefault("features", {})

    @property
    def authored_faces_left(self) -> bool:
        """**Which way this rig's art is DRAWN**, as the rig already declares it.

        ``features["facing"]`` is written by
        ``scripts/build_scientist_fighter_rigs.py`` from ``CharacterSpec.facing``
        (default ``"west"``; Noether overrides to ``"east"`` because her SVG view
        is drawn east-facing and her poses are mirrored to match). The value is
        accurate for every rig that carries it — it was simply never read by
        anything downstream, so the game kept assuming every sheet faces +x.

        This is the accessor that ends that: the sheet build publishes the answer
        into the manifest and the renderer XORs it into the facing flip.

        ``"east"`` and an absent key both mean "drawn facing +x", which is the
        engine's standing assumption, so a rig that says nothing is unaffected.
        """
        return str(self.features.get("facing", "east")).strip().lower() == "west"

    @property
    def svg_source(self) -> Dict[str, object]:
        """Optional source-SVG binding for ``sprite`` parts::

            {"path": "rel/to/this.rig.json/art.svg", "view": "VIEW-front-right",
             "ref_dpi": 96.0, "scale": 0.1845}

        ``sprite`` parts name SVG element ids and a ``pivot`` in *reference
        pixels* (the SVG rendered at ``ref_dpi``); ``scale`` is base-frame units
        per reference pixel, so the same art drives both the bone geometry and
        the rendered raster."""
        return self.data.setdefault("svg_source", {})

    @property
    def animation_constraints(self) -> dict:
        """Authoring constraints evaluated continuously by the rig solver.

        Transform pins keep arbitrary selected parts fixed in frame space and
        are stored separately from generated channel data so rebuild scripts
        can preserve them while replacing clips.
        """
        return constraints_root(self)

    @property
    def gameplay_geometry(self) -> dict:
        """Authoring-only collision/hurt/hit geometry and cue bindings.

        Sheet publication and game runtime intentionally ignore this block in
        the first authoring slice.  Accessing it creates the versioned container
        so editor mutations have one stable location.
        """
        from .gameplay_geometry import geometry_root

        return geometry_root(self)

    @property
    def sprite_tuning(self) -> Dict[str, float]:
        """Optional in-game sheet tuning, emitted to the RON's ``tuning`` field
        and read by the runtime ``SheetRegistry``:

        - ``collision_scale`` — the in-game display SIZE driver
          (height = collision * collision_scale). Raise it to make a character
          render bigger/taller without touching its gameplay collision box.
        - ``frame_sample_inset`` — pixels trimmed off each atlas cell edge.

        (Feet placement is NOT a tuning knob — it rides
        ``body_metrics.feet_anchor_norm`` in the emitted record.)

        Absent → the runtime's ``DEFAULT_TUNING`` (collision_scale 1.5). This is
        how a rig specifies its own defaults instead of inheriting the fallback."""
        return self.data.setdefault("sprite_tuning", {})

    def bone(self, name: str) -> Optional[dict]:
        for b in self.bones:
            if b["name"] == name:
                return b
        return None

    def rows(self) -> List[Tuple[str, int, int]]:
        return [
            (name, int(c.get("frames", 8)), int(c.get("duration_ms", 100)))
            for name, c in self.clips.items()
        ]

    def ik_bone_names(self) -> set:
        out = set()
        for leg in self.ik_legs:
            out.update({leg.get("upper"), leg.get("lower"), leg.get("foot")})
        for chain in self.ik_chains:
            out.update({chain.get("upper"), chain.get("lower"), chain.get("end")})
        out.discard(None)
        return out

    def foot_leg_for_bone(self, bone_name: str) -> Optional[dict]:
        for leg in self.ik_legs:
            if bone_name in (leg.get("foot"), leg.get("lower"), leg.get("upper")):
                return leg
        return None

    # ---- Evaluation ----------------------------------------------------------

    @profile
    def build_skeleton(self) -> Skeleton:
        key = tuple(
            (
                bone["name"],
                bone.get("parent"),
                tuple(bone.get("offset", (0.0, 0.0))),
                float(bone.get("length", 0.0)),
                float(bone.get("rest_angle", 0.0)),
            )
            for bone in self.bones
        )
        if key == self._skeleton_cache_key and self._skeleton_cache is not None:
            return self._skeleton_cache
        sk = Skeleton()
        for name, parent, offset, length, rest_angle in key:
            sk.bone(
                name,
                parent=parent,
                offset=offset,
                length=length,
                rest_angle=rest_angle,
            )
        self._skeleton_cache_key = key
        self._skeleton_cache = sk
        return sk

    @profile
    def sample(self, clip_name: str, t: float) -> Dict[str, float]:
        clip = self.clips.get(clip_name) or {"channels": {}}
        loop = bool(clip.get("loop", True))
        return {
            name: sample_channel_spec(spec, t, loop)
            for name, spec in clip.get("channels", {}).items()
        }

    @profile
    def solve(self, clip_name: str, t: float):
        """Sample channels, run leg + generic two-bone IK, return worlds/params."""
        s = self.sample(clip_name, t)
        fr = self.frame
        cx = float(fr.get("center_x", fr["width"] / 2))
        gy = float(fr.get("ground_y", fr["height"] - 2))
        ankle_h = float(fr.get("ankle_h", 0.0))
        root = (cx + s.get("root_x", 0.0), gy + s.get("root_y", 0.0))
        sk = self.build_skeleton()
        angles = {n: v for n, v in s.items() if n in sk.bones}
        bone_offsets = {
            name: (
                float(s.get(f"bone.{name}.x", 0.0)),
                float(s.get(f"bone.{name}.y", 0.0)),
            )
            for name in sk.bones
            if f"bone.{name}.x" in s or f"bone.{name}.y" in s
        }

        def world_for(sampled_angles):
            return sk.world(sampled_angles, root=root, offsets=bone_offsets)

        w0 = world_for(angles)
        def solve_chain(
            chain: dict,
            target: Point,
            *,
            end_name: Optional[str],
            pitch: Optional[float],
            bend: Optional[float] = None,
        ) -> None:
            up, lo = chain["upper"], chain["lower"]
            if up not in sk.bones or lo not in sk.bones:
                return
            origin = w0[up].origin
            upper_len = sk.bones[up].length
            lower_len = sk.bones[lo].length
            max_reach_ratio = chain.get("max_reach_ratio")
            if max_reach_ratio is not None:
                ratio = max(0.0, min(1.0, float(max_reach_ratio)))
                dx = target[0] - origin[0]
                dy = target[1] - origin[1]
                distance = math.hypot(dx, dy)
                max_distance = (upper_len + lower_len) * ratio
                if distance > max_distance and distance > 1e-9:
                    scale = max_distance / distance
                    target = (origin[0] + dx * scale, origin[1] + dy * scale)
            a1, a2 = two_bone_ik(
                origin,
                target,
                upper_len,
                lower_len,
                bend=float(chain.get("bend", 1.0) if bend is None else bend),
            )
            parent = sk.bones[up].parent
            parent_angle = w0[parent].angle if parent else 0.0
            angles[up] = a1 - parent_angle - sk.bones[up].rest_angle
            angles[lo] = a2 - a1 - sk.bones[lo].rest_angle
            if end_name and end_name in sk.bones and pitch is not None:
                angles[end_name] = pitch - a2 - sk.bones[end_name].rest_angle

        for leg in self.ik_legs:
            pre = leg.get("channel_prefix", "foot")
            # rest_x/rest_lift/rest_pitch default the foot to its drawn stance, so
            # a clip only needs to drive the channels it actually animates.
            x = s.get(f"{pre}_x", float(leg.get("rest_x", 0.0)))
            lift = s.get(f"{pre}_lift", float(leg.get("rest_lift", 0.0)))
            pitch = s.get(f"{pre}_pitch", float(leg.get("rest_pitch", 0.0)))
            bend = s.get(f"{pre}_bend", float(leg.get("bend", 1.0)))
            solve_chain(
                leg,
                (cx + x, gy - ankle_h - lift),
                end_name=leg.get("foot"),
                pitch=pitch,
                bend=bend,
            )

        for chain in self.ik_chains:
            pre = chain.get("channel_prefix", "target")
            x = s.get(f"{pre}_x", float(chain.get("rest_x", 0.0)))
            y = s.get(f"{pre}_y", float(chain.get("rest_y", 0.0)))
            end_name = chain.get("end")
            pitch = None
            if end_name:
                pitch_key = f"{pre}_pitch"
                pitch_mode = str(chain.get("pitch_mode", "world"))
                if pitch_key in s:
                    pitch = s[pitch_key]
                elif pitch_mode == "world":
                    pitch = float(chain.get("rest_pitch", 0.0))
                elif pitch_mode != "follow_lower":
                    raise ValueError(
                        f"unknown IK hand pitch_mode {pitch_mode!r} for {pre!r}"
                    )
            bend = s.get(f"{pre}_bend", float(chain.get("bend", 1.0)))
            solve_chain(
                chain,
                (cx + x, gy + y),
                end_name=end_name,
                pitch=pitch,
                bend=bend,
            )

        # Continuous transform pins are applied after ordinary FK/IK sampling.
        # They constrain an arbitrary local anchor on a selected bone and may
        # preserve its world rotation. Pinning a foot bone therefore holds the
        # complete boot/toe artwork rigidly while parent bob is absorbed by IK.
        clip = self.clips.get(clip_name) or {}
        for pin in transform_pins(self, clip_name, create=False):
            if not pin_active(clip, pin, t):
                continue
            bone_name = str(pin.get("bone") or "")
            solver = pin.get("solver") or {}
            upper = str(solver.get("upper") or "")
            lower = str(solver.get("lower") or "")
            if (
                not bone_name
                or bone_name not in sk.bones
                or upper not in sk.bones
                or lower not in sk.bones
            ):
                continue

            current_world = world_for(angles)
            sampled = current_world.get(bone_name)
            if sampled is None:
                continue
            raw_anchor = pin.get("anchor_local") or (0.0, 0.0)
            anchor_local = (float(raw_anchor[0]), float(raw_anchor[1]))
            sampled_anchor = sampled.to_world(anchor_local)
            raw_target = pin.get("target") or sampled_anchor
            anchor_target = (
                float(raw_target[0]) if pin.get("lock_x", True) else sampled_anchor[0],
                float(raw_target[1]) if pin.get("lock_y", True) else sampled_anchor[1],
            )
            mode = str(solver.get("mode", "endpoint_bone"))
            chain_root = current_world[upper].origin
            parent = sk.bones[upper].parent
            parent_angle = current_world[parent].angle if parent else 0.0

            if mode == "point_on_lower":
                # The visual endpoint is authored directly on the terminal
                # lower bone (for example a hand circle centered at arm_l's
                # tip), so there is no separate wrist/hand bone whose rotation
                # can absorb an orientation lock.  Solve the selected local
                # point exactly and let the lower-bone rotation follow IK.
                radius = math.hypot(anchor_local[0], anchor_local[1])
                if radius <= 1e-6:
                    continue
                anchor_angle = math.degrees(
                    math.atan2(anchor_local[1], anchor_local[0])
                )
                a1, anchor_world_angle = two_bone_ik(
                    chain_root,
                    anchor_target,
                    sk.bones[upper].length,
                    radius,
                    bend=float(solver.get("bend", 1.0)),
                )
                lower_world_angle = anchor_world_angle - anchor_angle
                angles[upper] = a1 - parent_angle - sk.bones[upper].rest_angle
                angles[lower] = (
                    lower_world_angle - a1 - sk.bones[lower].rest_angle
                )
                continue

            desired_angle = (
                float(pin.get("rotation", sampled.angle))
                if pin.get("lock_rotation", True)
                else sampled.angle
            )
            radians = math.radians(desired_angle)
            rotated_anchor = (
                anchor_local[0] * math.cos(radians)
                - anchor_local[1] * math.sin(radians),
                anchor_local[0] * math.sin(radians)
                + anchor_local[1] * math.cos(radians),
            )
            origin_target = (
                anchor_target[0] - rotated_anchor[0],
                anchor_target[1] - rotated_anchor[1],
            )

            a1, a2 = two_bone_ik(
                chain_root,
                origin_target,
                sk.bones[upper].length,
                sk.bones[lower].length,
                bend=float(solver.get("bend", 1.0)),
            )
            angles[upper] = a1 - parent_angle - sk.bones[upper].rest_angle
            angles[lower] = a2 - a1 - sk.bones[lower].rest_angle
            angles[bone_name] = desired_angle - a2 - sk.bones[bone_name].rest_angle
        return world_for(angles), s

    # ---- Sprite parts (rasterized SVG subsets) ------------------------------

    def _svg_path(self) -> Optional[Path]:
        src = self.svg_source.get("path")
        if not src:
            return None
        cache_key = (str(src), str(self.source_path) if self.source_path else None)
        if cache_key == self._svg_path_cache_key:
            return self._svg_path_cache
        p = Path(str(src))
        if not p.is_absolute() and self.source_path is not None:
            p = (self.source_path.parent / p).resolve()
        self._svg_path_cache_key = cache_key
        self._svg_path_cache = p
        return p

    @profile
    def sprite_image(self, part: dict, S: float) -> Optional[Tuple[Image.Image, Point]]:
        """Rasterize a ``sprite`` part's SVG subset at composite scale ``S``.

        Returns ``(cropped RGBA, pivot_in_crop_px)`` — the pivot is the part's
        joint (``pivot``, in reference px) located inside the cropped raster.
        Cached per ``(part, round(S))`` so a whole sheet rasterizes each part
        once. ``None`` if the SVG is unavailable or the subset renders empty."""
        sprite = self.sprite_raster(part, S)
        if sprite is None:
            return None
        return sprite.image, sprite.pivot

    @profile
    def sprite_raster(self, part: dict, S: float) -> Optional[SpriteRaster]:
        """Return a cached SVG part plus its reusable pivot-centered raster."""
        src = self.svg_source
        # Key on everything the cached value derives from (subset + pivot +
        # source + scale): two sprite parts with the same (or absent) name but
        # a different SVG include-list, pivot, source, or scale must not share
        # a raster. Build and check this key before touching the filesystem;
        # cache hits are the overwhelmingly common editor path.
        key = (
            str(src.get("path", "")),
            str(src.get("view", "")),
            float(src.get("ref_dpi", 96.0)),
            float(src.get("scale", 1.0)),
            part.get("name", ""),
            tuple(part.get("include") or ()),
            tuple(part.get("pivot", (0.0, 0.0))),
            int(round(S * 256)),
        )
        cached = self._sprite_cache.get(key)
        if cached is not None:
            return cached

        svg_path = self._svg_path()
        if svg_path is None or not svg_path.exists():
            return None
        from .svg_parts import rasterize_subset

        ref_dpi = float(src.get("ref_dpi", 96.0))
        scale = float(src.get("scale", 1.0))  # base-frame units per reference px
        view = str(src.get("view", ""))
        # 1 ref-px -> scale*S composite px, so render the SVG at this dpi.
        dpi = ref_dpi * scale * S
        img, (off_x, off_y), _ppu = rasterize_subset(
            svg_path, view, list(part.get("include", [])), dpi
        )
        if img is None:
            return None
        px, py = part.get("pivot", (0.0, 0.0))
        pivot = (px * scale * S - off_x, py * scale * S - off_y)
        radius = int(math.ceil(max(
            math.hypot(cx - pivot[0], cy - pivot[1])
            for cx in (0, img.width)
            for cy in (0, img.height)
        ))) + 2
        padded = Image.new("RGBA", (2 * radius, 2 * radius), (0, 0, 0, 0))
        padded.alpha_composite(
            img,
            (
                radius - int(round(pivot[0])),
                radius - int(round(pivot[1])),
            ),
        )
        prepared = SpriteRaster(
            image=img,
            pivot=pivot,
            padded=padded,
            radius=radius,
            cache_key=key,
            working_scale=float(S),
            premultiplied=img.convert("RGBa"),
        )
        self._sprite_cache[key] = prepared
        return prepared

    # ---- Painting -----------------------------------------------------------

    @profile
    def render_at(
        self,
        clip_name: str,
        t: float,
        supersample: Optional[int] = None,
        scale: Optional[int] = None,
        solved=None,
        padding: Optional[RenderPadding] = None,
    ) -> Image.Image:
        """Render one frame at normalized time ``t`` (continuous — the GUI
        scrubs with this). Output size is ``(width*scale, height*scale)``;
        ``scale`` defaults to the document's ``frame.render_scale`` (1), so
        a doc can publish at 2x/4x resolution while geometry stays authored
        in base-frame units. ``solved`` may provide a previously computed
        ``(world, params)`` pair so the editor can share one solve between the
        sprite render, bone overlay, and hit testing. ``padding`` adds
        transparent render overscan around the logical frame *before* parts are
        painted; unlike padding a finished frame, this preserves pixels from
        rotations that would otherwise be clipped at the logical-frame edge.
        """
        fr = self.frame
        w, h = int(fr["width"]), int(fr["height"])
        pad_left, pad_top, pad_right, pad_bottom = normalize_render_padding(padding)
        out_w = w + pad_left + pad_right
        out_h = h + pad_top + pad_bottom
        rs = int(scale if scale is not None else fr.get("render_scale", 1))
        rs = max(1, rs)
        ss = max(1, int(supersample if supersample is not None else fr.get("supersample", 4)))
        S = float(rs * ss)
        img = Image.new("RGBA", (int(out_w * S), int(out_h * S)), (0, 0, 0, 0))
        draw = blending_draw(img)
        world, params = solved if solved is not None else self.solve(clip_name, t)
        world = translate_bone_worlds(world, float(pad_left), float(pad_top))

        # Raster preparation and z-order remain deterministic on the caller
        # thread. Independent non-zero SVG transforms can then run concurrently;
        # composition below still happens strictly in authoritative part order.
        paint_items: List[Tuple[dict, Optional[SpriteRaster]]] = []
        rotation_slots: List[int] = []
        rotation_requests: List[Tuple[SpriteRaster, float]] = []
        for part in visible_parts(self.parts, self.features):
            sprite = self.sprite_raster(part, S) if part.get("kind") == "sprite" else None
            slot = len(paint_items)
            paint_items.append((part, sprite))
            if sprite is None:
                continue
            bone_name = part.get("bone")
            if bone_name not in world:
                continue
            delta = normalize_degrees(
                world[bone_name].angle - float(part.get("rest_angle", 0.0))
            )
            if delta != 0.0:
                rotation_slots.append(slot)
                rotation_requests.append((sprite, delta))

        prepared_rotations: Dict[int, Image.Image] = {}
        if rotation_requests:
            prepared_rotations = dict(
                zip(
                    rotation_slots,
                    self._sprite_transform_cache.rotated_many(rotation_requests),
                )
            )

        for slot, (part, sprite) in enumerate(paint_items):
            paint_part(
                img,
                draw,
                part,
                world,
                S,
                params,
                self.palette,
                sprite=sprite,
                transform_cache=self._sprite_transform_cache,
                rotated_sprite=prepared_rotations.get(slot),
            )
        if ss == 1:
            return img
        # SVG parts are already antialiased at the supersample resolution.
        # Lanczos adds negative-lobe ringing around high-contrast white shells,
        # which survives as isolated pale pixels around the transparent sprite.
        return resize_transparent_sprite(
            img,
            (out_w * rs, out_h * rs),
            reducing_gap=3.0,
        )

    def measure_render_padding(
        self,
        samples,
        *,
        margin: int = 2,
        probe_padding: Optional[RenderPadding] = None,
    ) -> Tuple[int, int, int, int]:
        """Measure the overscan needed to preserve the supplied rendered poses.

        ``render_at`` intentionally paints into a fixed logical canvas unless a
        caller supplies ``padding``.  That is appropriate for an editor viewport,
        but sprite publication must not silently sever a hand, weapon, or rotated
        limb just because an authored pose leaves the nominal frame.

        This helper performs a cheap 1x/1-supersample probe for the exact clip
        times that a caller plans to publish, measures their alpha bounds in a
        generously padded canvas, and returns the smallest logical-pixel
        ``(left, top, right, bottom)`` overscan that contains them plus ``margin``.
        The final render can then use that padding at its normal resolution.

        The probe is deliberately separate from sprite sampling: callers pass the
        times they actually intend to render, whether those are legacy publication
        samples, an adaptive bake plan, or a hand-picked review sequence.
        """
        fr = self.frame
        width = int(fr["width"])
        height = int(fr["height"])
        margin = max(0, int(margin))
        if probe_padding is None:
            # A full nominal-frame radius on every side is generous enough for a
            # limb/weapon orbit without making the sequential 1x probe expensive.
            probe_padding = max(width, height)
        probe_left, probe_top, probe_right, probe_bottom = normalize_render_padding(
            probe_padding
        )
        required = [0, 0, 0, 0]
        saw_sample = False
        for clip_name, t in samples:
            saw_sample = True
            image = self.render_at(
                str(clip_name),
                float(t),
                supersample=1,
                scale=1,
                padding=(probe_left, probe_top, probe_right, probe_bottom),
            )
            bbox = image.getchannel("A").getbbox()
            if bbox is None:
                continue
            if (
                bbox[0] <= 0
                or bbox[1] <= 0
                or bbox[2] >= image.width
                or bbox[3] >= image.height
            ):
                raise ValueError(
                    f"render-padding probe for {clip_name!r} reached the probe canvas edge; "
                    "increase probe_padding instead of accepting clipped bounds"
                )
            logical_left = probe_left
            logical_top = probe_top
            logical_right = probe_left + width
            logical_bottom = probe_top + height
            required[0] = max(required[0], logical_left - bbox[0])
            required[1] = max(required[1], logical_top - bbox[1])
            required[2] = max(required[2], bbox[2] - logical_right)
            required[3] = max(required[3], bbox[3] - logical_bottom)
        if not saw_sample:
            return (0, 0, 0, 0)
        return tuple(max(0, int(math.ceil(value)) + margin) for value in required)

    def frame_time(self, clip_name: str, frame_idx: int, nframes: Optional[int] = None) -> float:
        """Normalized time for a frame index under the loop conventions:
        loops sample i/n (no duplicated end frame), one-shots i/(n-1)."""
        clip = self.clips.get(clip_name) or {}
        n = int(nframes or clip.get("frames", 8))
        if bool(clip.get("loop", True)):
            return frame_idx / max(1, n)
        return frame_idx / max(1, n - 1)

    def render_frame(
        self,
        clip_name: str,
        frame_idx: int,
        nframes: int,
        *,
        padding: Optional[RenderPadding] = None,
    ) -> Image.Image:
        return self.render_at(
            clip_name,
            self.frame_time(clip_name, frame_idx, nframes),
            padding=padding,
        )


# ---- Part painting -----------------------------------------------------------
# Module-level so generated Python targets (rigdoc_codegen) can paint the
# same part vocabulary without carrying a RigDocument around.


@profile
def blit_rotated(
    canvas: Image.Image,
    sprite: Image.Image,
    pivot: Point,
    world_px: Point,
    delta_deg: float,
    opacity: float = 1.0,
    *,
    prepared: Optional[SpriteRaster] = None,
    transform_cache: Optional[SpriteTransformCache] = None,
    rotated_sprite: Optional[Image.Image] = None,
) -> None:
    """Rotate ``sprite`` about its ``pivot`` by ``delta_deg`` and composite it so
    the pivot lands at ``world_px``.

    Rig documents pass a prepared pivot-centered raster and a bounded transform
    cache. Standalone callers retain the original behavior through the public
    ``sprite`` / ``pivot`` arguments.
    """
    angle = normalize_degrees(delta_deg)
    px, py = pivot

    # Most rigid torso/head pieces and every part at its rest pose need no
    # rotation. Composite the cropped source directly instead of allocating a
    # padded square and asking PIL to resample an unchanged image.
    if angle == 0.0:
        source = sprite
        if opacity < 1.0:
            source = sprite.copy()
            source.putalpha(
                source.getchannel("A").point(lambda value: int(value * opacity))
            )
        canvas.alpha_composite(
            source,
            (
                int(round(world_px[0])) - int(round(px)),
                int(round(world_px[1])) - int(round(py)),
            ),
        )
        return

    if prepared is not None:
        if rotated_sprite is not None:
            rot = rotated_sprite
            anchor_x = rot.width // 2
            anchor_y = rot.height // 2
        elif transform_cache is not None:
            rot = transform_cache.rotated(prepared, angle)
            anchor_x = rot.width // 2
            anchor_y = rot.height // 2
        else:
            R = prepared.radius
            rot = rotate_transparent_sprite(
                prepared.padded,
                -angle,
                center=(R, R),
            )
            anchor_x = R
            anchor_y = R
    else:
        w, h = sprite.size
        radius = max(
            math.hypot(cx - px, cy - py) for cx in (0, w) for cy in (0, h)
        )
        R = int(math.ceil(radius)) + 2
        pad = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
        pad.alpha_composite(sprite, (R - int(round(px)), R - int(round(py))))
        # The toolkit's angles are clockwise-positive in screen space (+y down);
        # PIL's rotate() is counter-clockwise-positive, so negate to match bones.
        rot = rotate_transparent_sprite(
            pad,
            -angle,
            center=(R, R),
        )
        anchor_x = R
        anchor_y = R
    if opacity < 1.0:
        # Cached rotations stay full-opacity and immutable; fade a throwaway copy.
        rot = rot.copy()
        rot.putalpha(rot.getchannel("A").point(lambda v: int(v * opacity)))
    canvas.alpha_composite(
        rot,
        (
            int(round(world_px[0])) - anchor_x,
            int(round(world_px[1])) - anchor_y,
        ),
    )


@profile
def paint_part(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    part: dict,
    world: Dict[str, BoneWorld],
    S: float,
    params: Dict[str, float],
    palette: Dict[str, str],
    sprite: Optional[Union[SpriteRaster, Tuple[Image.Image, Point]]] = None,
    transform_cache: Optional[SpriteTransformCache] = None,
    rotated_sprite: Optional[Image.Image] = None,
) -> None:
    bone_name = part.get("bone")
    if bone_name not in world:
        return
    opacity = 1.0
    oc = part.get("opacity_channel")
    if oc:
        # Default 0: a part bound to an opacity channel is HIDDEN in clips
        # that don't drive that channel (a blade only shows in clips that
        # animate slash_vis).
        #
        # `opacity_default` inverts that for the member of a SWAP SET that is
        # the normal one. A torso needs alternates it can cut to, and the
        # default-hidden rule cannot express "this one unless told otherwise":
        # binding the base torso to a channel would erase it from every clip
        # that never mentions the swap, which is most of them.
        opacity = clamp(params.get(oc, float(part.get("opacity_default", 0.0))), 0.0, 1.0)
        if opacity <= 0.01:
            return
    # Global body fade (default 1.0) — a clip can phase the WHOLE character in/out
    # (e.g. a blink dematerialize) by driving ``body_opacity`` without tagging every
    # part with its own channel. No clip setting it leaves rendering unchanged.
    opacity *= clamp(params.get("body_opacity", 1.0), 0.0, 1.0)
    if part.get("kind") == "sprite":
        if sprite is None:
            return
        bw = world[bone_name]
        if isinstance(sprite, SpriteRaster):
            spr_img, pivot = sprite.image, sprite.pivot
            prepared = sprite
        else:
            spr_img, pivot = sprite
            prepared = None
        delta = bw.angle - float(part.get("rest_angle", 0.0))
        #  `bone.<name>.flip_x` mirrors a part about its own pivot. A clip
        # that never sets it renders exactly as before, so this is additive. The
        # mirror is applied in the part's LOCAL frame and the bone transform then
        # applies as usual, which is what an author means by "face the other way":
        # the head turns, it does not orbit.  a mirrored raster cannot come from
        # the rotation cache (that cache is keyed by angle alone), so the prepared
        # and pre-rotated fast paths are declined for this part only.
        if params.get(f"bone.{bone_name}.flip_x", 0.0) >= 0.5:
            spr_img = spr_img.transpose(Image.FLIP_LEFT_RIGHT)
            pivot = (spr_img.width - pivot[0], pivot[1])
            prepared = None
            rotated_sprite = None
        #  `bone.<name>.scale_y` squashes a part about its own pivot. Absent
        # or 1.0 renders exactly as before. Anchoring at the PIVOT is the whole
        # point: a squashed torso keeps its hip where the hips are, and shortens
        # upward, so whatever hangs off it moves by a knowable amount.
        sy = float(params.get(f"bone.{bone_name}.scale_y", 1.0))
        if sy != 1.0 and sy > 0.0:
            w, h = spr_img.size
            nh = max(1, int(round(h * sy)))
            spr_img = spr_img.resize((w, nh), Image.LANCZOS)
            pivot = (pivot[0], pivot[1] * sy)
            prepared = None
            rotated_sprite = None
        blit_rotated(
            img,
            spr_img,
            pivot,
            (bw.origin[0] * S, bw.origin[1] * S),
            delta,
            opacity,
            prepared=prepared,
            transform_cache=transform_cache,
            rotated_sprite=rotated_sprite,
        )
        return
    fill = parse_color(part.get("fill", "#FFFFFF"), palette, opacity)
    outline = parse_color(part.get("outline"), palette, opacity)
    ow = float(part.get("outline_w", 0.0)) * S
    translucent = (fill is not None and fill[3] < 255) or (
        outline is not None and outline[3] < 255
    )
    if translucent:
        # gnu_ton rule: translucent shapes composite via a scratch layer;
        # drawing them directly would replace destination alpha.
        target = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tdraw = blending_draw(target)
    else:
        target, tdraw = img, draw
    bw = world[bone_name]
    kind = part.get("kind", "polygon")
    if kind == "polygon":
        pts = [
            (p[0] * S, p[1] * S)
            for p in (bw.to_world(tuple(q)) for q in part.get("points", []))
        ]
        if len(pts) >= 3:
            radius = float(part.get("radius", 0.0)) * S
            poly = rounded_polygon(pts, radius) if radius > 0 else pts
            draw_polygon(tdraw, poly, fill, outline, ow)
    elif kind == "capsule":
        a_local = tuple(part.get("a", (0.0, 0.0)))
        b_local = part.get("b")
        if b_local is None:
            b_local = (bw.length, 0.0)
        a = bw.to_world(a_local)
        b = bw.to_world(tuple(b_local))
        r = float(part.get("radius", 2.0)) * S
        draw_capsule(
            tdraw,
            (a[0] * S, a[1] * S),
            (b[0] * S, b[1] * S),
            r,
            fill,
            outline if outline is not None else fill,
            ow * 0.5,
        )
    elif kind == "circle":
        # Optional "ry" stretches the circle into an ellipse (eyes).
        c = bw.to_world(tuple(part.get("center", (0.0, 0.0))))
        rx = float(part.get("radius", 2.0)) * S
        ry = float(part.get("ry", part.get("radius", 2.0))) * S
        box = (c[0] * S - rx, c[1] * S - ry, c[0] * S + rx, c[1] * S + ry)
        if outline is not None and ow > 0:
            tdraw.ellipse(box, fill=fill, outline=outline, width=max(1, int(ow)))
        else:
            tdraw.ellipse(box, fill=fill)
    if translucent:
        img.alpha_composite(target)


# ---- Sheet / GIF export ----------------------------------------------------


def render_sheet_for_doc(doc: RigDocument, out_dir: Path) -> List[Path]:
    """Render the document's full spritesheet bundle (PNG + YAML + RON +
    canonical + preview) via the standard tack-on sheet builder."""
    from .sheet_build import build_sheet

    fr = doc.frame
    rs = max(1, int(fr.get("render_scale", 1)))
    # Rigged docs live under targets/characters/rigged/ and render through the
    # trim-aware CharacterAnimator path, so they pack by the target's default
    # pack-group policy (registry/pack_groups.py). A doc may still opt out per
    # frame via `frame.trim: false`; absent that, `None` defers to the policy.
    outputs = build_sheet(
        target=doc.name,
        rows=doc.rows(),
        render_fn=doc.render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(fr["width"]) * rs, int(fr["height"]) * rs),
        sheet_tuning=doc.sprite_tuning or None,
        authored_faces_left=doc.authored_faces_left,
        actor_metadata=doc.data.get("actor_metadata"),
        trim=fr.get("trim"),
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[k]) for k in keys if outputs.get(k)]


def render_gifs_for_doc(doc: RigDocument, out_dir: Path, scale: int = 2) -> List[Path]:
    """One looping GIF per clip, rendered at ``scale``x base size."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fr = doc.frame
    w, h = int(fr["width"]) * scale, int(fr["height"]) * scale
    paths: List[Path] = []
    for name, frames, duration_ms in doc.rows():
        imgs = []
        for i in range(frames):
            frame = doc.render_frame(name, i, frames)
            bg = Image.new("RGBA", frame.size, (43, 33, 40, 255))
            bg.alpha_composite(frame)
            imgs.append(bg.convert("P").resize((w, h), Image.Resampling.NEAREST))
        path = out_dir / f"{doc.name}_{name}.gif"
        imgs[0].save(
            path, save_all=True, append_images=imgs[1:],
            duration=duration_ms, loop=0, disposal=2,
        )
        paths.append(path)
    return paths
