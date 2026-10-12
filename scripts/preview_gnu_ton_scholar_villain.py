#!/usr/bin/env python3
"""Render the GNU-ton scholar review board from the *actual* skeletal rig.

Uses RigDocument frame rendering (SVG part isolation + bone transforms), not a
painted mock-up or AI generated image. Individual frames can be compared with
what ``scripts/regen/sprites.sh --target gnu_ton_scholar_villain`` packs.

    cd tools/ambition_sprite2d_renderer
    python scripts/preview_gnu_ton_scholar_villain.py --output /tmp/gnu_scholar.png
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

RIG = ROOT / "ambition_sprite2d_renderer/targets/characters/rigged/gnu_ton_scholar_villain.rig.json"

BG = "#1b2030"
CARD = "#292f43"
INK = "#eee8df"
MUTED = "#b1b7c5"
GOLD = "#e4b45f"


def font(size: int, bold: bool = False):
    files = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in files:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def cropped(image: Image.Image, padding=6) -> Image.Image:
    bbox=image.getbbox()
    if bbox is None:
        raise AssertionError("empty rig frame")
    l,t,r,b=bbox
    return image.crop((max(0,l-padding),max(0,t-padding),min(image.width,r+padding),min(image.height,b+padding)))


def composite_center(canvas: Image.Image, source: Image.Image, rect, *, scale: float):
    x,y,w,h=rect
    source=cropped(source)
    factor=min(scale,w/source.width,h/source.height)
    dest=source.resize((max(1,round(source.width*factor)),max(1,round(source.height*factor))),Image.Resampling.LANCZOS)
    canvas.paste(dest,(int(x+(w-dest.width)/2),int(y+(h-dest.height)/2)),dest)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("gnu_ton_scholar_villain_review.png"))
    args=parser.parse_args()
    doc=RigDocument.load(RIG)
    out=Image.new("RGB",(1760,1090),BG)
    draw=ImageDraw.Draw(out)
    draw.text((51,34),"GNU-TON  /  THE SCHOLAR",font=font(39,True),fill=INK)
    draw.text((53,91),"Programmatically generated vector art  |  Animated with Ambition RigDocument",font=font(21),fill=MUTED)
    draw.line([(48,135),(1712,135)],fill=GOLD,width=2)

    # Large canonical rest drawing; the left panel includes true pixel sizes.
    draw.rounded_rectangle((48,158,555,1045),radius=22,fill=CARD)
    draw.text((79,188),"REVISED VILLAIN",font=font(27,True),fill=INK)
    draw.text((79,225),"Resting pose / three-quarter",font=font(17),fill=MUTED)
    rest=doc.render_frame("rest",0,10)
    composite_center(out,rest,(92,273,414,535),scale=4.0)
    draw.line([(82,834),(520,834)],fill="#485167",width=1)
    draw.text((86,852),"ACTUAL SMALL-SPRITE READ",font=font(17,True),fill=GOLD)
    for i,height in enumerate((96,64,48)):
        thumb=cropped(rest,0)
        r=height/thumb.height
        thumb=thumb.resize((max(1,round(r*thumb.width)),height),Image.Resampling.LANCZOS)
        tx=110+143*i+(87-thumb.width)//2
        ty=905+(96-height)//2
        out.paste(thumb,(tx,ty),thumb)
        draw.text((123+143*i,1009),str(height)+" px",font=font(15),fill=MUTED)

    poses=[("POINT", "point", 4, 8),("CONDUCT","conduct",5,10),
           ("INVOKE","invoke",4,8),("BRACE","brace",3,6),
           ("HIT","hit",2,6),("TUMBLE","tumble",4,8),
           ("DAZED","dazed",2,8),("DEATH","death",8,10)]
    cellw=276; cellh=426; gap=14
    for i,(label,row,index,count) in enumerate(poses):
        gx=i%4; gy=i//4
        x=576+gx*(cellw+gap); y=158+gy*(cellh+gap)
        draw.rounded_rectangle((x,y,x+cellw,y+cellh),radius=17,fill=CARD)
        draw.text((x+18,y+17),label,font=font(19,True),fill=GOLD)
        image=doc.render_frame(row,index,count)
        composite_center(out,image,(x+22,y+65,cellw-44,cellh-94),scale=2.05)
    draw.text((578,1031),
              f"{len(doc.bones)} BONES  /  {len(doc.parts)} RIGGED VECTOR PARTS  /  {len(doc.clips)} ANIMATION CLIPS",
              font=font(19,True),fill=MUTED)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    out.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
