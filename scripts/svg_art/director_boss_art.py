#!/usr/bin/env python3
"""Derive the final boss's drawing from the Director's.

The final boss (`bossofthegame_boss`) is the Director: the same SVG, rig and
pen, with two props added: a mechanical keyboard slung across his waist on
a strap, which he plays in his second phase ("Manual Override": he types),
and a microphone in his far hand (the band's vocals are his alone). His pen
is not drawn: it is his sword in Smash. This
script writes ``data/characters/director_boss/director_boss.svg`` from
``data/characters/director/director.svg``; rerun it after the Director's
drawing changes.

    uv run python scripts/svg_art/director_boss_art.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "ambition_sprite2d_renderer" / "data" / "characters"
SOURCE = ROOT / "director" / "director.svg"
OUT = ROOT / "director_boss" / "director_boss.svg"

# The Director's art coordinates (inside his `scale(4.4585)` view group): his
# torso spans x 80-108 and y 118-160, his shoulder is near (100, 122), and he
# faces west, so his front is toward smaller x.
STRAP = (
    '<path d="M 101.5,121.5 C 97,134 88,145 77.5,151.0" fill="none" '
    'stroke="#1c1d22" stroke-width="2.0" stroke-linecap="round"/>'
)
# Slung low and tilted down toward his front, like a keytar.
BODY = "M 68.0,148.5 L 110.0,157.5 L 108.4,166.5 L 66.4,157.5 Z"
KEY_ROWS = ((70.2, 150.2, 12), (70.6, 153.9, 12))


def keyboard() -> str:
    parts = [
        f'<path d="{BODY}" fill="#26272e" stroke="#000" stroke-width="0.45" stroke-linejoin="round"/>',
        # The lip the keys sit in.
        '<path d="M 68.6,149.2 L 109.5,158.0" fill="none" stroke="#4a4c57" stroke-width="0.7"/>',
    ]
    # Keycaps along the tilted top: pale caps, one red escape key.
    dx, dy = 3.25, 0.70
    for x0, y0, count in KEY_ROWS:
        for i in range(count):
            x, y = x0 + i * dx, y0 + i * dy
            fill = "#d23c3c" if (x0, i) == (KEY_ROWS[0][0], count - 1) else "#e6e2da"
            parts.append(
                f'<path d="M {x:.2f},{y:.2f} l 2.8,0.6 l -0.4,2.6 l -2.8,-0.6 Z" '
                f'fill="{fill}" stroke="#8f8a82" stroke-width="0.3"/>'
            )
    return "".join(parts)


# The microphone, in his far hand (the pen is in the near one): its handle
# in the fist along the hand and out past the fingertips, its grille at its
# end, so a clip that brings that hand up to his face brings the grille to
# his mouth. The hand hangs from (72, 159) at the wrist to its fingertips
# near (71, 174).
MIC_HANDLE = "M 70.0,163.0 L 72.8,163.2 L 72.3,181.6 L 69.7,181.4 Z"
MIC_GRILLE = (71.0, 184.9, 3.6)


def microphone() -> str:
    cx, cy, r = MIC_GRILLE
    parts = [
        f'<path d="{MIC_HANDLE}" fill="#1c1d22" stroke="#000" stroke-width="0.35" stroke-linejoin="round"/>',
        # The band where the handle meets the grille.
        '<path d="M 69.4,180.6 L 72.6,180.8 L 72.5,182.0 L 69.3,181.8 Z" fill="#8f939e" stroke="#000" stroke-width="0.25"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#b9bcc6" stroke="#000" stroke-width="0.35"/>',
    ]
    # The grille's mesh.
    for k in (-1.8, 0.0, 1.8):
        parts.append(
            f'<path d="M {cx - r * 0.85:.2f},{cy + k:.2f} L {cx + r * 0.85:.2f},{cy + k:.2f}" '
            'stroke="#6d717c" stroke-width="0.25"/>'
        )
        parts.append(
            f'<path d="M {cx + k:.2f},{cy - r * 0.85:.2f} L {cx + k:.2f},{cy + r * 0.85:.2f}" '
            'stroke="#6d717c" stroke-width="0.25"/>'
        )
    parts.append(f'<circle cx="{cx - 0.9}" cy="{cy - 1.0}" r="0.7" fill="#eef0f5"/>')
    return "".join(parts)


def derive(svg: str) -> str:
    torso_end = svg.index("</g>", svg.index('<g id="part-torso" '))
    insert_at = torso_end + len("</g>")
    art = (
        '\n    <g id="part-keyboard-strap" data-rig-bone="torso" data-rig-part="keyboard_strap" '
        'data-rig-z="44" inkscape:label="Keyboard Strap" inkscape:groupmode="layer">'
        f"{STRAP}</g>"
        '\n    <g id="part-keyboard" data-rig-bone="torso" data-rig-part="keyboard" '
        'data-rig-z="45" inkscape:label="Keyboard" inkscape:groupmode="layer">'
        f"{keyboard()}</g>"
    )
    svg = svg[:insert_at] + art + svg[insert_at:]
    torso_def = svg.index('<g id="ambition-rig-side-part-torso" ')
    def_end = svg.index("/>", torso_def) + 2
    defs = (
        '\n    <g id="ambition-rig-side-part-keyboard_strap" data-rig-part-def="keyboard_strap" '
        'data-rig-bone="torso" data-rig-z="44" data-rig-pivot="ambition-rig-side-bind-torso" '
        'data-rig-bind-angle="0" data-rig-elements="part-keyboard-strap"/>'
        '\n    <g id="ambition-rig-side-part-keyboard" data-rig-part-def="keyboard" '
        'data-rig-bone="torso" data-rig-z="45" data-rig-pivot="ambition-rig-side-bind-torso" '
        'data-rig-bind-angle="0" data-rig-elements="part-keyboard"/>'
    )
    svg = svg[:def_end] + defs + svg[def_end:]
    # The microphone, under the far hand's fingers.
    hand = svg.index('<g id="part-far-hand" ')
    mic = (
        '<g id="part-microphone" data-rig-bone="far_arm_hand" data-rig-part="microphone" '
        'data-rig-z="10" inkscape:label="Microphone" inkscape:groupmode="layer">'
        f"{microphone()}</g>\n      "
    )
    svg = svg[:hand] + mic + svg[hand:]
    hand_def = svg.index('<g id="ambition-rig-side-part-far_hand" ')
    hand_def_end = svg.index("/>", hand_def) + 2
    pivot = svg[hand_def:hand_def_end].split('data-rig-pivot="')[1].split('"')[0]
    angle = svg[hand_def:hand_def_end].split('data-rig-bind-angle="')[1].split('"')[0]
    svg = (
        svg[:hand_def_end]
        + f'\n    <g id="ambition-rig-side-part-microphone" data-rig-part-def="microphone" '
        f'data-rig-bone="far_arm_hand" data-rig-z="10" data-rig-pivot="{pivot}" '
        f'data-rig-bind-angle="{angle}" data-rig-elements="part-microphone"/>'
        + svg[hand_def_end:]
    )
    svg = without_the_pen(svg)
    return svg.replace('data-character="director"', 'data-character="director_boss"')


def without_the_pen(svg: str) -> str:
    """Empty the pen's art: it is his sword in Smash, and the Ambition boss
    does not fight with it (Jon, 2026-11-13). Its rig part stays, drawing
    nothing, so the skeleton is the Director's."""
    start = svg.index('<g id="part-near-pen" ')
    body = svg.index(">", start) + 1
    depth, i = 1, body
    while depth:
        nxt_open, nxt_close = svg.find("<g", i), svg.find("</g>", i)
        if nxt_open != -1 and nxt_open < nxt_close:
            depth, i = depth + 1, nxt_open + 2
        else:
            depth, i = depth - 1, nxt_close + 4
    return svg[:body] + svg[i - 4:]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(derive(SOURCE.read_text()))
    print(OUT)


if __name__ == "__main__":
    main()
