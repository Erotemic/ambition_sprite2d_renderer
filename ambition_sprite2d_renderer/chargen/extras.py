"""Parts a target adds to the drawing of a spec: its own gear and props.

A spec draws a person from the generator's vocabulary. A main character is
more than that: she carries her own tools (a pole, a map tube, a pencil on
her ear). Her target draws those as rig parts from the same figure, in 3D,
in every view, as the generator draws its own parts, and the parts go into
the same multiview SVG and rigs.

Use: ``with using(fn): ...`` around the code that draws the spec (its SVG,
its rigs, a turnaround). ``fn(ctx, zmap)`` returns the extra parts of the
view ``ctx.view`` (``drawkit.Part``; ``zmap`` is that view's paint order,
``draw.zmap_for``). Outside the block a spec draws as it always did.
"""

from __future__ import annotations

import contextlib
import contextvars
from typing import Callable, Dict, Iterator, List, Tuple

from .drawkit import Ctx, Part

ExtraParts = Callable[[Ctx, Dict[str, float]], List[Part]]

_EXTRAS: contextvars.ContextVar[Tuple[ExtraParts, ...]] = contextvars.ContextVar("chargen_extra_parts", default=())


@contextlib.contextmanager
def using(*fns: ExtraParts) -> Iterator[None]:
    """Draw the parts of ``fns`` with every spec drawn in the block."""
    token = _EXTRAS.set(_EXTRAS.get() + tuple(fns))
    try:
        yield
    finally:
        _EXTRAS.reset(token)


def extra_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """The extra parts of one view (none outside a ``using`` block)."""
    out: List[Part] = []
    for fn in _EXTRAS.get():
        out += fn(ctx, zmap)
    return out


__all__ = ["ExtraParts", "extra_parts", "using"]
