"""Geometry contracts for tailored shells and smooth body profiles."""
from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.chargen.body import build
from ambition_sprite2d_renderer.chargen.geometry import Loft, RingKey
from ambition_sprite2d_renderer.chargen.spec import BASES, generate
from ambition_sprite2d_renderer.chargen.wear import opening, opening_edge


def test_shape_preserving_loft_respects_nonuniform_keys_and_tangents():
    keys = [RingKey(y, rx, 4, 4) for y, rx in ((0, 2), (1, 4), (10, 6), (12, 5), (30, 5))]
    loft = Loft(keys, shape_preserving=True)
    for k in keys:
        assert loft.section(k.y).rx == pytest.approx(k.rx)
    for a, b in zip(keys, keys[1:]):
        for i in range(101):
            r = loft.section(a.y + (b.y - a.y) * i / 100).rx
            assert min(a.rx, b.rx) - 1e-9 <= r <= max(a.rx, b.rx) + 1e-9
    eps = 1e-5
    for k in keys[1:-1]:
        left = (k.rx - loft.section(k.y - eps).rx) / eps
        right = (loft.section(k.y + eps).rx - k.rx) / eps
        assert left == pytest.approx(right, abs=1e-4)
    shell = loft.shell(0.8)
    assert shell.shape_preserving
    for i in range(31):
        assert shell.section(i).rx == pytest.approx(loft.section(i).rx + 0.8)


@pytest.mark.parametrize("base", sorted(BASES))
def test_tailored_opening_has_constant_lower_width(base):
    fig = build(generate(base, 11))
    shell = fig.torso.shell(0.8)
    edge = opening_edge(fig, shell, half=12, lapel=22)
    margin = opening(edge)
    start = fig.y_chest + 0.12 * fig.T
    widths = []
    for i in range(11):
        y = start + (fig.y_belt - start) * i / 10
        a = edge(y)
        assert 0 < a < 90
        assert margin(a, y) == pytest.approx(0, abs=1e-9)
        assert margin(a + 1, y) > 0 and margin(a - 1, y) < 0
        widths.append(shell.point(a, y)[0] - shell.section(y).cl)
    assert max(widths) - min(widths) < 0.01
