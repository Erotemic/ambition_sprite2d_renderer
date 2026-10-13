"""The three house dogs (Honey, Roadie, Bezoar) on the companion dog's rig.

Each has its own drawing and its own leg length, and borrows the companion
dog's clips. Three things must agree on the leg length: the drawing, the
joints of the rig, and how far a clip lowers the body. When they do not, the
paws are in the ground or over it.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from ambition_sprite2d_renderer.targets.characters import _house_dog

DOGS = sorted(_house_dog.LEG_SCALE)


def _companion() -> dict:
    return json.loads(_house_dog.COMPANION_RIG_PATH.read_text())


@pytest.mark.parametrize("dog", DOGS)
def test_a_house_dog_plays_each_row_of_the_companion_dog(dog: str) -> None:
    rows = [name for name, _frames, _ms in _house_dog.doc(dog).rows()]
    assert rows == list(_companion()["clips"]), "a house dog has the companion dog's rows, in its order"


@pytest.mark.parametrize("dog", DOGS)
def test_the_leg_joints_are_where_the_drawing_has_them(dog: str) -> None:
    scale = _house_dog.LEG_SCALE[dog]
    companion = {part["name"]: part["pivot"] for part in _companion()["parts"]}
    for part in json.loads(_house_dog.rig_path(dog).read_text())["parts"]:
        # The mouth at rest is a part of a house dog only; it turns with the head.
        x, y = companion["head" if part["name"] == "rest_mouth" else part["name"]]
        assert part["pivot"] == pytest.approx([x, _house_dog.leg_y(y, scale)], abs=0.01), part["name"]


@pytest.mark.parametrize("dog", DOGS)
def test_a_bark_shows_one_mouth(dog: str) -> None:
    """The mouth at rest has a tongue that hangs out. A bark shows the bark
    mouth in its place, not over it: in each frame of each row, one of the
    two is shown."""
    doc = _house_dog.doc(dog)
    for name, frames, _ms in doc.rows():
        for frame in range(frames):
            shown = doc.sample(name, doc.frame_time(name, frame, frames))
            # A channel a clip does not state is at the default of its part.
            rest, bark = shown.get("rest_mouth", 1.0), shown.get("bark_mouth", 0.0)
            assert round(rest + bark) == 1, (name, frame, rest, bark)


@pytest.mark.parametrize("dog", sorted(_house_dog.LEFT_SIDE))
def test_a_dog_with_a_left_side_has_a_mirrored_row_for_each_row(dog: str) -> None:
    left = _house_dog.doc(dog, left_side=True)
    assert [name for name, _f, _ms in left.rows()] == [name for name, _f, _ms in _house_dog.doc(dog).rows()]
    assert left.data["frame"]["center_x"] * 2 == left.data["frame"]["width"], "a mirrored row turns about the middle of the frame"


@pytest.mark.parametrize("dog", DOGS)
@pytest.mark.parametrize("row", ["idle", "sit_idle", "petted"])
def test_the_paws_are_on_the_ground(dog: str, row: str) -> None:
    """Standing, sitting and lying down to be petted: the lowest drawn point
    of the dog is at the ground line of its frame, as the companion dog's is."""
    def lowest(doc, frame: int) -> int:
        frames = next(count for name, count, _ms in doc.rows() if name == row)
        alpha = np.asarray(doc.render_frame(row, frame, frames).convert("RGBA"))[..., 3]
        return int(np.nonzero(alpha.max(axis=1) > 40)[0].max())

    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

    companion = RigDocument.load(_house_dog.COMPANION_RIG_PATH)
    house = _house_dog.doc(dog)
    for frame in (0, 3):
        assert abs(lowest(house, frame) - lowest(companion, frame)) <= 2, f"{dog} {row} frame {frame}"
