"""Poison tests for transform-aware, semantically-honest part discovery.

These pin the three structural correctness bugs a GPT 5.6 review demonstrated
in the auto-capture converter (2026-07-23):

1. **Nested/sibling transforms were discarded** when matching part
   occurrences, so two occurrences differing only by an ancestor transform
   (a composite-fold ``translate``, a resize ``scale``, a layer ``rotate``,
   or two separately-transformed siblings) collapsed onto ONE placement — the
   second occurrence rendered at the first's location. Fixed by flattening
   every transform into geometry before discovery.

2. **Semantic component names were ignored during dedup**, so two explicitly
   named components with identical geometry (``left_thruster`` /
   ``right_thruster``) merged into one part — editing one would edit both.
   Fixed by keying candidate identity on the full Inkscape label path.

3. (status honesty lives in ``test_status_levels.py``.)

Each test asserts on the emitted placements/parts, so a silently-broken
matcher fails here instead of shipping a mislocated sprite.
"""
from __future__ import annotations

import re

from ambition_sprite2d_renderer.authoring.auto_capture import discover_parts

# inkscape:label needs its namespace declared; the discovery splitter injects
# the declaration, so bare prefixed attributes in these fixtures parse fine.
TRI = "0,0 10,0 0,10"  # asymmetric enough that a rotation is recoverable


def _uses(body: str):
    """[(pid, translate_xy_or_None, has_rotate)] for every <use> in a body."""
    out = []
    for m in re.finditer(r'<use\b[^>]*href="#(part_[0-9]+)"[^>]*?'
                         r'transform="([^"]*)"', body):
        pid, xform = m.group(1), m.group(2)
        t = re.search(r"translate\(([-\d.]+)\s+([-\d.]+)\)", xform)
        xy = (float(t.group(1)), float(t.group(2))) if t else None
        out.append((pid, xy, "rotate(" in xform))
    return out


# ---------------------------------------------------------------------------
# Bug 1 — transforms must be composed into the matching coordinate space.
#
# The genuine failure is *non-peelable* transforms: two (or more) separately
# transformed sibling layers in ONE frame. A shared sole-child outer wrapper
# (a per-frame crop/resize) is peeled to a prefix and re-applied, so these
# fixtures always carry >= 2 top-level siblings to exercise the inner-flatten
# path the reviewed bug lived in.
# ---------------------------------------------------------------------------
def _sib(x: int, inner: str = None) -> str:
    return f'<g transform="translate({x} 0)">{inner or f"<polygon points=\'{TRI}\' fill=\'red\'/>"}</g>'


def test_separate_sibling_translates_place_distinctly() -> None:
    """GPT's core repro: two identical shapes under DIFFERENT sibling
    translates in one frame must land 20px apart, not both at the first's."""
    frame = _sib(10) + _sib(30)
    frames = {("walk", 0): frame, ("walk", 1): frame}
    parts, bodies = discover_parts(frames)
    assert len(parts) == 1, "the recurring triangle should register once"
    u = _uses(bodies[("walk", 0)])
    assert len(u) == 2, "each occurrence gets its own placement"
    assert u[0][0] == u[1][0], "both placements reuse the same part def"
    dx = abs(u[1][1][0] - u[0][1][0])
    assert abs(dx - 20.0) < 1e-3, (u, "second sibling collapsed onto the first")


def test_nested_transform_composition_places_distinctly() -> None:
    """translate ∘ translate must compose; two nested siblings 100px apart."""
    def nest(x):
        return (f'<g transform="translate({x} 0)"><g transform="translate(5 5)">'
                f'<polygon points="{TRI}" fill="red"/></g></g>')
    frame = nest(100) + nest(200)
    frames = {("a", 0): frame}
    parts, bodies = discover_parts(frames)
    assert len(parts) == 1
    u = _uses(bodies[("a", 0)])
    assert len(u) == 2
    assert abs(abs(u[1][1][0] - u[0][1][0]) - 100.0) < 1e-3, u


def test_scale_is_flattened_into_the_def_geometry() -> None:
    """A ``scale`` on a non-peelable sibling flattens into the def, and equal
    scaled siblings still dedup to one part placed at distinct spots."""
    def sc(x):
        return f'<g transform="scale(2 2)"><polygon points="{x},0 {x + 5},0 {x},5" fill="red"/></g>'
    frame = sc(0) + sc(20)
    frames = {("a", 0): frame}
    parts, bodies = discover_parts(frames)
    assert len(parts) == 1
    (_pid, (_name, part_body)), = parts.items()
    coords = [float(v) for v in re.findall(r"[-\d.]+", re.search(
        r'points="([^"]+)"', part_body).group(1))]
    # 5px side * scale 2 == 10px triangle localized spans ~6.67px; an unscaled
    # 5px original would span only ~3.33px. Past 5px proves the scale baked in.
    assert max(coords) > 5.0, part_body
    u = _uses(bodies[("a", 0)])
    assert abs(abs(u[1][1][0] - u[0][1][0]) - 40.0) < 1e-3, u  # 20px * scale 2


def test_differently_scaled_occurrences_do_not_false_merge() -> None:
    """A 2x sibling is not a rigid motion of the 1x, so it must NOT be placed
    as the 1x part — it gets its own def (or stays verbatim), never merged."""
    frame = (f'<polygon points="{TRI}" fill="red"/>'
             f'<g transform="scale(2 2)"><polygon points="{TRI}" fill="red"/></g>')
    frames = {("a", 0): frame, ("a", 1): frame}
    parts, bodies = discover_parts(frames)
    u = _uses(bodies[("a", 0)])
    pids = {p for p, _xy, _r in u}
    # If they false-merged there would be a single shared pid; distinct sizes
    # must never resolve to the same part.
    if len(u) == 2:
        assert len(pids) == 2, "1x and 2x must not share a def"


def test_rotation_is_recovered_not_dropped() -> None:
    """A rotated sibling must place with a recovered rotate(); its unrotated
    twin must not — and both share one reference-orientation def."""
    frame = (f'<polygon points="{TRI}" fill="red"/>'
             f'<g transform="translate(100 0)"><g transform="rotate(90 0 0)">'
             f'<polygon points="{TRI}" fill="red"/></g></g>')
    frames = {("a", 0): frame, ("a", 1): frame}
    parts, bodies = discover_parts(frames)
    assert len(parts) == 1, "one def, shared in its reference orientation"
    rots = sorted(r for _p, _xy, r in _uses(bodies[("a", 0)]))
    assert rots == [False, True], "exactly one placement carries a rotate()"


# ---------------------------------------------------------------------------
# Bug 2 — semantic component identity is authoritative, geometry is not.
# ---------------------------------------------------------------------------
def _named(side: str, x: int) -> str:
    return (f'<g inkscape:label="{side}_thruster">'
            f'<polygon points="{x},0 {x + 10},0 {x},10" fill="red"/></g>')


def test_named_components_stay_separate_despite_identical_geometry() -> None:
    frames = {
        ("a", 0): _named("left", 0) + _named("right", 0),
        ("a", 1): _named("left", 0) + _named("right", 0),
    }
    parts, bodies = discover_parts(frames)
    names = {name for _pid, (name, _body) in parts.items()}
    assert names == {"left_thruster", "right_thruster"}, names
    assert len(parts) == 2, "geometrically identical, semantically distinct"
    pids = {p for p, _xy, _r in _uses(bodies[("a", 0)])}
    assert len(pids) == 2, "the two named parts must not share one def"


def test_same_semantic_path_merges_across_frames() -> None:
    frames = {("a", i): _named("left", 0) for i in range(4)}
    parts, _bodies = discover_parts(frames)
    assert len(parts) == 1
    assert next(iter(parts.values()))[0] == "left_thruster"


def test_nested_paths_disambiguate_identical_leaf_labels() -> None:
    """Same leaf label (``foreclaw``) under different arms must not merge; the
    part is named by its full path. The arm carries per-frame jitter so it is
    not itself rigid and discovery descends into the claw."""
    def arm(side: str, jitter: int) -> str:
        return (f'<g inkscape:label="{side}_arm">'
                f'<g inkscape:label="foreclaw"><polygon points="{TRI}" fill="red"/></g>'
                f'<polygon points="0,{jitter} 2,{jitter}" fill="blue"/></g>')

    frames = {
        ("a", 0): arm("left", 0) + arm("right", 0),
        ("a", 1): arm("left", 40) + arm("right", 40),
    }
    parts, _bodies = discover_parts(frames)
    names = {name for _pid, (name, _body) in parts.items()}
    assert "left_arm/foreclaw" in names and "right_arm/foreclaw" in names, names
    # The two identical claws remain two distinct editable parts.
    claws = [p for p, (n, _b) in parts.items() if n.endswith("/foreclaw")]
    assert len(claws) == 2
