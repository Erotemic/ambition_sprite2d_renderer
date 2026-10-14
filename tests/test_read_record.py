"""What `read_record` records of a render: the authored files it reads and the
directories it lists, and not its outputs, the code or the import system.

Each case runs in a child interpreter: an audit hook cannot be removed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RENDERER = Path(__file__).resolve().parents[1]


def record_of(root: Path, body: str) -> list[str]:
    script = f"""
import json, os, sys
from pathlib import Path
from ambition_sprite2d_renderer import read_record
root = Path({str(root)!r})
read_record.start(root, [root / "out"])
{body}
read_record.write(root / "record.reads")
"""
    subprocess.run([sys.executable, "-c", script], check=True, cwd=RENDERER)
    return (root / "record.reads").read_text().splitlines()


def test_a_read_of_another_targets_art_is_recorded(tmp_path: Path) -> None:
    """The case the name-keyed guess missed: a rig that draws another
    character's SVG (review of 2026-10-14)."""
    art = tmp_path / "data" / "characters" / "villain"
    art.mkdir(parents=True)
    (art / "villain.svg").write_text("<svg/>")
    lines = record_of(tmp_path, "Path(root, 'data/characters/villain/villain.svg').read_text()")
    assert lines == ["f data/characters/villain/villain.svg"]


def test_outputs_code_and_the_import_system_are_not_recorded(tmp_path: Path) -> None:
    (tmp_path / "out").mkdir()
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "helper.py").write_text("X = 1\n")
    (tmp_path / "shapes").mkdir()
    (tmp_path / "shapes" / "a.json").write_text("{}")
    body = """
(root / "out" / "sheet.png").write_text("written")
(root / "out" / "sheet.png").read_text()
sys.path.insert(0, str(root))
import pkg.helper
sorted(os.listdir(root / "shapes"))
"""
    assert record_of(tmp_path, body) == ["d shapes"]
