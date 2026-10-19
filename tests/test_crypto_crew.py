from __future__ import annotations

import pytest

from ambition_sprite2d_renderer.targets.characters import crypto_crew

CREW = ("craig", "eve", "judy", "mallory", "olivia", "peggy", "sybil", "trent", "trudy", "victor", "walter")


def test_the_module_publishes_each_of_the_crew():
    assert set(crypto_crew.TARGETS) == set(CREW)


@pytest.mark.parametrize("name", CREW)
def test_a_member_of_the_crew_has_the_rows_a_hall_character_plays(name):
    assert {"idle", "walk", "talk", "interact"} <= {row for row, _frames, _ms in crypto_crew.PEOPLE[name].rows}
    assert crypto_crew.META[name]["actor"]["character_id"] == f"npc_{name}"
