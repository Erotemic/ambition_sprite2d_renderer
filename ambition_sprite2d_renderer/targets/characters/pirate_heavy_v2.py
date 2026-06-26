from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

TARGET_NAME = 'pirate_heavy_v2'
LABEL_WIDTH = 100
FRAME_W = 256
FRAME_H = 256
SUPER = 4
ROWS = [
    ('idle', 6, 125),
    ('walk', 8, 92),
    ('attack', 7, 82),
    ('fly', 6, 92),
]

# Palette
OUTLINE = (24, 18, 22, 255)
OUTLINE_SOFT = (52, 39, 48, 255)
SKIN = (168, 112, 85, 255)
SKIN_HI = (213, 156, 120, 255)
SKIN_SH = (116, 78, 63, 255)
HAIR = (70, 44, 37, 255)
HAIR_HI = (122, 83, 59, 255)
COAT = (91, 50, 115, 255)
COAT_HI = (127, 81, 154, 255)
COAT_SH = (56, 32, 72, 255)
CRIMSON = (166, 39, 46, 255)
CRIMSON_DK = (110, 26, 31, 255)
GOLD = (214, 167, 63, 255)
GOLD_HI = (246, 214, 112, 255)
CREAM = (235, 218, 188, 255)
CREAM_SH = (193, 170, 140, 255)
PANTS = (53, 74, 126, 255)
PANTS_HI = (84, 108, 168, 255)
PANTS_SH = (34, 48, 84, 255)
BOOT = (89, 58, 40, 255)
BOOT_HI = (132, 87, 58, 255)
BOOT_SH = (56, 35, 25, 255)
WHITE = (248, 241, 227, 255)


def _yaml_scalar(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if v is None:
        return 'null'
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == '' or any(ch in s for ch in ':#[]{}\n"\'') or s.strip() != s:
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _yaml_dump(obj, indent=0):
    pad = ' ' * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(_yaml_dump(v, indent + 2))
            else:
                lines.append(f"{pad}{k}: {_yaml_scalar(v)}")
        return '\n'.join(lines)
    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                dumped = _yaml_dump(item, indent + 2).splitlines()
                if dumped:
                    lines.append(f"{pad}- {dumped[0].lstrip()}")
                    lines.extend(dumped[1:])
                else:
                    lines.append(f"{pad}-")
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
        return '\n'.join(lines)
    return f"{pad}{_yaml_scalar(obj)}"


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: tuple[float, float]) -> tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _rot(x: float, y: float, deg: float) -> tuple[float, float]:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _poly(draw, pts, fill, outline=OUTLINE, width=1.1):
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline:
        draw.line(ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint='curve')


def _line(draw, pts, fill, width=1.0):
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint='curve')


def _ellipse(draw, cx, cy, rx, ry, fill, outline=OUTLINE, width=1.0):
    draw.ellipse((_s(cx-rx), _s(cy-ry), _s(cx+rx), _s(cy+ry)), fill=fill, outline=outline, width=max(1, _s(width)))


def _rect(draw, x0, y0, x1, y1, fill, outline=OUTLINE, width=1.0):
    draw.rectangle((_s(x0), _s(y0), _s(x1), _s(y1)), fill=fill, outline=outline, width=max(1, _s(width)))


def _path_poly(origin, pts, deg=0.0):
    out = []
    for x, y in pts:
        rx, ry = _rot(x, y, deg)
        out.append((origin[0] + rx, origin[1] + ry))
    return out


class Pose:
    def __init__(self, anim: str, idx: int, count: int):
        # base settings
        self.root_x = 0.0
        self.root_y = 0.0
        self.body_bob = 0.0
        self.body_tilt = -4.0
        self.head_tilt = 0.0
        self.head_yaw = 0.0
        self.near_arm = 0.0
        self.far_arm = 0.0
        self.near_forearm = 0.0
        self.far_forearm = 0.0
        self.near_leg = 0.0
        self.far_leg = 0.0
        self.near_knee = 0.0
        self.far_knee = 0.0
        self.near_lift = 0.0
        self.far_lift = 0.0
        self.coat_sway = 0.0
        self.sash_sway = 0.0
        self.attack_push = 0.0
        self.attack_raise = 0.0
        self.blink = False
        self.mouth_open = 0.0
        self.fly = False

        t = idx / max(1, count - 1)
        phase = 2 * math.pi * idx / max(1, count)
        s = math.sin(phase)
        c = math.cos(phase)

        if anim == 'idle':
            self.body_bob = s * 1.8
            self.body_tilt = -6.0 + s * 1.4
            self.head_tilt = -2.0 + c * 1.2
            self.head_yaw = -2.0 + s * 1.0
            self.near_arm = 0.0 + s * 3.0
            self.far_arm = 0.0 - s * 2.0
            self.near_forearm = -65.0
            self.far_forearm = 20.0
            self.coat_sway = s * 2.5
            self.sash_sway = c * 3.0
            self.blink = idx == count - 2
        elif anim == 'walk':
            self.root_x = s * 3.5
            self.body_bob = abs(s) * 3.2 - 1.2
            self.body_tilt = -7.0 + s * 3.2
            self.head_tilt = -1.5 - s * 1.5
            self.head_yaw = -4.0 + s * 0.8
            self.near_arm = 5.0 + 10.0 * s
            self.far_arm = -2.0 - 10.0 * s
            self.near_forearm = -58.0 - 8.0 * s
            self.far_forearm = 18.0 + 8.0 * s
            self.near_leg = -18.0 * s
            self.far_leg = 18.0 * s
            self.near_knee = 16.0 * max(0.0, s)
            self.far_knee = 16.0 * max(0.0, -s)
            self.near_lift = 10.0 * max(0.0, s)
            self.far_lift = 10.0 * max(0.0, -s)
            self.coat_sway = -s * 6.0
            self.sash_sway = -s * 8.0
        elif anim == 'attack':
            # Heavy forward shove / punch attack, no weapon.
            tt = 0.5 - 0.5 * math.cos(math.pi * t)
            hit = math.sin(tt * math.pi)
            self.root_x = -4.0 + tt * 10.0
            self.body_bob = -hit * 2.0
            self.body_tilt = -12.0 + tt * 18.0
            self.head_tilt = -4.0 + tt * 4.0
            self.head_yaw = -5.0 + tt * 2.5
            self.near_arm = -5.0 + tt * 10.0
            self.near_forearm = -60.0 + tt * 5.0
            self.far_arm = -18.0 + tt * 55.0
            self.far_forearm = 12.0 - tt * 50.0
            self.near_leg = -5.0 - hit * 4.0
            self.far_leg = 8.0 + hit * 2.0
            self.near_knee = 6.0 + hit * 6.0
            self.far_knee = 2.0
            self.attack_push = tt * 16.0
            self.attack_raise = hit * 4.0
            self.coat_sway = 9.0 - tt * 10.0
            self.sash_sway = 6.0 - tt * 14.0
            self.mouth_open = 0.15 + hit * 0.2
        elif anim == 'fly':
            self.fly = True
            self.root_y = -6.0 + s * 2.0
            self.body_bob = s * 1.5
            self.body_tilt = -9.0 + s * 3.5
            self.head_tilt = -1.0 + c * 1.0
            self.head_yaw = -4.0
            self.near_arm = -6.0 + s * 3.0
            self.far_arm = 4.0 - s * 3.0
            self.near_forearm = -62.0
            self.far_forearm = 18.0
            self.near_leg = -20.0
            self.far_leg = 15.0
            self.near_knee = 20.0
            self.far_knee = 16.0
            self.near_lift = 16.0 + max(0.0, s) * 3.0
            self.far_lift = 12.0 + max(0.0, -s) * 3.0
            self.coat_sway = 10.0 + s * 5.0
            self.sash_sway = 8.0 + c * 5.0


def _leg_points(hip, thigh_len, shin_len, thigh_angle, knee_angle, foot_angle, foot_lift=0.0):
    knee = (hip[0] + _rot(0, thigh_len, thigh_angle)[0], hip[1] + _rot(0, thigh_len, thigh_angle)[1])
    ankle = (knee[0] + _rot(0, shin_len, thigh_angle + knee_angle)[0], knee[1] + _rot(0, shin_len, thigh_angle + knee_angle)[1] - foot_lift)
    toe = (ankle[0] + _rot(12, 2, foot_angle)[0], ankle[1] + _rot(12, 2, foot_angle)[1])
    heel = (ankle[0] + _rot(-5, 1, foot_angle)[0], ankle[1] + _rot(-5, 1, foot_angle)[1])
    return knee, ankle, toe, heel


def _arm_points(shoulder, upper_len, lower_len, upper_angle, lower_angle):
    elbow = (shoulder[0] + _rot(0, upper_len, upper_angle)[0], shoulder[1] + _rot(0, upper_len, upper_angle)[1])
    hand = (elbow[0] + _rot(0, lower_len, upper_angle + lower_angle)[0], elbow[1] + _rot(0, lower_len, upper_angle + lower_angle)[1])
    return elbow, hand


def draw_frame(anim: str, idx: int, count: int) -> Image.Image:
    pose = Pose(anim, idx, count)
    img = Image.new('RGBA', (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')

    root = (126.0 + pose.root_x, 191.0 + pose.root_y + pose.body_bob)
    pelvis = root
    chest = (pelvis[0] - 3.0, pelvis[1] - 62.0)
    neck = (chest[0] + 9.0, chest[1] - 26.0)
    head = (neck[0] + 19.0, neck[1] - 2.0)

    near_hip = (pelvis[0] - 11.0, pelvis[1] - 8.0)
    far_hip = (pelvis[0] + 8.0, pelvis[1] - 7.0)
    near_shoulder = (chest[0] - 30.0, chest[1] - 3.0)
    far_shoulder = (chest[0] + 22.0, chest[1] - 9.0)

    # Legs and feet
    near_knee, near_ankle, near_toe, near_heel = _leg_points(near_hip, 36.0, 34.0, pose.near_leg, pose.near_knee, 4.0, pose.near_lift)
    far_knee, far_ankle, far_toe, far_heel = _leg_points(far_hip, 35.0, 32.0, pose.far_leg, pose.far_knee, 2.0, pose.far_lift)

    # Arms
    near_elbow, near_hand = _arm_points(near_shoulder, 26.0, 23.0, 68 + pose.near_arm, pose.near_forearm)
    far_elbow, far_hand = _arm_points(far_shoulder, 30.0, 24.0, 332 + pose.far_arm, pose.far_forearm)

    # Back leg behind body
    _poly(d, [
        (far_hip[0]-8, far_hip[1]-3), (far_hip[0]+8, far_hip[1]-2),
        (far_knee[0]+7, far_knee[1]), (far_knee[0]-7, far_knee[1]+2),
        (far_ankle[0]-6, far_ankle[1]), (far_ankle[0]+7, far_ankle[1]-2),
    ], PANTS_SH)
    _poly(d, [
        (far_ankle[0]-8, far_ankle[1]-3), (far_ankle[0]+6, far_ankle[1]-4),
        (far_toe[0]+3, far_toe[1]+1), (far_toe[0], far_toe[1]+5),
        (far_heel[0]-2, far_heel[1]+5), (far_heel[0]-5, far_heel[1]+1),
    ], BOOT_SH)
    _rect(d, far_ankle[0]-9, far_ankle[1]-10, far_ankle[0]+6, far_ankle[1]-3, BOOT)
    _rect(d, far_ankle[0]-2, far_ankle[1]-6, far_ankle[0]+3, far_ankle[1]-1, GOLD, width=0.7)

    # Coat tails behind
    sway = pose.coat_sway
    _poly(d, [(pelvis[0]-24, pelvis[1]-15), (pelvis[0]-2, pelvis[1]-22), (pelvis[0]-7+sway*0.2, pelvis[1]+35), (pelvis[0]-30+sway*0.5, pelvis[1]+37)], COAT_SH)
    _poly(d, [(pelvis[0]+6, pelvis[1]-20), (pelvis[0]+28, pelvis[1]-11), (pelvis[0]+33+sway*0.5, pelvis[1]+34), (pelvis[0]+9+sway*0.2, pelvis[1]+32)], COAT_SH)
    _poly(d, [(pelvis[0]-4, pelvis[1]-21), (pelvis[0]+8, pelvis[1]-17), (pelvis[0]+13+sway*0.3, pelvis[1]+30), (pelvis[0]+1+sway*0.2, pelvis[1]+31)], CRIMSON_DK)

    # Torso / coat
    torso = _path_poly(chest, [(-38, -7), (-28, -29), (-4, -40), (22, -35), (40, -18), (45, 8), (33, 34), (8, 41), (-17, 38), (-36, 27), (-45, 8)], pose.body_tilt)
    _poly(d, torso, COAT)
    blouse = _path_poly((chest[0]+1, chest[1]-1), [(-20, -18), (-2, -29), (15, -24), (22, -8), (18, 20), (0, 26), (-19, 18), (-23, 2)], pose.body_tilt)
    _poly(d, blouse, CREAM)
    _line(d, _path_poly((chest[0]+1, chest[1]-3), [(-1, -18), (0, 20)], pose.body_tilt), CREAM_SH, 0.9)
    # cleavage and blouse folds for female read
    _line(d, _path_poly((chest[0]+1, chest[1]-2), [(-9, -8), (-1, 2), (-5, 14)], pose.body_tilt), CREAM_SH, 0.8)
    _line(d, _path_poly((chest[0]+1, chest[1]-2), [(8, -10), (2, 2), (6, 14)], pose.body_tilt), CREAM_SH, 0.8)

    # Collar and lapels
    _poly(d, _path_poly(chest, [(-31,-4), (-24,-23), (-13,-22), (-11,-1), (-22,13), (-34,8)], pose.body_tilt), COAT_SH)
    _poly(d, _path_poly(chest, [(15,-22), (30,-17), (38,-2), (31,10), (17,1), (12,-10)], pose.body_tilt), COAT_SH)
    _line(d, _path_poly(chest, [(-25,-20), (-31,-3), (-23,12)], pose.body_tilt), GOLD_HI, 0.8)
    _line(d, _path_poly(chest, [(16,-19), (31,-4), (29,10)], pose.body_tilt), GOLD_HI, 0.8)

    # Belt / sash
    belt = _path_poly((pelvis[0]-2, pelvis[1]-31), [(-31, -5), (26, -5), (27, 5), (-30, 6)], pose.body_tilt * 0.4)
    _poly(d, belt, CRIMSON_DK)
    _rect(d, pelvis[0]-7, pelvis[1]-39, pelvis[0]+8, pelvis[1]-22, GOLD)
    _rect(d, pelvis[0]-2, pelvis[1]-34, pelvis[0]+3, pelvis[1]-27, (92, 61, 37, 255), width=0.8)
    _poly(d, [(pelvis[0]+7, pelvis[1]-28), (pelvis[0]+21, pelvis[1]-27), (pelvis[0]+20+pose.sash_sway*0.4, pelvis[1]+4), (pelvis[0]+8, pelvis[1]+5)], CRIMSON)
    _poly(d, [(pelvis[0]+14, pelvis[1]-27), (pelvis[0]+28, pelvis[1]-25), (pelvis[0]+31+pose.sash_sway*0.7, pelvis[1]+2), (pelvis[0]+18, pelvis[1]+5)], CRIMSON_DK)

    # Buttons / trim
    for dx, dy in [(-22,-10), (-18,2), (24,-6), (20,7)]:
        pt = _path_poly(chest, [(dx, dy)], pose.body_tilt)[0]
        _ellipse(d, pt[0], pt[1], 1.8, 1.8, GOLD_HI, width=0.6)

    # Back arm behind torso
    _line(d, [far_shoulder, far_elbow], COAT_SH, 8.5)
    _line(d, [far_elbow, far_hand], COAT_SH, 7.5)
    _ellipse(d, far_hand[0], far_hand[1], 4.5, 4.5, SKIN, width=0.8)

    # Head / neck
    _rect(d, neck[0]-5, neck[1]-1, neck[0]+6, neck[1]+11, SKIN_SH)
    _ellipse(d, head[0], head[1], 21, 23, SKIN)
    # face plane / profile to right
    _poly(d, [(head[0]-3, head[1]-18), (head[0]+10, head[1]-16), (head[0]+18, head[1]-9), (head[0]+20, head[1]-2), (head[0]+15, head[1]+7), (head[0]+5, head[1]+12), (head[0]-5, head[1]+10), (head[0]-10, head[1]+2), (head[0]-9, head[1]-9)], SKIN_HI, outline=None)
    # nose and lips
    nose = [(head[0]+17, head[1]-4), (head[0]+26, head[1]-1), (head[0]+18, head[1]+3)]
    _poly(d, nose, SKIN)
    if pose.blink:
        _line(d, [(head[0]+8, head[1]-6), (head[0]+13, head[1]-6)], OUTLINE, 1.0)
    else:
        _ellipse(d, head[0]+11, head[1]-6, 2.2, 1.8, OUTLINE, outline=None)
    _line(d, [(head[0]+5, head[1]-11), (head[0]+14, head[1]-12)], OUTLINE, 1.0)
    mouth_y = head[1] + 10
    _line(d, [(head[0]+7, mouth_y), (head[0]+15, mouth_y + pose.mouth_open * 6)], (109, 44, 49, 255), 1.0)
    _line(d, [(head[0]+10, mouth_y), (head[0]+13, mouth_y)], WHITE, 0.7)

    # hair, earring, bandana
    _poly(d, [(head[0]-16, head[1]-10), (head[0]-12, head[1]-22), (head[0]-1, head[1]-25), (head[0]+10, head[1]-21), (head[0]+18, head[1]-12), (head[0]+16, head[1]-2), (head[0]+6, head[1]-7), (head[0]-3, head[1]-10)], HAIR)
    _poly(d, [(head[0]-18, head[1]+1), (head[0]-26, head[1]+10), (head[0]-21, head[1]+21), (head[0]-11, head[1]+15), (head[0]-11, head[1]+4)], HAIR)
    _line(d, [(head[0]-6, head[1]-18), (head[0]+2, head[1]-22), (head[0]+11, head[1]-17)], HAIR_HI, 0.8)
    _ellipse(d, head[0]-16, head[1]+6, 4, 5.5, GOLD_HI, width=0.8)
    _poly(d, [(head[0]-22, head[1]-9), (head[0]-13, head[1]-15), (head[0]-7, head[1]-9), (head[0]-12, head[1]-2), (head[0]-21, head[1]-4)], CRIMSON)
    _poly(d, [(head[0]-23, head[1]-5), (head[0]-29, head[1]-1), (head[0]-24, head[1]+2)], CRIMSON)

    # Hat
    hat_y = head[1] - 20
    _poly(d, [(head[0]-34, hat_y-2), (head[0]-21, hat_y-14), (head[0]-2, hat_y-17), (head[0]+17, hat_y-14), (head[0]+31, hat_y-2), (head[0]+19, hat_y+2), (head[0]-1, hat_y), (head[0]-22, hat_y+2)], COAT_SH)
    _line(d, [(head[0]-28, hat_y-1), (head[0]-19, hat_y-12), (head[0]-1, hat_y-15), (head[0]+17, hat_y-12), (head[0]+26, hat_y-1)], GOLD, 0.8)
    _ellipse(d, head[0]-1, hat_y-10, 3.0, 3.4, GOLD_HI, width=0.6)
    _line(d, [(head[0]-5, hat_y-6), (head[0]+3, hat_y-6)], GOLD_HI, 0.7)
    _line(d, [(head[0]-3, hat_y-3), (head[0]+1, hat_y-8)], GOLD_HI, 0.6)
    _line(d, [(head[0]+1, hat_y-3), (head[0]-3, hat_y-8)], GOLD_HI, 0.6)
    # feather
    _poly(d, [(head[0]+18, hat_y-12), (head[0]+36, hat_y-18), (head[0]+44, hat_y-10), (head[0]+24, hat_y-6)], CREAM)
    _line(d, [(head[0]+22, hat_y-11), (head[0]+40, hat_y-12)], CRIMSON_DK, 0.6)

    # Near arm in front. If attack, extend fist.
    _line(d, [near_shoulder, near_elbow], COAT_HI, 9.5)
    _line(d, [near_elbow, near_hand], COAT_HI, 8.0)
    # cuff
    _ellipse(d, near_hand[0]-1, near_hand[1]-1, 5.2, 4.7, COAT_SH)
    _ellipse(d, near_hand[0], near_hand[1], 4.6, 4.2, SKIN, width=0.8)
    # gold cuff trim
    cuff_mid = ((near_elbow[0]+near_hand[0])/2, (near_elbow[1]+near_hand[1])/2)
    _line(d, [(cuff_mid[0]-4, cuff_mid[1]-1), (cuff_mid[0]+4, cuff_mid[1]+1)], GOLD_HI, 0.7)

    # Hips / coat front sides to create wide female silhouette
    _poly(d, [(pelvis[0]-40, pelvis[1]-15), (pelvis[0]-21, pelvis[1]-4), (pelvis[0]-24, pelvis[1]+33), (pelvis[0]-42, pelvis[1]+30)], COAT_SH)
    _poly(d, [(pelvis[0]+22, pelvis[1]-11), (pelvis[0]+40, pelvis[1]-3), (pelvis[0]+40, pelvis[1]+31), (pelvis[0]+21, pelvis[1]+31)], COAT_SH)

    # Front leg / pants and boot, explicitly connected to body
    _poly(d, [
        (near_hip[0]-9, near_hip[1]-2), (near_hip[0]+10, near_hip[1]-4),
        (near_knee[0]+8, near_knee[1]+1), (near_knee[0]-10, near_knee[1]+2),
        (near_ankle[0]-8, near_ankle[1]-2), (near_ankle[0]+8, near_ankle[1]-3),
    ], PANTS)
    # front boot aligned under lower leg
    _poly(d, [
        (near_ankle[0]-10, near_ankle[1]-4), (near_ankle[0]+7, near_ankle[1]-5),
        (near_toe[0]+5, near_toe[1]+2), (near_toe[0]-1, near_toe[1]+7),
        (near_heel[0]-4, near_heel[1]+7), (near_heel[0]-7, near_heel[1]+1),
    ], BOOT)
    _rect(d, near_ankle[0]-10, near_ankle[1]-12, near_ankle[0]+7, near_ankle[1]-4, BOOT_HI)
    _rect(d, near_ankle[0]-1, near_ankle[1]-8, near_ankle[0]+5, near_ankle[1]-2, GOLD, width=0.7)

    # Pant seam highlights
    _line(d, [(near_hip[0]-1, near_hip[1]+1), (near_ankle[0]-1, near_ankle[1]-8)], PANTS_HI, 0.8)
    _line(d, [(far_hip[0], far_hip[1]+1), (far_ankle[0], far_ankle[1]-6)], (61, 83, 130, 255), 0.7)

    # simple hand for far hand if visible / attack opposite fist
    if anim == 'attack':
        # add pushed-forward fist on attack pose to make hit read without a weapon
        fist = (far_hand[0] + pose.attack_push, far_hand[1] - pose.attack_raise)
        _line(d, [far_elbow, fist], COAT_SH, 8.5)
        _ellipse(d, fist[0]+2, fist[1], 5.5, 5.5, SKIN, width=0.8)
        _line(d, [(fist[0]+5, fist[1]-1), (fist[0]+9, fist[1]-1)], OUTLINE, 0.7)

    return img.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def build_sheet() -> tuple[Image.Image, dict, Image.Image]:
    row_h = FRAME_H
    max_cols = max(n for _, n, _ in ROWS)
    sheet = Image.new('RGBA', (LABEL_WIDTH + FRAME_W * max_cols, row_h * len(ROWS)), (0, 0, 0, 0))
    meta = {
        'target': TARGET_NAME,
        'image': f'{TARGET_NAME}_preview_sheet.png',
        'label_width': LABEL_WIDTH,
        'frame_width': FRAME_W,
        'frame_height': FRAME_H,
        'rows': [],
    }
    canonical = None

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    all_bboxes = []
    per_anim_bbox = {}
    for r, (name, count, dur) in enumerate(ROWS):
        # row label
        lab = Image.new('RGBA', (LABEL_WIDTH, row_h), (12, 20, 34, 230))
        ld = ImageDraw.Draw(lab)
        ld.text((10, 8), name, fill=(235, 235, 235, 255), font=font)
        ld.text((10, 24), f'{count} @ {dur}ms', fill=(180, 190, 210, 255), font=font)
        sheet.alpha_composite(lab, (0, r * row_h))

        rects = []
        row_boxes = []
        for i in range(count):
            fr = draw_frame(name, i, count)
            if canonical is None and name == 'idle' and i == 0:
                canonical = fr.copy()
            x = LABEL_WIDTH + i * FRAME_W
            y = r * row_h
            sheet.alpha_composite(fr, (x, y))
            rects.append({'x': x, 'y': y, 'w': FRAME_W, 'h': FRAME_H})
            bbox = fr.getbbox()
            if bbox:
                row_boxes.append({'x': bbox[0], 'y': bbox[1], 'w': bbox[2]-bbox[0], 'h': bbox[3]-bbox[1]})
                all_bboxes.append(bbox)
        meta['rows'].append({
            'animation': name,
            'row_index': r,
            'frame_count': count,
            'duration_ms': dur,
            'duration_secs': round(dur / 1000.0, 3),
            'rects': rects,
        })
        if row_boxes:
            x0 = min(b['x'] for b in row_boxes)
            y0 = min(b['y'] for b in row_boxes)
            x1 = max(b['x'] + b['w'] for b in row_boxes)
            y1 = max(b['y'] + b['h'] for b in row_boxes)
            per_anim_bbox[name] = {'hurtbox': {'bbox': {'x': x0, 'y': y0, 'w': x1-x0, 'h': y1-y0}}}

    if all_bboxes:
        x0 = min(b[0] for b in all_bboxes)
        y0 = min(b[1] for b in all_bboxes)
        x1 = max(b[2] for b in all_bboxes)
        y1 = max(b[3] for b in all_bboxes)
        meta['body_metrics'] = {
            'body_pixel_bbox': {'x': x0, 'y': y0, 'w': x1-x0, 'h': y1-y0},
            'feet_pixel': {'x': 130.0, 'y': 237.0},
            'feet_anchor_norm': {'x': round((130.0 / FRAME_W) - 0.5, 4), 'y': round((237.0 / FRAME_H) - 0.5, 4)},
            'animations': per_anim_bbox,
        }
    return sheet, meta, canonical


def emit_preview_bundle(out_dir: str | Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet, meta, canonical = build_sheet()
    sheet_path = out_dir / f'{TARGET_NAME}_preview_sheet.png'
    meta_path = out_dir / f'{TARGET_NAME}_preview_sheet.yaml'
    can_path = out_dir / f'{TARGET_NAME}_canonical_transparent.png'
    sheet.save(sheet_path)
    canonical.save(can_path)
    meta_path.write_text(_yaml_dump(meta) + '\n')
    return [sheet_path, meta_path, can_path]


def main(argv: Iterable[str] | None = None) -> int:
    import sys

    args = list(argv if argv is not None else sys.argv[1:])
    out_dir = Path(args[0]) if args else Path(__file__).resolve().parent / 'generated' / TARGET_NAME
    paths = emit_preview_bundle(out_dir)
    for p in paths:
        print(p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
