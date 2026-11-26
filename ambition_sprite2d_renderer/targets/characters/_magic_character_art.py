"""Small vector-style drawing vocabulary for the Magical dimension.

All geometry is expressed in final sprite pixels. Art is supersampled; the
published image is transparent, with no detached shadows or floor art.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

INK = '#29303a'


def clamp(t): return max(0., min(1., t))
def smooth(t):
    t = clamp(t)
    return t*t*(3.-2.*t)
def lerp(a,b,t): return a+(b-a)*t
def mix(a,b,t): return tuple(lerp(x,y,t) for x,y in zip(a,b))
def add(a,b): return a[0]+b[0],a[1]+b[1]
def sub(a,b): return a[0]-b[0],a[1]-b[1]
def mul(a,k): return a[0]*k,a[1]*k
def norm(a): return math.hypot(*a)
def unit(a): return mul(a,1/max(1e-8,norm(a)))
def perp(a): return -a[1],a[0]
def rot(p,deg):
    t=math.radians(deg); c,s=math.cos(t),math.sin(t)
    return c*p[0]-s*p[1],s*p[0]+c*p[1]
def polar(r,deg): return rot((r,0.),deg)
def track(t,keys):
    if t<=keys[0][0]: return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b: return lerp(x,y,smooth((t-a)/(b-a)))
    return keys[-1][1]
def bezier(p0,p1,p2,p3,n=20):
    return [mix(mix(mix(p0,p1,t),mix(p1,p2,t),t),mix(mix(p1,p2,t),mix(p2,p3,t),t),t) for t in (i/n for i in range(n+1))]
def phase(i,n,loop): return i/max(1,n if loop else n-1)


class Canvas:
    def __init__(self,size,super_scale=3):
        self.size=size; self.s=super_scale
        self.image=Image.new('RGBA',tuple(v*self.s for v in size)); self.d=ImageDraw.Draw(self.image)
    def line(self,p,c=INK,w=1.5,closed=False):
        if len(p)<2:return
        q=[(x*self.s,y*self.s) for x,y in p]
        if closed:q.append(q[0])
        self.d.line(q,fill=c,width=max(1,round(w*self.s)),joint='curve')
        if not closed:
            r=w*self.s/2
            for x,y in (q[0],q[-1]):self.d.ellipse((x-r,y-r,x+r,y+r),fill=c)
    def poly(self,p,c,edge=INK,w=1.8):
        self.d.polygon([(x*self.s,y*self.s) for x,y in p],fill=c)
        if edge:self.line(p,edge,w,True)
    def oval(self,c,rx,ry,fill,edge=INK,w=1.5,angle=0):
        p=[add(c,rot((rx*math.cos(t),ry*math.sin(t)),angle)) for t in (math.tau*i/44 for i in range(44))]
        self.poly(p,fill,edge,w)
    def disk(self,c,r,fill,edge=INK,w=1.5):self.oval(c,r,r,fill,edge,w)
    def box(self,c,rx,ry,fill,edge=INK,w=1.6,r=4,angle=0):
        pts=[]
        r=min(r,rx,ry)
        for x,y,offset in [(rx-r,ry-r,0),(-rx+r,ry-r,90),(-rx+r,-ry+r,180),(rx-r,-ry+r,270)]:
            for i in range(7):
                pts.append(add(c,rot(add((x,y),polar(r,offset+i*15)),angle)))
        self.poly(pts,fill,edge,w)
    def tube(self,a,b,r,c,light=None,dark=None,edge=INK):
        u=unit(sub(b,a));n=perp(u)
        if norm(sub(a,b))<.001:return
        self.poly([add(a,mul(n,r)),add(b,mul(n,r)),add(b,mul(n,-r)),add(a,mul(n,-r))],c,edge,1.5)
        if light:self.line([add(a,mul(n,-r*.58)),add(b,mul(n,-r*.58))],light,max(.6,r*.34))
        if dark:self.line([add(a,mul(n,r*.61)),add(b,mul(n,r*.61))],dark,max(.7,r*.45))
    def bolt(self,c,r=3,fill='#b4b6ae'):
        self.disk(c,r,fill,INK,.9); self.line([add(c,(-r*.50,r*.25)),add(c,(r*.50,-r*.25))],INK,.8)
    def gear(self,c,r,teeth,ang,fill,light,hub):
        pts=[]
        for i in range(teeth*4):
            pts.append(add(c,polar(r*(1 if i%4 in (1,2) else .79),ang+360*i/(teeth*4))))
        self.poly(pts,fill,INK,1.4);self.disk(c,r*.61,light,INK,1.0);self.disk(c,r*.24,hub,INK,1.1)
        for k in range(3):self.disk(add(c,polar(r*.43,ang+120*k)),r*.11,hub,None)
    def finish(self):return self.image.resize(self.size,Image.Resampling.LANCZOS)


def anchored_death(im,ground):
    """Plant the toppled solid art on the same ground row as its feet."""
    bb=im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
    if bb:
        out=Image.new('RGBA',im.size);out.paste(im,(0,round(ground+1-bb[3])));return out
    return im



def star(d, center, r, color, edge=None, points=4, angle=-90):
    d.poly([add(center,polar(r*(1 if i%2==0 else .28),angle+i*180/points)) for i in range(2*points)],color,edge,1.1)


def curve(d, points, fill, edge=INK, w=1.8):
    """A closed silhouette specified as consecutive cubic Bezier segments."""
    path=[points[0]]
    for i in range(1,len(points),3):
        path.extend(bezier(path[-1],*points[i:i+3],n=14)[1:])
    d.poly(path,fill,edge,w)


def metadata(target,name,kind,plan,mass,locomotion,traits,description,enemy=False):
    tags=['magical',*traits]+(['enemy'] if enemy else ['fighter'])
    return {'actor':{'character_id':target,'display_name':name},'body':{'body_plan':plan,'body_kind':kind,'mass_class':mass,'traits':traits,'locomotion_hint':locomotion},'visual':{'default_pose':'idle','portrait':{'animation':'idle','frame':0}},'tags':tags,'authoring_description':description,'animation_bindings':{'default':{'animation':'idle','events':[]},'locomotion.walk':{'animation':'walk','events':[]},'combat.hurt':{'animation':'hit','events':[]},'combat.death':{'animation':'death','events':[]}}}


def publish(target,rows,render,frame_size,actor,box,out_dir,grounded=False):
    from pathlib import Path
    from ...authoring.sheet_build import build_sheet
    from ...core.measure import body_metrics_for_box
    outputs=build_sheet(target=target,rows=rows,render_fn=render,out_dir=Path(out_dir),frame_size=frame_size,auto_crop=False,trim=True,actor_metadata=actor,body_metrics_fn=lambda w,h:body_metrics_for_box(box,w,h),animation_key_map={name:name for name,_,_ in rows},sits_on_ground=grounded)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
