"""SVG affine transforms and lengths in reference pixels."""

from __future__ import annotations

import math
import re

Matrix = tuple[float, float, float, float, float, float]


def matrix_mul(left: Matrix, right: Matrix) -> Matrix:
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def transform_matrix(raw: str | None) -> Matrix:
    current: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    if not raw:
        return current
    for match in re.finditer(r"([A-Za-z]+)\s*\(([^)]*)\)", raw):
        name = match.group(1).lower()
        values = [float(v) for v in re.split(r"[\s,]+", match.group(2).strip()) if v]
        if name == "matrix" and len(values) == 6:
            op: Matrix = tuple(values)  # type: ignore[assignment]
        elif name == "translate" and len(values) in {1, 2}:
            op = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if len(values) == 2 else 0.0)
        elif name == "scale" and len(values) in {1, 2}:
            sy = values[1] if len(values) == 2 else values[0]
            op = (values[0], 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "rotate" and len(values) in {1, 3}:
            angle = math.radians(values[0])
            ca, sa = math.cos(angle), math.sin(angle)
            rot: Matrix = (ca, sa, -sa, ca, 0.0, 0.0)
            if len(values) == 3:
                cx, cy = values[1], values[2]
                op = matrix_mul(
                    matrix_mul((1.0, 0.0, 0.0, 1.0, cx, cy), rot),
                    (1.0, 0.0, 0.0, 1.0, -cx, -cy),
                )
            else:
                op = rot
        elif name == "skewx" and len(values) == 1:
            op = (1.0, 0.0, math.tan(math.radians(values[0])), 1.0, 0.0, 0.0)
        elif name == "skewy" and len(values) == 1:
            op = (1.0, math.tan(math.radians(values[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise ValueError(f"unsupported SVG transform component {match.group(0)!r}")
        current = matrix_mul(current, op)
    return current


def length_to_reference_px(raw: str | None, *, dpi: float) -> float | None:
    if not raw:
        return None
    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:[eE]([+-]?\d+))?\s*([A-Za-z%]*)\s*",
        raw,
    )
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2):
        value *= 10.0 ** int(match.group(2))
    unit = match.group(3).lower()
    if unit in {"", "px"}:
        return value
    if unit == "mm":
        return value * dpi / 25.4
    if unit == "cm":
        return value * dpi / 2.54
    if unit == "in":
        return value * dpi
    if unit == "pt":
        return value * dpi / 72.0
    if unit == "pc":
        return value * dpi / 6.0
    return None
