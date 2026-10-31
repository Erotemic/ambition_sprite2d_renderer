"""The void polygons are their source fighters with a void paint, and only that.

The gameplay reads the source fighter's frame data, so a void part must have
the source part's alpha (its silhouette): the crop, the anchors and the hit
volumes of the sheet are the source's. The paint must have no colour.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from PIL import ImageChops

from ambition_sprite2d_renderer.authoring.svg_parts import rasterize_subset
from ambition_sprite2d_renderer.targets.characters._void_polygon import facet_grey

SOURCES = ("pointed_polygon", "pugnacious_polygon", "projectile_polygon")


def _void(name):
    return importlib.import_module(f"ambition_sprite2d_renderer.targets.characters.void_{name}")


@pytest.mark.parametrize("name", SOURCES)
def test_void_parts_keep_the_source_silhouette(name):
    void = _void(name).VOID
    source, painted = void.source._doc(), void.doc
    # The publication's own raster scale (frame px per reference px, 4x supersample).
    dpi = 96.0 * float(source.svg_source["scale"]) * 4
    for part in source.data["parts"]:
        a, off_a, _ = rasterize_subset(source.svg_source["path"], source.svg_source["view"], part["include"], dpi)
        b, off_b, _ = rasterize_subset(painted.svg_source["path"], painted.svg_source["view"], part["include"], dpi)
        if a is None:
            assert b is None, part["name"]
            continue
        assert (a.size, off_a) == (b.size, off_b), part["name"]
        diff = ImageChops.difference(a.getchannel("A"), b.getchannel("A")).getextrema()[1]
        assert diff <= 2, f"{name}.{part['name']}: alpha moved by {diff}"


@pytest.mark.parametrize("name", SOURCES)
def test_void_paint_has_no_colour(name):
    void = _void(name).VOID
    painted = void.doc
    for part in painted.data["parts"]:
        image, _, _ = rasterize_subset(painted.svg_source["path"], painted.svg_source["view"], part["include"], 96.0)
        if image is None:
            continue
        pixels = np.asarray(image.convert("RGBA")).reshape(-1, 4).astype(int)
        seen = pixels[pixels[:, 3] > 32, :3]
        spread = int((seen.max(axis=1) - seen.min(axis=1)).max()) if len(seen) else 0
        assert spread <= 2, f"{name}.{part['name']}: a colour, spread {spread}"


@pytest.mark.parametrize("name", SOURCES)
def test_void_target_publishes_the_source_rows(name):
    module = _void(name)
    assert module.TARGET_NAME == f"void_{name}"
    assert module.VOID.doc.rows() == module.VOID.source._doc().rows()
    assert module.ACTOR_METADATA["actor"]["character_id"] == f"void_{name}"
    assert "void" in module.ACTOR_METADATA["tags"]


def test_facet_grey_keeps_the_shading_order_and_stays_dark():
    dark, lit = facet_grey("#34236F"), facet_grey("#C08AF5")
    assert int(dark[1:3], 16) < int(lit[1:3], 16) <= 64
