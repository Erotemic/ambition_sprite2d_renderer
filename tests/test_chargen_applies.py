"""Which knobs draw (``chargen/applies.py``). Every ``REQUIRES`` rule is
measured again by drawing: the field changes the picture when its rule holds
and changes nothing when it does not. A species measure keeps one value of
each distinct picture, and a field no species draws stays shown."""

from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.chargen import applies as A
from ambition_sprite2d_renderer.chargen import spec as S

_VALUES = {key: values for key, values in A.knobs()}


def _draws(d, key) -> bool:
    a, b = _VALUES[key][0], _VALUES[key][-1]
    return A.fingerprint(A._set(d, key, a)) != A.fingerprint(A._set(d, key, b))


@pytest.mark.parametrize("key", sorted(A.REQUIRES))
def test_a_requires_rule_holds_when_drawn(key):
    other, values = A.REQUIRES[key]
    d = A.base("human")
    on = A.enable(d, key)
    assert A.allowed(on, key)
    assert _draws(on, key), f"{key} draws nothing although {other} allows it"
    if other == "outfit.accessories":
        off = A._set(d, other, [])
    else:
        choices = dict(S.CHOICES)[other] if other in S.CHOICES else ()
        refused = [v for v in choices if v not in values]
        if not refused:
            pytest.skip(f"every {other} allows {key}")
        off = A._set(d, other, refused[0])
    assert not A.allowed(off, key)
    assert not _draws(off, key), f"{key} draws although {other}={A._get(off, other)!r} refuses it"


def test_a_species_measure_keeps_one_value_of_each_picture_and_a_field_nobody_draws_stays():
    knobs = A.knobs()
    results = {}
    for sp in ("human", "alligator"):
        for key, values in knobs:
            for i, v in enumerate(values):
                # A made-up measure: the alligator draws no hair style but the wig,
                # and nobody draws the accent colour.
                if key == "hair.style" and sp == "alligator":
                    fp = "wig" if v == "nihongami" else "bare"
                elif key == "outfit.accent_color":
                    fp = "same"
                else:
                    fp = f"{key}={i}"
                results[(sp, key, v)] = fp
    table = A.summarize(results)
    assert table["alligator"]["values"]["hair.style"] == ["bald", "nihongami"]
    assert table["human"]["values"]["hair.style"] == list(S.HAIR_STYLES)
    assert table["alligator"]["fields"]["outfit.accent_color"] is True
