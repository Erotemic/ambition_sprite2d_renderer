"""The opening of a door: a strip of frames, from closed to open.

A door picture has a leaf (or two leaves) in an opening of a frame. To open
it, each leaf moves away from the camera into the room behind the door, and
the opening shows that room: dark, darkest at the top, with a faint glow of
the door's own light on the floor of the threshold. The frame and the step
do not change: they are in front of the leaf.

A leaf moves in one of two ways:

- ``SWING``: it turns on its hinge (the jamb on its side) into the room. Its
  width is ``cos(angle)`` of its width, its far edge is smaller (it is farther
  from the camera), and it is darker as it turns away from the light;
- ``SLIDE``: it moves in its own plane into the wall on its hinge side (a
  bulkhead, a paper screen).

The input is the closed picture at work resolution (before the downsample)
as straight-alpha float arrays, and the leaf masks. The output is one
picture of the same kind for each frame. Frame 0 is the closed picture.
This module draws; the caller downsamples and publishes, in the same way it
publishes the closed picture, so frame 0 is the same picture to the pixel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

RGB = tuple[float, float, float]

#: The frames of an opening, the closed picture first.
OPENING_FRAMES = 6
#: The angle of a swung leaf in the last frame, in degrees.
OPEN_ANGLE_DEG = 80.0

SWING = "swing"
SLIDE = "slide"


@dataclass(frozen=True)
class Leaf:
    """One leaf of a door, at work resolution.

    `mask` is the coverage (0..1) of the leaf when it is closed. `hinge_x` is
    the column of its hinge (the jamb it turns on or slides into), and
    `free_x` the column of its other edge."""

    mask: np.ndarray
    hinge_x: float
    free_x: float
    motion: str = SWING


@dataclass(frozen=True)
class Room:
    """The room that the open door shows.

    `dark` is the colour of its air; `glow` the light of the door, which
    falls on the floor of the threshold. `top` and `bottom` are the rows of
    the top and the floor of the opening. `alpha` is its cover: less than 1
    for a door that is part clear (a drawing)."""

    dark: RGB
    glow: RGB
    top: float
    bottom: float
    alpha: float = 1.0


def opening_progress(frames: int = OPENING_FRAMES) -> list[float]:
    """How open the door is in each frame, 0 (closed) to 1 (open). The
    motion is slow at the two ends (a smoothstep)."""
    out = []
    for k in range(frames):
        t = k / (frames - 1)
        out.append(t * t * (3.0 - 2.0 * t))
    return out


def _room(shape: tuple[int, int], opening: np.ndarray, room: Room) -> np.ndarray:
    """The colour of the room seen through the opening."""
    h, w = shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    span = max(room.bottom - room.top, 1.0)
    t = np.clip((ys - room.top) / span, 0.0, 1.0)[:, :, None]
    dark = np.asarray(room.dark, dtype=np.float32)
    glow = np.asarray(room.glow, dtype=np.float32)
    deep = dark * 0.22
    near = dark * 0.75 + glow * 0.04
    colour = deep + (near - deep) * t**1.6
    # The glow on the floor: strong at the threshold, less to the sides.
    cols = np.where(opening.max(axis=0) > 0.5)[0]
    cx = (cols.min() + cols.max() + 1) * 0.5 if cols.size else w * 0.5
    half = (cols.max() + 1 - cols.min()) * 0.5 if cols.size else w * 0.5
    floor = np.exp(-np.clip(room.bottom - ys, 0.0, None) / (span * 0.09))
    side = np.exp(-(((xs - cx) / (half * 0.8)) ** 2))
    colour = colour + (glow - colour) * (0.38 * floor * side)[:, :, None]
    return np.clip(colour, 0.0, 255.0)


def _place(leaf: Leaf, progress: float, eye_y: float, depth: float, shape: tuple[int, int]):
    """For each pixel, the pixel of the closed leaf that is seen there, and
    how much light the leaf has there. Returns `(src_x, src_y, valid, light)`."""
    h, w = shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    side = 1.0 if leaf.free_x >= leaf.hinge_x else -1.0
    width = abs(leaf.free_x - leaf.hinge_x)
    if leaf.motion == SLIDE:
        shift = progress * width
        src_x = xs + side * shift
        src_y = ys
        valid = (side * (src_x - leaf.hinge_x) >= 0.0)
        light = np.full((h, w), 1.0 - 0.18 * progress, dtype=np.float32)
        return src_x, src_y, valid, light
    angle = math.radians(OPEN_ANGLE_DEG) * progress
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    # The leaf seen from the front: width × cos(angle), with the hinge fixed.
    u = side * (xs - leaf.hinge_x) / max(width * cos_a, 1e-3)
    valid = (u >= 0.0) & (u <= 1.0)
    u = np.clip(u, 0.0, 1.0)
    # A part of the leaf that is farther from the camera is smaller about the
    # eye line. The scale is linear across the leaf, so its top and its foot
    # stay straight lines.
    scale = 1.0 - u * (1.0 - depth / (depth + width * sin_a))
    src_x = leaf.hinge_x + side * u * width
    src_y = eye_y + (ys - eye_y) / scale
    # It turns away from the light, and its far edge is in the room's dark.
    light = (1.0 - 0.5 * sin_a) * (1.0 - 0.22 * sin_a * u)
    return src_x, src_y, valid, light.astype(np.float32)


def _sample(image: np.ndarray, src_x: np.ndarray, src_y: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    ix = np.clip(np.floor(src_x).astype(np.int64), 0, w - 1)
    iy = np.clip(np.floor(src_y).astype(np.int64), 0, h - 1)
    inside = (src_x >= 0) & (src_x < w) & (src_y >= 0) & (src_y < h)
    out = image[iy, ix]
    if out.ndim == 3:
        return out * inside[:, :, None]
    return out * inside


def opening_frames(
    rgb: np.ndarray,
    alpha: np.ndarray,
    opening: np.ndarray,
    leaves: list[Leaf],
    room: Room,
    *,
    eye_y: float | None = None,
    frames: int = OPENING_FRAMES,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """The frames of the opening of a door, each as `(rgb, alpha)`.

    `rgb` (H, W, 3, 0..255) and `alpha` (H, W, 0..1) are the closed picture,
    straight alpha. `opening` is the coverage of the hole in the frame: the
    room shows there, and a leaf shows only there (the frame is in front of
    it). Frame 0 is the input, not changed."""
    closed = (rgb.copy(), alpha.copy())
    shape = alpha.shape
    if eye_y is None:
        eye_y = room.top + (room.bottom - room.top) * 0.55
    # The distance of the camera, in work pixels: the far edge of a leaf at
    # right angles is about 0.7 of its height.
    widest = max(abs(leaf.free_x - leaf.hinge_x) for leaf in leaves)
    depth = 2.4 * widest
    behind = _room(shape, opening, room)
    out = []
    for progress in opening_progress(frames):
        if progress <= 0.0:
            # Not cast or changed: frame 0 is the closed picture to the pixel.
            out.append(closed)
            continue
        # The room through the opening.
        frame_rgb = rgb + (behind - rgb) * opening[:, :, None]
        frame_a = alpha + (room.alpha - alpha) * opening
        for leaf in leaves:
            src_x, src_y, valid, light = _place(leaf, progress, eye_y, depth, shape)
            cover = _sample(leaf.mask, src_x, src_y) * _sample(alpha, src_x, src_y) * valid * opening
            colour = _sample(rgb, src_x, src_y) * light[:, :, None]
            # The leaf goes over the room: straight-alpha "over".
            out_a = cover + frame_a * (1.0 - cover)
            weight = np.where(out_a > 1e-6, cover / np.maximum(out_a, 1e-6), 0.0)[:, :, None]
            frame_rgb = frame_rgb * (1.0 - weight) + colour * weight
            frame_a = out_a
        out.append((np.clip(frame_rgb, 0.0, 255.0), np.clip(frame_a, 0.0, 1.0)))
    return out
