"""A sluice of the cistern that wheel I opens: the look of a `LockWall`.

See ``_temple_kit`` for the keys and the doors of the Noodly Temple.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _temple_kit as kit

TARGET_NAME = "temple_gate_sluice_1"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in kit.SHEET_FILES_SUFFIXES)
ROWS = kit.DOOR_ROWS


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return kit.build_door(out_dir, target_name=TARGET_NAME, display="Sluice I", kind="sluice", wheel=1, shut_by=False)
