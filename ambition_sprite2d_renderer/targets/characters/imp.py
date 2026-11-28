"""A small horned imp with bat wings, cloven feet, and a barbed tail."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from ._magic_character_art import Canvas, add, bezier, phase, rot, track
from ._imp_front import paint_front, turn_frame
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = 'imp'
FRAME_SIZE = (220, 192)
BODY_BOX = (83, 52, 142, 150)
ROWS = [
    ('idle', 16, 60), ('walk', 16, 50), ('run', 16, 38), ('fly', 16, 50),
    ('turnaround', 3, 73), ('notice', 10, 35), ('aim', 16, 35), ('windup', 16, 35),
    ('shoot', 6, 30), ('hit', 9, 55), ('death', 20, 55),
]

ACTOR_METADATA = {
    'actor': {'character_id': TARGET_NAME, 'display_name': 'Imp'},
    'body': {'body_plan': 'Biped', 'body_kind': 'Floating',
             'mass_class': 'Light', 'locomotion_hint': 'Fly',
             'traits': ['enemy', 'fantasy', 'monster', 'imp', 'winged']},
    'brain': {'default_preset': 'skirmisher_ranger'},
    'actions': {'default_preset': 'imp_ember'},
    'visual': {'default_pose': 'idle', 'portrait': {'animation': 'idle', 'frame': 0}},
    'tags': ['enemy', 'fantasy', 'monster', 'imp', 'winged'],
    'authoring_description': (
        'A lean soot-dark imp with swept horns, pointed ears, sulfur eyes, '
        'dark membrane wings, cloven feet, and a long barbed tail.'),
    'gameplay_description': (
        'The imp flies around its target. Its throat glows before it spits an '
        'ember. It moves away during recovery.'),
    'animation_bindings': {
        'default': {'animation': 'idle', 'events': []},
        'locomotion.walk': {'animation': 'walk', 'events': []},
        'locomotion.run': {'animation': 'run', 'events': []},
        'locomotion.fly': {'animation': 'fly', 'events': []},
        'action.ranged.primary': {'animation': 'shoot', 'events': [
            {'t': 0.0, 'event': 'projectile_release', 'source': 'imp.ember'}]},
        'combat.hurt': {'animation': 'hit', 'events': []},
        'combat.death': {'animation': 'death', 'events': []},
    },
}

INK = '#21191f'
SKIN = '#514042'
SHADE = '#31242d'
LIGHT = '#77615e'
FAR = '#44343a'
HORN = '#a89477'
MEMBRANE = '#2d202d'
MEMBRANE_LIGHT = '#5d4a50'
EMBER = '#e48a3d'
EMBER_PALE = '#ffd488'


@dataclass(frozen=True)
class Pose:
    cycle: float
    bob: float = 0.0
    pitch: float = 0.0
    charge: float = 0.0
    spit: float = 0.0
    alarm: float = 0.0
    hurt: float = 0.0
    death: float = 0.0


def _pose(anim: str, i: int, n: int) -> Pose:
    t = phase(i, n, anim in ('idle', 'walk', 'run', 'fly'))
    p = math.tau * t
    if anim == 'idle':
        return Pose(p, 2.2 * math.sin(p))
    if anim in ('walk', 'fly', 'run'):
        return Pose(p, 2.0 * math.sin(p), 13.0 if anim == 'run' else 9.0)
    if anim == 'notice':
        u = track(t, [(0, 0), (.55, 1), (1, .5)])
        return Pose(p, -3 * u, -7 * u, alarm=u)
    if anim in ('aim', 'windup'):
        u = track(t, [(0, 0), (.8, 1), (1, 1)])
        return Pose(p, 0, -6 * u, charge=u)
    if anim == 'shoot':
        u = track(t, [(0, 1), (.3, .55), (1, 0)])
        return Pose(p, 0, -6 * u, charge=u * .65, spit=u)
    if anim == 'hit':
        u = math.sin(math.pi * t)
        return Pose(p, 2 * u, -23 * u, hurt=u)
    if anim == 'death':
        u = track(t, [(0, 0), (.08, .18), (.22, .56), (.55, .88), (1, 1)])
        return Pose(p, 6 * u, -34 * u, hurt=min(1.0, u * 1.2), death=u)
    raise ValueError(anim)


def _render_frame(anim: str, i: int, n: int):
    if anim == 'turnaround':
        return turn_frame(i, n, lambda: _render_frame('idle', 0, 16),
                          lambda: paint_front(FRAME_SIZE,
                              ((BODY_BOX[0]+BODY_BOX[2]-1)/2, 101), adult=False),
                          BODY_BOX)
    q = _pose(anim, i, n)
    c = Canvas(FRAME_SIZE)
    p = q.cycle
    origin = (110, 101 + q.bob)

    def P(x, y):
        return add(origin, rot((x, y), q.pitch))

    def poly(points, color, edge=INK, width=1.8):
        c.poly([P(*v) for v in points], color, edge, width)

    def line(points, color=INK, width=1.6):
        c.line([P(*v) for v in points], color, width)

    def oval(x, y, rx, ry, color, edge=INK, width=1.5, angle=0):
        c.oval(P(x, y), rx, ry, color, edge, width, angle + q.pitch)

    def path(start, *segments):
        pts = [start]
        for a, b, end in segments:
            pts.extend(bezier(pts[-1], a, b, end, 14)[1:])
        return pts

    def shape(start, *segments, color, edge=INK, width=1.8):
        poly(path(start, *segments), color, edge, width)

    # The tail attaches at the pelvis. The barb follows the last segment.
    sway = 7 * math.sin(p - .7) - 5 * q.death
    tip = (-61 + 6 * q.charge - 8 * q.death, 14 + sway + 10 * q.death)
    tail = path((-10, 20), ((-39, 36), (-68, 43), (-73, 29 + sway)),
                ((-80, 13 + sway), (-72, 12 + sway + 8 * q.death), tip))
    line(tail, INK, 8)
    line(tail, SHADE, 5.4)
    line(tail[:-5], SKIN, 2)
    poly([(tip[0] - 4, tip[1] - 6), (tip[0] + 11, tip[1] - 2),
          (tip[0] + 2, tip[1] + 9), (tip[0] + 1, tip[1] + 3),
          (tip[0] - 5, tip[1] + 2)], SKIN)

    # Each wing has a wrist and three fingers. The membrane curves between
    # the fingers. The same projected joints move the ribs and the outline.
    def wing(far):
        beat = math.sin(p + (.36 if far else 0))
        fold = .68 * q.death + .22 * q.hurt
        hinge = (-9, -15) if not far else (5, -19)
        span = (0.72 + .20 * math.cos(p)) * max(.18, (1 - fold))
        tilt = 14 * beat - 8 * q.charge + 58 * q.death
        if far:
            span *= .78
            tilt -= 18 + 8 * q.death
        def W(x, y):
            # The far wing extends on the opposite side of the back.
            return add(hinge, rot((x * span * (-1 if far else 1), y + 10 * q.death), tilt * (-1 if far else 1)))
        shoulder = W(0, 0)
        wrist = W(-45, -35 - 17 * beat)
        thumb = W(-41, -47 - 17 * beat)
        tips = [W(-84, -43 - 10 * beat), W(-73, -3 + 18 * beat),
                W(-42, 22 + 16 * beat), W(-10, 14)]
        outline = [shoulder, wrist, thumb, W(-48, -40 - 17 * beat), tips[0]]
        for a, b in zip(tips, tips[1:]):
            control_a = (a[0] * .66 + wrist[0] * .34, a[1] * .66 + wrist[1] * .34)
            control_b = (b[0] * .62 + wrist[0] * .38, b[1] * .62 + wrist[1] * .38)
            outline.extend(bezier(a, control_a, control_b, b, 12)[1:])
        outline.append(shoulder)
        poly(outline, '#231a24' if far else MEMBRANE, INK, 2.2)
        for k, (a, b) in enumerate(zip(tips, tips[1:])):
            a1 = (wrist[0] * .18 + a[0] * .82, wrist[1] * .18 + a[1] * .82)
            b1 = (wrist[0] * .18 + b[0] * .82, wrist[1] * .18 + b[1] * .82)
            poly([wrist, a1, ((a1[0] + b1[0]) / 2, (a1[1] + b1[1]) / 2), b1],
                 '#38262d' if far else (MEMBRANE_LIGHT if k == 0 else '#493940'), None)
        line([shoulder, wrist], INK, 6)
        line([shoulder, wrist], FAR if far else SKIN, 3.8)
        for tip in tips[:-1]:
            line([wrist, tip], '#322228' if far else '#3a292f', 2.3)
        line([wrist, thumb], INK, 3)
        line([wrist, thumb], HORN, 1.6)
        if not far:
            line([W(-6, -5), W(-22, -20), wrist], '#8a7267', 1.2)

    wing(True)
    wing(False)

    # The legs stay tucked during flight. Separate the near and far feet.
    def limb(points, radius, color, highlight):
        line(points, INK, 2 * radius + 2.2)
        line(points, color, 2 * radius)
        if highlight:
            line([(x - 1.5, y - 1.5) for x, y in points], highlight, max(1.0, radius * .5))

    def leg(far):
        swing = 2.5 * math.sin(p + (math.pi if far else 0))
        x = -7 if far else 9
        death_fold = 13 * q.death
        knee = (x + 8 + swing - 3 * q.death, 28 - 5 * q.charge + death_fold)
        ankle = (x - 3 + swing - 4 * q.death, 40 - 5 * q.charge + 14 * q.death)
        limb([(x, 16), knee, ankle], 5.0, FAR if far else SKIN, None if far else '#8a7267')
        ax, ay = ankle
        poly([(ax - 4, ay - 1), (ax + 3, ay - 2), (ax + 11, ay + 2),
              (ax + 12, ay + 7), (ax + 5, ay + 7), (ax + 2, ay + 5),
              (ax, ay + 7), (ax - 5, ay + 6)], '#34262a')
        line([(ax + 5, ay + 2), (ax + 4, ay + 6)], '#21191f', 1.3)

    leg(True)

    def arm(far):
        # The imp faces canvas-right. Its visible (near) shoulder is on
        # canvas-left; the far shoulder is on the muzzle side. Give each
        # arm a distinct pose, rather than translating a single silhouette.
        sway = math.sin(p + (1.0 if far else 0.0))
        recoil = max(q.hurt, q.death)
        if far:
            shoulder = (12, -13)
            elbow = (23 + 3 * q.death, 5 + 1.7 * sway + 5 * q.death)
            hand = (33 + 4 * q.charge + 3 * q.spit + 6 * q.death,
                    2 - 6 * q.charge - 3 * q.spit + 12 * q.death)
        else:
            shoulder = (-13, -12)
            elbow = (-29 - 3 * recoil, -1 + 2 * sway + 2 * q.death)
            hand = (-25 + 2 * q.charge - 14 * q.death,
                    13 - 5 * q.charge - 7 * q.death + 1.7 * sway)
        color = FAR if far else SKIN
        limb([shoulder, elbow, hand], 4.6, color,
             None if far else '#8a7267')
        # Orient the palm and claws along the forearm; keep them on their
        # own side of the body even as the elbow and wrist change pose.
        hx, hy = hand
        dx, dy = hx - elbow[0], hy - elbow[1]
        angle = math.atan2(dy, dx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        def H(u, v):
            return (hx + u * cos_a - v * sin_a,
                    hy + u * sin_a + v * cos_a)
        oval(hx, hy, 5.8, 4.7, color, angle=math.degrees(angle))
        for k in range(3):
            v = (k - 1) * 3.0
            spread = (k - 1) * (1.1 + 1.7 * q.death)
            reach = 7.5 + 1.8 * q.death - abs(k - 1) * .9
            poly([H(2.4, v - 1.35), H(5.2, v + spread - 1.2),
                  H(reach, v + spread + .7), H(4.0, v + 1.2)],
                 '#80694e' if far else HORN, INK, 1)

    # Canvas-right (far) arm is behind both the torso and the face.
    arm(True)
    # Lean torso and paler belly, behind the near arm and leg.
    shape((-13, -22), ((-4, -28), (14, -22), (16, -11)),
          ((19, 1), (7, 7), (11, 18)), ((8, 25), (-9, 25), (-14, 17)),
          ((-20, 7), (-22, -13), (-13, -22)), color=SKIN)
    shape((-6, -17), ((1, -21), (13, -12), (13, -4)),
          ((10, 6), (4, 7), (6, 17)), ((-5, 22), (-11, 10), (-10, 0)),
          ((-11, -7), (-10, -14), (-6, -17)), color=LIGHT, edge=None)
    line([(-9, 0), (-2, 2), (5, 0)], SHADE, 1.3)
    line([(-8, 8), (-2, 10), (4, 8)], SHADE, 1.3)
    leg(False)
    # Canvas-left (near) arm overlays the torso, not the face.
    arm(False)

    # Horns and the far ear are behind the head. Horn ridges follow the curve.
    def horn(x, y, far):
        shape((x - 6, y + 3), ((x - 11, y - 10), (x - 19, y - 15), (x - 12, y - 27)),
              ((x - 12, y - 17), (x + 4, y - 14), (x + 5, y - 2)),
              ((x + 2, y + 2), (x - 3, y + 5), (x - 6, y + 3)),
              color='#88745d' if far else HORN)
        line([(x - 7, y - 6), (x + 1, y - 9)], '#655248', 1.4)
        line([(x - 11, y - 13), (x - 5, y - 16)], '#655248', 1.3)

    horn(15, -39, True)
    poly([(16, -36), (41, -43), (31, -24), (19, -19)], FAR)
    poly([(23, -32), (35, -39), (28, -27)], '#5f4a49', None)
    horn(-10, -40, False)
    # Angular cheek, brow, muzzle and jaw; a readable three-quarter face.
    shape((-21, -38), ((-8, -49), (12, -47), (22, -36)),
          ((27, -30), (24, -27), (30, -23)), ((36, -20), (34, -14), (25, -13)),
          ((22, -3), (11, 2), (-1, -1)), ((-16, -2), (-25, -15), (-24, -27)),
          ((-24, -33), (-23, -36), (-21, -38)), color=SKIN, width=2.2)
    shape((-19, -31), ((-10, -41), (5, -42), (17, -34)),
          ((9, -35), (-2, -31), (-8, -24)), ((-14, -20), (-19, -25), (-19, -31)),
          color=LIGHT, edge=None)
    poly([(-22, -29), (-45, -42), (-39, -17), (-22, -13)], SKIN)
    poly([(-26, -27), (-39, -36), (-35, -21), (-25, -19)], SHADE, None)
    line([(-40, -36), (-34, -26), (-26, -22)], '#8a7267', 1.3)

    # Eyes: the brows, not the pupils, supply the expression.
    if q.hurt > .22 or q.death > .2:
        squint = max(q.hurt, q.death)
        line([(-12, -28), (-1, -22), (8, -28)], INK, 2.8)
        line([(15, -29), (21, -23), (26, -26)], INK, 2.5)
        line([(-15, -32), (-3, -31), (8, -27)], SHADE, 3.2)
        line([(14, -31), (25, -34)], SHADE, 2.5)
        if squint < .65:
            oval(4, -24, 1.2, 1.8, '#e8d86e', None)
            oval(20, -25, 1.0, 1.4, '#e8d86e', None)
    else:
        wide = 2.5 * q.alarm
        poly([(-11, -29 - wide), (10, -25 - wide), (7, -19 + wide), (-6, -19 + wide)], '#e9d16e', INK, 1.6)
        poly([(15, -27 - wide), (25, -29 - wide), (24, -22 + wide), (17, -20 + wide)], '#e9d16e', INK, 1.3)
        oval(4, -24, 2.1, 4.2 + wide * .4, '#372229', None)
        oval(21, -25, 1.35, 3.3 + wide * .4, '#372229', None)
        line([(-13, -32 - wide), (0, -31 - wide), (11, -26 - wide)], SHADE, 3.7)
        line([(15, -29 - wide), (24, -33 - wide)], SHADE, 2.8)
    oval(28, -22, 2.1, 1.4, SHADE, None)

    # The throat and mouth warn of the shot. Do not draw the projectile here:
    # the combat system publishes the actual projectile at the authored muzzle.
    glow = max(q.charge, q.spit)
    if glow > .05:
        oval(19, -9, 9 + 2 * glow, 8 + 2 * glow, '#7c4a33', None)
        oval(23, -10, 6 * glow, 5 * glow, EMBER, None)
    if q.death > .08:
        scream = q.death
        oval(21, -11, 8 + 2.0 * scream, 5.2 + 2.8 * scream, '#2a1518', INK, 1.7)
        poly([(14, -16), (18, -14), (16, -10)], '#e6d4b2', INK, .8)
        poly([(24, -16), (27, -15), (25, -11)], '#e6d4b2', INK, .8)
        line([(11, -11), (18, -8), (27, -9)], '#4a2328', 1.6)
    elif q.spit > .05:
        oval(29, -12, 6 + 2 * q.spit, 4 + 3 * q.spit, '#301a1e', INK, 1.7)
        oval(30, -11, 3.5 * q.spit, 3 * q.spit, EMBER_PALE, None)
        poly([(24, -17), (27, -16), (26, -12)], '#f0d9ac', INK, .8)
    elif q.charge > .05:
        line([(14, -12), (25, -12), (31, -15)], '#4c292a', 3.4)
        line([(23, -12), (30, -14)], EMBER, 1.6 + 1.4 * q.charge)
    elif q.hurt > .18:
        line([(11, -10), (20, -7), (29, -13)], INK, 2.4)
        poly([(20, -10), (24, -11), (22, -6)], '#f0d9ac', INK, .8)
        line([(3, -11), (8, -9)], SHADE, 1.4)
    else:
        line([(10, -11), (19, -9), (28, -13)], INK, 2.3)
        poly([(19, -10), (23, -11), (21, -6)], '#f0d9ac', INK, .8)
        line([(2, -10), (7, -8)], SHADE, 1.4)

    im = c.finish()
    if q.death > 0:
        fade = min(1.0, max(0.0, (1.0 - phase(i, n, False)) / .36))
        im.putalpha(im.getchannel('A').point(lambda a: round(a * fade)))
    return im


def render(out_dir: str | Path, **opts):
    del opts
    out = build_sheet(
        target=TARGET_NAME, rows=ROWS, render_fn=_render_frame,
        out_dir=Path(out_dir), frame_size=FRAME_SIZE, auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda w, h: body_metrics_for_box(BODY_BOX, w, h),
        animation_key_map={name: name for name, _, _ in ROWS},
        pose_bodies='authored', sits_on_ground=False,
    )
    return [out[k] for k in ('spritesheet', 'yaml', 'ron', 'actor', 'preview',
                              'canonical', 'canonical_transparent')]
