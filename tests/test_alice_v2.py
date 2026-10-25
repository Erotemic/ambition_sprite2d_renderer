"""Alice v2: her sheet keeps the first Alice's rows, and her gear is drawn in
every view of the character generator.

The game binds Alice's rows by name, so v2 can replace the first sheet only
if it publishes every row that sheet had. Her gear is drawn through
``chargen.extras``; the hook must add nothing to a spec drawn outside it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ambition_sprite2d_renderer.chargen import extras
from ambition_sprite2d_renderer.chargen.geometry import VIEWS
from ambition_sprite2d_renderer.chargen.rig import draw_views
from ambition_sprite2d_renderer.targets.characters import alice_v2
from ambition_sprite2d_renderer.targets.characters._alice_v2_gear import alice_parts
from ambition_sprite2d_renderer.targets.characters._alice_v2_motion import ROWS, alice_library

FIRST_ALICE = Path(alice_v2.__file__).resolve().parents[2] / "configs" / "review" / "alice.yaml"


def test_alice_v2_publishes_every_row_of_the_first_alice():
    first = yaml.safe_load(FIRST_ALICE.read_text(encoding="utf8"))["animations"]
    assert not set(first) - set(ROWS)
    assert len(ROWS) == len(set(ROWS))


def test_alice_v2_has_a_clip_for_every_row():
    from ambition_sprite2d_renderer.chargen.body import build

    lib = alice_library(build(alice_v2.load_spec()))
    assert not set(ROWS) - set(lib)


@pytest.fixture(scope="module")
def drawn():
    with extras.using(alice_parts):
        return draw_views(alice_v2.load_spec())[1]


def test_alice_v2_gear_is_drawn_in_every_view(drawn):
    assert [dv.view.key for dv in drawn] == [v.key for v in VIEWS]
    for dv in drawn:
        names = {p.name for p in dv.parts}
        assert {"hair", "pole", "satchel", "letter"} <= names, dv.view.key
        bones = {p.name: p.bone for p in dv.parts}
        assert bones["pole"] == "near_grip" and bones["letter"] == "far_grip"


def test_extra_parts_are_drawn_only_inside_the_hook():
    plain = draw_views(alice_v2.load_spec(), VIEWS[:1])[1][0]
    assert not {"pole", "satchel", "letter"} & {p.name for p in plain.parts}
