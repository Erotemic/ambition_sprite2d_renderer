"""A gate of the cistern that wheel I shuts: the look of a `LockWall`.

See ``_temple_kit`` for the keys and the doors of the Noodly Temple.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _temple_kit as kit

TARGET_NAME = "temple_gate_wheel_1_shut"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in kit.SHEET_FILES_SUFFIXES)
ROWS = kit.DOOR_ROWS


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return kit.build_door(out_dir, target_name=TARGET_NAME, display="Wheel Gate I", kind="wheel", wheel=1, shut_by=True)
