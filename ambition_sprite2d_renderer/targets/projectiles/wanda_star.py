"""Wanda's gold and turquoise star projectile, authored towards +x."""
from __future__ import annotations
import math
from pathlib import Path
from ..characters._magic_character_art import Canvas, star, add, polar
TARGET_NAME='wanda_star'
FRAME_SIZE=(96,64)
ROWS=[('travel',12,55)]
ACTOR_METADATA={'actor':{'character_id':'prop_wanda_star','display_name':'Wanda Star'},'visual_description':{'intent':'A gold four-pointed star on a turquoise comet trail, travelling to the right.'},'tags':['projectile','magical','wanda']}
def _render_frame(anim,i,n):
    d=Canvas(FRAME_SIZE);t=i/n;angle=360*t;center=(65,32)
    d.poly([(8,32),(43,22),(65,19),(77,32),(65,45),(43,42)],(59,173,170,115),None)
    d.poly([(17,32),(46,27),(63,23),(73,32),(63,41),(46,37)],(154,234,217,200),None)
    for j in range(4):
        x=18+j*9+4*math.sin(math.tau*t+j);y=32+8*math.sin(j*2+t*math.tau)
        star(d,(x,y),2.4+j*.3,(241,225,157,180),None,4)
    star(d,center,23,'#8a624d',None,4,angle);star(d,center,20,'#edbd69',None,4,angle);star(d,center,15,'#fff0bb',None,4,angle);d.disk(center,5,'#fff9e1',None)
    return d.finish()
def render(out_dir,**opts):
    from ...authoring.sheet_build import build_sheet
    output=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=_render_frame,out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA)
    return [Path(output[k]) for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if output.get(k)]
TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
