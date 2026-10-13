"""The Pesto Key of the Noodly Temple: a pickup.

See ``_temple_kit`` for the keys and the doors of the Noodly Temple.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import _temple_kit as kit

TARGET_NAME = "temple_key_pesto"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in kit.SHEET_FILES_SUFFIXES)
ROWS = kit.KEY_ROWS


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return kit.build_key(out_dir, target_name=TARGET_NAME, sauce="pesto", display="Pesto Key")
