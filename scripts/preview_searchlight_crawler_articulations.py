#!/usr/bin/env python3
"""Show independent crawler actions while its eight legs keep walking.

From the sprite-renderer directory:

    uv run python scripts/preview_searchlight_crawler_articulations.py \
      --output /tmp/searchlight_articulations.png \
      --gif-output /tmp/searchlight_articulations.gif

All figures come from the SVG rig and its real IK solver.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.articulation_layers import (
    Articulation, PoseComposer,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from preview_searchlight_crawler import BG, CARD, GOLD, INK, MUTED, font

RIG = ROOT / (
    "ambition_sprite2d_renderer/targets/characters/rigged/searchlight_crawler/"
    "searchlight_crawler.rig.json"
)


def actions(kind: str, t: float) -> list[Articulation]:
    """Give each device its own time. Do not change the foot step time."""
    sensors = [Articulation("aim", "aim_scan", t * 0.9),
               Articulation("beam", "beam_search")]
    tracked = [Articulation("aim", values={"light": 26.0,
                                                 "bone.light.x": 2.0}),
               Articulation("beam", "beam_focus")]
    iris = [Articulation("iris", "iris_blink", t * 1.3)]
    alert = [Articulation("alarm", "alarm_flash", t * 1.7)]
    vent = [Articulation("vent", "vent_cycle", t * 1.1)]
    chassis = [Articulation("chassis", "chassis_brace", t)]
    if kind == "walk":
        return []
    if kind == "search":
        return sensors
    if kind == "track":
        return tracked
    if kind == "iris":
        return iris + [Articulation("beam", "beam_search")]
    if kind == "alarm":
        return alert
    if kind == "vent":
        return vent
    if kind == "brace":
        return chassis
    if kind == "all":
        return sensors + iris + alert + vent + chassis
    raise ValueError(kind)


def rendered(doc: RigDocument, composer: PoseComposer, t: float, kind: str):
    solved = composer.solve("walk", t, actions(kind, t))
    return doc.render_at("walk", t, solved=solved)


def paste_sprite(canvas: Image.Image, sprite: Image.Image, box: tuple[int, int, int, int]):
    """Fit the fixed-size rig frame in the box. Do not crop each pose."""
    x, y, width, height = box
    factor = min(width / sprite.width, height / sprite.height)
    out = sprite.resize((int(sprite.width*factor), int(sprite.height*factor)),
                        Image.Resampling.LANCZOS)
    canvas.paste(out, (int(x+(width-out.width)/2),
                       int(y+(height-out.height)/2)), out)


def board(doc: RigDocument, composer: PoseComposer) -> Image.Image:
    width, height = 1790, 1050
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((42, 26), "SEARCHLIGHT CRAWLER / INDEPENDENT ARTICULATIONS",
              font=font(34, True), fill=INK)
    draw.text((44, 78), "Real SVG parts + skeletal IK  |  Every sample uses the walk gait",
              font=font(20), fill=MUTED)
    draw.line(((40,121),(1750,121)),fill=GOLD,width=2)

    draw.rounded_rectangle((35,144,676,1008),radius=20,fill=CARD)
    draw.text((62,170), "ALL SYSTEMS WHILE SKITTERING",
              font=font(23,True),fill=GOLD)
    draw.text((64,209), "Legs remain planted while other parts move.",
              font=font(18),fill=MUTED)
    large = rendered(doc, composer, 0.28, "all")
    paste_sprite(image, large, (62,265,583,518))
    draw.line(((62,808),(645,808)),fill="#57667a",width=1)
    for i, (line, color) in enumerate((
        ("8 independent IK feet, four staggered step pairs", INK),
        ("Light: swivel + telescoping aim offsets", MUTED),
        ("Lens: focus, two shutter leaves, warning iris", MUTED),
        ("Body: brace; rear vent and mast move separately", MUTED),
    )):
        draw.text((64,829+i*37),line,font=font(17),fill=color)

    specs = [
        ("WALK BASE", "walk", 0.31),
        ("LAMP SWEEP", "search", 0.27),
        ("TARGET + FOCUS", "track", 0.37),
        ("IRIS SHUTTERS", "iris", 0.19),
        ("ALARM MAST", "alarm", 0.37),
        ("EXHAUST VENT", "vent", 0.27),
        ("CHASSIS BRACE", "brace", 0.24),
        ("ALL TOGETHER", "all", 0.44),
    ]
    for i, (label, name, time) in enumerate(specs):
        col, row = i%4, i//4
        x, y = 703+col*268, 144+row*434
        draw.rounded_rectangle((x,y,x+251,y+413),radius=16,fill=CARD)
        draw.text((x+14,y+14),label,font=font(17,True),fill=GOLD)
        shot=rendered(doc,composer,time,name)
        paste_sprite(image, shot, (x+6,y+51,239,289))
        draw.text((x+14,y+365),f"walk phase {int(time*100)}%",
                  font=font(14),fill=MUTED)
    return image


def motion(doc: RigDocument, composer: PoseComposer, output: Path) -> None:
    """Animate two independent action arrangements with a fixed camera."""
    frames = []
    count = 24
    width, height = 1070, 510
    for i in range(count):
        t = i / count
        frame = Image.new("RGB", (width,height), BG)
        draw = ImageDraw.Draw(frame)
        draw.text((25,18),"SEARCHLIGHT / COMPOSED MOTION",font=font(26,True),fill=INK)
        draw.text((29,62),"LEFT: lamp scanning + alarm    RIGHT: focused lamp + iris",
                  font=font(16),fill=MUTED)
        for kind, x in (("all",25),("track",540)):
            draw.rounded_rectangle((x,100,x+504,480),radius=15,fill=CARD)
            action_set=actions(kind,t)
            if kind=="track":
                action_set += [Articulation("iris","iris_blink",t*1.3),
                               Articulation("vent","vent_cycle",t*1.1)]
            solved=composer.solve("walk",t,action_set)
            shot=doc.render_at("walk",t,solved=solved)
            paste_sprite(frame,shot,(x+4,120,496,309))
            draw.text((x+16,439),f"Foot phase: {int(t*100)}%",font=font(16),fill=MUTED)
        frames.append(frame)
    output.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=90, disposal=2, loop=0, optimize=True)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("searchlight_articulations.png"))
    parser.add_argument("--gif-output",type=Path)
    args=parser.parse_args()
    doc=RigDocument.load(RIG)
    composer=PoseComposer(doc)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    board(doc,composer).save(args.output)
    print(args.output)
    if args.gif_output:
        motion(doc,composer,args.gif_output)
        print(args.gif_output)


if __name__ == "__main__":
    main()
