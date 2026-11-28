"""Draw Mother Lode's bedrock shell and exposed mineral seams."""
from math import pi, sin, tau
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageOps

from ._clockwork_enemy_art import Canvas, add, mix, phase, rot, track
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = "mother_lode"
FRAME_SIZE = (392, 336)
BODY = (119, 64, 273, 272)
ROWS = [
    ("idle", 8, 125), ("hammer_lift", 10, 90), ("side_sweep", 8, 49),
    ("fault_coil", 9, 95), ("fault", 8, 51), ("shed_tell", 10, 105),
    ("shed", 10, 54), ("hit", 5, 66), ("death", 18, 70), ("death_idle", 1, 250),
    ("split_tell", 12, 100), ("split", 8, 51), ("core_open", 12, 80),
]

INK = (26, 19, 34)
BEDROCK = (73, 59, 82)
SLATE = (103, 83, 105)
IRON = (137, 101, 105)
GALENA = (121, 136, 148)
COPPER = (200, 122, 85)
AMBER = (255, 203, 117)
IVORY = (255, 239, 191)
JADE = (125, 238, 207)
VIOLET = (204, 135, 246)
ROSE = (255, 142, 182)
OXIDES = ((244, 173, 110), (231, 123, 170), (164, 113, 219), (105, 170, 214), (102, 213, 182))


def colour(a, b, t):
    return tuple(round(v) for v in mix(a, b, t))


def face_gradient(c, path, fill, light):
    """Shade the face within its bevel."""
    points = [(round(x * c.s), round(y * c.s)) for x, y in path]
    x0 = min(x for x, _ in points)
    y0 = min(y for _, y in points)
    size = (max(x for x, _ in points) - x0 + 1, max(y for _, y in points) - y0 + 1)
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in points], fill=255)
    ramp = Image.linear_gradient("L").resize(size)
    shade = ImageOps.colorize(ramp, colour(fill, IVORY, light * 0.31), colour(fill, INK, 0.32))
    c.image.paste(shade, (x0, y0), mask)


def bevel(c, path, fill, *, light=0.6, width=0.13, seed=0):
    """Put an edge, a bevel and small mineral grains on a plate."""
    cx = sum(x for x, _ in path) / len(path)
    cy = sum(y for _, y in path) / len(path)
    land = [mix(p, (cx, cy), width) for p in path]
    c.poly(path, INK, INK, 2.8)
    rim = colour(fill, IVORY, light * 0.54)
    for i, a in enumerate(path):
        j = (i + 1) % len(path)
        b = path[j]
        facing = (b[0] - a[0]) * 0.77 - (b[1] - a[1]) * 0.55
        shade = rim if facing > 2 else colour(fill, INK, 0.52)
        c.poly([a, b, land[j], land[i]], shade, None)
    c.line(path, INK, 1.35, closed=True)
    face_gradient(c, land, fill, light)

    rng = Random(seed)
    for i, a in enumerate(land):
        b = land[(i + 1) % len(path)]
        for _ in range(round(abs((a[0]-cx)*(b[1]-cy) - (a[1]-cy)*(b[0]-cx)) / 230)):
            s = rng.uniform(0.1, 0.88)
            point = mix((cx, cy), mix(a, b, rng.random()), s)
            c.line([point, add(point, (rng.uniform(0.9, 3.3), rng.uniform(-0.8, 0.35)))],
                   colour(fill, IVORY if rng.random() < 0.57 else INK, rng.uniform(0.10, 0.34)), 0.8)


def vein(c, path, hue, power=0.0):
    c.line(path, colour(INK, hue, 0.26), 5.7 + 3 * power)
    c.line(path, colour(IRON, hue, 0.65 + 0.35 * power), 1.9 + 2.0 * power)
    if power >= 0.6:
        c.line(path[1:-1], colour(hue, IVORY, 0.54), 1.05)
    for i in range(1, len(path) - 1):
        x, y = path[i]
        if i % 2:
            c.line([(x, y), (x - 5, y + 1), (x - 8, y + 5)], colour(IRON, hue, 0.58), 1.15)


def crystal(c, base, tip, width, hue, *, light=0.0):
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = (dx * dx + dy * dy) ** 0.5
    side = (dy * width / length, -dx * width / length)
    left = add(mix(base, tip, 0.77), side)
    right = add(mix(base, tip, 0.61), (-side[0], -side[1]))
    left_heel = add(base, (side[0] * 0.73, side[1] * 0.73))
    right_heel = add(base, (-side[0] * 0.64, -side[1] * 0.64))
    ridge = mix(base, tip, 0.7)
    c.poly([left_heel, left, tip, right, right_heel], colour(hue, INK, 0.35), INK, 1.7)
    c.poly([left_heel, left, tip, ridge, base], colour(hue, INK, 0.16), None)
    c.poly([left, tip, ridge], colour(hue, IVORY, 0.45 + 0.3 * light), None)
    c.poly([ridge, tip, right], colour(hue, INK, 0.6), None)
    c.line([left, tip, right], colour(hue, IVORY, 0.38 + 0.40 * light), 1.12)
    c.line([base, ridge], colour(hue, IVORY, 0.48 + 0.29 * light), 1.12)
    c.line([mix(left_heel, left, 0.42), mix(base, ridge, 0.49), mix(right_heel, right, 0.43)],
           colour(hue, IVORY, 0.24), 1.05)


def hopper(c, base, size, angle, power, offset):
    """Draw a recessed bismuth crystal with stepped oxide bands."""
    def square(radius, depth):
        return [add(base, rot((radius * x, radius * y + depth), angle))
                for x, y in ((-1.0, -0.67), (0.70, -1.0), (1.0, 0.61), (-0.67, 1.0))]

    outer = square(size, 0)
    heel = square(size * 0.82, size * 0.70)
    c.poly([outer[0], outer[1], outer[2], heel[2], heel[3], heel[0]], (69, 41, 77), INK, 2.2)
    c.poly(square(size, 0), (37, 24, 53), INK, 2.2)
    for k in range(5):
        start = square(size * (1 - k * 0.166), k * size * 0.08)
        lip = square(size * (0.91 - k * 0.166), k * size * 0.08)
        inset = square(size * (0.834 - k * 0.166), (k + 1) * size * 0.08)
        for i in range(4):
            j = (i + 1) % 4
            hue = OXIDES[(offset + k + i) % len(OXIDES)]
            face = colour(hue, INK, 0.09 * k)
            c.poly([start[i], start[j], lip[j], lip[i]], colour(face, IVORY, power * 0.5), None)
            c.poly([lip[i], lip[j], inset[j], inset[i]], colour(face, INK, 0.53), None)
        c.line([start[3], start[0], start[1]], colour(OXIDES[(offset+k) % len(OXIDES)], IVORY, 0.50), 0.95)


def core(c, at, scale, power):
    def p(x, y):
        return add(at, (x * scale, y * scale))

    shell = [p(-19, 2), p(-10, -13), p(7, -18), p(23, -6), p(17, 11), p(1, 18), p(-14, 13)]
    bevel(c, shell, (98, 47, 64), light=0.48, width=0.24, seed=12)
    c.poly([p(-10, 3), p(-2, -8), p(9, -11), p(14, -1), p(8, 10), p(-4, 10)], COPPER, INK, 1.4)
    c.poly([p(-2, -8), p(9, -11), p(12, -4), p(-5, 2)], AMBER, None)
    c.poly([p(-5, 2), p(12, -4), p(5, 8), p(-4, 10)], colour(COPPER, AMBER, power), None)
    c.line([p(-7, 0), p(-1, -6), p(7, -8)], IVORY, 0.85 + power)
    c.line([p(-19, 3), p(-12, -11), p(-2, -14)], colour(COPPER, IVORY, 0.20), 1.15)


def foot(c, hip, heel, far=False):
    x, y = heel
    bevel(c, [hip, add(hip, (28, -2)), (x + 29, y - 33),
              (x + 20, y - 14), (x - 15, y - 13), (x - 23, y - 38)],
          BEDROCK if far else SLATE, light=0.38, seed=2)
    bevel(c, [(x - 19, y - 16), (x + 7, y - 24), (x + 26, y - 16), (x + 34, y - 5),
              (x + 24, y), (x - 26, y), (x - 29, y - 7)],
          SLATE if far else IRON, light=0.45, seed=6)
    for offset in (9, 20):
        c.line([(x + offset, y - 6), (x + offset + 3, y - 1)], INK, 1.55)


def claw(c, at, angle, power, hue, far=False):
    def p(x, y):
        return add(at, rot((x, y), angle))

    outline = [p(-36, -27), p(-19, -42), p(13, -44), p(36, -26), p(40, -5),
               p(33, 13), p(16, 18), p(-25, 16), p(-38, 7)]
    bevel(c, outline, SLATE if far else GALENA, light=0.65, width=0.19, seed=71)
    c.poly([p(-32, -9), p(-12, -12), p(2, -9), p(18, -15), p(35, -9), p(33, 13),
            p(16, 17), p(-25, 16)], colour(SLATE, INK, 0.24), None)
    vein(c, [p(-25, 0), p(-13, -7), p(0, -5), p(11, -15), p(26, -14)], hue, power)
    for dx in (-19, 1, 21):
        bevel(c, [p(dx-7, 4), p(dx+6, 2), p(dx+11, 8), p(dx+8, 16), p(dx-6, 16)],
              SLATE if far else (148, 146, 157), light=0.41, seed=4+dx)


def foreleg(c, shoulder, hand, bend, angle, power, hue, far=False):
    elbow = add(mix(shoulder, hand, 0.50), bend)
    a, b = shoulder
    x, y = elbow
    heel = (hand[0] - 14, hand[1] - 17)
    bevel(c, [(a-19, b-16), (a+14, b-23), (x+23, y-18), (x+28, y+5),
              (heel[0]+22, heel[1]+8), (heel[0]-13, heel[1]+10),
              (x-21, y+12), (x-30, y-1)],
          BEDROCK if far else SLATE, light=0.58, seed=15)
    bevel(c, [(x-21, y-7), (x-5, y-23), (x+21, y-19), (x+30, y-7),
              (x+13, y+10), (x-6, y+13)], SLATE if far else IRON, light=0.50, seed=22)
    claw(c, hand, angle, power, hue, far=far)


def face(c, head, charge, blink, alarm):
    def p(x, y):
        return add(head, (x, y))

    bevel(c, [p(-38,-7), p(-17,-34), p(5,-37), p(29,-26), p(42,-13),
              p(42,8), p(25,18), p(-9,20), p(-34,5)], GALENA, width=0.16, seed=11)
    c.poly([p(-26,-12), p(-11,-27), p(6,-30), p(28,-20), p(34,-10),
            p(14,-5), p(2,4), p(-22,1)], (56, 42, 64), None)
    c.poly([p(-26,-13), p(-11,-28), p(7,-30), p(29,-19), p(21,-16), p(5,-21), p(-9,-18)],
           (213, 188, 172), None)
    vein(c, [p(-21,-25), p(-10,-29), p(0,-29), p(11,-26)], AMBER, charge * 0.65)
    eye_y = -12 - alarm * 1.8
    light = colour(AMBER, IVORY, charge * 0.62)
    c.oval(p(10,eye_y), 12, 5.6 * blink, colour(COPPER, AMBER, 0.54), None, angle=-13)
    c.oval(p(11,eye_y-0.5), 8.4, max(0.7, 3.2 * blink), light, None, angle=-13)
    if blink > 0.5:
        c.oval(p(15,eye_y-0.6), 2.2, 3.2, INK, None, angle=-10)
        c.disk(p(13,eye_y-2.2), 1.1, IVORY, None)
    c.line([p(30,-8), p(36,-5), p(34,0)], colour(GALENA, IVORY, 0.65), 1.7)
    c.poly([p(-10,9), p(5,10), p(23,5), p(37,5), p(31,11), p(11,17), p(-7,15)], INK, None)
    c.line([p(-7,13), p(9,14), p(26,9)], (174, 127, 125), 1.3)
    for dx, dy in ((17,6), (24,5), (31,5)):
        c.poly([p(dx-2,dy), p(dx+4,dy-1), p(dx+1,dy+4)], (226, 202, 163), None)


def rubble(c, t):
    fragments = (
        ((104, 259), (82, 268), 19, SLATE), ((122, 236), (112, 271), 28, IRON),
        ((149, 195), (151, 268), 33, SLATE), ((201, 193), (239, 270), 29, BEDROCK),
        ((231, 218), (273, 271), 33, IRON), ((255, 257), (321, 268), 26, SLATE),
    )
    for i, (origin, end, w, hue) in enumerate(fragments):
        x, y = mix(origin, end, t)
        y -= sin(pi * t) * (22 + (i * 13) % 37)
        angle = (1 - t) * (9 * i - 19)
        shape = [add((x, y), rot(p, angle))
                 for p in ((-w, -2), (-w * 0.73, -15), (-5, -30 - w * 0.31),
                           (w * 0.60, -21), (w, -5), (w * 0.66, 0))]
        bevel(c, shape, hue, light=0.54, width=0.20, seed=i+40)
        if i in (1, 3, 4):
            crystal(c, (x, y-14), (x+(i-2)*10, y-42-w*0.54), w*0.37, OXIDES[i%5])

    core(c, mix((174, 211), (194, 251), t), 1.08, 0.62)
    for i in range(14):
        direction = -1 if i % 2 else 1
        x = 185 + direction * (12 + i * 2 + (43 + i * 6) * t)
        y = 218 - i * 3 - sin(pi * t) * (40 + i * 2) + t * 30
        if t < 0.84:
            c.disk((x, y), (1.0 + i % 3 * 0.68) * (1 - t), colour(AMBER, SLATE, i / 13), None)
    bevel(c, [(158, 270), (176, 261), (192, 264), (208, 261), (228, 269), (221, 272), (165, 272)],
          BEDROCK, light=0.4, seed=99)


def render_frame(anim, index, count):
    c = Canvas(FRAME_SIZE, super_scale=2)
    t = phase(index, count, anim == "idle")
    split = 1 if anim == "death_idle" else (t if anim == "death" else 0)
    if split >= 0.56:
        rubble(c, (split - 0.56) / 0.44)
        return c.finish()

    lift = track(t, [(0, 0), (0.45, 0.50), (0.80, 0.88), (1, 1)]) if anim == "hammer_lift" else 0
    hammer = track(t, [(0, 0.83), (0.16, 1), (0.43, 1), (1, 0)]) if anim == "side_sweep" else 0
    coil = track(t, [(0, 0), (0.58, 0.88), (1, 1)]) if anim == "fault_coil" else 0
    fault = track(t, [(0, 1), (0.32, 0.86), (1, 0)]) if anim == "fault" else 0
    shed = t if anim == "shed_tell" else (1 - t if anim == "shed" else 0)
    brace = track(t, [(0, 0), (0.35, 0.2), (0.80, 0.88), (1, 1)]) if anim == "split_tell" else 0
    fracture = track(t, [(0, 1), (0.17, 1), (0.60, 0.72), (1, 0.18)]) if anim == "split" else 0
    opening = track(t, [(0, 0.42), (0.18, 1), (0.67, 0.91), (1, 0)]) if anim == "core_open" else 0
    hurt = sin(pi * t) if anim == "hit" else split * 1.79
    breathe = 2.4 * sin(tau * t) if anim == "idle" else 0.0
    shift = -6 * lift + 12 * hammer - 10 * coil + 5 * fault - 12 * hurt
    y = (breathe - 10 * lift + 17 * hammer + 26 * coil + 15 * fault - 17 * shed +
         50 * hurt + 24 * brace - 17 * fracture + 22 * opening)

    def body(x, yy):
        return x + shift, yy + y

    hue = ROSE if brace or fracture else JADE if coil or fault else VIOLET if shed else AMBER
    pulse = max(lift * 0.88, hammer, coil * 0.95, fault, shed, hurt * 0.66, brace, fracture)
    left = mix(mix((118, 230), (83, 106), lift), (59, 242), hammer)
    right = mix(mix((258, 236), (314, 99), lift), (326, 243), hammer)
    left = mix(mix(left, (109, 235), coil), (91, 248), fault)
    right = mix(mix(right, (252, 244), coil), (258, 249), fault)
    left = add(left, (-14 * shed - 10 * hurt, -18 * shed + 10 * hurt))
    right = add(right, (20 * shed - 13 * hurt, -18 * shed + 9 * hurt))
    left = mix(mix(mix(left, (144, 245), brace), (60, 246), fracture), (98, 253), opening)
    right = mix(mix(mix(right, (240, 248), brace), (324, 245), fracture), (293, 252), opening)

    foot(c, body(182, 201), (190, 267), far=True)
    foreleg(c, body(135, 155), left, (-11, 4), -12 + 23 * lift - 28 * hammer, pulse, hue, far=True)
    foot(c, body(140, 196), (142, 272))

    crystal(c, body(130, 141), body(93, 78 - 10 * shed), 13, (158, 112, 179), light=pulse)
    crystal(c, body(151, 145), body(126, 63 - 7 * shed), 20, (152, 187, 194), light=pulse)
    crystal(c, body(209, 122), body(223, 45 - 10 * shed), 15, (229, 159, 93), light=pulse)
    crystal(c, body(232, 131), body(252, 76 - 14 * shed), 11, (126, 157, 219), light=pulse)
    hopper(c, body(168 - 5 * shed, 100 - 13 * shed), 35, -13 - 8 * shed, pulse * 0.66, 2)
    hopper(c, body(202 + 9 * shed, 91 - 14 * shed), 21, 17 + 8 * shed, pulse * 0.66, 0)

    bevel(c, [body(*p) for p in ((94,181),(104,153),(131,121),(174,110),(220,112),(254,129),
                                  (277,157),(271,189),(245,213),(208,226),(161,225),(116,213))],
          BEDROCK, width=0.17, seed=70)
    bevel(c, [body(*p) for p in ((99,172),(112,146),(142,125),(159,116),(188,127),(170,154),
                                  (148,181),(128,197),(109,191))],
          SLATE, light=0.58, seed=64)
    if opening:
        bevel(c, [body(*p) for p in ((144,158),(173,128),(210,127),(232,146),(229,180),
                                     (207,202),(172,203),(148,184))],
              INK, light=0.30, width=0.12, seed=44)
        for side in (-1, 1):
            def plate(x, yy):
                return body(185 + side * (x + 23 * opening), yy - 10 * opening)

            bevel(c, [plate(*p) for p in ((0,127),(13,114),(38,122),(53,148),(39,176),
                                          (21,193),(7,192),(13,161))],
                  IRON, light=0.62, width=0.16, seed=44)
            vein(c, [plate(*p) for p in ((14,175),(25,159),(27,145),(37,135))], AMBER, opening)
    else:
        bevel(c, [body(*p) for p in ((151,150),(187,116),(209,114),(232,125),(245,153),
                                     (225,180),(208,195),(183,200),(158,187),(148,171))],
              IRON, light=0.62, width=0.18, seed=44)
    bevel(c, [body(*p) for p in ((136,195),(156,189),(182,200),(202,202),(219,211),(202,222),
                                  (166,224),(143,215))],
          BEDROCK, light=0.43, seed=73)
    for fragments in (((108,173),(117,166),(133,164),(143,157)),
                      ((114,181),(125,173),(144,171),(151,164)),
                      ((133,191),(145,181),(160,178)),
                      ((164,212),(179,215),(193,212))):
        c.line([body(*p) for p in fragments], (157, 112, 117), 1.38)
    vein(c, [body(*p) for p in ((113,184),(127,180),(144,167),(163,169),(186,155),(193,150))], hue, pulse)
    vein(c, [body(*p) for p in ((183,182),(191,171),(212,166),(220,146),(224,137))], hue, pulse * 0.87)
    core(c, body(182, 166), 0.92 + 0.12 * shed + 0.58 * opening,
         0.22 + 0.78 * max(pulse, opening))

    bevel(c, [body(*p) for p in ((217,144),(229,116),(250,119),(268,139),(261,158),
                                 (247,169),(226,164))], SLATE, light=0.54, seed=53)
    head = body(249 + 3 * lift + 6 * hammer - 5 * coil + 12 * opening,
                132 - 12 * lift + 14 * coil + 14 * opening + 6 * brace)
    blink = 0.27 if anim == "idle" and index == count - 1 else 1 - 0.66 * opening
    face(c, head, pulse, blink, shed - coil - opening)
    foreleg(c, body(226, 172), right, (15, 2), 12 - 35 * lift + 18 * hammer, pulse, hue)

    if anim in ("shed_tell", "shed"):
        release = t if anim == "shed" else 0
        for i, angle in enumerate((-143, -111, -70, -42)):
            x, yy = body(176 + 19 * (i-1.5), 73)
            x += (i - 1.5) * (11 * shed + 39 * release)
            yy += -23 * shed + (55 + 15 * i) * release ** 2
            crystal(c, (x, yy), add((x, yy), rot((12 + 4 * shed, 0), angle + 150 * release)),
                    3.3, OXIDES[i], light=shed)

    if fracture:
        for side in (-1, 1):
            for i in range(4):
                x = 196 + side * (34 + 15 * i + (35 + i * 11) * t)
                yy = 114 + (i % 2) * 22 - (16 + i * 12) * sin(pi * t)
                tail = add((x, yy), (-side * (10 + 5 * i) * fracture, 6))
                crystal(c, tail, (x, yy), 2.4 + 0.7 * i, ROSE, light=fracture)

    return c.finish()


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Mother Lode"},
    "body": {"body_plan": "Quadruped", "body_kind": "Wide", "mass_class": "Heavy", "locomotion_hint": "Walk"},
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "tags": ["boss", "science", "mine", "elemental"],
}


def render(out_dir: str | Path, **_opts):
    outputs = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=render_frame, out_dir=Path(out_dir),
                          frame_size=FRAME_SIZE, auto_crop=False, actor_metadata=ACTOR_METADATA,
                          animation_key_map={name: name for name, _, _ in ROWS},
                          body_metrics_fn=lambda w, h: body_metrics_for_box(BODY, w, h), sits_on_ground=True)
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]
