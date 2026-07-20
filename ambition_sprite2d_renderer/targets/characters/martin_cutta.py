"""Martin Cutta: the leaner half of the kernel-raiding duo."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ._runge_kutta_duo import (
    DuoStyle,
    _make_actor_metadata,
    render_target,
    render_target_canonical,
    render_target_portraits,
)

STYLE = DuoStyle(
    target_name="martin_cutta",
    display_name="Martin Cutta",
    character_id="npc_martin_cutta",
    coat=(44, 78, 90, 255),
    coat_light=(66, 109, 121, 255),
    coat_deep=(31, 53, 61, 255),
    shirt=(209, 212, 217, 255),
    shirt_shade=(166, 170, 177, 255),
    apron=(112, 128, 139, 255),
    apron_shade=(77, 92, 102, 255),
    strap=(51, 90, 97, 255),
    glove=(58, 92, 100, 255),
    glove_light=(85, 125, 134, 255),
    pants=(80, 86, 102, 255),
    pants_shade=(56, 61, 74, 255),
    boot=(46, 54, 68, 255),
    boot_light=(70, 82, 99, 255),
    accent=(90, 211, 202, 255),
    accent_light=(148, 236, 229, 255),
    accent_deep=(46, 152, 145, 255),
    hair=(48, 52, 61, 255),
    hair_light=(84, 92, 105, 255),
    hair_deep=(24, 28, 33, 255),
    head_kind="swept",
    beard=False,
    moustache=False,
    body_kind="solid",
    trim="strapped",
)


def render(out_dir: Path | str = Path(".")) -> List[Path]:
    return render_target(STYLE, Path(out_dir))


def render_canonical(out_dir: Path | str = Path(".")) -> Path:
    return render_target_canonical(STYLE, Path(out_dir))


def render_portraits(out_dir: Path | str = Path(".")) -> List[Path]:
    return render_target_portraits(STYLE, Path(out_dir))


ACTOR_METADATA = _make_actor_metadata(STYLE)
