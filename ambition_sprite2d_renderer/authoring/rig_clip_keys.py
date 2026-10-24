"""Channel values for the clips of a ``RigDocument``, and its rest IK targets.

A clip channel is one of: a constant (``{"const": v}``), an expression of
``t`` (``{"expr": "..."}``), or keys (``{"keys": [[t, v, ease], ...]}``).
These helpers write them, and read where an IK chain's hand or foot rests, so
a clip can be authored as offsets from the drawing's rest pose.

``RigDocument.frame_time`` samples a loop at ``i/n`` and a one-shot at
``i/(n-1)``; :func:`keys` spaces keys for a loop and :func:`shot` for a
one-shot, so each key lands on a frame.
"""

from __future__ import annotations

from typing import Iterable, Mapping


def const(value: float) -> dict:
    return {"const": round(float(value), 4)}


def expr(text: str) -> dict:
    return {"expr": text}


def keys(values: Iterable[float], *, ease: str = "smooth") -> dict:
    """Keys for a LOOPING clip: value ``i`` at ``t = i/n``."""
    values = list(values)
    n = len(values)
    return {"keys": [[round(i / n, 6), round(float(v), 4), ease] for i, v in enumerate(values)]}


def shot(values: Iterable[float], *, ease: str = "smooth") -> dict:
    """Keys for a ONE-SHOT clip: value ``i`` at ``t = i/(n-1)``, so the last
    key is the last frame (a recovery frame is not spent repeating)."""
    values = list(values)
    n = len(values)
    return {"keys": [[round(i / max(1, n - 1), 6), round(float(v), 4), ease] for i, v in enumerate(values)]}


def rest(doc: Mapping, prefix: str, axis: str) -> float:
    """Where the IK chain ``prefix`` (``near_hand``, ``far_foot``, ...) rests,
    on ``axis`` (``x``, ``y``, ``lift``), in the document's channel units."""
    for chain in doc.get("ik_chains", []):
        if chain.get("channel_prefix") == prefix:
            return float(chain[f"rest_{axis}"])
    for leg in doc.get("ik_legs", []):
        if leg.get("channel_prefix") == prefix:
            return float(leg[f"rest_{axis}"])
    raise KeyError((prefix, axis))


def rest_pitch(doc: Mapping, prefix: str) -> float:
    for collection in (doc.get("ik_chains", []), doc.get("ik_legs", [])):
        for chain in collection:
            if chain.get("channel_prefix") == prefix:
                return float(chain["rest_pitch"])
    raise KeyError(prefix)


__all__ = ["const", "expr", "keys", "rest", "rest_pitch", "shot"]
