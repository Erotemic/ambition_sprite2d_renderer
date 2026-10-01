"""A hybrid flipbook names the rows it leaves to the baked sheet.

The runtime reads ``baked_clips`` (``RiggedSpriteAsset::realization``) and
refuses a flipbook that states a sheet row as neither a clip nor a baked clip.
"""

from PIL import Image

from ambition_sprite2d_renderer.authoring.part_flipbook import PartDraw, PartFlipbook, PartRaster


def _flipbook(baked):
    part = PartRaster("a", Image.new("RGBA", (4, 4), (255, 0, 0, 255)), (2.0, 2.0))
    clips = {"idle": (0.1, [[PartDraw(0, (0.0, -3.0))]])}
    flipbook = PartFlipbook("t", (8, 8), (4.0, 7.0), [part], clips, baked)
    flipbook.pack()
    return flipbook.to_ron()


def test_a_hybrid_names_its_baked_rows_after_its_clips():
    text = _flipbook(["transform", "smear"])
    assert 'baked_clips: ["transform", "smear"],' in text
    assert text.index("clips: {") < text.index("baked_clips:")
    assert '"transform":' not in text, "a baked row has no draws"


def test_a_flipbook_of_parts_alone_writes_no_baked_clips():
    assert "baked_clips" not in _flipbook([])
