"""Publish the director card's atlas and placement metadata together."""
from pathlib import Path
import importlib.util
import sys

PUBLICATION_ROOT = "vanity_card_made_this_meme"
PUBLICATION_TIERS = ["full"]
SHEET_FILES = ["vanity_card_parts.png", "manifest.ron"]


def render(out_dir, **opts):
    root = Path(__file__).resolve().parents[3]
    script = root / "scripts/export_director_vanity_card.py"
    spec = importlib.util.spec_from_file_location("director_card_export", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    module.PAYLOAD_DIR = directory
    module.MANIFEST = directory / "manifest.ron"
    metadata, atlas = module.bake(False)
    sheet, rects = module.pack_atlas(atlas)
    module.write_parts(sheet)
    module.write_manifest(metadata, atlas, rects)
    return [directory / name for name in SHEET_FILES]
