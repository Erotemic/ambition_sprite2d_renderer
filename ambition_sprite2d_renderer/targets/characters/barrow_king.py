"""The Barrow King, a hand-drawn procedural boss for the rural opening.

Each frame uses the same articulated parts. The king carries the lamp in his
far hand and attacks with the near claw. The cape, crown, lamp, and spectral
light are not part of the physical body. The six rows match the melee actor
contract; the attack row has a windup, a low forward sweep, and a recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ...core.draw import blending_draw, resize_transparent_sprite
from ...core.measure import body_metrics_for_box

TARGET_NAME = "barrow_king"
FRAME_SIZE = (416, 336)
GROUND = 300
CX = 158
SUPER = 3
# The body excludes the crown points, cloak train, staff and effects.
BODY_BOX = (111, GROUND - 198, 205, GROUND + 1)
ROWS = [
    ("idle", 6, 140), ("walk", 8, 110), ("dash", 6, 70),
    ("attack_side", 16, 60), ("hurt", 3, 90), ("death", 12, 100),
]
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "The Barrow King"},
    "body": {
        "body_plan": "Humanoid", "body_kind": "Undead", "mass_class": "Medium",
        "traits": ["undead", "king", "barrow"], "locomotion_hint": "Walk",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["enemy", "undead", "hobford", "barrow"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "authoring_description": (
        "An ancient barrow-wight in royal armor, a crown, and a torn burgundy "
        "mantle. He collects modern electrical appliances as grave goods and "
        "holds a floor lamp as a royal sceptre. Original character based on "
        "the maintainer's concept sheet; the spectral claw is the existing "
        "melee attack, not a new combat ability."
    ),
}

INK = "#201a22"
INK2 = "#35252c"
WINE = "#702c45"
WINE_DARK = "#401e32"
WINE_LIGHT = "#9c4358"
WINE_HI = "#bb6170"
CLOTH = "#343b47"
CLOTH_DARK = "#222932"
CLOTH_HI = "#58626b"
FUR = "#c2b7a3"
FUR_DARK = "#82796f"
FUR_HI = "#e3d7bf"
GOLD = "#b98b47"
GOLD_DARK = "#6e4d2d"
GOLD_HI = "#edc77e"
GOLD_EDGE = "#fff0b1"
ARMOR = "#514e4b"
ARMOR_HI = "#827b69"
ARMOR_DARK = "#343335"
BONE = "#c6bda2"
BONE_DARK = "#847e6e"
BONE_HI = "#e5dac0"
HAIR = "#b2b4af"
HAIR_DARK = "#646e70"
HAIR_HI = "#dddcd0"
TEAL = (75, 202, 187, 255)
TEAL_HI = (194, 255, 236, 255)
TEAL_DARK = (29, 105, 110, 255)


def _lerp(a, b, t):
    return a + (b - a) * t


def _smooth(t):
    return t * t * (3 - 2 * t)


def _point(a, b, t):
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _rotate(p, angle):
    c, s = math.cos(angle), math.sin(angle)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _rgba(c, alpha):
    return (*c[:3], round(c[3] * max(0, min(1, alpha))))


def _curve(a, b, c, d, n=20):
    return [tuple((1-t)**3*a[j] + 3*(1-t)**2*t*b[j] + 3*(1-t)*t*t*c[j] + t**3*d[j]
                  for j in range(2)) for t in (i / n for i in range(n+1))]


class Pen:
    """Draw shapes in frame coordinates or in a local part coordinate system."""
    def __init__(self, image, transform=lambda p: p, *, scratch=False):
        self.image = image
        self.scratch = scratch
        # A private effect layer can be painted directly; composite it once.
        self.draw = ImageDraw.Draw(image) if scratch else blending_draw(image)
        self.transform = transform

    def local(self, origin, angle=0):
        return Pen(self.image, lambda p: self.transform(_add(origin, _rotate(p, angle))), scratch=self.scratch)

    def xy(self, p):
        x, y = self.transform(p)
        return (round(x * SUPER), round(y * SUPER))

    def poly(self, points, fill, outline=INK, width=1.4):
        pts = [self.xy(p) for p in points]
        self.draw.polygon(pts, fill=fill)
        if outline is not None and width > 0:
            self.draw.line(pts + pts[:1], fill=outline, width=max(1, round(width * SUPER)), joint="curve")

    def line(self, points, fill, width=1):
        self.draw.line([self.xy(p) for p in points], fill=fill,
                       width=max(1, round(width * SUPER)), joint="curve")

    def ellipse(self, center, radii, fill, outline=INK, width=1):
        # A polygon also supports rotated local coordinates.
        x, y = center
        rx, ry = radii
        self.poly([(x + rx*math.cos(i*math.tau/40), y + ry*math.sin(i*math.tau/40))
                   for i in range(40)], fill, outline, width)

    def curve(self, a, b, c, d, fill, width=1):
        self.line(_curve(a, b, c, d), fill, width)


def _segment(pen, a, b, width_a, width_b, fill, light, dark):
    """A tapered, shaded segment between two joints."""
    length = max(0.001, math.dist(a, b))
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    p = pen.local(a, angle)
    p.poly([(0,-width_a), (length,-width_b), (length,width_b), (0,width_a)], fill)
    p.poly([(0,-width_a+1), (length,-width_b+1), (length,-width_b*.28), (0,-width_a*.25)], light, None)
    p.poly([(0,width_a*.4), (length,width_b*.35), (length,width_b-1), (0,width_a-1)], dark, None)


def _glow(image, centers, radius, color, opacity):
    layer = Image.new("RGBA", image.size)
    p = Pen(layer, scratch=True)
    for center in centers:
        p.ellipse(center, (radius, radius), _rgba(color, opacity), None)
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * SUPER * .48)))


@dataclass(frozen=True)
class Pose:
    # Hip displacement and torso rotation (positive = lean forward).
    dx: float = 0
    dy: float = 0
    lean: float = .02
    head_tilt: float = 0
    near_foot: tuple[float, float] = (22, 0)
    far_foot: tuple[float, float] = (-25, 0)
    # Elbows and wrists, in the torso's coordinate system.
    near_elbow: tuple[float, float] = (-53, -38)
    near_wrist: tuple[float, float] = (-52, 5)
    far_elbow: tuple[float, float] = (64, -67)
    far_wrist: tuple[float, float] = (91, -57)
    staff_tilt: float = -.07
    claw_angle: float = 1.40
    cape: float = 0
    jaw: float = 0
    light: float = .8
    sweep: float = -1
    fade: float = 1


def _blend(a, b, t):
    t = _smooth(max(0, min(1, t)))
    values = {}
    for key, val in vars(a).items():
        other = getattr(b, key)
        values[key] = _point(val, other, t) if isinstance(val, tuple) else _lerp(val, other, t)
    return Pose(**values)


IDLE = Pose()
WINDUP = replace(IDLE, dx=-7, dy=3, lean=-.14, head_tilt=.06,
                 near_elbow=(-53,-109), near_wrist=(-26,-139), claw_angle=-1.85,
                 far_elbow=(62,-62), far_wrist=(87,-42), staff_tilt=.12,
                 cape=-9, jaw=.45, light=1)
STRIKE_START = replace(IDLE, dx=0, dy=5, lean=.14, near_elbow=(15,-67),
                       near_wrist=(54,-48), claw_angle=-.3,
                       far_wrist=(84,-46), staff_tilt=.10, cape=4, jaw=.85, light=1)
STRIKE_END = replace(IDLE, dx=8, dy=12, lean=.28, near_elbow=(8,-43),
                     near_wrist=(43,-12), claw_angle=.85,
                     far_elbow=(54,-71), far_wrist=(79,-59), staff_tilt=.15,
                     near_foot=(31,0), cape=15, jaw=.65, light=1)


def pose_for(animation, i, n):
    t = i / max(1, n)
    u = i / max(1, n-1)
    phase = math.tau*t
    wave = math.sin(phase)
    if animation == "idle":
        return replace(IDLE, dy=-1.2*wave, cape=3*wave, head_tilt=.015*wave,
                       staff_tilt=-.07+.025*wave, light=.78+.09*wave)
    if animation == "walk":
        # Alternating planted feet. The upper body carries the heavy mantle.
        near = (22 + 15*wave, -8*max(0, math.cos(phase)))
        far = (-25 - 15*wave, -8*max(0, -math.cos(phase)))
        return replace(IDLE, dy=-2*abs(wave), dx=2*wave, lean=.07+.03*wave,
                       near_foot=near, far_foot=far, cape=6*wave,
                       near_elbow=(-53,-38+5*wave), near_wrist=(-50+7*wave,5),
                       staff_tilt=-.06-.06*wave, light=.82)
    if animation == "dash":
        return replace(IDLE, dx=4, dy=3, lean=.24, cape=16+4*wave,
                       near_foot=(22+22*wave,-8*max(0, math.cos(phase))),
                       far_foot=(-25-22*wave,-8*max(0,-math.cos(phase))),
                       near_elbow=(-63,-62), near_wrist=(-85,-29),
                       staff_tilt=.20, far_wrist=(83,-58))
    if animation == "attack_side":
        if i < 4:
            return _blend(IDLE, WINDUP, i/3)
        if i < 7:
            return replace(WINDUP, light=.93+.035*(i-4), cape=-9+math.sin(i)*2)
        if i < 11:
            return replace(_blend(STRIKE_START, STRIKE_END, (i-7)/3), sweep=(i-7)/3)
        return _blend(STRIKE_END, IDLE, (i-10)/5)
    if animation == "hurt":
        k = 1-u
        return replace(IDLE, dx=-5*k, dy=5*k, lean=-.16*k, head_tilt=-.12*k,
                       near_elbow=(-55,-45), near_wrist=(-38,-8), jaw=k,
                       staff_tilt=.12*k-.07, cape=-7*k, light=.95)
    if animation == "death":
        k = _smooth(min(1, u/.63))
        return replace(IDLE, dx=-8*k, dy=22*k, lean=.40*k, head_tilt=.35*k,
                       near_elbow=(-39,-36), near_wrist=(-10,-5),
                       far_elbow=(59,-53), far_wrist=(87,-28),
                       staff_tilt=.78*k, near_foot=(33,0), far_foot=(-28,0),
                       cape=14*k, jaw=k, light=1-u*.75,
                       fade=1-max(0,(u-.63)/.37))
    raise ValueError(animation)


def draw_aura(p, pose, phase):
    # Thin, broken wisps behind the solid silhouette.
    layer = Image.new("RGBA", p.image.size)
    q = Pen(layer, p.transform, scratch=True)
    for i, (x,y) in enumerate([(-43,-92), (-38,-47), (-25,9)]):
        offset = math.sin(phase+i)*9
        a = (x,y)
        b = (x-44,y-18+offset)
        c = (x-21,y-38-offset)
        d = (x-73,y-43+offset)
        pts = _curve(a,b,c,d,26)
        for j in range(len(pts)-1):
            t = j/(len(pts)-1)
            q.line(pts[j:j+2], _rgba(TEAL,.38*(1-t)*pose.light), 7*(1-t)+.8)
            if j < 17:
                q.line(pts[j:j+2], _rgba(TEAL_HI,.22*(1-t)), 1.1)
    p.image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5*SUPER)))


def draw_cape(p, pose):
    # The train trails behind the body. Its bottom follows the ground rather
    # than swinging down through the floor during a lunge.
    s = pose.cape
    hem = [(-98-s*.5,64),(-81-s*.8,59),(-72-s*.7,69),(-55-s*.3,55),
           (-48,67),(-28,55),(-18,66),(0,50),(16,62),(29,38)]
    back = [(-46,-92),(-64,-73),(-70-s*.4,-20),(-83-s*.5,28)] + hem + [(38,-20),(43,-78),(25,-91)]
    p.poly(back, WINE_DARK, width=2.2)
    p.poly([(-45,-87),(-59,-69),(-66-s*.3,-5),(-80-s*.5,45),(-72-s*.7,59),
            (-45,43),(-37,-12),(-20,-85)], WINE, None)
    p.poly([(-30,-77),(-31,-18),(-48,51),(-29,55),(-13,20),(-4,-73)], WINE_LIGHT, None)
    p.poly([(9,-82),(17,-25),(9,40),(25,49),(35,-19),(39,-77)], WINE, None)
    for start, end in [((-56,-60),(-89-s*.4,57)),((-37,-68),(-48,52)),((-12,-59),(-19,52)),((24,-66),(27,39))]:
        p.curve(start, (start[0]-14,-15), (end[0]+8,24), end, WINE_DARK, 2.2)
        p.curve((start[0]+4,start[1]), (start[0]-8,-15), (end[0]+12,24), (end[0]+4,end[1]-5), WINE_HI, .8)
    # Tarnished gold border, with a repeated stitched diamond pattern.
    border = [(-49,-85),(-61,-57),(-64-s*.35,-15),(-77-s*.4,25),(-92-s*.5,60)]
    p.line(border,GOLD_DARK,4.8)
    p.line(border,GOLD,2.3)
    for i in range(6):
        y=-48+18*i
        x=-62-s*.22 - max(0,y+12)*.34
        p.poly([(x,y-4),(x+4,y),(x,y+4),(x-4,y)],GOLD_DARK,None)
        p.line([(x-2,y),(x,y-2),(x+2,y),(x,y+2),(x-2,y)],GOLD_HI,.8)
    # The king's tree device, embroidered into the outer mantle.
    crest = p.local((-48,-8))
    crest.line([(0,21),(1,-17)],GOLD,2)
    for x,y in [(-15,-9),(14,-13),(-10,-21),(7,-25),(-17,2),(12,1)]:
        crest.line([(0,9),(x*.6,y+6),(x,y)],GOLD,1.4)
        crest.line([(x*.6,y+6),(x+(-5 if x<0 else 5),y+5)],GOLD,.9)
    crest.line([(-9,25),(0,20),(10,25)],GOLD,1.4)
    for x,y in [(-75,41),(-34,36),(-61,16),(18,23)]:
        p.poly([(x-4,y-3),(x+2,y-5),(x+6,y+1),(x+2,y+5),(x-4,y+2)],CLOTH_DARK,INK2,.6)


def draw_leg(p, hip, knee, foot, near):
    # The greaves and boots remain visible under the long torn robes.
    col = ARMOR if near else ARMOR_DARK
    hi = ARMOR_HI if near else ARMOR
    _segment(p,hip,knee,15,12,CLOTH if near else CLOTH_DARK,CLOTH_HI if near else CLOTH,INK2)
    _segment(p,knee,(foot[0]-2,foot[1]-9),11,7,col,hi,ARMOR_DARK)
    p.ellipse(knee,(12,10),GOLD_DARK)
    p.poly([(knee[0]-9,knee[1]-5),(knee[0],knee[1]-10),(knee[0]+9,knee[1]-4),
            (knee[0]+5,knee[1]+6),(knee[0]-4,knee[1]+8)],col,GOLD,1.2)
    f = p.local(foot)
    f.poly([(-11,-20),(5,-21),(10,-10),(20,-5),(19,-1),(12,0),(-13,0),(-14,-5)],col,width=1.6)
    f.poly([(-10,-17),(3,-17),(8,-9),(17,-5),(1,-5),(-9,-7)],hi,None)
    f.line([(-13,-4),(19,-4)],GOLD_DARK,1.7)
    for x in [1,6,11]:
        f.line([(x,-10),(x+3,-5)],ARMOR_DARK,.9)


def draw_robe(p):
    p.poly([(-35,-15),(28,-13),(43,23),(44,50),(35,44),(30,63),(19,51),
            (11,63),(2,47),(-9,57),(-13,39),(-29,54),(-27,31),(-43,44),(-39,4)],CLOTH_DARK,width=1.8)
    p.poly([(-33,-12),(-17,-10),(-18,19),(-28,43),(-37,39),(-33,3)],CLOTH_HI,None)
    p.poly([(-12,-9),(13,-10),(19,39),(12,56),(2,43),(-9,53)],CLOTH,None)
    p.poly([(20,-9),(30,-9),(40,27),(42,45),(34,39),(29,57),(22,35)],CLOTH_HI,None)
    p.line([(-33,-12),(-31,13),(-38,38)],GOLD_DARK,3)
    p.line([(28,-10),(31,11),(41,44)],GOLD,2)
    p.poly([(-5,9),(0,4),(6,14),(2,24),(-4,19)],INK,None)
    p.poly([(26,32),(31,30),(35,36),(31,44),(25,40)],INK,None)


def arm_joints(shoulder, elbow, wrist):
    """Use the authored segment directions with fixed limb lengths."""
    def extend(a, b, length):
        return _point(a, b, length / max(.001, math.dist(a, b)))
    fore = (wrist[0]-elbow[0], wrist[1]-elbow[1])
    elbow = extend(shoulder, elbow, 43)
    return elbow, extend(elbow, _add(elbow, fore), 38)


def draw_arm(p, shoulder, elbow, wrist, near):
    col = WINE if near else WINE_DARK
    _segment(p, shoulder, elbow, 17, 11, col, WINE_LIGHT if near else WINE, WINE_DARK)
    # An armored sleeve ends in an exposed bony hand.
    p.ellipse(shoulder,(21,17),GOLD_DARK)
    p.poly([(shoulder[0]-18,shoulder[1]-6),(shoulder[0]-5,shoulder[1]-18),
            (shoulder[0]+14,shoulder[1]-14),(shoulder[0]+20,shoulder[1]-3),
            (shoulder[0]+12,shoulder[1]+12),(shoulder[0]-10,shoulder[1]+10)],ARMOR,GOLD,1.8)
    p.line([(shoulder[0]-13,shoulder[1]-6),(shoulder[0]-4,shoulder[1]-12),(shoulder[0]+12,shoulder[1]-8)],GOLD_HI,1.6)
    _segment(p,elbow,wrist,10,6,BONE if near else BONE_DARK,BONE_HI if near else BONE, BONE_DARK)
    theta=math.atan2(wrist[1]-elbow[1],wrist[0]-elbow[0])
    a=p.local(elbow,theta)
    a.poly([(1,-12),(20,-10),(29,-7),(27,7),(8,11),(0,12)],ARMOR,GOLD_DARK,1.4)
    a.line([(3,-9),(19,-7),(25,-5)],GOLD_HI,1.4)
    a.line([(2,8),(24,5)],GOLD,1.2)
    a.poly([(11,0),(16,-4),(21,0),(16,4)],GOLD_DARK,None)


def draw_claw(p,wrist,angle,spread):
    q=p.local(wrist,angle)
    q.poly([(-5,-7),(8,-12),(18,-7),(18,8),(6,13),(-5,6)],BONE,width=1.4)
    q.poly([(0,-5),(10,-7),(14,-3),(9,6),(2,7)],BONE_HI,None)
    for i,y in enumerate([-8,-2,4,9]):
        reach=16-abs(i-1.5)*3
        tip_y=y+(i-1.5)*spread
        pts=[(11,y),(22,y*.9),(22+reach*.58,tip_y-4),(22+reach,tip_y+4)]
        q.line(pts,INK,5.5)
        q.line(pts,BONE_DARK,3.8)
        q.line(pts[:-1],BONE_HI,2.1)
        q.poly([pts[-2],(pts[-1][0]+2,pts[-1][1]-1),pts[-1]],BONE_HI,None)
    q.line([(2,8),(6,17),(15,20),(19,15)],INK,6)
    q.line([(2,8),(6,17),(15,20),(19,15)],BONE,3.9)


def draw_staff(p, wrist, angle, light):
    # A single rigid lamp rotates around the grip. The electrical cord is
    # attached to its base and ends in a visibly unplugged two-pin plug.
    q=p.local(wrist,angle)
    q.poly([(-5,-83),(5,-83),(3,77),(0,84),(-3,77)],GOLD_DARK,width=1.5)
    q.line([(-2,-80),(-1,75)],GOLD_HI,1.6)
    q.line([(3,-79),(2,73)],GOLD,.9)
    for y in [-63,-43,-8,16,53,73]:
        q.ellipse((0,y),(6,3.3),GOLD,INK,1)
        q.line([(-4,y-1),(4,y-1)],GOLD_HI,1)
    for y in [-55,-48,-35,-28]:
        q.line([(-5,y),(5,y+8)],GOLD,1.5)
    q.ellipse((0,81),(11,4),GOLD_DARK,width=1.2)
    q.ellipse((0,79),(9,2.8),GOLD,GOLD_DARK,.8)
    cord=_curve((1,70),(15,78),(29,62),(23,51)) + _curve((23,51),(17,38),(30,31),(33,39))[1:]
    q.line(cord,INK,3.4)
    q.line(cord,"#7b6650",1.1)
    q.poly([(29,35),(36,33),(40,44),(33,47)],"#c1b9a0",INK,1)
    q.line([(33,46),(35,51)],GOLD_HI,1.5)
    q.line([(37,44),(39,49)],GOLD_HI,1.5)
    # Warm light, with a broad pleated lampshade that reads at game scale.
    center=q.transform((0,-103))
    _glow(p.image,[center],31,(250,182,78,255),.22*light)
    q.ellipse((0,-84),(10,4),GOLD,INK,1.2)
    q.poly([(-16,-127),(12,-128),(19,-115),(33,-88),(25,-83),(-26,-83),(-32,-88)],"#d09a53",width=1.8)
    q.poly([(-15,-124),(-7,-125),(-12,-88),(-26,-89)],"#edc67e",None)
    q.poly([(-7,-125),(5,-126),(13,-88),(-12,-88)],"#ffe5a4",None)
    q.poly([(5,-126),(12,-125),(28,-88),(13,-88)],"#e7b76f",None)
    for a,b in [((-16,-126),(-30,-88)),((-7,-125),(-12,-88)),((5,-126),(13,-88)),((12,-126),(30,-88))]:
        q.line([a,b],"#a77a42",1.3)
    q.line([(-30,-88),(-21,-84),(0,-83),(24,-84),(31,-88)],GOLD_DARK,3)
    q.line([(-29,-89),(-21,-86),(0,-85),(24,-86),(30,-89)],GOLD_HI,1.2)
    q.ellipse((0,-128),(9,2.7),GOLD,GOLD_DARK,1)
    for x in range(-25,26,5):
        q.line([(x,-83),(x+1,-78-abs(x)*.06)],GOLD,1)
        q.ellipse((x+1,-78-abs(x)*.06),(1.2,1.9),GOLD_HI,GOLD_DARK,.5)
    # The fingers overlap the shaft so the lamp cannot appear to float.
    q.poly([(-9,-9),(5,-9),(10,-5),(10,9),(1,12),(-9,6)],BONE,width=1.3)
    for y in [-6,-1,4,9]:
        q.line([(-4,y),(7,y+1),(8,y+4)],BONE_DARK,2.7)
        q.line([(-4,y-1),(6,y)],BONE_HI,1.7)


def draw_torso(p):
    # A broad cuirass and two overlapping skirt plates give the king weight.
    p.poly([(-45,-90),(-27,-99),(21,-97),(43,-84),(41,-51),(32,-24),
            (25,-5),(-26,-4),(-42,-31),(-50,-64)],ARMOR_DARK,width=2.1)
    p.poly([(-43,-79),(-23,-90),(0,-86),(-4,-32),(-26,-15),(-40,-34)],ARMOR_HI,None)
    p.poly([(0,-86),(23,-92),(37,-79),(38,-49),(26,-22),(-4,-32)],ARMOR,None)
    p.poly([(-33,-77),(-9,-69),(0,-56),(10,-70),(31,-80),(27,-43),(0,-29),(-27,-43)],ARMOR,GOLD_DARK,2)
    p.line([(-32,-76),(-9,-68),(0,-56),(11,-70),(30,-78)],GOLD_HI,2.2)
    p.line([(-24,-44),(0,-33),(25,-45)],GOLD,1.4)
    p.poly([(-14,-52),(0,-64),(14,-52),(0,-40)],GOLD_DARK,GOLD,1.3)
    p.poly([(-7,-52),(0,-58),(7,-52),(0,-46)],"#355f60",GOLD_HI,.8)
    for i in range(3):
        y=-35+i*9
        p.poly([(-30+i*2,y),(-1,y+8),(29-i*2,y),(26-i*2,y+7),(-1,y+14),(-27+i*2,y+7)],ARMOR_DARK,GOLD_DARK,1.3)
        p.line([(-26+i*2,y+2),(-1,y+10),(25-i*2,y+2)],ARMOR_HI,1.2)
    # Embossed border and rivets.
    for side in [-1,1]:
        p.curve((side*35,-77),(side*43,-54),(side*30,-34),(side*23,-12),GOLD,2.6)
        for i in range(4):
            p.ellipse((side*(35-i*3),-69+15*i),(1.8,1.8),GOLD_HI,GOLD_DARK,.5)
    p.poly([(-33,-13),(29,-13),(34,1),(23,9),(-24,10),(-35,3)],GOLD_DARK,width=1.5)
    p.line([(-32,-10),(29,-10)],GOLD_HI,2)
    p.ellipse((0,0),(14,12),GOLD,GOLD_DARK,2)
    p.poly([(-8,-4),(-5,-8),(6,-8),(10,-3),(7,3),(4,8),(-4,8),(-7,3)],ARMOR_DARK,GOLD_HI,.9)
    for x in [-3,4]:
        p.ellipse((x,-2),(2.1,2.5),INK,None)
    p.line([(-3,5),(-3,8),(3,8),(3,5)],GOLD_DARK,1)
    # A rectangular charger is worn on a chain as another grave good.
    p.curve((-31,-70),(-23,-30),(18,-30),(31,-70),GOLD_HI,1.7)
    pendant=p.local((14,-27),.21)
    pendant.poly([(-5,-7),(6,-7),(6,6),(-5,6)],"#c6bda9",INK,1)
    pendant.line([(-2,-7),(-2,-11)],GOLD_HI,1)
    pendant.line([(3,-7),(3,-11)],GOLD_HI,1)
    pendant.line([(-2,2),(3,2)],INK2,1.3)


def draw_fur(p):
    # Broad, irregular fur mantle: hand-drawn tufts rather than a smooth rim.
    top=[(-64,-81),(-59,-95),(-46,-91),(-43,-102),(-30,-97),(-21,-107),
         (-9,-101),(3,-108),(15,-102),(27,-105),(36,-96),(49,-99),(58,-88),(65,-82)]
    bottom=[(58,-66),(50,-72),(45,-60),(36,-66),(29,-58),(21,-69),(13,-63),(4,-75),
            (-7,-67),(-16,-74),(-26,-64),(-37,-71),(-42,-63),(-50,-72),(-58,-67),(-66,-79)]
    p.poly(top+bottom,FUR_DARK,width=1.8)
    p.poly(top+[(60,-77),(49,-72),(36,-78),(30,-68),(19,-78),(9,-73),(-3,-83),
                (-17,-77),(-27,-82),(-36,-74),(-46,-79),(-58,-73),(-64,-81)],FUR,None)
    for i in range(15):
        x=-57+i*8
        y=-89-5*math.cos(i*.65)
        p.poly([(x-4,y-3),(x+4,y-5),(x+1,y+7),(x-1,y+3)],FUR_HI,None)
        p.line([(x+4,y+1),(x+2,y+9)],FUR_DARK,1)
    # Large circular cloak clasps with a cross-knot relief.
    for x,y in [(-36,-73),(37,-72)]:
        p.ellipse((x,y),(12,12),GOLD_DARK,width=1.5)
        p.ellipse((x,y),(9.5,9.5),GOLD,GOLD_HI,1.2)
        p.ellipse((x,y),(6.8,6.8),ARMOR_DARK,GOLD_DARK,.7)
        for a in [0,math.pi/2,math.pi,math.pi*1.5]:
            p.poly([_add((x,y),_rotate((0,-2),a)),_add((x,y),_rotate((3,-6),a)),
                    _add((x,y),_rotate((0,-8),a)),_add((x,y),_rotate((-3,-6),a))],GOLD_HI,None)
        p.ellipse((x,y),(2.2,2.2),GOLD_HI,None)


def draw_head(p, pose, phase):
    # Asymmetric three-quarter skull, hair and crown. The beard follows the
    # head rather than moving independently of the jaw.
    q=p.local((5,-120),pose.head_tilt)
    sway=2*math.sin(phase)+pose.cape*.23
    hair=[(-25,-23),(-12,-31),(7,-31),(25,-20),(28,-2),(25,15),(28+sway,37),
          (18,31),(14+sway,45),(4,28),(-5+sway,42),(-11,25),(-23+sway,39),
          (-18,18),(-34+sway,30),(-30,10),(-39+sway,18),(-32,-7)]
    q.poly(hair,HAIR_DARK,width=1.7)
    for x,y in [(-27,-13),(-19,-20),(15,-20),(24,-8)]:
        q.poly([(x-4,y),(x+6,y-5),(x+3,12),(x+7+sway,29),(x-2+sway,21),(x-8,28),(x-5,5)],HAIR,None)
        q.curve((x,y),(x-5,1),(x+1,16),(x+1+sway,23),HAIR_HI,1.4)
    # Bone planes and dark eye sockets; the facing side is the brighter one.
    q.poly([(-21,-19),(-10,-27),(11,-26),(22,-16),(25,-4),(23,4),(17,10),
            (19,17),(10,23),(-6,21),(-13,13),(-21,8),(-25,-7)],BONE_DARK,width=1.7)
    q.poly([(-17,-17),(-7,-24),(11,-23),(21,-14),(23,-3),(14,2),(2,-5),
            (-8,-1),(-16,6),(-22,-2)],BONE,None)
    q.poly([(-7,-23),(9,-23),(17,-16),(4,-16),(-2,-8),(-13,-10)],BONE_HI,None)
    q.poly([(-18,-3),(-7,-8),(2,-3),(-1,7),(-10,10),(-17,6)],INK,width=.7)
    q.poly([(7,-4),(19,-9),(24,-4),(20,6),(11,8),(6,3)],INK,width=.7)
    # Glowing narrow eyes, not circular cartoon eyeballs.
    for x,y in [(-7,1),(16,0)]:
        _glow(p.image,[q.transform((x,y))],9,TEAL,.49*pose.light)
        q.poly([(x-4,y-1),(x+3,y-3),(x+4,y),(x-1,y+3)],_rgba(TEAL,pose.light),None)
        q.line([(x-2,y),(x+2,y-1)],TEAL_HI,1.8)
    q.poly([(3,0),(0,10),(5,13),(9,10),(7,3)],INK,None)
    q.poly([(-19,7),(-11,9),(-6,15),(-11,17),(-16,11)],BONE,None)
    q.poly([(18,8),(23,5),(22,12),(15,16),(10,13)],BONE_HI,None)
    drop=4+7*pose.jaw
    q.poly([(-8,15),(13,14),(14,21+drop),(8,25+drop),(-4,24+drop),(-10,19)],BONE_DARK,INK,1.2)
    q.poly([(-6,15),(13,14),(10,20+drop*.7),(-4,20+drop*.7)],INK,None)
    for x in [-5,0,5,10]:
        q.poly([(x,15),(x+3,15),(x+3,19),(x+.5,20)],BONE_HI,INK2,.5)
        q.line([(x,23+drop),(x,20+drop)],BONE,1.3)
    # Layered silver moustache, long forked beard, and weathered strands.
    q.poly([(-16,12),(-5,10),(2,14),(12,10),(23,11),(27,17),(17,17),(6,16),
            (-1,22),(-10,19),(-23,23)],HAIR_DARK,width=1)
    q.poly([(-16,12),(-5,11),(2,14),(-1,17),(-11,16),(-21,21)],HAIR_HI,None)
    q.poly([(6,14),(13,11),(23,12),(26,16),(17,15)],HAIR_HI,None)
    beard=[(-15,19),(-8,23),(1,19),(10,20),(18,17),(19,34),(12+sway,57),
           (5+sway,44),(-2+sway,62),(-6+sway,49),(-14+sway,54),(-11,39),(-21+sway,46),(-18,30)]
    q.poly(beard,HAIR_DARK,width=1.4)
    for x,y,end in [(-15,24,44),(-8,25,50),(-1,22,56),(6,23,45),(13,22,49)]:
        q.poly([(x-4,y),(x+4,y-3),(x+3,33),(x+sway+3,end-7),(x+sway,end),(x+sway-4,end-9),(x-5,33)],HAIR,None)
        q.curve((x,y),(x-2,32),(x+sway+2,end-10),(x+sway,end-4),HAIR_HI,1.3)
    # Tall irregular crown: brass band, arches, facets and dark red jewels.
    crown=[(-26,-20),(-30,-39),(-20,-34),(-23,-54),(-11,-41),(-8,-61),
           (0,-43),(7,-57),(14,-39),(25,-52),(23,-33),(34,-39),(28,-18)]
    q.poly(crown,GOLD_DARK,width=1.9)
    q.poly([(-24,-22),(-27,-36),(-18,-31),(-20,-49),(-10,-36),(-8,-56),
            (0,-39),(7,-52),(14,-35),(23,-47),(20,-29),(30,-35),(25,-20)],GOLD,None)
    for x,y in [(-23,-54),(-8,-61),(7,-57),(25,-52)]:
        q.poly([(x,y+4),(x+3,y+12),(x+1,y+22),(x-2,y+12)],GOLD_HI,None)
    q.poly([(-27,-29),(-13,-26),(4,-29),(20,-28),(31,-31),(28,-18),(11,-15),(-7,-16),(-25,-19)],GOLD_DARK,width=1.2)
    q.line([(-26,-28),(-12,-25),(4,-28),(20,-27),(30,-30)],GOLD_HI,2)
    q.line([(-25,-20),(-7,-17),(11,-16),(28,-19)],GOLD_HI,1.5)
    for x,y,r in [(-16,-25,5),(3,-25,8),(22,-26,5)]:
        q.poly([(x,y-r),(x+r*.7,y),(x,y+r),(x-r*.7,y)],GOLD_HI,INK2,1)
        q.poly([(x,y-r+2),(x+r*.5,y),(x,y+r-2),(x-r*.5,y)],"#863c48",None)
        q.poly([(x,y-r+2),(x-r*.5,y),(x,y+1)],"#d77875",None)
    for x,y in [(-25,-35),(-9,-39),(9,-38),(26,-35)]:
        q.ellipse((x,y),(2,2),GOLD_HI,GOLD_DARK,.7)


def draw_sweep(image, pose):
    if pose.sweep < 0:
        return
    # A low, forward slash. The brightest part follows the claw's swing.
    t=pose.sweep
    center=(CX+4,GROUND-103)
    start=-1.10+1.05*t
    end=start+.9
    pts=[]
    for i in range(25):
        u=i/24
        a=_lerp(start,end,u)
        r=88+12*math.sin(math.pi*u)
        pts.append((center[0]+r*math.cos(a),center[1]+r*math.sin(a)))
    layer=Image.new("RGBA", image.size)
    g=Pen(layer, scratch=True)
    g.line(pts,_rgba(TEAL,.48),16)
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(5*SUPER)))
    crisp=Image.new("RGBA", image.size)
    p=Pen(crisp, scratch=True)
    for i in range(len(pts)-1):
        u=i/(len(pts)-1)
        width=1+9*math.sin(math.pi*u)
        p.line(pts[i:i+2],_rgba(TEAL,.75),width)
        p.line(pts[i:i+2],_rgba(TEAL_HI,.92),max(.8,width*.22))
    for i in range(4):
        x,y=pts[5+i*5]
        p.line([(x-6,y-4),(x+2,y+1)],_rgba(TEAL_HI,.7),1.6)
    image.alpha_composite(crisp)


def render_frame(animation, index, nframes):
    pose=pose_for(animation,index,nframes)
    phase=math.tau*index/max(1,nframes)
    image=Image.new("RGBA",(FRAME_SIZE[0]*SUPER,FRAME_SIZE[1]*SUPER))
    p=Pen(image)
    hip=(CX+pose.dx,GROUND-70+pose.dy)
    torso=p.local(hip,pose.lean)
    # Keep the legs and the cloak hem near the ground while the upper body leans.
    def cape_transform(pt):
        x,y=torso.transform(pt)
        return (x,min(y,GROUND-2)) if pt[1]>25 else (x,y)
    draw_aura(torso,pose,phase)
    draw_cape(Pen(image,cape_transform),pose)
    for foot_local,near in [(pose.far_foot,False),(pose.near_foot,True)]:
        foot=(CX+foot_local[0],GROUND+foot_local[1])
        h=(hip[0]+(13 if near else -15),hip[1]-1)
        k=((h[0]+foot[0])/2+(6 if near else -5),(h[1]+foot[1])/2-2)
        draw_leg(p,h,k,foot,near)
    far_shoulder = (29,-81)
    far_elbow, far_wrist = arm_joints(far_shoulder, pose.far_elbow, pose.far_wrist)
    draw_arm(torso,far_shoulder,far_elbow,far_wrist,False)
    # Draw the lamp after the far arm; it must stay in front of the wrist.
    draw_staff(torso,far_wrist,pose.staff_tilt,pose.light)
    draw_robe(Pen(image,cape_transform))
    draw_torso(torso)
    near_shoulder = (-26,-77)
    near_elbow, near_wrist = arm_joints(near_shoulder, pose.near_elbow, pose.near_wrist)
    draw_arm(torso,near_shoulder,near_elbow,near_wrist,True)
    draw_fur(torso)
    draw_head(torso,pose,phase)
    draw_claw(torso,near_wrist,pose.claw_angle,3.2)
    draw_sweep(image,pose)
    if animation=="death" and index>4:
        u=index/max(1,nframes-1)
        for i in range(7):
            a=i*2.399
            x=hip[0]+math.cos(a)*(12+u*42)
            y=hip[1]-25-u*(28+(i%3)*16)
            p.ellipse((x,y),(2.4,4.5),_rgba(TEAL,(1-u)*.8),None)
    if pose.fade<1:
        # Multiply existing alpha. Never turn the transparent canvas opaque.
        image.putalpha(image.getchannel("A").point(lambda a: round(a*pose.fade)))
    return resize_transparent_sprite(image, FRAME_SIZE)


def _body_metrics(fw, fh):
    return body_metrics_for_box(BODY_BOX,fw,fh)


def render(out_dir: str | Path, **opts):
    # Keep the art coordinates and the authored collision rectangle in the
    # same frame space. Publication produces the lower quality tiers.
    del opts
    outputs=build_sheet(target=TARGET_NAME,rows=ROWS,render_fn=render_frame,
                        out_dir=Path(out_dir),frame_size=FRAME_SIZE,auto_crop=False,
                        actor_metadata=ACTOR_METADATA,body_metrics_fn=_body_metrics,
                        pose_bodies="authored",
                        animation_key_map={name:name for name,_,_ in ROWS})
    return [Path(outputs[k]) for k in ("spritesheet","yaml","ron","actor","preview","canonical","canonical_transparent") if outputs.get(k)]


TARGETS={TARGET_NAME:{"render":render,"actor_metadata":ACTOR_METADATA}}
