"""Publish the controller and apple pie as separate sprites."""

from io import BytesIO
from pathlib import Path

from PIL import Image
from resvg_py import svg_to_bytes

TARGET_NAME = "vanity_gifts"
PUBLICATION_TIERS = ["full"]
SHEET_FILES = ["gamepad.png", "apple_pie.png"]


def render(out_dir, **opts):
    assets = Path(__file__).resolve().parents[3] / "assets"
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    outputs = [directory / name for name in SHEET_FILES]
    for source, output in zip(["gamepad-draft.svg", "apple-pie.svg"], outputs):
        png = svg_to_bytes(svg_string=(assets / source).read_text(), dpi=260)
        image = Image.open(BytesIO(bytes(png))).convert("RGBA")
        image = image.crop(image.getbbox())
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        image.save(output)
    return outputs
