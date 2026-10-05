"""Sanic power-up box: invincibility.

A steel item monitor showing its icon; break it and the icon pops out and
grants the power-up (the ``break`` row's ``grant_powerup`` event). See
``_sanic_powerup_box`` for the shared box and its rows (``idle``,
``break``, ``broken``).
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _sanic_powerup_box as box

TARGET_NAME = "sanic_powerup_invincibility"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in box.SHEET_FILES_SUFFIXES)
ROWS = box.ROWS


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return box.build(out_dir, target_name=TARGET_NAME, icon=box.INVINCIBLE_ICON, icon_kind="invincibility", display="Invincibility Box",
                     effect="invincibility")


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return box.canonical(out_dir, target_name=TARGET_NAME, icon=box.INVINCIBLE_ICON, icon_kind="invincibility")
