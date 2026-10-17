#!/usr/bin/env python3
"""Render Searchlight Crawler poses from the SVG rig.

    cd tools/ambition_sprite2d_renderer
    uv run python scripts/preview_searchlight_crawler.py \
        --output searchlight_crawler_review.png \
        --gif-output searchlight_crawler_motion.gif
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.skeleton import BoneWorld
from ambition_sprite2d_renderer.authoring.surface_gait import (
    Gait, Leg, SurfaceContact, SurfacePose,
)

RIG = (
    ROOT
    / "ambition_sprite2d_renderer/targets/characters/rigged/searchlight_crawler/"
    "searchlight_crawler.rig.json"
)
BG = "#151b25"
CARD = "#252e3b"
CARD_INNER = "#1e2632"
INK = "#f3f1ea"
MUTED = "#b1bdc8"
GOLD = "#e5b567"
DIVIDER = "#46566a"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def cropped(image: Image.Image, pad: int = 5) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        raise RuntimeError("SVG rig rendered an empty pose")
    l, t, r, b = bbox
    return image.crop((max(0, l - pad), max(0, t - pad),
                       min(image.width, r + pad), min(image.height, b + pad)))


def centered(canvas: Image.Image, sprite: Image.Image, box: tuple[int, int, int, int],
             max_scale: float = 6.0) -> None:
    x, y, width, height = box
    sprite = cropped(sprite)
    factor = min(max_scale, width / sprite.width, height / sprite.height)
    size = (max(1, round(sprite.width * factor)), max(1, round(sprite.height * factor)))
    resized = sprite.resize(size, Image.Resampling.LANCZOS)
    canvas.paste(resized, (round(x + (width - size[0]) / 2),
                           round(y + (height - size[1]) / 2)), resized)


def card(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(xy, radius=19, fill=CARD)


def gait_parts(doc: RigDocument) -> tuple[Gait, dict[str, Leg]]:
    """Read gait data from the rig. Do not copy stride values into the viewer."""
    spec = doc.data["footfall"]
    gait = Gait(**{key: spec[key] for key in ("stride", "stance", "lift")})
    legs = {
        name: Leg(name, tuple(info["rest_tip"]), info["tarsus_length"],
                  info["tarsus_pitch"], info["phase"])
        for name, info in spec["legs"].items()
    }
    return gait, legs


def show_pose(canvas: Image.Image, doc: RigDocument, t: float,
              at: tuple[int, int], scale: float,
              *, markers: bool = True) -> None:
    """Draw a pose at one fixed size and one fixed ground anchor."""
    x, y = at
    source = doc.render_at("walk", t)
    size = (round(source.width * scale), round(source.height * scale))
    sprite = source.resize(size, Image.Resampling.LANCZOS)
    canvas.paste(sprite, (x, y), sprite)
    if markers:
        gait, legs = gait_parts(doc)
        world, _ = doc.solve("walk", t)
        draw = ImageDraw.Draw(canvas)
        for name, leg in legs.items():
            foot = world[f"{name}_tarsus"].tip
            px, py = x + foot[0] * scale, y + foot[1] * scale
            planted = gait.phase_at(t, leg.phase) < gait.stance
            color = "#79dc9a" if planted else "#e8b76a"
            r = max(2.3, 2.0 * scale)
            draw.ellipse((px-r, py-r, px+r, py+r), fill=color)


def build_board(doc: RigDocument) -> Image.Image:
    """Show only the real SVG walk and its foot contact states."""
    w, h = 1910, 1030
    out = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(out)
    draw.text((42, 23), "SEARCHLIGHT CRAWLER  /  WALK", font=font(42, True), fill=INK)
    draw.text((44, 88), "ARTICULATED SPIDER LEGS  /  CONTACT-DRIVEN IK", font=font(20), fill=MUTED)
    draw.line(((40, 128), (1870, 128)), fill=GOLD, width=2)

    card(draw, (34, 150, 628, 990))
    draw.text((60, 176), "PLANTED-FOOT GAIT", font=font(25, True), fill=INK)
    draw.text((60, 218), "The body holds its size. The legs take the steps.",
              font=font(17), fill=MUTED)
    x, y, scale = 57, 270, 1.93
    ground = y + doc.frame["ground_y"] * scale
    draw.line(((52, ground), (609, ground)), fill=DIVIDER, width=3)
    for gx in range(60, 612, 35):
        draw.line(((gx, ground), (gx, ground+12)), fill="#6e8190", width=2)
    show_pose(out, doc, 0.80, (x, y), scale)
    draw.line(((60, 725), (602, 725)), fill=DIVIDER, width=1)
    draw.text((66, 751), "SUPPORT FOOT", font=font(19, True), fill="#79dc9a")
    draw.text((66, 794), "LIFTED FOOT", font=font(19, True), fill="#e8b76a")
    gait, legs = gait_parts(doc)
    draw.text((66, 862), f"{len(legs)} legs  /  4 articulated parts per leg",
              font=font(19), fill=INK)
    draw.text((66, 898), f"{len({l.phase for l in legs.values()})} staggered step pairs",
              font=font(19), fill=MUTED)
    draw.text((66, 933), "Same source SVG. No frame-by-frame redraw.",
              font=font(16), fill=MUTED)

    phases = [0, 1/6, 2/6, 3/6, 4/6, 5/6]
    colw, rowh, gap = 397, 409, 17
    for i, t in enumerate(phases):
        col, row = i % 3, i // 3
        px, py = 655 + col * (colw + gap), 150 + row * (rowh + 13)
        card(draw, (px, py, px + colw, py + rowh))
        draw.text((px+20, py+15), f"STEP {i+1}", font=font(21, True), fill=GOLD)
        draw.text((px+20, py+48), f"Cycle position: {int(t*100)}%", font=font(15), fill=MUTED)
        art_scale = 1.25
        art_x = px + (colw - int(doc.frame["width"] * art_scale))//2
        art_y = py + 92
        floor_y = art_y + doc.frame["ground_y"] * art_scale
        draw.line(((px+13,floor_y),(px+colw-13,floor_y)), fill=DIVIDER, width=2)
        show_pose(out,doc,t,(art_x,art_y),art_scale)
        support = sum(gait.phase_at(t, leg.phase)<gait.stance for leg in legs.values())
        draw.text((px+19, py+rowh-45), f"{support} feet in contact", font=font(16), fill=MUTED)
    return out


def build_motion(doc: RigDocument, output: Path) -> None:
    """Render at fixed zoom. The floor scroll matches the gait's travel."""
    width, height = 1050, 510
    frames = []
    nframes = 24
    scale = 1.9
    image_x = (width - doc.frame["width"] * scale) / 2
    image_y = 74
    floor_y = image_y + doc.frame["ground_y"] * scale
    gait, legs = gait_parts(doc)
    speed = gait.stride / gait.stance
    for i in range(nframes):
        t = i / nframes
        frame = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(frame)
        draw.text((35, 22), "SEARCHLIGHT CRAWLER  /  SKITTER", font=font(29, True), fill=INK)
        draw.text((37, 70), "Fixed scale  |  Four staggered step pairs  |  World-space foot support",
                  font=font(17), fill=MUTED)
        draw.line(((32, floor_y), (1018, floor_y)), fill=DIVIDER, width=3)
        # A camera follows the crawler. The floor shows the body's travel.
        for tick in range(-14, 15):
            x = width/2 + (tick*30-speed*t)*scale
            if 20 < x < width-20:
                draw.line(((x,floor_y),(x,floor_y+14)),fill="#8b9da9",width=2)
        show_pose(frame, doc, t, (round(image_x), round(image_y)), scale)
        draw.text((40, 463), "GREEN  planted   /   AMBER  swinging", font=font(17), fill=MUTED)
        draw.text((855, 463), f"{i+1:02d} / {nframes:02d}", font=font(18), fill=MUTED)
        frames.append(frame)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=77,
                   disposal=2, loop=0, optimize=True)


def rotated_world(doc: RigDocument, worlds: dict[str, BoneWorld],
                  tangent: tuple[float, float]) -> dict[str, BoneWorld]:
    """Turn a local rig to face a wall, slope, or ceiling for review."""
    angle = math.degrees(math.atan2(tangent[1], tangent[0]))
    dx, dy = tangent
    cx, cy = doc.frame["center_x"], doc.frame["ground_y"]
    return {
        name: BoneWorld(
            (cx + dx*(b.origin[0]-cx)-dy*(b.origin[1]-cy),
             cy + dy*(b.origin[0]-cx)+dx*(b.origin[1]-cy)),
            b.angle + angle, b.length,
        )
        for name,b in worlds.items()
    }


def build_surface_board(doc: RigDocument) -> Image.Image:
    """Show the same leg solver on three different contact surfaces."""
    gait, legs = gait_parts(doc)
    speed = gait.stride / gait.stance
    slope = 0.18
    q = math.hypot(1.0, slope)
    cases = [
        ("FLAT GROUND", lambda t: SurfacePose((speed*t,0.0),(1.0,0.0)),
         lambda point,down: SurfaceContact((point[0],0.0),(0.0,-1.0))),
        ("SLOPE", lambda t: SurfacePose((speed*t/q, slope*speed*t/q),(1/q,slope/q)),
         lambda point,down: SurfaceContact((point[0],slope*point[0]),(slope/q,-1/q))),
        ("WALL", lambda t: SurfacePose((0.0,-speed*t),(0.0,-1.0)),
         lambda point,down: SurfaceContact((0.0,point[1]),(-1.0,0.0))),
    ]
    w,h=1570,540
    board=Image.new("RGB",(w,h),BG)
    draw=ImageDraw.Draw(board)
    draw.text((34,25),"SEARCHLIGHT CRAWLER  /  SURFACE CONTACTS",font=font(31,True),fill=INK)
    draw.text((36,76),"One articulated rig. The probe selects each foot contact.",font=font(18),fill=MUTED)
    draw.line(((30,118),(1540,118)),fill=GOLD,width=2)
    for i,(name,frame_at,probe) in enumerate(cases):
        x=28+i*516
        card(draw,(x,140,x+495,510))
        draw.text((x+22,161),name,font=font(23,True),fill=GOLD)
        t=0.31
        channels=gait.contact_channels(t,legs,frame_at,probe)
        world,params=doc.solve("walk",t,channel_overrides=channels)
        rotated=rotated_world(doc,world,frame_at(t).tangent)
        pad=180
        source=doc.render_at("walk",t,solved=(rotated,params),padding=pad)
        cx=pad+doc.frame["center_x"]
        cy=pad+doc.frame["ground_y"]
        crop=source.crop((cx-183,cy-175,cx+183,cy+150))
        scale=0.99
        new=(round(crop.width*scale),round(crop.height*scale))
        sprite=crop.resize(new,Image.Resampling.LANCZOS)
        ox,oy=x+66,204
        if name=="WALL":
            draw.line(((ox+183,oy+20),(ox+183,oy+320)), fill=DIVIDER,width=3)
        elif name=="SLOPE":
            draw.line(((ox+3,oy+175-180*slope),(ox+363,oy+175+180*slope)),fill=DIVIDER,width=3)
        else:
            draw.line(((ox+10,oy+175),(ox+360,oy+175)),fill=DIVIDER,width=3)
        board.paste(sprite,(ox,oy),sprite)
        for leg in legs.values():
            if gait.phase_at(t,leg.phase)>=gait.stance:
                continue
            foot=rotated[f"{leg.name}_tarsus"].tip
            sx=ox+(foot[0]-doc.frame["center_x"]+183)*scale
            sy=oy+(foot[1]-doc.frame["ground_y"]+175)*scale
            r=3
            draw.ellipse((sx-r,sy-r,sx+r,sy+r),fill="#79dc9a")
    return board


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("searchlight_crawler_review.png"))
    parser.add_argument("--gif-output", type=Path, default=None)
    parser.add_argument("--surface-output", type=Path, default=None)
    args = parser.parse_args()
    doc = RigDocument.load(RIG)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_board(doc).save(args.output)
    print(args.output)
    if args.gif_output is not None:
        build_motion(doc, args.gif_output)
        print(args.gif_output)
    if args.surface_output is not None:
        args.surface_output.parent.mkdir(parents=True, exist_ok=True)
        build_surface_board(doc).save(args.surface_output)
        print(args.surface_output)


if __name__ == "__main__":
    main()
