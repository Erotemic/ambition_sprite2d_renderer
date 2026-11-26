"""Small shared supersampled vector drawing and publishing helpers."""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw

INK = '#202735'

def clamp(t):
    return max(0., min(1., t))

def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)

def lerp(a,b,t):
    return a+(b-a)*t

def track(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t <= b:
            return lerp(x,y,smooth((t-a)/(b-a)))
    return keys[-1][1]

def add(a,b):
    return a[0]+b[0],a[1]+b[1]

def mul(a,k):
    return a[0]*k,a[1]*k

def polar(r,deg):
    a=math.radians(deg)
    return r*math.cos(a),r*math.sin(a)

def rot(p,deg):
    c,s=polar(1,deg)
    return p[0]*c-p[1]*s,p[0]*s+p[1]*c

def rgbmix(a,b,t):
    return tuple(round(lerp(x,y,clamp(t))) for x,y in zip(a,b))

def phase(i,n,loop):
    return i/max(1,n if loop else n-1)

class Canvas:
    def __init__(self,size,scale=3):
        self.size=size;self.s=scale
        self.image=Image.new('RGBA',tuple(v*scale for v in size))
        self.d=ImageDraw.Draw(self.image)
    def line(self,p,fill=INK,w=1.4,closed=False):
        if len(p)<2:return
        q=[(x*self.s,y*self.s) for x,y in p]
        if closed:q.append(q[0])
        self.d.line(q,fill=fill,width=max(1,round(w*self.s)),joint='curve')
        if not closed:
            r=w*self.s/2
            for x,y in (q[0],q[-1]):self.d.ellipse((x-r,y-r,x+r,y+r),fill=fill)
    def poly(self,p,fill,edge=INK,w=1.4):
        self.d.polygon([(x*self.s,y*self.s) for x,y in p],fill=fill)
        if edge:self.line(p,edge,w,True)
    def oval(self,c,rx,ry,fill,edge=INK,w=1.4,angle=0):
        self.poly([add(c,rot((rx*math.cos(t),ry*math.sin(t)),angle)) for t in (math.tau*i/52 for i in range(52))],fill,edge,w)
    def disk(self,c,r,fill,edge=INK,w=1.4):
        self.oval(c,r,r,fill,edge,w)
    def tube(self,a,b,r,fill,light=None,dark=None):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.001:return
        n=(-dy/length,dx/length)
        def p(c,s):return add(c,mul(n,s))
        self.poly([p(a,r),p(b,r),p(b,-r),p(a,-r)],fill,INK,1.5)
        if light:self.line([p(a,-r*.52),p(b,-r*.52)],light,max(.7,r*.4))
        if dark:self.line([p(a,r*.58),p(b,r*.58)],dark,max(.7,r*.42))
    def finish(self):return self.image.resize(self.size,Image.Resampling.LANCZOS)

def floating_actor(target,name,dimension,traits,description,gameplay):
    return {
        'actor': {'character_id':target,'display_name':name},
        'body': {'body_plan':'Floating','body_kind':'Small','mass_class':'Light','locomotion_hint':'Fly','traits':['enemy',dimension,*traits]},
        'visual': {'default_pose':'idle','portrait':{'animation':'idle','frame':0}},
        'tags':['enemy',dimension,*traits],
        'authoring_description':description,'gameplay_description':gameplay,
        'animation_bindings': {'default':{'animation':'idle','events':[]},'locomotion.walk':{'animation':'walk','events':[]},'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]}},
    }

def publish(target, rows, frame, size, metadata, metrics, out_dir, **opts):
    from ...authoring.sheet_build import build_sheet
    # Match the existing painted enemy target contract. The true body box
    # excludes transient trails, sparks, and the expanding replication row.
    outputs=build_sheet(target=target,rows=rows,render_fn=frame,out_dir=Path(out_dir),frame_size=size,
        auto_crop=False,actor_metadata=metadata,body_metrics_fn=metrics,animation_key_map={a:a for a,_,_ in rows})
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
