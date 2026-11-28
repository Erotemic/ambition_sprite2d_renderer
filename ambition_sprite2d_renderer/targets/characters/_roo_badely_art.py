"""Roo Badely's wallaroo art on the Pirate Admiral's existing fighter rig.

All points are in the pirate rig's paint coordinates. The hands, feet,
weapon and joints retain the shared rig. The tail and the accessories do
not have attack sockets. The head, coat and tail have their own contours.
"""
from __future__ import annotations

import math

from ...authoring.sheet_build import circle, line, poly, transform
from ...core.measure import body_metrics_for_box

INK = (21, 19, 26, 255)
FUR = (51, 45, 50, 255)
FUR_SHADE = (33, 29, 37, 255)
FUR_LIGHT = (79, 70, 74, 255)
MUZZLE = (123, 111, 106, 255)
GREY = (125, 117, 115, 255)
EAR = (108, 77, 79, 255)
SCAR = (206, 137, 118, 255)
SCAR_EDGE = (112, 66, 68, 255)
EYE = (245, 219, 173, 255)
NAVY = (38, 38, 65, 255)
NAVY_LIGHT = (62, 59, 93, 255)
NAVY_DARK = (25, 25, 43, 255)
GOLD = (232, 176, 54, 255)
GOLD_DARK = (151, 96, 34, 255)
GOLD_LIGHT = (255, 222, 127, 255)
RED = (168, 40, 44, 255)
RED_DARK = (100, 27, 41, 255)
IVORY = (238, 220, 184, 255)
LEATHER = (83, 54, 43, 255)
PANTS = (70, 54, 49, 255)


def curve(start, *segments, steps=10):
    """Sample cubic contours. The same points serve paint and floor placement."""
    out = [start]
    for a, b, end in segments:
        x, y = out[-1]
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            out.append((u**3*x + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*end[0],
                        u**3*y + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*end[1]))
    return out


def oval(x, y, rx, ry, n=24):
    return [(x + rx * math.cos(math.tau * i / n), y + ry * math.sin(math.tau * i / n)) for i in range(n)]


def _shape(draw, start, segments, fill, edge=None, width=2):
    poly(draw, curve(start, *segments), fill, edge, width=width)


# Broad jaw and short, blunt wallaroo muzzle. The grey marking is part of
# the fur, not a separate beard. The eye scar crosses the brow and cheek.
_HEAD = curve((-28, -5), ((-32, -21), (-21, -34), (-5, -35)),
              ((9, -38), (24, -30), (28, -16)), ((33, -11), (40, -8), (49, -4)),
              ((54, 1), (52, 14), (44, 20)), ((37, 28), (19, 31), (9, 28)),
              ((-3, 27), (-10, 22), (-19, 22)), ((-24, 17), (-28, 7), (-28, -5)))
_FRONT_HEAD = curve((-30, -8), ((-33, -24), (-17, -36), (0, -36)),
                    ((18, -36), (32, -24), (30, -8)), ((34, 1), (31, 15), (24, 21)),
                    ((14, 34), (-14, 34), (-24, 21)), ((-32, 15), (-34, 1), (-30, -8)))
_THREEQ_HEAD = curve((-29, -7), ((-32, -24), (-18, -35), (-2, -35)),
                     ((16, -35), (31, -28), (35, -14)), ((40, -8), (44, -3), (45, 3)),
                     ((43, 13), (36, 23), (26, 26)), ((14, 30), (3, 29), (-7, 27)),
                     ((-17, 25), (-26, 18), (-30, 9)), ((-31, 2), (-31, -2), (-29, -7)))
_HAT = curve((-51, -19), ((-43, -33), (-36, -43), (-28, -49)),
             ((-17, -43), (-7, -41), (0, -45)), ((9, -53), (19, -59), (26, -55)),
             ((34, -41), (45, -34), (54, -21)), ((36, -17), (13, -23), (-4, -24)),
             ((-24, -23), (-39, -17), (-51, -19)))
_FRONT_HAT = curve((-49, -20), ((-41, -37), (-31, -45), (-25, -49)),
                   ((-12, -44), (-5, -42), (0, -46)), ((8, -48), (18, -54), (25, -49)),
                   ((36, -42), (43, -31), (49, -20)), ((32, -17), (15, -24), (0, -25)),
                   ((-15, -24), (-32, -17), (-49, -20)))
_THREEQ_HAT = curve((-50, -20), ((-42, -36), (-31, -45), (-21, -48)),
                    ((-10, -43), (-3, -43), (6, -46)), ((16, -50), (28, -49), (39, -38)),
                    ((46, -30), (51, -25), (52, -19)), ((32, -16), (14, -22), (0, -24)),
                    ((-16, -24), (-33, -18), (-50, -20)))


# Articulation helpers return a local drawing and an independently placed
# pivot. The same fixed contours are used by the floor solver and the painter.
# No pose-dependent vertices in these moving parts.
def _placed(points, origin, angle):
    return [transform(pt, origin, angle) for pt in points]


def _view(anim, index, count):
    if anim != 'turnaround' or count < 2:
        return 1.0
    return max(-1., min(1., 2 * index / (count - 1) - 1))


_EAR_OUTER = curve((-10,0), ((-20,-15),(-21,-42),(-10,-51)),
                   ((1,-55),(13,-24),(10,-5)), ((7,5),(-5,7),(-10,0)))
_EAR_INNER = curve((-6,-3), ((-13,-18),(-16,-39),(-10,-43)),
                   ((-3,-40),(6,-20),(5,-5)), ((2,0),(-3,1),(-6,-3)))
_BANDANA_LONG = curve((0,-4), ((-13,-5),(-26,2),(-37,14)),
                      ((-25,12),(-16,10),(-8,7)), ((-4,4),(0,3),(0,-4)))
_BANDANA_SHORT = curve((0,-3), ((-12,2),(-20,14),(-23,27)),
                       ((-13,22),(-6,14),(2,4)), ((5,0),(4,-3),(0,-3)))


def _ear_parts(pose, view):
    # Ear roots move around the skull at a turn, but never change anatomical
    # track identity. Both ears have the same reusable local outline.
    droop = (13 if pose.get('mouth_open',0) >= .6 else 0)
    droop += max(-12., min(12., pose.get('head_tilt',0)*.4))
    droop += max(-10., min(10., pose.get('coat_sway',0)*.25))
    for side in (-1,1):
        near = side == -1 if view >= 0 else side == 1
        root = (side*(18-3*abs(view))-2*view, -31+2*side*view)
        angle = side*12 + view*8 + droop
        # Depth order changes, but the texture does not change with pose.
        yield ('roo_ear_left' if side < 0 else 'roo_ear_right', root, angle,
               _EAR_OUTER, _EAR_INNER, near)


def _bandana_parts(pose, view):
    sway = max(-28., min(28., pose.get('coat_sway',0)*.65))
    # At the front the knot remains behind the skull; when turning it moves
    # to the old/new rear cheek. Local ribbons rotate, rather than warp.
    side = -1 if view < 0 else 1
    root = (-27*view,-8)
    for name, outline, lag in (('roo_head_bandana_long',_BANDANA_LONG,sway),
                                ('roo_head_bandana_short',_BANDANA_SHORT,sway*.6-8)):
        # Fixed left/right artwork variants only at the view change.
        pts = [(side*x,y) for x,y in outline]
        yield name, root, side*lag, pts


def head_bounds(pose):
    """Bounds for the normal view used by the floor and portrait solvers."""
    ears = [(_placed(outline, root, angle), 2)
            for _,root,angle,outline,_,_ in _ear_parts(pose,1.)]
    ribbons = [(_placed(outline, root, angle), 2)
               for _,root,angle,outline in _bandana_parts(pose,1.)]
    return [(_HEAD, 2), *ears, *ribbons], [(_HAT, 2)]


def draw_head(draw, center, face_angle, hat_angle, pose, anim, index, count):
    view = _view(anim, index, count)
    side = -1 if view < 0 else 1
    abs_view = abs(view)

    def flip(points):
        return [(side * x, y) for x, y in points]

    def P(points, color, edge=None, width=2):
        poly(draw, flip(points), color, edge, width=width)

    def L(points, color, width=2):
        line(draw, flip(points), color, width=width)

    def O(x, y, rx, ry, color, edge=None, width=2):
        P(oval(x, y, rx, ry), color, edge, width)

    for name, root, angle, outline in _bandana_parts(pose,view):
        with draw.part(name, transform(root, center, face_angle), face_angle+angle):
            poly(draw, outline, RED, INK, width=3)
            line(draw, [outline[0],outline[len(outline)//3]], RED_DARK, width=2)

    # Painter order follows projected depth; the two persistent identities
    # do not swap when one ear passes in front of the other.
    ears = sorted(_ear_parts(pose,view), key=lambda part: part[-1])
    for name, root, angle, outer, inner, near in ears:
        with draw.part(name, transform(root,center,face_angle), face_angle+angle):
            poly(draw, outer, FUR, INK, width=3)
            poly(draw, inner, EAR)
            line(draw, [(-11,-39),(-7,-20)], FUR_LIGHT, width=2)

    with draw.part('face', center, face_angle):
        if abs_view < 0.25:
            P(_FRONT_HEAD, FUR, INK, 3)
            P(curve((-25, -5), ((-20, -20), (-13, -20), (-5, -14)), ((4, -6), (17, -12), (24, -5)),
                    ((30, 4), (27, 21), (17, 26)), ((7, 33), (-9, 33), (-20, 25)), ((-26, 19), (-29, 6), (-25, -5))), MUZZLE)
            P([(-11, -1), (0, -4), (11, -1), (7, 6), (0, 9), (-7, 6)], INK)
            eyes = [(-15, -13, 8), (15, -13, 8)]
            scar_x = 15
            mouth = [(-11, 16), (0, 14), (11, 16)]
            whisker = [(11, 22), (17, 24)]
            cheek = [(-12, 6), (-8, 5)]
        elif abs_view < 0.75:
            P(_THREEQ_HEAD, FUR, INK, 3)
            P(curve((-24, -3), ((-20, 15), (-9, 24), (11, 27)), ((22, 27), (26, 17), (26, 10)),
                    ((27, 4), (30, 0), (34, -1)), ((39, 1), (41, 8), (36, 16)),
                    ((29, 24), (17, 29), (7, 26)), ((0, 24), (-2, 12), (0, 2)),
                    ((-5, -7), (-12, -16), (-17, -18)), ((-23, -15), (-26, -9), (-24, -3))), MUZZLE)
            P(curve((-21, -3), ((-18, -10), (-11, -10), (-6, -8)), ((-1, -5), (2, -1), (0, 4)),
                    ((-3, 10), (-9, 13), (-13, 16)), ((-18, 14), (-21, 8), (-21, -3))), GREY)
            P(curve((31, -2), ((35, -2), (39, 0), (41, 4)), ((40, 8), (35, 10), (30, 7)), ((28, 4), (29, 0), (31, -2))), INK)
            eyes = [(-6, -13, 5), (12, -12, 9)]
            scar_x = 10
            mouth = [(8, 16), (17, 14), (28, 15)]
            whisker = [(10, 22), (15, 25)]
            cheek = [(-12, 5), (-8, 3)]
            L([(28, -1), (33, 1)], FUR_LIGHT, 2)
            L([(30, 8), (29, 13)], FUR_SHADE, 2)
        else:
            P(_HEAD, FUR, INK, 3)
            P(curve((-27, -3), ((-26, 14), (-17, 25), (8, 28)), ((15, 26), (13, 19), (6, 10)),
                    ((-7, -3), (-11, -20), (-14, -25)), ((-24, -20), (-27, -12), (-27, -3))), FUR_SHADE)
            P(curve((15, -4), ((24, -8), (34, -3), (46, 0)), ((53, 3), (50, 14), (43, 20)),
                    ((33, 28), (18, 30), (9, 25)), ((4, 20), (7, 10), (15, -4))), MUZZLE)
            P(curve((-23, -3), ((-19, -11), (-13, -8), (-6, -7)), ((-2, -1), (-3, 3), (-7, 8)),
                    ((-1, 7), (3, 10), (5, 12)), ((-1, 14), (-8, 15), (-10, 17)),
                    ((-14, 14), (-17, 16), (-20, 11)), ((-26, 8), (-28, 1), (-23, -3))), GREY)
            P(curve((37, -3), ((43, -4), (49, -2), (52, 1)), ((52, 5), (48, 9), (43, 6)), ((40, 4), (39, 1), (37, -3))), INK)
            L([(43, -1), (48, 1)], FUR_LIGHT, 2)
            L([(44, 8), (43, 13)], FUR_SHADE, 2)
            eyes = [(6, -12, 12)]
            scar_x = 5
            mouth = [(20, 17), (29, 15), (39, 16), (44, 14)]
            whisker = [(9, 23), (16, 26)]
            cheek = [(-16, 4), (-12, 2)]
        # The healed scar is wider at the cheek. It crosses the eye without
        # obscuring the pupil. Small creases at the brow and mouth show age.
        P([(scar_x + 1, -29), (scar_x - 4, -19), (scar_x - 1, -15), (scar_x - 7, -5),
           (scar_x - 13, 11), (scar_x - 6, 4), (scar_x + 3, -13), (scar_x + 2, -18), (scar_x + 5, -27)], SCAR_EDGE)
        P([(scar_x + 2, -28), (scar_x - 1, -19), (scar_x + 1, -15), (scar_x - 5, -5),
           (scar_x - 11, 9), (scar_x - 5, 2), (scar_x + 4, -14), (scar_x + 3, -18), (scar_x + 5, -27)], SCAR)
        if abs_view >= 0.75:
            L(whisker, FUR_LIGHT, 2)
            L(cheek, MUZZLE, 2)
            L([(15, 9), (13, 13)], FUR_SHADE, 2)
        elif abs_view >= 0.25:
            L(whisker, FUR_LIGHT, 2)
            L(cheek, MUZZLE, 2)
            L([(10, 10), (9, 13)], FUR_SHADE, 2)
        # A little red fabric beneath the hat.
        P([(-26, -20), (-17, -29), (16, -28), (26, -21), (12, -24), (-14, -22)], RED, INK, 2)

    # Eye/lid and mouth substitutions are separate from the head's rigid
    # contour. A blink must not interrupt the head's motion between poses.
    for i,(ex,ey,w) in enumerate(eyes):
        name = 'roo_eye_near' if i == len(eyes)-1 else 'roo_eye_far'
        origin=transform((side*ex,ey),center,face_angle)
        with draw.part(name,origin,face_angle):
            h = 6.5 if pose.get('wide') else 4.3
            if pose.get('x_eyes'):
                L([(-w*.6,-4),(w*.6,4)],INK,3)
                L([(-w*.6,4),(w*.6,-4)],INK,3)
            elif pose.get('blink'):
                L([(-w,0),(0,2),(w,-1)],INK,3)
            else:
                P(curve((-w,0),((-w*.4,-h),(w*.5,-h),(w,-1)),
                        ((w*.55,h),(-w*.25,h+1),(-w,0))),EYE,INK,2)
                O(min(4,w*.3),.4,2.8,3.5,INK)
            L([(-w-2,-5),(0,-7),(w+1,-4)],FUR_LIGHT,3)
            L([(-w+1,7),(w*.5,8)],FUR_SHADE,2)
    mx,my = mouth[0]
    local = [(x-mx,y-my) for x,y in mouth]
    with draw.part('roo_mouth',transform((side*mx,my),center,face_angle),face_angle):
        L(local,INK,2)
        if pose.get('mouth_open',0) > .25:
            a,b=local[0],local[-1]
            mid=((a[0]+b[0])/2,max(a[1],b[1])+8*pose['mouth_open'])
            P([a,*local[1:],mid],INK)
            if pose['mouth_open'] > .55:
                L([(a[0]+3,a[1]+1),(b[0]-3,b[1]+2)],IVORY,2)

    with draw.part('hat', center, hat_angle):
        hat_shape = _FRONT_HAT if abs_view < 0.25 else _THREEQ_HAT if abs_view < 0.75 else _HAT
        P(hat_shape, NAVY, INK, 4)
        P(curve((-49, -20), ((-32, -23), (-19, -31), (0, -32)),
                ((18, -32), (35, -23), (51, -21)), ((30, -19), (12, -23), (0, -26)),
                ((-20, -25), (-32, -18), (-49, -20))), NAVY_DARK)
        L([(-46, -22), (-32, -42), (-27, -47), (-10, -42), (0, -46), (25, -54), (34, -41), (49, -23)], GOLD, 4)
        L([(-45, -23), (-33, -39), (-28, -44)], GOLD_LIGHT, 2)
        # Skull and crossed bones on the captain's hat.
        x = 10 if abs_view >= 0.75 else 5 if abs_view >= 0.25 else 0
        y = -39
        L([(x - 7, y + 5), (x + 7, y + 12)], IVORY, 3)
        L([(x + 7, y + 5), (x - 7, y + 12)], IVORY, 3)
        O(x, y, 6.2, 6.0, IVORY)
        P([(x - 3, y + 3), (x + 3, y + 3), (x + 3, y + 7), (x - 3, y + 7)], IVORY)
        O(x - 2.5, y - 1, 1.4, 1.5, INK)
        O(x + 2.5, y - 1, 1.4, 1.5, INK)


# Overlapping tapered tail sections. The distal part's rounded base sits
# under the proximal part's rounded end; their rotation tracks can tween.
_TAIL_ROOT = curve((-10,-10), ((-29,-10),(-42,11),(-61,29)),
                   ((-74,40),(-73,51),(-60,53)),
                   ((-40,49),(-24,29),(-8,16)), ((1,6),(-2,-6),(-10,-10)))
_TAIL_TIP = curve((9,-10), ((-8,-4),(-25,1),(-44,-6)),
                  ((-54,-10),(-59,-15),(-59,-15)),
                  ((-56,1),(-35,13),(-15,13)),
                  ((0,13),(11,7),(12,0)), ((14,-5),(12,-9),(9,-10)))
_TAIL_JOINT = (-63,41)


def tail_angle(pose):
    tilt = pose['body_tilt']
    fold = 60 * math.exp(-((abs(tilt)-90)/25)**2)
    return tilt + pose['coat_sway']*.45 - fold


def tail_parts(pose, hip=(0.,0.), view=1.):
    # Tail lags the body's turn, with a curved distal follow-through. Normal
    # facing remains the original guard silhouette. No signed-scale tween.
    angle = tail_angle(pose)
    bend = max(-25., min(25., pose['coat_sway']*.6))
    # Discrete projected sections are only selected in the five-view turn.
    # A frontal tail lies behind the body instead of swinging across it.
    v = abs(view)
    side = -1 if view < 0 else 1
    if v < .25:
        root=curve((-10,-10),((-23,-3),(-27,13),(-25,28)),
                   ((-26,40),(-12,43),(-9,31)),((-7,19),(-2,9),(-2,0)),
                   ((-1,-8),(-4,-11),(-10,-10)))
        tip=curve((4,-8),((-5,-4),(-14,1),(-22,1)),
                  ((-22,10),(-9,16),(1,11)),((8,8),(9,-3),(4,-8)))
        joint0=(-19,30)
    elif v < .75:
        root=curve((-10,-10),((-28,-8),(-35,10),(-44,28)),
                   ((-54,40),(-50,50),(-40,51)),((-24,45),(-15,24),(-7,15)),
                   ((1,5),(-2,-6),(-10,-10)))
        tip=curve((7,-9),((-4,-6),(-17,1),(-33,-7)),
                  ((-37,-10),(-40,-12),(-40,-12)),((-35,6),(-20,13),(-6,13)),
                  ((8,12),(13,0),(7,-9)))
        joint0=(-42,39)
    else:
        root,tip,joint0=_TAIL_ROOT,_TAIL_TIP,_TAIL_JOINT
    # Reflect the *local* drawings only at an authored view change. There
    # is never an interpolated signed scale or affine warp of a sprite.
    root=[(side*x,y) for x,y in root]
    tip=[(side*x,y) for x,y in tip]
    joint=transform((side*joint0[0],joint0[1]),hip,angle)
    return [('roo_tail_tip',joint,angle+side*bend,tip),
            ('roo_tail_root',hip,angle,root)]


def draw_tail(draw, hip, pose, view=1.):
    for name, root, deg, outline in tail_parts(pose,hip,view):
        with draw.part(name,root,deg):
            poly(draw,outline,FUR,INK,width=3)
            # Long highlight follows each curved segment, staying inside the
            # contour. A joint is overlapped by the thicker root section.
            if abs(view) < .75:
                continue
            side = -1 if view < 0 else 1
            if name == 'roo_tail_root':
                pts=curve((-12,-5),((-34,7),(-49,30),(-63,35)),steps=8)
            else:
                pts=curve((-9,0),((-24,4),(-42,-3),(-53,-9)),steps=8)
            line(draw,[(side*x,y) for x,y in pts],FUR_LIGHT,width=4)


def coat_tail_outline(side, b):
    return [(side * 44 * b, -14), (side * 9, -14), (side * 12, 38), (side * 25, 49), (side * 38 * b, 43)]


def draw_coat_tails(draw, hip, tilt, sway, b):
    for side in (-1, 1):
        name = 'coat_tail_left' if side < 0 else 'coat_tail_right'
        with draw.part(name, hip, tilt - side * sway):
            pts = coat_tail_outline(side, b)
            poly(draw, pts, NAVY if side < 0 else NAVY_LIGHT, INK, width=4)
            poly(draw, [(side * 12, 33), (side * 25, 43), (side * 38 * b, 37), (side * 38 * b, 43), (side * 25, 49), (side * 12, 38)], GOLD)
            line(draw, [(side * 37 * b, -5), (side * 34 * b, 34)], NAVY_DARK, width=2)
    with draw.part('roo_sash_tail', hip, tilt - sway * .8):
        poly(draw, [(10, -18), (22, -18), (25, 27), (19, 41), (14, 35), (8, 39), (12, 15)], RED, INK, width=2)
        line(draw, [(19, -13), (17, 18), (19, 30)], RED_DARK, width=2)


def draw_torso(draw, chest, tilt, pal, look):
    b = look.build
    with draw.part('torso', chest, tilt):
        poly(draw, [(-42 * b, -14), (-30 * b, -29), (28 * b, -29), (40 * b, -14), (37 * b, 34),
                   (42 * b, 68), (0, 76), (-44 * b, 68), (-39 * b, 34)], NAVY, INK, width=5)
        poly(draw, [(24 * b, -25), (37 * b, -12), (35 * b, 32), (39 * b, 64), (26 * b, 70)], NAVY_DARK)
        poly(draw, [(-15, -25), (16, -25), (21, 43), (-14, 45)], IVORY, INK, width=3)
        # Open high collar and gold piping. The panels meet at the sash.
        poly(draw, [(-31, -28), (-13, -27), (-4, 8), (-18, 34), (-29, 10)], NAVY_LIGHT, INK, width=3)
        poly(draw, [(15, -27), (29, -28), (30, 8), (20, 34), (6, 10)], NAVY_LIGHT, INK, width=3)
        line(draw, [(-15, -25), (-5, 8), (-16, 31)], GOLD, width=3)
        line(draw, [(15, -25), (7, 10), (20, 31)], GOLD, width=3)
        poly(draw, [(21 * b, -28), (33 * b, -22), (-29 * b, 36), (-37 * b, 28)], LEATHER, INK, width=3)
        poly(draw, [(-9, 2), (-1, -6), (8, 2), (0, 10)], GOLD, INK, width=2)
        poly(draw, [(-4, 2), (-1, -1), (3, 2), (0, 5)], LEATHER)
        for x in (-26, 26):
            for y in (20, 32):
                circle(draw, (x, y), 2.7, GOLD, INK, width=1)
        poly(draw, [(-41 * b, 35), (38 * b, 35), (40 * b, 51), (-43 * b, 51)], RED, INK, width=3)
        line(draw, [(-36 * b, 40), (34 * b, 39)], RED_DARK, width=2)
        poly(draw, [(-40 * b, 37), (37 * b, 37), (38 * b, 46), (-41 * b, 46)], LEATHER, INK, width=2)
        poly(draw, [(-9, 32), (9, 32), (9, 49), (-9, 49)], GOLD, INK, width=2)
        poly(draw, [(-4, 36), (4, 36), (4, 45), (-4, 45)], LEATHER)
        # Epaulettes remain at the original shoulder sockets.
        for side in (-1, 1):
            poly(draw, [(side * 48 * b, -11), (side * 45 * b, -27), (side * 25 * b, -32), (side * 23 * b, -19)], GOLD, INK, width=3)
            line(draw, [(side * 27 * b, -25), (side * 43 * b, -22)], GOLD_LIGHT, width=2)
            for k in range(3):
                x = side * (29 + 7 * k) * b
                line(draw, [(x, -15 - k), (x + side * 1.5, -6 - k)], GOLD, width=3)


def draw_gear(draw, hip, tilt, pose):
    # Chain and watch share a pendulum frame at the actual belt attachment.
    # The coil has its own attachment and angle. No re-rasterized chain/coil
    # geometry is needed for any pose, even when the torso is rolling.
    sway = max(-36., min(36., pose['coat_sway']*.85))
    anchor = transform((8,-23), hip, tilt)
    with draw.part('roo_watch', anchor, tilt+sway):
        line(draw,[(0,0),(-5,10),(4,19),(9,23)],GOLD_DARK,width=4)
        line(draw,[(0,0),(-5,10),(4,19),(9,23)],GOLD_LIGHT,width=2)
        circle(draw,(9,25),12,GOLD,INK,width=2)
        circle(draw,(9,25),8.5,IVORY,GOLD_DARK,width=2)
        line(draw,[(9,19),(9,25),(13,27)],INK,width=2)
        for dx,dy in ((0,-7),(7,0),(0,7),(-7,0)):
            circle(draw,(9+dx,25+dy),.9,GOLD_DARK)
    anchor = transform((-27,-17),hip,tilt)
    with draw.part('roo_string',anchor,tilt+sway*.65):
        for shift in (-2,2):
            pts=curve((shift,0),((-11+shift,6),(-12+shift,25),(-3+shift,29)),
                      ((6+shift,30),(9+shift,9),(shift,0)))
            line(draw,pts,GOLD_DARK,width=4)
            line(draw,pts,IVORY,width=2)
        line(draw,[(-4,2),(4,4)],LEATHER,width=3)


def body_metrics(w, h):
    """Keep the original admiral's standing body and weapon scale.

    The new ears, tail and carried watch must not change the existing
    collision rectangle or the hand sockets' world scale. The reference
    box is measured from the original published 224 x 164 idle frame.
    """
    x0, y0, x1, y1 = (82, 35, 167, 149)
    return body_metrics_for_box((round(x0 * w / 224), round(y0 * h / 164),
                                 round(x1 * w / 224), round(y1 * h / 164)), w, h)
