"""A cheap check that an image fits in memory before it is made.

A packed sheet page can be very large (a boss that packs one page per layer
reaches 15040 x 11968 RGBA, 720 MB), and a publish holds several of them at
once on top of every rendered frame. When memory runs out the kernel kills
the largest process on the machine, which need not be the renderer. So an
allocation of a page asks first: :func:`require` reads ``MemAvailable`` from
``/proc/meminfo`` (microseconds) and raises :class:`OutOfImageMemory`, naming
what needed the memory, when the image would leave less than
:data:`RESERVE_BYTES` free. Where ``/proc/meminfo`` is absent (not Linux),
nothing is checked.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

#: What an allocation must leave free for everything else on the machine.
RESERVE_BYTES = int(float(os.environ.get("AMBITION_ART_MEMORY_RESERVE_GB", "1.5")) * (1 << 30))
#: Below this an image is not worth a check.
SMALL_BYTES = 64 << 20

_MEMINFO = "/proc/meminfo"


class OutOfImageMemory(MemoryError):
    """An image would leave the machine short of memory."""


def available_bytes() -> Optional[int]:
    """``MemAvailable`` in bytes, or None where it cannot be read."""
    try:
        with open(_MEMINFO, encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def image_bytes(size: Tuple[int, int], mode: str = "RGBA") -> int:
    """The bytes of a ``mode`` image of ``size`` (four a pixel for RGBA)."""
    per = {"RGBA": 4, "RGB": 3, "L": 1, "LA": 2, "1": 1}.get(mode, 4)
    return max(0, int(size[0])) * max(0, int(size[1])) * per


def require(nbytes: int, what: str) -> None:
    """Raise :class:`OutOfImageMemory` when ``nbytes`` more would leave less
    than :data:`RESERVE_BYTES` available. ``what`` says what wanted it."""
    if nbytes < SMALL_BYTES:
        return
    free = available_bytes()
    if free is None or nbytes + RESERVE_BYTES <= free:
        return
    gib = 1 << 30
    raise OutOfImageMemory(
        f"{what} needs {nbytes / gib:.2f} GiB, but only {free / gib:.2f} GiB is available and "
        f"{RESERVE_BYTES / gib:.2f} GiB must stay free (AMBITION_ART_MEMORY_RESERVE_GB); "
        "run one publish at a time, or make the pages smaller"
    )


def require_image(size: Tuple[int, int], what: str, mode: str = "RGBA") -> None:
    """:func:`require` for one ``mode`` image of ``size``."""
    require(image_bytes(size, mode), f"{what} ({int(size[0])}x{int(size[1])} {mode})")


def require_images(sizes, what: str, mode: str = "RGBA") -> None:
    """:func:`require` for several images made together (the pages of a pack)."""
    sizes = list(sizes)
    total = sum(image_bytes(s, mode) for s in sizes)
    shape = ", ".join(f"{int(w)}x{int(h)}" for w, h in sizes[:4]) + (" ..." if len(sizes) > 4 else "")
    require(total, f"{what} ({len(sizes)} {mode} page(s): {shape})")


__all__ = ["OutOfImageMemory", "RESERVE_BYTES", "available_bytes", "image_bytes", "require", "require_image", "require_images"]
