"""The input-prompt target: every declared product renders, reads, and differs
from its neighbours, and every device layout spot lies on its device."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image

from ambition_sprite2d_renderer import artifacts
from ambition_sprite2d_renderer.core.equivalence import parse_ron
from ambition_sprite2d_renderer.targets.icons import input_glyphs as target

#: Bevy `GamepadButton` variants a prompt can name. The file rule is their
#: snake_case, so a Rust caller maps a button to a file with no table.
BEVY_BUTTONS = (
    "South", "East", "West", "North", "LeftTrigger", "RightTrigger",
    "LeftTrigger2", "RightTrigger2", "Select", "Start", "Mode",
    "LeftThumb", "RightThumb", "DPadUp", "DPadDown", "DPadLeft", "DPadRight",
)


def _snake(name: str) -> str:
    """snake_case as the `heck` crate makes it: ``DPadUp`` -> ``d_pad_up``,
    ``LeftTrigger2`` -> ``left_trigger2``."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("input_glyphs")
    target.render(out)
    return out


def test_every_declared_product_exists_with_ink(rendered: Path) -> None:
    for name in target.SHEET_FILES:
        path = rendered / name
        assert path.is_file(), name
        if name.endswith(".png"):
            with Image.open(path) as img:
                assert img.mode == "RGBA", name
                assert img.getchannel("A").getbbox() is not None, f"{name} is empty"


def test_layouts_name_their_images_for_the_installer(rendered: Path) -> None:
    for device in target.DEVICES:
        png, ron = target.device_files(device)
        assert artifacts.references(rendered / ron) == [png]


def test_every_bevy_button_has_a_glyph_in_every_style() -> None:
    for style in target.STYLES:
        for button in BEVY_BUTTONS:
            assert target.gamepad_file(style, _snake(button)) in target.SHEET_FILES, (style, button)


def _groups() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for name in target.SHEET_FILES:
        if not name.endswith(".png"):
            continue
        if name.startswith("input_device_"):
            kind = "device"
        elif name.startswith("input_glyph_key_"):
            kind = "key"
        elif name.startswith("input_glyph_mouse_"):
            kind = "mouse"
        else:
            kind = "pad:" + name.removeprefix("input_glyph_").split("_", 1)[0]
        groups.setdefault(kind, []).append(name)
    return groups


def test_each_glyph_differs_from_the_others_of_its_kind(rendered: Path) -> None:
    groups = _groups()
    assert set(groups) == {"device", "key", "mouse", *(f"pad:{s}" for s in target.STYLES)}
    for kind, names in groups.items():
        seen: dict[bytes, str] = {}
        for name in names:
            with Image.open(rendered / name) as img:
                pixels = img.tobytes()
            assert pixels not in seen, f"{kind}: {name} is identical to {seen.get(pixels)}"
            seen[pixels] = name


def test_every_layout_spot_lies_on_its_device(rendered: Path) -> None:
    declared = set(target.SHEET_FILES)
    for device in target.DEVICES:
        png, ron = target.device_files(device)
        layout = parse_ron((rendered / ron).read_text())
        with Image.open(rendered / png) as img:
            alpha = img.getchannel("A")
            assert tuple(layout["size"]) == img.size
        w, h = img.size
        assert layout["controls"], device
        for control, spot in layout["controls"].items():
            r = spot["rect"]
            assert 0 <= r["x"] and 0 <= r["y"] and r["x"] + r["w"] <= w and r["y"] + r["h"] <= h, (device, control)
            x, y = spot["center"]
            assert r["x"] <= x <= r["x"] + r["w"] and r["y"] <= y <= r["y"] + r["h"], (device, control)
            assert 0 < spot["radius"] <= min(r["w"], r["h"]) / 2 + 0.11, (device, control)
            assert alpha.getpixel((int(x), int(y))) == 255, f"{device}: {control} centre is off the device"
            assert spot["shape"] in ("Circle", "Rect")
            if spot["glyph"] is not None:
                assert spot["glyph"] in declared, (device, control, spot["glyph"])
        if device in target.STYLES:
            assert set(BEVY_BUTTONS) <= set(layout["controls"]), device
            for button in BEVY_BUTTONS:
                assert layout["controls"][button]["glyph"] == target.gamepad_file(device, _snake(button))
