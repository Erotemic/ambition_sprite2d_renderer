"""Moving Goalposts, the literal mobile target of Capital.

A walking football goal with two independently telescoping enamelled posts,
a telescoping crossbar, a real deforming net and a referee-like display face.
It redefines its opening, then charges with the whole frame. The net is art,
not a solid wall, and no actual objective or scoring rule is changed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw

TARGET_NAME = 'moving_goalposts'
FRAME_SIZE = (360, 254)
SUPER = 3
CX, GROUND = 180., 218.
WINDUP_S, ACTIVE_S, RECOVER_S = .66, .30, .68
TOTAL_S = WINDUP_S + ACTIVE_S + RECOVER_S
ROWS = [('idle', 16, 100), ('walk', 16, 80), ('notice', 8, 75),
        ('windup', 12, 60), ('attack_side', 48, 34), ('hit', 8, 75),
        ('death', 18, 90)]
LOOPS = {'idle', 'walk', 'windup'}
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Moving Goalposts'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Medium',
             'locomotion_hint': 'Walk', 'traits': ['enemy', 'business', 'machine']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'business', 'machine', TARGET_NAME],
    'authoring_description': ('A literal football goal for the moving-goalposts fallacy, changing its '
        'height, width and position with telescoping hardware and a deforming net. '
        'Its mechanical referee face and charge are fictional combat inventions.'),
    'gameplay_description': ('A grounded, mobile opponent that narrows the opening, sets its feet, '
        'then extends the goal and charges. The long recovery is an opening. '
        'The net is decorative and the game does not change its rules.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}
INK='#263744'; STEEL_D='#485c69'; STEEL='#78939c'; STEEL_L='#b9cbd0'
ENAMEL='#e9e8dc'; WHITE='#fff9e7'; SHADE='#a4b8bc'; RED='#ba4d49'; RED_D='#783d3d'
GOLD='#dbad5b'; GOLD_D='#96683c'; RUBBER='#374550'; LIGHT='#e0f3ee'; SCREEN='#233e45'
NET_D=(47,75,84,175); NET_L=(194,222,219,190)


def clamp(t): return max(0., min(1., t))
def smooth(t):
    t=clamp(t); return t*t*(3-2*t)
def lerp(a,b,t): return a+(b-a)*t
def mix(a,b,t): return tuple(lerp(x,y,t) for x,y in zip(a,b))
def add(a,b): return a[0]+b[0],a[1]+b[1]
def sub(a,b): return a[0]-b[0],a[1]-b[1]
def mul(a,k): return a[0]*k,a[1]*k
def norm(a): return math.hypot(*a)
def unit(a): return mul(a,1/max(1e-9,norm(a)))
def perp(a): return -a[1],a[0]
def rot(p,a):
    t=math.radians(a); c,s=math.cos(t),math.sin(t)
    return c*p[0]-s*p[1],s*p[0]+c*p[1]
def track(t,keys):
    if t<=keys[0][0]: return keys[0][1]
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b: return lerp(x,y,smooth((t-a)/(b-a)))
    return keys[-1][1]


class Canvas:
    def __init__(self):
        self.image=Image.new('RGBA',tuple(v*SUPER for v in FRAME_SIZE)); self.d=ImageDraw.Draw(self.image)
    def line(self,p,c=INK,w=1.4,closed=False):
        q=[(x*SUPER,y*SUPER) for x,y in p]
        if closed:q.append(q[0])
        self.d.line(q,fill=c,width=max(1,round(w*SUPER)),joint='curve')
        if not closed:
            r=w*SUPER/2
            for x,y in (q[0],q[-1]): self.d.ellipse((x-r,y-r,x+r,y+r),fill=c)
    def poly(self,p,c,edge=INK,w=1.8):
        self.d.polygon([(x*SUPER,y*SUPER) for x,y in p],fill=c)
        if edge:self.line(p,edge,w,True)
    def oval(self,c,rx,ry,fill,edge=INK,w=1.5,angle=0):
        p=[add(c,rot((rx*math.cos(t),ry*math.sin(t)),angle)) for t in (math.tau*i/36 for i in range(36))]
        self.poly(p,fill,edge,w)
    def finish(self): return self.image.resize(FRAME_SIZE,Image.Resampling.LANCZOS)


@dataclass(frozen=True)
class Pose:
    x: float; width: float; height_l: float; height_r: float
    lean: float; drop: float; phase: float; stride: float
    mood: float; blink: float; dead: float; collapse: float
    recoil: float


def pose(anim,i,n):
    t=i/(n if anim in LOOPS else max(1,n-1)); p=math.tau*t
    x=0.; width=102.; hl=130.; hr=140.; lean=0.; drop=0.; stride=0.
    mood=.13; blink=max(0.,math.cos(p-4.4))**65; dead=collapse=recoil=0.
    if anim=='idle':
        # Even at rest the standards adjust slightly, never leaving their sockets.
        width+=2*math.sin(p); hl+=2*math.sin(p); hr+=2*math.sin(p+.5)
    elif anim=='walk':
        stride=1.; x=3*math.sin(p); drop=2*abs(math.sin(p)); lean=5+4*math.sin(p)
        width+=4*math.sin(p+.6); hl+=2*math.sin(p); hr-=2*math.sin(p)
        mood=.27; blink=0.
    elif anim=='notice':
        v=math.sin(math.pi*t); width+=10*v; hr+=8*v; hl+=5*v; lean=-4*v
        mood=.55; blink=0.
    elif anim=='windup':
        # Brain-held row can begin at any phase: hold the entire tell.
        width=83+1.2*math.sin(p); hl=112+.7*math.sin(p); hr=120+.7*math.sin(p)
        lean=-9.; drop=7.; x=-5.; mood=.98; blink=0.
    elif anim=='attack_side':
        sec=t*TOTAL_S; w=WINDUP_S; e=w+ACTIVE_S; end=TOTAL_S
        width=track(sec,[(0,102),(w,83),(w+.14,142),(e,128),(e+.27,90),(end,102)])
        hl=track(sec,[(0,130),(w,112),(w+.15,145),(e,130),(e+.25,123),(end,130)])
        hr=track(sec,[(0,140),(w,120),(w+.15,154),(e,147),(e+.25,132),(end,140)])
        lean=track(sec,[(0,0),(w,-9),(w+.11,14),(e,12),(e+.22,-4),(end,0)])
        drop=track(sec,[(0,0),(w,7),(w+.15,0),(e,3),(e+.22,5),(end,0)])
        x=track(sec,[(0,0),(w,-5),(w+.16,9),(e,8),(e+.22,1),(end,0)])
        stride=track(sec,[(0,0),(w,0),(w+.11,1),(e,.5),(e+.22,0),(end,0)])
        # A stomp rather than a full gait cycle during the charge.
        p=track(sec,[(0,0),(w,0),(w+.11,1.5),(e,3.14),(end,6.28)])
        mood=track(sec,[(0,.13),(w,.98),(e,1),(e+.25,.5),(end,.13)]); blink=0.
    elif anim=='hit':
        v=math.sin(math.pi*t); x=-8*v; lean=-13*v; width=102-9*v
        hl-=8*v; hr-=5*v; drop=5*v; recoil=v; mood=.7; blink=v
    elif anim=='death':
        dead=smooth(t); width=102-29*dead; hl=130-38*dead; hr=140-47*dead
        collapse=74*dead; x=6*dead; mood=.0; blink=dead
    return Pose(x,width,hl,hr,lean,drop,p,stride,mood,blink,dead,collapse,recoil)


def section(d,a,b,r,fill=ENAMEL,edge=INK,highlight=WHITE,shading=SHADE):
    """A closed, shaded, straight rectangular tube. Faces follow its axis."""
    v=unit(sub(b,a)); n=perp(v)
    p=lambda c,s:add(c,mul(n,s))
    d.poly([p(a,-r),p(b,-r),p(b,r),p(a,r)],fill,edge,1.8)
    d.poly([p(a,r*.38),p(b,r*.38),p(b,r*.85),p(a,r*.85)],shading,None)
    d.line([p(a,-r*.58),p(b,-r*.58)],highlight,max(.9,r*.22))


def band(d,a,b,r,t,width=5,col=RED):
    v=unit(sub(b,a)); c=mix(a,b,t); n=perp(v)
    p=lambda s,k:add(add(c,mul(v,s)),mul(n,k))
    d.poly([p(-width/2,-r-.35),p(width/2,-r-.35),p(width/2,r+.35),p(-width/2,r+.35)],col,INK,.9)
    d.line([p(-width/2+1,-r*.66),p(width/2-1,-r*.66)],'#f4a38a',.9)


def telescopic(d,a,b,r,sleeve=72.,outer=ENAMEL):
    """Inner chrome piston remains inside the larger sleeve at all lengths."""
    v=unit(sub(b,a)); n=perp(v); c=add(a,mul(v,sleeve))
    section(d,a,b,r*.68,STEEL_L,INK,LIGHT,STEEL)
    section(d,a,c,r,outer)
    # Raised metal collar and a small colored stripe at the sleeve's end.
    section(d,add(c,mul(v,-4)),add(c,mul(v,2.5)),r+1,STEEL,INK,STEEL_L,STEEL_D)
    band(d,a,c,r,.24,5.5)
    # Calibration rings on the exposed inner tube, useful to read telescoping.
    exposed=norm(sub(b,c)); count=int((exposed-5)//9)
    for k in range(max(0,count)):
        pt=add(c,mul(v,8+9*k)); d.line([add(pt,mul(n,-r*.5)),add(pt,mul(n,r*.5))],STEEL_D,.8)


def grid(d,a,b,c,e,nx,ny,slack=0.):
    """Bilinear net panel. Shared boundary vertices are the actual tube endpoints."""
    def pt(u,v):
        p=mix(mix(a,b,u),mix(c,e,u),v)
        return add(p,(0,slack*math.sin(math.pi*u)*math.sin(math.pi*v)))
    for i in range(nx+1):
        u=i/nx; pts=[pt(u,j/12) for j in range(13)]; d.line(pts,NET_D,1.65);d.line(pts,NET_L,.75)
    for j in range(ny+1):
        v=j/ny; pts=[pt(i/16,v) for i in range(17)];d.line(pts,NET_D,1.65);d.line(pts,NET_L,.75)


def bolt(d,c,r=2.2):
    d.oval(c,r,r,STEEL_D,INK,.8);d.oval(add(c,(-.4,-.55)),r*.48,r*.48,STEEL_L,None)


def foot(d,ankle,angle):
    # Treaded rubber pads and red heel reflectors. Bottom of sole = ankle + 6.
    p=lambda u,v:add(ankle,rot((u,v),angle))
    d.poly([p(-11,-9),p(5,-10),p(13,-7),p(18,-2),p(18,4),p(13,6),p(-13,6),p(-16,2),p(-15,-4)],RUBBER,INK,1.8)
    d.poly([p(-13,1),p(17,1),p(17,4),p(13,6),p(-13,6)],STEEL_D,None)
    d.poly([p(-10,-8),p(5,-8),p(13,-5),p(16,-1),p(-10,-1)],STEEL,INK,1.0)
    d.poly([p(-12,-7),p(-7,-7),p(-7,-3),p(-12,-3)],RED,RED_D,.8)
    for xx in (-7,1,9): d.line([p(xx,3),p(xx,6)],INK,1.1)


def leg(d,base,ankle,angle=0.,far=False):
    knee=add(mix(base,ankle,.53),rot((5 if not far else -4,-1),angle))
    section(d,base,knee,5.1,STEEL_D if far else STEEL,INK,STEEL_L,STEEL_D)
    section(d,knee,ankle,4.4,STEEL,INK,STEEL_L,STEEL_D)
    d.oval(knee,5.1,5.1,GOLD_D,INK,1.3);bolt(d,knee,2.7)
    foot(d,ankle,angle)


def face(d,a,b,q):
    # Mechanically attached referee board, hung below the centre of the crossbar.
    u=unit(sub(b,a)); n=perp(u); c=add(mix(a,b,.56),mul(n,15))
    def P(x,y):return add(c,add(mul(u,x),mul(n,y)))
    # Two mounting brackets overlap the actual beam.
    for x in (-17,17):section(d,P(x,-19),P(x,-7),3.0,STEEL,INK,STEEL_L,STEEL_D)
    d.poly([P(-28,-12),P(24,-12),P(29,-6),P(29,11),P(23,16),P(-24,16),P(-29,10),P(-29,-6)],STEEL_D,INK,2)
    d.poly([P(-24,-8),P(24,-8),P(25,10),P(22,12),P(-24,12)],SCREEN,INK,1.0)
    d.line([P(-24,-10),P(23,-10)],STEEL_L,1.25)
    for x in (-23,23):bolt(d,P(x,12),1.6)
    # Eyes and brow are part of the inset screen rather than painted on the net.
    ang=math.degrees(math.atan2(u[1],u[0])); blink=q.blink
    for x in (-12,10):
        ey=-1; rx=7.9; ry=max(.7,6.5*(1-.85*blink)-1.8*q.mood)
        d.oval(P(x,ey),rx,ry,'#edf3de',None,angle=ang)
        if blink<.72:
            look=2.2 if q.dead<.5 else 0.
            d.oval(P(x+look,ey+.3),3.6,max(.8,ry*.75),INK,None,angle=ang)
            d.oval(P(x+look-.9,ey-1.1),1.05,1.05,WHITE,None)
        # Separate brow changes from skeptical to accusatory.
        slope=1.5+3.3*q.mood
        sign=1 if x<0 else -1
        d.line([P(x-7,ey-ry-1-sign*slope*.5),P(x+7,ey-ry-1+sign*slope*.5)],GOLD if q.mood>.75 else STEEL_L,1.9)
    if q.dead>.45:
        d.line([P(-7,9),P(7,9)],STEEL,1.3)
    elif q.mood>.7:
        d.line([P(-6,10),P(-2,7.5),P(6,8),P(9,10)],'#e6aa76',1.7)
    else:
        d.line([P(-6,7.5),P(0,10),P(8,7)],'#e6aa76',1.5)


def _render_frame(anim,i,n):
    q=pose(anim,i,n); d=Canvas()
    # Work in a grounded local frame. Net, posts and face share the same pose.
    def P(x,y):return add((CX+q.x,GROUND),rot((x,y),q.collapse))
    wl=-51.+(102.-q.width)*.25; wr=wl+q.width
    # The front frame is asymmetric in perspective, with the right corner nearer.
    # Its bases remain joined to the articulated legs even when it changes width.
    bl=P(wl,-25+q.drop*.25); br=P(wr,-25+q.drop*.25)
    tl=P(wl+q.lean*1.5,-25-q.height_l+q.drop)
    tr=P(wr+q.lean*1.5,-25-q.height_r+q.drop)
    # Rear support is lower and behind. Its front edge is never filled in:
    # the actual opening of the goal remains visibly empty.
    rbl=P(wl-36,-27+q.drop*.25); rbr=P(wr-36,-27+q.drop*.25)
    rtl=P(wl-30+q.lean*.8,-25-q.height_l*.74+q.drop)
    rtr=P(wr-30+q.lean*.8,-25-q.height_r*.74+q.drop)
    # Connected mesh panels, back first. Rear frame is a slightly darker metal.
    grid(d,rtl,rtr,rbl,rbr,10,9,4+q.recoil*4)
    grid(d,tl,tr,rtl,rtr,10,4,1.2)
    grid(d,tl,rtl,bl,rbl,4,10,2.)
    grid(d,tr,rtr,br,rbr,4,10,2.)
    for a,b in [(rbl,rtl),(rtl,rtr),(rtr,rbr),(rbl,rbr),(bl,rbl),(br,rbr),(tl,rtl),(tr,rtr)]:
        section(d,a,b,2.8,STEEL,INK,STEEL_L,STEEL_D)
    for p in (rtl,rtr,rbl,rbr):bolt(d,p,2.2)
    # Far foot first, near foot later. Swing trajectories are periodic; one pad
    # is planted during a walk. On death the whole assembly is tipped together.
    for side,base,x in [(-1,bl,wl),(1,br,wr)]:
        ph=q.phase+(0 if side==1 else math.pi)
        stride=q.stride
        footx=x+21*stride*math.sin(ph)
        lift=15*stride*max(0,math.cos(ph))
        ankle=P(footx,-8-lift)
        leg(d,base,ankle,angle=q.collapse,far=side==-1)
    # Front uprights. Sleeves, collars and exposed calibration rings reveal the
    # actual sliding components; the net is regenerated from their endpoints.
    telescopic(d,bl,tl,6.8,68.)
    telescopic(d,br,tr,7.7,73.)
    # Crossbar has two sleeves facing each other with a central piston.
    section(d,tl,tr,5.5,STEEL_L,INK,LIGHT,STEEL)
    v=unit(sub(tr,tl)); a=add(tl,mul(v,29.));b=add(tr,mul(v,-24.))
    section(d,tl,a,7.0,ENAMEL);section(d,tr,b,7.0,ENAMEL)
    for start,end in [(tl,a),(tr,b)]:
        v=unit(sub(end,start)); section(d,add(end,mul(v,-4)),add(end,mul(v,1.5)),7.8,STEEL,INK,STEEL_L,STEEL_D)
        band(d,start,end,7.0,.31,7)
    # Elbow housings overlap and join both tubes at each corner.
    for pt,r in [(tl,7.7),(tr,8.3)]:
        d.oval(pt,r,r,ENAMEL,INK,1.8);d.oval(add(pt,(-1.3,-1.4)),r*.58,r*.58,WHITE,None);bolt(d,pt,2.3)
    for pt,r in [(bl,8.0),(br,8.8)]:
        d.oval(pt,r,r,STEEL_D,INK,1.6);d.oval(pt,r*.72,r*.72,STEEL,INK,.8);bolt(d,pt,3.1)
    face(d,tl,tr,q)
    # Dead body rests on its lowest visible edge; do not bake a ground shadow.
    out=d.finish()
    if q.dead>0:
        bb=out.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
        if bb:
            shift=int(GROUND+1-bb[3]); moved=Image.new('RGBA',FRAME_SIZE); moved.paste(out,(0,shift));out=moved
    return out


def _body_metrics(fw,fh):
    # Measure the stable front frame rather than the shifting net and attack
    # envelope. Ground anchor stays between the two front posts.
    from ...core.measure import body_metrics_for_box
    return body_metrics_for_box((125,49,236,219),fw,fh)


def render(out_dir: str | Path, **opts):
    from ...authoring.sheet_build import build_sheet
    outputs=build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
                        out_dir=Path(out_dir), frame_size=FRAME_SIZE,
                        auto_crop=False, actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,
                        animation_key_map={a:a for a,_,_ in ROWS}, sits_on_ground=True)
    return [outputs[k] for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent')]
