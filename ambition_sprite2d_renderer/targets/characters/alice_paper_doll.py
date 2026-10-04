"""Alice's SVG cut-paper parts, posed in the target's 128-unit authoring space.

Each part (a ``<use>`` of a symbol in ``assets/alice.svg``) is rendered once
by resvg in its own frame, at its own scale, and placed turned
(``_toon_rig``): the frame is composed from the pieces, as a rig document
is, not one picture rendered per frame."""
from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import resvg_py

from ...authoring import shape_rig

#: How far (design units) a piece's raster reaches around its origin.
_REACH = 40.0


@lru_cache(maxsize=1)
def _definitions():
    source = Path(__file__).resolve().parents[3] / "assets" / "alice.svg"
    root = ET.parse(source).getroot()
    return ET.tostring(root.find('{http://www.w3.org/2000/svg}defs'), encoding='unicode')


def _svg_piece(key, body, scale):
    """The SVG ``body`` (design units, around the origin) rendered once at
    ``scale``: a piece with its pivot at the origin. ``key`` names ``body``."""
    size = int(math.ceil(2 * _REACH * scale))

    def paint(draw):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{-_REACH} {-_REACH} {size / scale} {size / scale}">{_definitions()}'
            f'<g stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
        )
        rendered = Image.open(BytesIO(resvg_py.svg_to_bytes(svg_string=svg, skip_system_fonts=True))).convert('RGBA')
        draw._img.alpha_composite(rendered)

    return shape_rig.piece(("alice_svg", key, scale), (size, size), (_REACH * scale, _REACH * scale), paint)


def draw_doll(frame, cx, feet_y, pose, scale, solve):
    """Place the doll's pieces on ``frame`` (a ``_toon_rig.Frame``). Return
    the solved grip; every piece and accessory shares these joints."""
    cx, ground = cx / scale, feet_y / scale
    side = pose.view.value == 'side'
    front = pose.view.value == 'front'
    spread = 0.48 if side else (1 if front else .86)
    hip = ground - (42 if pose.walk_index >= 0 else 44) + pose.walk_body_y + 10 * pose.crouch
    shoulder = hip - 27 + 4 * pose.crouch
    lean = -pose.lean * .55
    body_x = cx + lean

    def place(key, body, x, y, angle, name):
        frame.place(_svg_piece(key, body, scale), (x * scale, y * scale), angle, name)

    def part(name, x, y, angle=0, sx=1, sy=1, track=None):
        sx, sy = round(sx, 3), round(sy, 3)
        place((name, sx, sy), f'<use href="#{name}" transform="scale({sx} {sy})"/>', x, y, angle, track or name)

    def bone(name, a, b, length, track):
        angle = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) - 90
        # The solve keeps each bone its length; a stretch is rounded.
        part(name, *a, angle, sy=round(math.dist(a, b) / length, 2), track=track)

    def leg(near):
        sign = 1 if near else -1
        which = 'near' if near else 'far'
        root = (cx + sign * 4 * spread, hip)
        target = (cx + sign * 5 * spread, ground - 6)
        if pose.walk_index >= 0:
            phase = pose.walk_index * math.tau / 8 + (0 if near else math.pi)
            target = (cx + math.cos(phase)*12*pose.gait_scale,
                      ground - 6 - max(0, math.sin(phase))*9*pose.gait_scale)
        authored = pose.near_foot if near else pose.far_foot
        if authored is not None:
            target = (cx + authored[0], ground - 6 + authored[1])
        knee, ankle = solve(root, target, 21, 17, bend_sign=1 if side else sign)
        bone('thigh', root, knee, 21, f'{which}_thigh')
        bone('shin', knee, ankle, 17, f'{which}_shin')
        part('foot', *ankle, sx=1 if side or near else -.8, track=f'{which}_foot')

    hands = {}
    def arm(near):
        sign = 1 if near else -1
        which = 'near' if near else 'far'
        root = (body_x + sign * 9 * spread, shoulder+3)
        authored = pose.near_hand if near else pose.far_hand
        target = (body_x + sign*14*spread, shoulder+28)
        if pose.walk_index >= 0:
            target = (root[0] - sign*math.cos(pose.walk_index*math.tau/8)*8*pose.arm_swing, shoulder+27)
        if near and pose.prop == 'folio' and pose.walk_index < 0:
            target = (body_x+14, shoulder+23-pose.map_open*5)
        if not near and pose.gesture:
            target = (body_x-15, shoulder+25-pose.gesture*6)
        if authored is not None:
            target = (body_x+authored[0], shoulder+authored[1])
        elbow, grip = solve(root, target, 14, 13, bend_sign=pose.near_bend if near else pose.far_bend)
        hands[near] = grip
        bone('upper-arm', root, elbow, 14, f'{which}_upper_arm')
        bone('forearm', elbow, grip, 13, f'{which}_forearm')
        part('hand', *grip, angle=-15 if near else 15, track=f'{which}_hand')

    head_x, head_y = body_x + (1.8 if side else 0), shoulder - 15
    part('hair-back', head_x, head_y, pose.head_tilt)
    arm(False)
    leg(False)
    leg(True)
    part('tails', cx, hip-1, pose.step*4, sx=.7 if side else 1, sy=.42)
    part('torso', body_x, shoulder, sx=.65 if side else 1)
    # The strap passes under the near arm and terminates at the bag's top
    # edge. Its length changes with the pose, so it is two copies of one
    # fixed piece, one from each end, meeting along the strap (the strap
    # runs 26 to 39 units; each copy is 20).
    strap_a, strap_b = (body_x+7, shoulder+3), (cx-9, hip+4)
    along = math.degrees(math.atan2(strap_b[1]-strap_a[1], strap_b[0]-strap_a[0]))
    strap = '<path d="M0 0 L20 0" stroke="#342b38" stroke-width="2.5"/><path d="M0 0 L20 0" stroke="#ae8265" stroke-width="1"/>'
    place('strap', strap, *strap_a, along, 'strap')
    place('strap', strap, *strap_b, along + 180.0, 'strap_lower')
    part('satchel', cx-10, hip+8, pose.step*5, sx=.8)
    arm(True)
    # The head is one base piece per view; the expression (the blink over
    # the eye apertures, the talking mouth) is an overlay piece turned with
    # it about the same point.
    head = 'head-side' if side else 'head'
    head_sx = .94 if not front and not side else 1
    place(('head', head, head_sx), f'<g transform="scale({head_sx} 1)"><use href="#{head}"/></g>', head_x, head_y, pose.head_tilt, 'head')
    if pose.blink:
        # Cover the eye apertures only; brows and nose retain their construction.
        lids = ''.join(
            f'<path d="M{x-1.7} {.4} h3.4" stroke="#e8b58e" stroke-width="2.1"/><path d="M{x-1.7} {.6} q1.7 1 3.4 0" fill="none" stroke="#67484a" stroke-width=".55"/>'
            for x in ([4] if side else [-2.5, 4])
        )
        place(('blink', head_sx, side), f'<g transform="scale({head_sx} 1)">{lids}</g>', head_x, head_y, pose.head_tilt, 'face')
    # The mouth opens in two steps.
    talk = 0.0 if pose.talk_open <= .15 else (.5 if pose.talk_open < .7 else 1.0)
    if talk:
        place(('mouth', head_sx, talk), f'<g transform="scale({head_sx} 1)"><ellipse cx="{1.3}" cy="{7}" rx="1.25" ry="{.3+talk}" fill="#77404a"/></g>', head_x, head_y, pose.head_tilt, 'mouth')
    # An engraved cipher wheel hangs from the belt, distinct from the held map.
    wheel = ['<g stroke="#604849" stroke-width=".45"><circle r="3.8" fill="#d1a568"/><circle r="2.8" fill="#f1d59b"/><circle r="1.7" fill="#3b4f62"/>']
    for i in range(12):
        a = i*math.tau/12
        wheel.append(f'<path d="M{math.cos(a)*2.9} {math.sin(a)*2.9} L{math.cos(a)*3.5} {math.sin(a)*3.5}"/>')
    wheel.append('<path d="M0 -2 L.6 0 L0 1.5 L-.6 0Z" fill="#e6ba76"/></g>')
    place('cipher_wheel', ''.join(wheel), cx+7, hip+5, 0.0, 'cipher_wheel')
    return tuple(v*scale for v in hands[True])
