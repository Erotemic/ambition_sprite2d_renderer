"""Content drawing code must use the renderer's compositing helpers, not raw `ImageDraw.Draw`.

Raw Pillow drawing replaces destination RGBA pixels instead of applying the
project's alpha-compositing semantics. The guard covers content-authoring paths
where translucent drawing would otherwise cut holes in existing art."""
from __future__ import annotations

import re
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "ambition_sprite2d_renderer"
SCANNED = ("targets", "authoring")

# Modules that legitimately touch ImageDraw.Draw: the fix itself, the SVG
# recorder twins, and the capture interceptor that hooks Draw by design.
ALLOWED = {"draw_recorder.py", "auto_capture.py"}

_RAW = re.compile(r"\bImageDraw\.Draw\s*\(")


def _violations() -> list:
    out = []
    for sub in SCANNED:
        for f in (PKG / sub).rglob("*.py"):
            if f.name in ALLOWED or "__pycache__" in str(f):
                continue
            for i, line in enumerate(f.read_text().splitlines(), 1):
                if _RAW.search(line) and "# raw-draw-ok" not in line:
                    out.append(f"{f.relative_to(PKG)}:{i}: {line.strip()}")
    return out


def test_scan_catches_planted_raw_draw(tmp_path: Path) -> None:
    """Poison check: the predicate must actually match the bug pattern."""
    assert _RAW.search("    d = ImageDraw.Draw(img, 'RGBA')")
    assert _RAW.search("draw = ImageDraw.Draw( layer )")
    assert not _RAW.search("draw = blending_draw(img)")


def test_no_raw_imagedraw_on_content_paths() -> None:
    bad = _violations()
    assert not bad, (
        "Raw ImageDraw.Draw clobbers alpha instead of compositing. Use "
        "`from ambition_sprite2d_renderer.core.draw import blending_draw` "
        "(or add `# raw-draw-ok` with a justification for a non-content "
        "image):\n  " + "\n  ".join(bad)
    )
