"""Alice's SVG cut-paper parts, posed in the target's 128-unit authoring space."""
from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import resvg_py


@lru_cache(maxsize=1)
def _definitions():
    source = Path(__file__).resolve().parents[3] / "assets" / "alice.svg"
    root = ET.parse(source).getroot()
    return ET.tostring(root.find('{http://www.w3.org/2000/svg}defs'), encoding='unicode')


def draw_doll(image, cx, feet_y, pose, scale, solve):
    """Return the solved grip; every piece and accessory shares these joints."""
    cx, ground = cx / scale, feet_y / scale
    side = pose.view.value == 'side'
    front = pose.view.value == 'front'
    spread = 0.48 if side else (1 if front else .86)
    hip = ground - (42 if pose.walk_index >= 0 else 44) + pose.walk_body_y + 10 * pose.crouch
    shoulder = hip - 27 + 4 * pose.crouch
    lean = -pose.lean * .55
    body_x = cx + lean
    pieces = []

    def part(name, x, y, angle=0, sx=1, sy=1, opacity=1):
        pieces.append(f'<use href="#{name}" transform="translate({x} {y}) rotate({angle}) scale({sx} {sy})" opacity="{opacity}"/>')

    def bone(name, a, b, length, opacity=1):
        angle = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) - 90
        part(name, *a, angle, sy=math.dist(a, b)/length, opacity=opacity)

    def leg(near):
        sign = 1 if near else -1
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
        bone('thigh', root, knee, 21)
        bone('shin', knee, ankle, 17)
        part('foot', *ankle, sx=1 if side or near else -.8)

    hands = {}
    def arm(near):
        sign = 1 if near else -1
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
        bone('upper-arm', root, elbow, 14)
        bone('forearm', elbow, grip, 13)
        part('hand', *grip, angle=-15 if near else 15)

    head_x, head_y = body_x + (1.8 if side else 0), shoulder - 15
    part('hair-back', head_x, head_y, pose.head_tilt)
    arm(False)
    leg(False)
    leg(True)
    part('tails', cx, hip-1, pose.step*4, sx=.7 if side else 1, sy=.42)
    part('torso', body_x, shoulder, sx=.65 if side else 1)
    # The strap passes under the near arm and terminates at the bag's top edge.
    pieces.append(f'<path d="M{body_x+7} {shoulder+3} L{cx-9} {hip+4}" stroke="#342b38" stroke-width="2.5"/><path d="M{body_x+7} {shoulder+3} L{cx-9} {hip+4}" stroke="#ae8265" stroke-width="1"/>')
    part('satchel', cx-10, hip+8, pose.step*5, sx=.8)
    arm(True)
    part('head-side' if side else 'head', head_x, head_y, pose.head_tilt, sx=.94 if not front and not side else 1)
    pieces.append(f'<g transform="translate({head_x} {head_y}) rotate({pose.head_tilt}) scale({.94 if not front and not side else 1} 1)">')
    if pose.blink:
        # Cover the eye apertures only; brows and nose retain their construction.
        for x in ([4] if side else [-2.5,4]):
            pieces.append(f'<path d="M{x-1.7} {.4} h3.4" stroke="#e8b58e" stroke-width="2.1"/><path d="M{x-1.7} {.6} q1.7 1 3.4 0" fill="none" stroke="#67484a" stroke-width=".55"/>')
    if pose.talk_open > .1:
        pieces.append(f'<ellipse cx="{1.3}" cy="{7}" rx="1.25" ry="{.3+pose.talk_open}" fill="#77404a"/>')
    pieces.append('</g>')
    # An engraved cipher wheel hangs from the belt, distinct from the held map.
    wx, wy = cx+7, hip+5
    pieces.append(f'<g transform="translate({wx} {wy})" stroke="#604849" stroke-width=".45"><circle r="3.8" fill="#d1a568"/><circle r="2.8" fill="#f1d59b"/><circle r="1.7" fill="#3b4f62"/>')
    for i in range(12):
        a = i*math.tau/12
        pieces.append(f'<path d="M{math.cos(a)*2.9} {math.sin(a)*2.9} L{math.cos(a)*3.5} {math.sin(a)*3.5}"/>')
    pieces.append('<path d="M0 -2 L.6 0 L0 1.5 L-.6 0Z" fill="#e6ba76"/></g>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" height="{image.height}" viewBox="0 0 {image.width/scale} {image.height/scale}">{_definitions()}<g stroke-linecap="round" stroke-linejoin="round">{"".join(pieces)}</g></svg>'
    image.alpha_composite(Image.open(BytesIO(resvg_py.svg_to_bytes(svg_string=svg, skip_system_fonts=True))).convert('RGBA'))
    return tuple(v*scale for v in hands[True])
