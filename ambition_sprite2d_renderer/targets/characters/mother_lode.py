"""Draw the mineral shell, attack poses, and broken shell of Mother Lode."""
from math import pi, sin, tau
from pathlib import Path

from ._clockwork_enemy_art import Canvas, mix, phase, track
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = "mother_lode"
FRAME_SIZE = (392, 336)
BODY = (119, 64, 273, 272)
ROWS = [
    ("idle", 8, 125), ("hammer_lift", 10, 90), ("side_sweep", 8, 49),
    ("fault_coil", 9, 95), ("fault", 8, 51), ("shed_tell", 10, 105),
    ("shed", 10, 54), ("hit", 5, 66), ("death", 18, 70), ("death_idle", 1, 250),
]
STONE = ((41, 56, 65), (63, 81, 88), (95, 109, 109), (155, 157, 131))
ORE = ((75, 128, 142), (95, 158, 151), (197, 168, 111), (138, 106, 142))
HOT = (249, 211, 145)
GLINT = (171, 228, 215)


def plate(c, points, colour, facet=STONE[3]):
    c.poly(points, colour, w=2.6)
    a, b, tip = points[:3]
    c.line([a, b, tip], facet, 1.5)


def spine(c, x, y, w, h, lean, colour):
    tip = (x + lean, y - h)
    left = (x - w, y - h * 0.61)
    right = (x + w, y - h * 0.51)
    foot = (x + w * 0.48, y)
    plate(c, [(x - w * 0.63, y), left, tip, right, foot], colour)
    c.poly([tip, right, foot, (x, y - h * 0.22)], STONE[0], None)
    c.line([tip, (x + lean * 0.34, y - h * 0.36), (x, y - 5)], GLINT, 1.3)


def fist(c, x, y, w, height, charge):
    points = [(x - w, y), (x - w * 0.7, y - height), (x + w * 0.4, y - height * 1.15),
              (x + w, y - height * 0.58), (x + w * 0.78, y + height * 0.22),
              (x - w * 0.62, y + height * 0.2)]
    plate(c, points, STONE[1])
    c.poly([points[1], points[2], points[3], (x + 4, y - height * 0.46), (x - 14, y - height * 0.44)],
           STONE[2], None)
    c.line([(x - 18, y - height * 0.4), (x - 5, y - 7), (x + 5, y - 10), (x + 19, y + 2)],
           HOT if charge else ORE[0], 3 if charge else 1.5)


def broken(c, t):
    for i, (x, y, w, h, colour) in enumerate(((115, 229, 27, 49, ORE[0]), (150, 230, 25, 31, STONE[2]),
                                               (244, 236, 24, 58, ORE[2]), (289, 224, 27, 42, ORE[3]),
                                               (324, 259, 16, 34, STONE[2]), (75, 260, 17, 29, STONE[1]))):
        x = 198 + (x - 198) * (0.48 + 0.52 * t)
        y = y - sin(pi * t) * (31 + i * 7)
        spine(c, x, y, w, h, (i % 3 - 1) * 13, colour)
    c.oval((204, 247), 17, 11, ORE[0])
    c.oval((204, 247), 9, 5, GLINT, None)


def render_frame(anim, index, count):
    c = Canvas(FRAME_SIZE, super_scale=2)
    t = phase(index, count, anim == "idle")
    split = 1 if anim == "death_idle" else (t if anim == "death" else 0)
    if split > 0.5:
        broken(c, (split - 0.5) * 2)
        return c.finish()

    lift = t if anim == "hammer_lift" else 0
    hammer = track(t, [(0, 0.04), (0.28, 1), (0.57, 0.87), (1, 0)]) if anim == "side_sweep" else 0
    coil = t if anim == "fault_coil" else 0
    fault = sin(pi * t) if anim == "fault" else 0
    shed = t if anim == "shed_tell" else (1 - t if anim == "shed" else 0)
    hurt = sin(pi * t) if anim == "hit" else split * 2
    y = 3 * sin(tau * t) + 22 * coil + 11 * hammer - 10 * shed + 34 * hurt
    shift = 11 * coil - 10 * hammer
    def body(x, dy):
        return x + shift, dy + y

    plate(c, [(79, 254), (93, 202), body(143, 142), body(173, 167), (149, 252), (128, 272), (84, 272)], STONE[0], STONE[2])
    plate(c, [(168, 252), body(181, 172), body(227, 166), (242, 235), (229, 272), (176, 272)], STONE[1])
    for x, yy, w, h, lean, colour in ((107, 162, 12, 57, -22, ORE[3]), (139, 133, 16, 58, -15, ORE[0]),
                                       (161, 124, 19, 101, -16, ORE[1]), (198, 120, 20, 89, 19, ORE[2]),
                                       (225, 128, 16, 61, 23, ORE[3]), (249, 142, 12, 44, 24, ORE[0])):
        spine(c, *body(x, yy), w, h + 11 * shed, lean, colour)

    far_hand = mix(mix((111, 215), (88, 92), lift), (61, 258), hammer)
    fx, fy = far_hand
    fy += 11 * coil - 13 * shed + 7 * hurt
    plate(c, [body(132, 142), body(112, 130), (fx - 13, fy - 3),
              (fx + 15, fy + 12), body(148, 169)], STONE[0])
    fist(c, fx, fy, 26 + 4 * hammer, 37, lift > 0.25 or hammer > 0.4)

    outline = [body(*p) for p in ((77, 172), (100, 112), (143, 91), (187, 96), (226, 105),
                                  (251, 139), (244, 174), (208, 201), (136, 219), (100, 201))]
    plate(c, outline, STONE[1])
    for points, colour in (
        (((103, 142), (121, 112), (153, 101), (187, 116), (157, 150), (132, 160)), STONE[2]),
        (((90, 171), (114, 151), (142, 158), (154, 188), (127, 208), (102, 193)), STONE[0]),
        (((151, 182), (156, 154), (186, 132), (216, 136), (222, 170), (197, 193)), STONE[2]),
        (((188, 191), (214, 171), (239, 160), (220, 192), (181, 210), (156, 211)), STONE[0]),
    ):
        plate(c, [body(*p) for p in points], colour, (115, 135, 131))

    for i, (x, yy) in enumerate(((110, 134), (132, 129), (108, 182), (149, 204), (184, 158), (199, 187))):
        p = [body(x, yy), body(x + 13, yy - 8), body(x + 21, yy - 8), body(x + 18, yy - 3)]
        c.line(p, ORE[i % len(ORE)], 3.0)
        c.line(p[1:3], STONE[3], 0.85)
    c.line([body(130, 197), body(153, 172), body(167, 176), body(184, 148), body(202, 142)],
           GLINT if coil > 0.4 or fault > 0.2 else ORE[0], 4.8 if fault else 2.2)
    for j in range(3):
        x, yy = body(135 + j * 10, 189 - j * 7)
        c.oval((x, yy), 2, 3 + 3 * shed, ORE[j], None)

    head = [body(*p) for p in ((210, 120), (231, 91), (263, 94), (281, 112), (277, 143),
                               (257, 153), (225, 142))]
    plate(c, head, STONE[2], HOT)
    c.poly([body(*p) for p in ((234, 113), (254, 105), (272, 113), (267, 126), (249, 132), (232, 124))],
           STONE[0])
    eye = body(258, 117)
    c.oval(eye, 7, 2.4 + sin(tau * t) * 0.6 + 2 * shed, HOT if lift or hammer else GLINT, None)
    c.disk(body(260, 116), 1.3, (255, 245, 211), None)
    c.line([body(252, 139), body(267, 136), body(272, 132)], STONE[0], 2.2)

    hand = mix(mix((263, 236), (288, 96), lift), (331, 262), hammer)
    x = hand[0] - 22 * coil + 6 * fault
    yy = hand[1] + 15 * coil - 15 * shed + 7 * hurt
    plate(c, [body(211, 143), body(233, 147), (x + 8, yy - 18), (x - 20, yy + 2),
              body(216, 173)], STONE[1])
    fist(c, x, yy, 31 + 5 * hammer, 43, lift > 0.25 or hammer > 0.4)
    if anim in ("shed_tell", "shed"):
        for j in range(4):
            drop = t if anim == "shed" else 0
            x, yy = body(118 + j * 36 + (j - 1.5) * 39 * drop,
                         78 - (9 + j % 2 * 17) * shed + 112 * drop * drop)
            spine(c, x, yy, 4 + j % 2 * 2, 11, 2, ORE[j])
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
