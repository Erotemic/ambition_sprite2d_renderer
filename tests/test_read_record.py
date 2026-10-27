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


def test_the_renderer_modules_the_process_imported_are_recorded(tmp_path: Path) -> None:
    """A render's code is the modules its process imported: an edit to one
    makes its sheet stale, and an edit to a module it did not import does
    not."""
    repo = RENDERER.parents[1]
    script = f"""
from pathlib import Path
from ambition_sprite2d_renderer import read_record
read_record.start(Path({str(repo)!r}), [])
import ambition_sprite2d_renderer.core.measure
read_record.write(Path({str(tmp_path / "record.reads")!r}))
"""
    subprocess.run([sys.executable, "-c", script], check=True, cwd=RENDERER)
    lines = (tmp_path / "record.reads").read_text().splitlines()
    package = "f tools/ambition_sprite2d_renderer/ambition_sprite2d_renderer"
    assert f"{package}/core/measure.py" in lines, lines
    assert f"{package}/read_record.py" in lines, lines
    # Control: a module of the package that the process did not import.
    assert f"{package}/authoring/faction_lineup.py" not in lines, lines
    assert not [line for line in lines if ".venv" in line], lines


def test_the_publish_entry_point_and_installer_share_one_input_recorder(tmp_path):
    import json
    import os
    module = tmp_path / 'probe.py'
    module.write_text("""from pathlib import Path
from PIL import Image
SHEET_FILES = ['probe.png']
def render(out_dir, **opts):
    color = Path(__file__).with_name('ink.txt').read_text().strip()
    path = Path(out_dir) / 'probe.png'
    Image.new('RGBA', (8, 8), color).save(path)
    return [path]
""")
    (tmp_path / 'ink.txt').write_text('#ff0000')
    spec = {'name':'probe','kind':'module','category':'props','module_path':'probe','config_path':None,
            'out_dir':str(tmp_path/'render'),'dest_root':str(tmp_path/'sprites'),'opts':{'seed':3},
            'reads':str(tmp_path/'probe.reads'),'root':str(tmp_path),
            'excluded':[str(tmp_path/'render'),str(tmp_path/'sprites'),str(tmp_path/'records')]}
    result = subprocess.run([sys.executable,'-m','ambition_sprite2d_renderer.read_record',json.dumps(spec)],
        cwd=RENDERER, capture_output=True, text=True, env=dict(os.environ,
            PYTHONPATH=str(tmp_path)+os.pathsep+str(RENDERER), AMBITION_REPO_ROOT=str(tmp_path),
            AMBITION_ART_PROVENANCE_DIR=str(tmp_path/'records')))
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path/'records/probe.json').read_text())
    assert receipt['generation']['complete']
    assert receipt['generation']['parameters'] == {'seed':3}
    assert any(row['path']=='ink.txt' and row['sha256'] for row in receipt['inputs'])
