"""Carl Runga: a heavy numerical operator trying to seize Oiler's Kernel."""

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
    target_name="carl_runga",
    display_name="Carl Runga",
    character_id="npc_carl_runga",
    coat=(95, 52, 42, 255),
    coat_light=(129, 74, 61, 255),
    coat_deep=(66, 35, 29, 255),
    shirt=(205, 195, 171, 255),
    shirt_shade=(164, 154, 131, 255),
    apron=(189, 138, 71, 255),
    apron_shade=(146, 102, 49, 255),
    strap=(88, 61, 35, 255),
    glove=(111, 66, 48, 255),
    glove_light=(136, 86, 62, 255),
    pants=(84, 86, 104, 255),
    pants_shade=(59, 60, 76, 255),
    boot=(72, 52, 37, 255),
    boot_light=(96, 72, 51, 255),
    accent=(239, 175, 70, 255),
    accent_light=(250, 209, 110, 255),
    accent_deep=(186, 116, 41, 255),
    hair=(137, 118, 101, 255),
    hair_light=(173, 154, 138, 255),
    hair_deep=(93, 79, 68, 255),
    head_kind="square",
    beard=True,
    moustache=True,
    body_kind="broad",
    trim="angled",
)


def render(out_dir: Path | str = Path(".")) -> List[Path]:
    return render_target(STYLE, Path(out_dir))


def render_canonical(out_dir: Path | str = Path(".")) -> Path:
    return render_target_canonical(STYLE, Path(out_dir))


def render_portraits(out_dir: Path | str = Path(".")) -> List[Path]:
    return render_target_portraits(STYLE, Path(out_dir))


ACTOR_METADATA = _make_actor_metadata(STYLE)
