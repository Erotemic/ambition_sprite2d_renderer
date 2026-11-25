"""Stereotyping: a walking cassette boombox with a mechanical label typewriter.

The cabinet is deliberately a wide, silver-and-black portable stereo, not a
face with two loudspeakers for eyes. Its radio tuner, cassette reels, woofer
cones, separate typewriter keyboard and paper feed are distinct mechanisms.
Two articulated arms hammer the keys, the carriage feeds paper, and the
cutter releases a volley of labels. All artwork is procedural; the labels in
these frames are visual anticipation/release cues, not gameplay projectiles.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ...core.draw import resize_transparent_sprite
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'stereotyping'
FRAME_SIZE = (400, 280)
SUPER = 3
ORIGIN = (150.0, 180.0)
GROUND = 256.0
BODY_BOX = (44, 56, 274, 256)
ROWS = [
    ('idle', 10, 100), ('walk', 16, 70), ('dash', 10, 65),
    ('notice', 8, 70), ('windup', 12, 65), ('attack_side', 20, 60),
    ('hit', 7, 65), ('death', 14, 85),
]
LOOPS = {'idle', 'walk', 'dash', 'windup'}
ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Stereotyping'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Standard', 'mass_class': 'Medium',
             'locomotion_hint': 'Walk', 'traits': ['neural', 'mechanical', 'cognitive_bias', 'stereo', 'typewriter']},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'neural', 'cognitive_bias'],
    'authoring_description': (
        'A walking silver cassette boombox grafted to a mechanical typewriter. '
        'It furiously sorts everything into crude categories, punches out paper '
        'labels and ejects them from a cutter. The cassette reels, speaker cones, '
        'key switches, paper and mechanical limbs are animated separately. '
        'Classification behavior and damaging or adhesive label projectiles '
        'are left to game content.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK = '#161c25'
BLACK = '#202832'
DARK = '#303c46'
STEEL_D = '#53616a'
STEEL = '#89999d'
SILVER = '#c0c8c6'
LIT = '#e9e6d7'
CREAM = '#eee0b8'
RUBBER = '#35343b'
COPPER = '#ad6e45'
GOLD = '#d8ad70'
TEAL = '#66c5cb'
GREEN = '#b4e1b3'
RED = '#d86954'
PAPER = '#f5e4b4'
PAPER_D = '#cbb88b'
PRINT = '#51423d'


def clamp(v):
    return max(0.0, min(1.0, v))


def smooth(v):
    v = clamp(v)
    return v*v*(3-2*v)


def mix(a, b, t):
    return a+(b-a)*t


def lerp(a, b, t):
    return (mix(a[0], b[0], t), mix(a[1], b[1], t))


def add(a, b):
    return (a[0]+b[0], a[1]+b[1])


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def mul(a, s):
    return (a[0]*s, a[1]*s)


def unit(a):
    return mul(a, 1/max(.0001, math.hypot(*a)))


def perp(a):
    return (-a[1], a[0])


def rotate(a, angle):
    c, s = math.cos(angle), math.sin(angle)
    return (a[0]*c-a[1]*s, a[0]*s+a[1]*c)


def alpha(rgb, amount):
    return (*rgb[:3], round(255*clamp(amount)))


def octagon(x0, y0, x1, y1, bevel=3):
    return [(x0+bevel,y0),(x1-bevel,y0),(x1,y0+bevel),(x1,y1-bevel),
            (x1-bevel,y1),(x0+bevel,y1),(x0,y1-bevel),(x0,y0+bevel)]


class Pen:
    """Logical pixels, optional rigid local coordinate frame, opaque shapes."""
    def __init__(self, image, transform=lambda p:p):
        self.image, self.d, self.transform = image, ImageDraw.Draw(image), transform

    def pts(self, points):
        return [(round(x*SUPER),round(y*SUPER)) for x,y in map(self.transform,points)]

    def poly(self, points, fill, outline=None, width=1.6):
        pts = self.pts(points)
        self.d.polygon(pts, fill=fill)
        if outline:
            self.d.line(pts+[pts[0]], fill=outline, width=max(1,round(width*SUPER)), joint='curve')

    def line(self, points, fill, width=1):
        self.d.line(self.pts(points), fill=fill, width=max(1,round(width*SUPER)), joint='curve')

    def rect(self, box, fill, outline=None, width=1.3, bevel=0):
        x0,y0,x1,y1=box
        self.poly(octagon(*box,bevel) if bevel else [(x0,y0),(x1,y0),(x1,y1),(x0,y1)], fill,outline,width)

    def oval(self, c, rx, ry, fill, outline=None, width=1.3, n=48):
        self.poly([(c[0]+rx*math.cos(k*math.tau/n),c[1]+ry*math.sin(k*math.tau/n)) for k in range(n)],fill,outline,width)

    def arc(self,c,rx,ry,a0,a1,color,width=1.2):
        self.line([(c[0]+rx*math.cos(mix(a0,a1,k/30)),c[1]+ry*math.sin(mix(a0,a1,k/30))) for k in range(31)],color,width)

    def local(self, origin, angle=0):
        return Pen(self.image,lambda p:self.transform(add(origin,rotate(p,angle))))

    def screw(self,c,r=2.4):
        self.oval(c,r,r,STEEL_D,INK,.8,n=16)
        self.arc(c,r-.5,r-.5,math.pi,1.7*math.pi,LIT,.6)
        self.line([add(c,(-r*.55,-r*.35)),add(c,(r*.55,r*.35))],INK,.7)


# Tiny stencil font, built into the source. No font file or text engine needed.
GLYPHS = {
    'A':('010','101','111','101','101'), 'B':('110','101','110','101','110'),
    'C':('011','100','100','100','011'), 'E':('111','100','110','100','111'),
    'F':('111','100','110','100','100'), 'H':('101','101','111','101','101'),
    'I':('111','010','010','010','111'), 'L':('100','100','100','100','111'),
    'M':('101','111','111','101','101'), 'N':('101','111','111','111','101'),
    'O':('010','101','101','101','010'), 'P':('110','101','110','100','100'),
    'R':('110','101','110','101','101'), 'S':('011','100','010','001','110'),
    'T':('111','010','010','010','010'), 'U':('101','101','101','101','111'),
    'Y':('101','101','010','010','010'), '0':('111','101','101','101','111'),
    '1':('010','110','010','010','111'), '2':('110','001','010','100','111'),
    '3':('110','001','010','001','110'), '4':('101','101','111','001','001'),
    '5':('111','100','110','001','110'), '6':('011','100','110','101','010'),
    '7':('111','001','010','010','010'), '8':('010','101','010','101','010'),
    '9':('010','101','011','001','110'), '?':('110','001','010','000','010'),
    ' ':('000',)*5, '-':('000','000','111','000','000'),
}


def text(p, s, x, y, scale, color):
    for i,ch in enumerate(s):
        for row,bits in enumerate(GLYPHS.get(ch,GLYPHS['?'])):
            for col,bit in enumerate(bits):
                if bit=='1':
                    a=x+(i*4+col)*scale; b=y+row*scale
                    p.rect((a,b,a+scale*.92,b+scale*.92),color)


@dataclass(frozen=True)
class Pose:
    shift: float = 0
    drop: float = 0
    tilt: float = 0
    back: float = -43
    front: float = 42
    back_lift: float = 0
    front_lift: float = 0
    typing: float = .12
    meter: float = .22
    reel: float = 0
    phase: float = 0
    paper: float = 5
    arm_spread: float = 0
    power: float = 1
    antenna: float = 0
    collapse: float = 0
    fade: float = 1


def gait(t, stride, lift):
    # Each foot has a stance interval and a raised swing interval.
    def foot(u):
        u %= 1
        if u < .58:
            return mix(stride,-stride,u/.58),0
        q=(u-.58)/.42
        return mix(-stride,stride,smooth(q)),lift*math.sin(math.pi*q)
    a,b=foot(t),foot(t+.5)
    return a,b


def pose_for(anim,i,n):
    t=i/(n if anim in LOOPS else max(1,n-1)); ph=math.tau*t
    base=Pose(phase=ph,reel=ph)
    if anim=='idle':
        return replace(base,drop=1.2*math.sin(ph),tilt=.8*math.sin(ph),meter=.22+.08*math.sin(2*ph),
                       typing=.20,antenna=1.8*math.sin(ph))
    if anim in ('walk','dash'):
        dash=anim=='dash'; (a,al),(b,bl)=gait(t,24 if dash else 17,19 if dash else 12)
        return replace(base,shift=6 if dash else 1,drop=-2.8*math.cos(2*ph),tilt=(8 if dash else 2)+2*math.sin(ph),
                       back=-43+a,front=42+b,back_lift=al,front_lift=bl,typing=.22,meter=.62 if dash else .4,
                       reel=2*ph,antenna=3*math.sin(ph-.6))
    if anim=='notice':
        k=smooth(t); return replace(base,tilt=-4*math.sin(math.pi*t),drop=-4*math.sin(math.pi*t),meter=.22+.56*k,
                                   typing=.16+.50*k,paper=5+5*k,antenna=4*math.sin(math.pi*t))
    if anim=='windup':
        return replace(base,drop=3+1.5*math.sin(2*ph),tilt=-3+1.2*math.sin(ph),typing=1,meter=.82+.16*math.sin(2*ph),
                       reel=3*ph,paper=14+5*math.sin(ph)**2,antenna=3*math.sin(2*ph))
    if anim=='attack_side':
        # The feed begins loaded, hammers a volley, then settles without a snap.
        attack=smooth(t/.18)*(1-smooth((t-.66)/.34))
        recoil=sum(math.exp(-((t-r)/.055)**2) for r in (.20,.40,.60))
        cycle = (t/.20)%1
        feed = mix(14,23,cycle) if t<.20 else (5+18*cycle if t<.60 else mix(6,5,smooth((t-.60)/.40)))
        return replace(base,shift=5*attack-3*recoil,drop=3*attack,tilt=mix(-3,8,attack)-4*recoil,
                       typing=1-.82*smooth((t-.72)/.28),meter=.28+.70*attack,reel=ph*4,
                       paper=feed,antenna=-5*recoil+3*attack)
    if anim=='hit':
        k=math.sin(math.pi*t); return replace(base,shift=-8*k,tilt=-12*k,drop=5*k,typing=.1*(1-k),
                                             meter=.25+.65*k,arm_spread=.8*k,antenna=-12*k,power=1-.45*k,paper=5+10*k)
    if anim=='death':
        k=smooth(t/.82); power=1-smooth((t-.12)/.6)
        return replace(base,shift=-6*k,drop=32*k,tilt=12*k,back=-47-11*k,front=43+17*k,
                       typing=.8*(1-smooth(t/.3)),meter=.45*power,reel=ph*.5,power=power,
                       arm_spread=.72*k,antenna=13*k,paper=5*(1-k),collapse=k,fade=1-.18*smooth((t-.85)/.15))
    raise ValueError(anim)


def transform_for(pose):
    a=math.radians(pose.tilt)
    return lambda p:add(add(ORIGIN,(pose.shift,pose.drop)),rotate(p,a))


def joint(a,b,l1,l2,side):
    u=unit(sub(b,a)); dist=max(abs(l1-l2)+.01,min(math.hypot(*sub(b,a)),l1+l2-.01))
    end=add(a,mul(u,dist)); along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    height=math.sqrt(max(0,l1*l1-along*along))
    return add(add(a,mul(u,along)),mul(perp(u),height*side)),end


def beam(p,a,b,w,face,edge=STEEL_D):
    q=perp(unit(sub(b,a)))
    shape=[add(a,mul(q,-w*.5)),add(b,mul(q,-w*.5)),add(b,mul(q,w*.5)),add(a,mul(q,w*.5))]
    p.poly(shape,face,INK,2)
    p.line([lerp(shape[0],shape[3],.16),lerp(shape[1],shape[2],.16)],LIT,1.25)
    p.line([lerp(shape[0],shape[3],.82),lerp(shape[1],shape[2],.82)],edge,2)


def draw_leg(p,hip,ankle,near,collapse):
    knee,ankle=joint(hip,ankle,39,39,-1)
    metal=STEEL if near else STEEL_D
    beam(p,hip,knee,18 if near else 16,metal)
    p.oval(hip,10,10,DARK,INK,2);p.oval(hip,5,5,metal,INK,1)
    beam(p,knee,ankle,14,STEEL_D if near else DARK)
    # telescoping shock, with piston rod and rubber bellows
    q=perp(unit(sub(ankle,knee))); a=add(knee,mul(q,7)); b=add(ankle,mul(q,7)); m=lerp(a,b,.6)
    beam(p,a,m,7,DARK);beam(p,m,b,4,SILVER)
    for z in (.2,.34,.48):
        c=lerp(a,m,z/.6);p.line([add(c,mul(q,-4)),add(c,mul(q,4))],INK,1.2)
    p.oval(knee,10,10,BLACK,INK,2);p.oval(knee,7,7,metal,INK,1);p.screw(knee,3.3)
    x,y=ankle
    p.poly([(x-13,y-8),(x+7,y-8),(x+12,y-3),(x+23,y-2),(x+25,y+6),
            (x+19,y+10),(x-14,y+10),(x-17,y+5)],BLACK,INK,2.4)
    p.poly([(x-12,y-7),(x+6,y-7),(x+11,y-2),(x+21,y),(x+22,y+3),(x-14,y+3)],metal,INK,1.1)
    p.line([(x-13,y+7),(x+21,y+7)],STEEL_D,2)
    for u in range(-10,19,7):p.line([(x+u,y+5),(x+u,y+9)],INK,1.4)


def draw_arm(p,shoulder,hand,near,side):
    elbow,hand=joint(shoulder,hand,39,39,side)
    metal=SILVER if near else STEEL_D
    beam(p,shoulder,elbow,12,metal)
    p.oval(shoulder,9,9,DARK,INK,2);p.oval(shoulder,5,5,metal,INK,1)
    beam(p,elbow,hand,10,STEEL if near else STEEL_D)
    p.oval(elbow,7.5,7.5,BLACK,INK,1.6);p.oval(elbow,4.8,4.8,metal,INK,1)
    p.oval(hand,5.6,5,BLACK,INK,1.5)
    return hand,elbow


def speaker(p,c,r,pulse):
    x,y=c
    # Recessed woofer, rubber surround, ribbed cone and perforated grille.
    p.oval(c,r+3,r+3,BLACK,INK,2)
    p.oval(c,r+1,r+1,STEEL_D,SILVER,1.1)
    p.oval(c,r-1,r-1,BLACK,INK,1.3)
    for rad,col in [(r-3,'#46525a'),(r-6,'#2b343b'),(r-8,'#42494d'),(r-11,'#30383d')]:
        p.oval(c,rad,rad,col)
    dome=r*.34+1.5*pulse
    p.oval(c,dome,dome,STEEL_D,INK,1)
    p.arc(c,dome-2,dome-2,math.pi,1.75*math.pi,STEEL,1.5)
    # Punched metal mesh, enough contrast to read at game scale.
    for j in range(-7,8):
        for i in range(-7,8):
            dx=i*4.2+(j%2)*2.1;dy=j*4.2
            if dx*dx+dy*dy<(r-3.4)**2:
                p.oval((x+dx,y+dy),1.05,1.05,'#161c23',n=10)
                if (i+j)%3==0:p.line([(x+dx-.8,y+dy-1.3),(x+dx+.6,y+dy-1.3)],'#687278',.55)
    p.arc(c,r+.3,r+.3,math.pi*1.04,math.pi*1.84,LIT,1.35)
    p.arc(c,r+.5,r+.5,-.1,math.pi*.83,INK,1.7)
    for a in (math.pi*.25,math.pi*.75,math.pi*1.25,math.pi*1.75):
        p.screw((x+(r+1)*math.cos(a),y+(r+1)*math.sin(a)),1.7)


def draw_reel(p,c,r,angle):
    p.oval(c,r,r,'#b7b9ab',INK,1.2)
    p.oval(c,r*.73,r*.73,BLACK)
    for k in range(3):
        a=angle+k*math.tau/3
        p.line([c,add(c,(r*.75*math.cos(a),r*.75*math.sin(a)))],SILVER,2)
    p.oval(c,2,2,SILVER,INK,.8)


def draw_cassette(p,pose):
    p.rect((-29,-86,29,-39),BLACK,INK,2,3)
    p.rect((-25,-82,25,-43),'#7c898b',STEEL_D,1.4,2)
    p.rect((-22,-78,22,-53),'#343e45',INK,1.4,2)
    p.rect((-19,-75,19,-55),'#5f635d',INK,.9,1)
    p.oval((-10,-65),8.2,8.2,'#352f2d');p.oval((10,-65),8.2,8.2,'#352f2d')
    draw_reel(p,(-10,-65),6.5,pose.reel);draw_reel(p,(10,-65),6.5,-pose.reel*.86)
    p.line([(-10,-57),(10,-57)],'#805c3d',1.3)
    p.poly([(-16,-52),(16,-52),(21,-45),(-21,-45)],SILVER,INK,.8)
    p.rect((-7,-50,7,-47),BLACK)
    p.line([(-21,-76),(-21,-54)],LIT,1)
    p.line([(-19,-76),(8,-76)],'#c0c5b8',.8)
    p.screw((-22,-46),1.4);p.screw((22,-46),1.4)
    text(p,'STEREO',-15,-81,.62,INK)


def draw_cabinet(p,pose):
    # Back/top/side planes make the stereo a three-dimensional rectangular case.
    p.poly([(-106,-112),(-90,-124),(111,-124),(123,-116),(123,-27),(106,-15),(-106,-15)],DARK,INK,2.8)
    p.poly([(-106,-112),(-90,-124),(111,-124),(123,-116),(106,-105)],SILVER,INK,1.8)
    p.poly([(106,-105),(123,-116),(123,-27),(106,-15)],STEEL_D,INK,2)
    p.line([(109,-103),(120,-111),(120,-31)],STEEL,1.5)
    for y in range(-94,-43,7):
        p.line([(110,y),(119,y-6)],BLACK,2.1)
    # Broad black rubber carry handle, with chrome hinge brackets.
    p.rect((-45,-125,-30,-119),STEEL,INK,1.3,1)
    p.rect((31,-125,46,-119),STEEL,INK,1.3,1)
    p.line([(-38,-122),(-38,-139),(-31,-145),(31,-145),(38,-139),(38,-122)],INK,8)
    p.line([(-38,-123),(-38,-139),(-31,-145),(31,-145),(38,-139),(38,-123)],STEEL_D,4.7)
    p.line([(-29,-146),(29,-146)],LIT,1.2)
    # Telescoping antenna (hinged above left speaker), flexing at its root.
    a=(-86,-122); b=add(a,rotate((24,-35),math.radians(pose.antenna)))
    c=lerp(a,b,.49); p.oval(a,4,3,STEEL_D,INK,1)
    p.line([a,c],INK,4.0);p.line([a,c],SILVER,2.1)
    p.line([c,b],INK,2.5);p.line([c,b],LIT,1.2);p.oval(b,1.8,1.8,SILVER,INK,.6)
    # Front face and separate black fascia, with beveled silver frame.
    p.rect((-106,-112,106,-15),SILVER,INK,2.8,4)
    p.rect((-101,-108,101,-19),STEEL,STEEL_D,1.2,3)
    p.line([(-99,-107),(99,-107)],LIT,1.7)
    p.rect((-99,-103,99,-25),BLACK,INK,1.5,3)
    # AM/FM tuning scale, station markings, movable needle.
    p.rect((-92,-100,92,-89),'#c5d3ca',INK,1.2,1)
    p.rect((-89,-98,89,-91),'#354a4c')
    for i in range(25):
        x=-86+i*7.1;p.line([(x,-97),(x,-93.4 if i%4==0 else -95)],CREAM,.65)
    for x,s in [(-85,'88'),(-49,'92'),(-12,'96'),(26,'100'),(67,'108')]:text(p,s,x,-91.6,.55,INK)
    needle=11+8*math.sin(pose.phase)*pose.typing
    p.line([(needle,-98),(needle,-91.7)],RED,1.5)
    # Main stereo speakers, a cassette transport, and physical switches.
    speaker(p,(-64,-57),30,pose.meter);speaker(p,(64,-57),30,pose.meter)
    draw_cassette(p,pose)
    # Distinct transport buttons just underneath the cassette window.
    for i in range(6):
        x=-25+i*8.6;p.rect((x,-37,x+7,-30),SILVER if i!=5 else RED,INK,.8,1)
        p.line([(x+1,-36),(x+6,-36)],LIT,.65)
    # Twin analogue VU meters plus input/volume knobs.
    for x in (-73,48):
        p.rect((x,-23,x+25,-17),BLACK,INK,.8)
        for j in range(8):
            value=pose.meter*(.87+.13*math.sin(pose.phase*2+x))
            col=('#a1d59d' if j<5 else '#dca760' if j<7 else RED) if pose.power>.05 and j/8<value else '#46544f'
            p.rect((x+1+j*3,-22,x+3+j*3,-18),col)
    for x in (-12,12):
        p.oval((x,-20),4.2,4.2,BLACK,INK,1);p.oval((x,-20),3,3,SILVER)
        p.line([(x,-20),(x+1.4,-22)],INK,1)
    for x in (-101,101):
        for y in (-106,-20):p.screw((x,y),2)
    # Front right label-printer module and cutter. Its lip masks the paper root.
    p.poly([(68,-121),(101,-121),(111,-115),(78,-115)],BLACK,INK,1.4)
    p.poly([(78,-115),(111,-115),(111,-110),(78,-110)],STEEL_D,INK,1.2)
    p.line([(80,-116),(109,-116)],COPPER,1.1)


# Keyboard: separate typewriter tray, perspective rows, round individual keys.
def key_center(row,col):
    count=(11,10,9)[row]
    return ((col-(count-1)/2)*12.0, -15+row*10.0)


def typing_keys(pose,anim):
    # Independent four-stroke rhythms. Every active hand target corresponds to
    # the very same depressed key used by the keyboard drawer.
    if pose.typing < .06 or pose.collapse>.2:return [],[]
    active=[]; hands=[]
    for side in (-1,1):
        phase=(pose.phase/math.tau*(6 if anim in ('windup','attack_side') else 3)+(0 if side==-1 else .48))
        stroke=math.floor(phase); u=phase-stroke
        row=(stroke+(0 if side==-1 else 1))%3
        count=(11,10,9)[row]
        col=(1+(stroke%3)) if side==-1 else (count-2-(stroke%3))
        press=pose.typing*(math.sin(math.pi*u)**6)
        prev_row=(stroke-1+(0 if side==-1 else 1))%3
        prev_count=(11,10,9)[prev_row]
        prev_col=(1+((stroke-1)%3)) if side==-1 else (prev_count-2-((stroke-1)%3))
        # At the beginning of a keystroke, the fingers travel to the next key.
        # The key only depresses once the finger reaches it.
        travel=smooth(u/.30)
        point=lerp(key_center(prev_row,prev_col),key_center(row,col),travel)
        active.append((row,col,press*travel)); hands.append((side,point,press*travel))
    return active,hands


def draw_keyboard(p,active):
    p.poly([(-77,-20),(77,-20),(90,-10),(84,20),(-84,20),(-90,-10)],BLACK,INK,2.5)
    p.poly([(-73,-20),(73,-20),(82,14),(-82,14)],STEEL_D,INK,1.3)
    p.poly([(-82,14),(82,14),(84,20),(-84,20)],STEEL,INK,1.2)
    p.line([(-79,16),(79,16)],LIT,1.3)
    # Visible platen and alternating linkage bars between the decks.
    p.rect((-72,-22,72,-17),BLACK,INK,1.2,2)
    p.line([(-69,-21),(69,-21)],STEEL,1.2)
    p.oval((-74,-19),4,4,COPPER,INK,1);p.oval((74,-19),4,4,COPPER,INK,1)
    press={(r,c):k for r,c,k in active}
    for row,count in enumerate((11,10,9)):
        for col in range(count):
            x,y=key_center(row,col); dy=2.2*press.get((row,col),0)
            p.oval((x,y+2),5,3.5,BLACK,INK,.85,n=20)
            p.oval((x,y-1+dy),4.7,3.5,CREAM,INK,.85,n=20)
            p.arc((x,y-1+dy),3.8,2.6,math.pi,1.8*math.pi,LIT,.7)
            p.line([(x-1.1,y-1+dy),(x+1.1,y-1+dy)],PRINT,.7)
    p.rect((-29,11,29,17),CREAM,INK,1,2)
    p.rect((-73,6,-52,12),CREAM,INK,1,1)
    p.rect((53,6,73,12),RED,INK,1,1)
    p.line([(-25,12),(25,12)],LIT,.8)


def hand_target(side,pose,hands):
    if pose.arm_spread>.02:
        return (side*(65+42*pose.arm_spread), 6+18*pose.arm_spread)
    h=next((v for v in hands if v[0]==side),None)
    if h:
        _,(x,y),press=h
        return (x+side*12,y-15-7*(1-press))
    return (side*57,-9)


def draw_hand(p,hand,finger,side):
    # Finger bones end at the actual active key rather than hovering nearby.
    v=unit(sub(finger,hand)); q=perp(v)
    p.oval(hand,6.4,4.8,STEEL,INK,1.5)
    for j in range(3):
        start=add(hand,mul(q,(j-1)*3.2));end=add(finger,mul(q,(j-1)*3.0))
        mid=add(lerp(start,end,.56),mul(q,side*1.6))
        p.line([start,mid,end],INK,4.5);p.line([start,mid,end],SILVER,2.6)
        p.oval(mid,1.6,1.6,STEEL_D,INK,.65,n=12)
    thumb=add(hand,mul(q,side*7))
    p.line([hand,thumb,add(thumb,mul(v,4))],INK,4.5)
    p.line([hand,thumb,add(thumb,mul(v,4))],STEEL,2.6)


def label(p,origin,angle,width,word):
    q=p.local(origin,angle)
    q.poly([(0,-6),(width-3,-6),(width,-3),(width,6),(0,6),(2,0)],PAPER,PRINT,1.05)
    q.poly([(width-5,-6),(width-3,-6),(width,-3),(width-5,-3)],PAPER_D,PRINT,.65)
    q.line([(3,-4),(width-6,-4)],'#fff4d6',.75)
    scale=min(1.15,(width-7)/(4*len(word)))
    text(q,word,4,-2.8,scale,PRINT)


def draw_feed(p,pose):
    length=pose.paper
    # Uncut paper rises from the actual cutter, then bows rightwards.
    p.poly([(82,-116),(103,-116),(103+length*.36,-116-length),
            (83+length*.36,-116-length-3)],PAPER,PRINT,1.05)
    if length>9:
        for j in range(3):
            y=-119-j*2.6
            p.line([(86+j*.9,y),(99+j*.9,y-1.2)],PRINT,.65)
    p.line([(79,-115.7),(110,-115.7)],BLACK,2)
    p.line([(80,-114.8),(109,-114.8)],SILVER,.8)


def draw_ejected(p,pose,anim,i,n,transform):
    t=i/max(1,n-1)
    if anim=='attack_side':
        for j,start in enumerate((.20,.40,.60)):
            age=t-start
            if age<0 or age>.43:continue
            u=age/.43
            # Use the emitter transform at launch, not its later recoiling pose.
            launch=transform_for(pose_for(anim,round(start*(n-1)),n))((103,-138))
            x,y=add(launch,(3+76*u,-4-20*u+42*u*u+j*1.5))
            if u>.85:
                # Disappears beyond the authored local effect, before frame edge.
                x-=9*smooth((u-.85)/.15)
            label(p,(x,y),-.35+u*.8+math.sin(u*math.tau)*.14,32,['TYPE A','TYPE B','SAME'][j])
    elif anim in ('hit','death'):
        if .08<t<.95:
            for j,word in enumerate(('TYPE A','?')):
                u=clamp((t-.08)/.87);x,y=transform((95,-130))
                label(p,(x+10+35*u+j*12,y-18*math.sin(math.pi*u)+70*u*u+j*12),u*(1.3+j*.5),27,word)


def render_frame(anim,i,n):
    pose=pose_for(anim,i,n); size=tuple(v*SUPER for v in FRAME_SIZE)
    img=Image.new('RGBA',size); world=Pen(img); tr=transform_for(pose); body=Pen(img,tr)
    active,hands=typing_keys(pose,anim)
    # Fixed foot plane across all body poses. The far leg goes behind the box.
    for side,x,lift in [(-1,pose.back,pose.back_lift),(1,pose.front,pose.front_lift)]:
        draw_leg(world,tr((side*44,11)),(ORIGIN[0]+x,GROUND-10-lift),side==1,pose.collapse)
    draw_cabinet(body,pose)
    draw_feed(body,pose)
    draw_keyboard(body,active)
    # Both shoulder sockets remain visible on the front frame; the arms are
    # rigidly articulated, and the hands follow the same transform as keys.
    for side in (-1,1):
        shoulder=tr((side*104,-37));target=tr(hand_target(side,pose,hands))
        target=(target[0],min(target[1],GROUND-16))
        hand,_=draw_arm(world,shoulder,target,side==1,1 if side==-1 else -1)
        h=next((a for a in hands if a[0]==side),None)
        if h and pose.arm_spread<.02:
            _,(x,y),press=h; finger=tr((x,y-4*(1-press)+2*press))
        else:finger=add(hand,rotate((side*-5,10),math.radians(pose.tilt)))
        finger=(finger[0],min(finger[1],GROUND-4))
        draw_hand(world,hand,finger,side)
    # Separate, slightly warm emission around VU/power lights, no neon wash.
    if pose.power>.03:
        glow=Image.new('RGBA',size);g=Pen(glow,tr)
        for x in (-65,55):g.oval((x,-20),13,4,alpha((120,226,169),.18*pose.meter*pose.power))
        g.oval((24,-20),3,3,alpha((255,116,75),.25*pose.power))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(2*SUPER)))
    if anim=='hit':
        k=math.sin(math.pi*i/max(1,n-1))
        for j in range(5):
            a=tr((108,-102+j*9));b=add(a,(8+10*k,-5-j*2))
            world.line([a,b],alpha((255,209,112),k),1.6)
    draw_ejected(world,pose,anim,i,n,tr)
    if pose.fade<1:img.putalpha(img.getchannel('A').point(lambda a:round(a*pose.fade)))
    return resize_transparent_sprite(img,FRAME_SIZE)


def _body_metrics(fw,fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    del opts
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,out_dir=Path(out_dir),
                        frame_size=FRAME_SIZE,auto_crop=False,actor_metadata=ACTOR_METADATA,
                        body_metrics_fn=_body_metrics,pose_bodies='authored',
                        animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[k]) for k in ('spritesheet','yaml','ron','actor','preview','canonical','canonical_transparent') if outputs.get(k)]


TARGETS={TARGET_NAME:{'render':render,'actor_metadata':ACTOR_METADATA}}
