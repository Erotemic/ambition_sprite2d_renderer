"""Missing quality products can be built without changing existing pixels."""
from PIL import Image

from ambition_sprite2d_renderer import quality


def test_missing_parallax_conversion_keeps_existing_pixels(tmp_path, monkeypatch):
    monkeypatch.setenv("AMBITION_ART_ASSET_ROOT", str(tmp_path))
    monkeypatch.setenv("AMBITION_ART_PROVENANCE_ROOT", str(tmp_path / "provenance"))
    monkeypatch.setenv("AMBITION_ART_PROVENANCE_DIR", str(tmp_path / "records"))
    src = tmp_path / "backgrounds/parallax_layers"
    src.mkdir(parents=True)
    for name in ("held", "new"):
        Image.new("RGBA", (32, 32), "red").save(src / f"{name}.png")
    tier = quality.VARIANTS[0]
    output = tmp_path / "backgrounds" / f"parallax_layers_{tier.suffix}"
    output.mkdir()
    Image.new("RGBA", (4, 4), "blue").save(output / "held.png")
    held = (output / "held.png").read_bytes()
    quality.generate_parallax_variants(tmp_path, tiers=(tier,), missing_only=True)
    assert (output / "held.png").read_bytes() == held
    with Image.open(output / "new.png") as image:
        assert image.size == (16, 16)
        assert image.getpixel((0, 0)) == (255, 0, 0, 255)
