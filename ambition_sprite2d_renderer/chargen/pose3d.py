"""Poses in 3D, solved into each view's 2D rig channels.

A generated character's motion is authored ONCE, in the body frame of
``geometry`` (``l`` left, ``y`` down, ``z`` forward, centimetres), and every
view's ``RigDocument`` gets the same motion seen from its own camera. That is
what makes a clip agree across the five views, and what lets a turn pass
through the back views.

A :class:`Pose` says where the hands and feet go (3D targets), how the trunk
leans, bends and the whole body spins, and what the face and hands do. For a
view, :func:`solve_frame` turns it into channels the rig already reads:

* rotations: ``pelvis`` (a spin), ``torso`` and ``head``, each the 3D angle
  seen from the view (a forward lean shows from the side, a side bend from
  the front);
* ``root_x`` / ``root_y``;
* the IK chains: ``<side>_hand_x/_y`` and ``<side>_foot_x/_lift/_pitch``, the
  3D target projected; each limb's ``_bend`` (which way the elbow or knee
  points) is chosen by solving the limb in 3D with a pole and keeping the 2D
  branch nearer the projected joint;
* the hand's world angle (``_pitch``) when the pose names a hand direction.

A hand target is kept inside 97% of the arm's reach in that view (a 3D reach
toward the camera is shorter on screen), so no frame straightens an elbow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Tuple

from .body import Figure
from .geometry import Vec3, View, add3, norm3, scale3, sub3

#: An unturned hand part holds an item this many degrees above forward
#: (the game's ``posed_hand.rs`` ITEM_REST_ANGLE).
ITEM_REST_ANGLE = 24.0

Point = Tuple[float, float]
SIDES = (("near", "right"), ("far", "left"))


@dataclass(frozen=True)
class Hand:
    """A hand's target in the TRUNK frame, from its shoulder (cm), the way
    its elbow points (``pole``), and how far the wrist bends the hand off the
    line of its forearm (``wrist``, degrees, positive clockwise on screen
    facing right). A held item runs across the fist, so it points across the
    forearm, turned by ``wrist``: a sword is swung by the arm, as a person
    swings one, not by twisting the wrist round."""

    at: Vec3
    pole: Vec3 = (0.0, 0.3, -1.0)
    wrist: float = 0.0
    #: Where a held item points, in the trunk frame (a direction): the wrist
    #: is then turned so the item points there in each view, in place of
    #: ``wrist``.
    item: Optional[Vec3] = None
    #: A two-handed grip: the other hand closes on the item this far (cm)
    #: along it from this hand.
    two_hand: float = 0.0


@dataclass(frozen=True)
class Foot:
    """An ankle's offset from where it stands at rest (WORLD frame, cm; ``y``
    up is negative), the toe's lift in degrees, and the way the knee points."""

    at: Vec3 = (0.0, 0.0, 0.0)
    toe: float = 0.0
    pole: Vec3 = (0.0, 0.0, 1.0)
    #: True: the offset is from the HIP (the foot moves with the body, in the
    #: air); False: from the rest ankle on the ground.
    body: bool = False


@dataclass(frozen=True)
class Pose:
    """One key pose. Angles in degrees; a positive lean tips the trunk
    forward, a positive side bend tips it to the character's left, a positive
    spin turns the whole body forward about the hips (a forward flip)."""

    root: Vec3 = (0.0, 0.0, 0.0)
    spin: float = 0.0
    lean: float = 0.0
    side: float = 0.0
    head: Tuple[float, float] = (0.0, 0.0)
    hands: Mapping[str, Hand] = field(default_factory=dict)
    feet: Mapping[str, Foot] = field(default_factory=dict)
    #: Face channels (``face.face_channels``) and hand shapes, held as data.
    face: Mapping[str, float] = field(default_factory=dict)
    extra: Mapping[str, float] = field(default_factory=dict)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp3(a: Vec3, b: Vec3, t: float) -> Vec3:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t), _lerp(a[2], b[2], t))


def _arc(a: Vec3, b: Vec3, t: float) -> Vec3:
    """``t`` of the way from ``a`` to ``b`` round the origin: the direction
    turns (slerp) and the distance changes evenly. A limb swings in an arc
    about its root; a straight line between two reaches would fold it."""
    ra = math.sqrt(sum(c * c for c in a))
    rb = math.sqrt(sum(c * c for c in b))
    if ra < 1e-6 or rb < 1e-6:
        return _lerp3(a, b, t)
    ua, ub = scale3(a, 1.0 / ra), scale3(b, 1.0 / rb)
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(ua, ub))))
    om = math.acos(dot)
    if om < 1e-4:
        u = ua
    elif om > math.pi - 1e-3:
        return _lerp3(a, b, t)
    else:
        so = math.sin(om)
        u = add3(scale3(ua, math.sin((1 - t) * om) / so), scale3(ub, math.sin(t * om) / so))
    return scale3(u, _lerp(ra, rb, t))


def blend(a: Pose, b: Pose, t: float, rest: "RestFrame") -> Pose:
    """The pose ``t`` of the way from ``a`` to ``b``. A hand or foot one pose
    leaves out is at rest there."""
    hands = {}
    for side in set(a.hands) | set(b.hands):
        ha = a.hands.get(side) or rest.rest_hand(side)
        hb = b.hands.get(side) or rest.rest_hand(side)
        item = None
        if ha.item is not None or hb.item is not None:
            ia, ib = ha.item or hb.item, hb.item or ha.item
            item = norm3(_lerp3(ia, ib, t))
        hands[side] = Hand(_arc(ha.at, hb.at, t), norm3(_lerp3(ha.pole, hb.pole, t)), _lerp(ha.wrist, hb.wrist, t), item,
                           _lerp(ha.two_hand, hb.two_hand, t))
    feet = {}
    for side in set(a.feet) | set(b.feet):
        fa = a.feet.get(side) or Foot(body=(b.feet.get(side) or Foot()).body)
        fb = b.feet.get(side) or Foot(body=fa.body)
        if fa.body != fb.body:
            # From planted to in the air: express both from the hip.
            fa, fb = rest.foot_from_hip(side, fa), rest.foot_from_hip(side, fb)
        feet[side] = Foot(_arc(fa.at, fb.at, t) if fa.body else _lerp3(fa.at, fb.at, t), _lerp(fa.toe, fb.toe, t), norm3(_lerp3(fa.pole, fb.pole, t)), fa.body)
    face = {k: _lerp(a.face.get(k, 0.0), b.face.get(k, 0.0), t) for k in set(a.face) | set(b.face)}
    extra = {k: _lerp(a.extra.get(k, 0.0), b.extra.get(k, 0.0), t) for k in set(a.extra) | set(b.extra)}
    return Pose(
        root=_lerp3(a.root, b.root, t), spin=_lerp(a.spin, a.spin + _wrap(b.spin - a.spin), t), lean=_lerp(a.lean, b.lean, t), side=_lerp(a.side, b.side, t),
        head=(_lerp(a.head[0], b.head[0], t), _lerp(a.head[1], b.head[1], t)), hands=hands, feet=feet, face=face, extra=extra,
    )


class RestFrame:
    """A figure's rest joints and limb lengths (3D), for solving poses."""

    def __init__(self, fig: Figure) -> None:
        self.fig = fig
        j = fig.joints
        self.j = j
        self.ua = {s: math.dist(j[f"{s}_shoulder"], j[f"{s}_elbow"]) for s in ("right", "left")}
        self.fa = {s: math.dist(j[f"{s}_elbow"], j[f"{s}_wrist"]) for s in ("right", "left")}
        self.th = {s: math.dist(j[f"{s}_hip"], j[f"{s}_knee"]) for s in ("right", "left")}
        self.sh = {s: math.dist(j[f"{s}_knee"], j[f"{s}_ankle"]) for s in ("right", "left")}

    def rest_hand(self, side: str) -> Hand:
        return Hand(sub3(self.j[f"{side}_wrist"], self.j[f"{side}_shoulder"]))

    def forearm_dir(self, side: str) -> Vec3:
        return norm3(sub3(self.j[f"{side}_handtip"], self.j[f"{side}_wrist"]))

    def foot_from_hip(self, side: str, foot: Foot) -> Foot:
        if foot.body:
            return foot
        rel = sub3(add3(self.j[f"{side}_ankle"], foot.at), self.j[f"{side}_hip"])
        return Foot(rel, foot.toe, foot.pole, True)


# ---- 3D limb solve ----------------------------------------------------------------


#: How far a head turns on its neck, either way (degrees): a human's, and a
#: species head the neck goes into (``HeadModel.neck_f``).
HEAD_TURN = 60.0
SPECIES_HEAD_TURN = 32.0

#: The angle above forward a held item rests at in an unturned hand (the
#: runtime's ``ITEM_REST_ANGLE``; the fist art is drawn to it).
ITEM_REST = 24.0

#: The furthest a drawn elbow folds (degrees between upper arm and forearm
#: directions); the rig's two-bone solve cannot fold past straight back.
ELBOW_FOLD = 150.0

#: How far a segment pointing at the camera is swung off the view axis, as a
#: fraction of its depth.
CAMERA_CHEAT = 0.55


def _ik3(root: Vec3, target: Vec3, l1: float, l2: float, pole: Vec3, prev: Optional[Vec3] = None) -> Vec3:
    """The middle joint of a two-bone limb from ``root`` to ``target``,
    bending toward ``pole``.

    A pole nearly along the limb's line names no side; ``prev`` (the last
    frame's bend direction) then decides, in proportion to how little the
    pole says, so the joint never flips across the limb between frames."""
    d = sub3(target, root)
    dist = math.sqrt(sum(c * c for c in d))
    dist = max(1e-6, min(dist, (l1 + l2) * 0.999))
    u = norm3(d)
    # The part of the pole square to the limb's line.
    pn = norm3(pole) if sum(c * c for c in pole) > 1e-12 else pole
    p = sub3(pn, scale3(u, sum(a * b for a, b in zip(pn, u))))
    if prev is not None:
        q = sub3(prev, scale3(u, sum(a * b for a, b in zip(prev, u))))
        say = math.sqrt(sum(c * c for c in p))
        p = add3(p, scale3(q, max(0.0, 1.0 - say) * 2.0))
    if sum(c * c for c in p) < 1e-9:
        p = (0.0, 0.0, 1.0) if abs(u[2]) < 0.9 else (1.0, 0.0, 0.0)
    p = norm3(p)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    return add3(add3(root, scale3(u, a)), scale3(p, h))


def _ik2_middle(root: Point, target: Point, l1: float, l2: float, bend: float) -> Point:
    """The middle joint the rig's own 2D solver puts down for ``bend``."""
    from ..authoring.skeleton import two_bone_ik

    a1, _a2 = two_bone_ik(root, target, l1, l2, bend=bend)
    return (root[0] + l1 * math.cos(math.radians(a1)), root[1] + l1 * math.sin(math.radians(a1)))


def _rot2(v: Point, deg: float) -> Point:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _unit(v: Point, fallback) -> Point:
    n = math.hypot(*v)
    if n < 1e-6:
        return fallback or (0.0, 1.0)
    return (v[0] / n, v[1] / n)


def _angle(v: Point) -> float:
    return math.degrees(math.atan2(v[1], v[0]))


# ---- one frame in one view -------------------------------------------------------


class ViewSolver:
    """Solves poses into one view's rig channels."""

    def __init__(self, fig: Figure, view: View, doc: dict, px_per_cm: float) -> None:
        from ..authoring.rigdoc import RigDocument

        self.fig, self.view, self.doc, self.px = fig, view, doc, px_per_cm
        self.reset()
        self.rest = RestFrame(fig)
        self.frame = doc["frame"]
        bones = {b["name"]: b for b in doc["bones"]}
        self.bone_len = {n: float(b["length"]) for n, b in bones.items()}
        probe = dict(doc, clips={"rest": {"loop": False, "frames": 1, "duration_ms": 100, "channels": {}}})
        self._probe = RigDocument(probe)
        world, _ = self._probe.solve("rest", 0.0)
        self.rest_world = world
        j = fig.joints
        hip_c = view.project(((j["right_hip"][0] + j["left_hip"][0]) / 2, j["right_hip"][1], (j["right_hip"][2] + j["left_hip"][2]) / 2))
        # Screen cm -> frame px about the rest hip centre (the rig's own map).
        self.hip_c = hip_c
        self.chains = {c["channel_prefix"]: c for c in doc.get("ik_chains", [])}
        # How far the head turns on its neck either way (degrees): a head the
        # neck goes into (a horse's, a dog's) turns less than a human's, or
        # its carried neck kinks off the neck below.
        self.head_turn = HEAD_TURN if fig.model is None or fig.model.neck_f is None else SPECIES_HEAD_TURN
        self.legs = {c["channel_prefix"]: c for c in doc.get("ik_legs", [])}

    def reset(self) -> None:
        """Forget the last frame (a new clip starts)."""
        self.votes: Dict[str, list] = {}
        self._last: Dict[tuple, object] = {}

    def _keep_bend(self, pre: str, root: Point, target: Point, l1: float, l2: float, want: Point) -> float:
        """The side the joint bends to: the one nearer the 3D joint seen in
        this view. The margin is kept (``votes``) so a clip can settle on one
        side for the whole motion (``motion.solve_clip``)."""
        d = {b: math.dist(_ik2_middle(root, target, l1, l2, b), want) for b in (1.0, -1.0)}
        best = min(d, key=d.get)
        self.votes.setdefault(pre, []).append((best, abs(d[1.0] - d[-1.0])))
        return best

    def to_frame(self, p_cm: Point) -> Point:
        """Screen cm (``View.project``) -> channel px from (center_x, ground_y)."""
        return ((p_cm[0] - self.hip_c[0]) * self.px, p_cm[1] * self.px)

    def body_channels(self, pose: Pose) -> Dict[str, float]:
        v = self.view
        s, c = v.s, v.c
        out = {
            "pelvis": pose.spin * s,
            "torso": pose.lean * s + pose.side * c,
            "head": max(-self.head_turn, min(self.head_turn, pose.head[0] * s + pose.head[1] * c)),
        }
        rx, ry = v.project(pose.root)[0], pose.root[1]
        out["root_x"] = rx * self.px
        out["root_y"] = ry * self.px
        return out

    def _probe_world(self, body: Dict[str, float]):
        clip = {"loop": False, "frames": 1, "duration_ms": 100, "channels": {k: {"const": v} for k, v in body.items()}}
        self._probe.data["clips"]["probe"] = clip
        world, _ = self._probe.solve("probe", 0.0)
        return world

    def item_angle(self, item: Vec3, trunk_rot: float) -> float:
        """The screen angle (degrees, y down) a held item pointing ``item``
        (trunk frame) is drawn at. An item pointing nearly at the camera is
        drawn swung toward the way the character faces (forward and a little
        up, the hand's rest hold), so it never vanishes or flips."""
        v = self.view
        o0 = v.project((0.0, 0.0, 0.0))
        p = v.project(norm3(item))
        p = _rot2((p[0] - o0[0], p[1] - o0[1]), trunk_rot)
        n = math.hypot(*p)
        if n < 0.45:
            r = math.radians(-ITEM_REST)
            w = (0.45 - n) / 0.45
            p = (p[0] + w * 0.45 * math.cos(r), p[1] + w * 0.45 * math.sin(r))
        return math.degrees(math.atan2(p[1], p[0]))

    def solve(self, pose: Pose) -> Dict[str, float]:
        v = self.view
        body = self.body_channels(pose)
        out = dict(body)
        world = self._probe_world(body)
        cx, gy = float(self.frame["center_x"]), float(self.frame["ground_y"])
        trunk_rot = body["pelvis"] + body["torso"]
        j = self.fig.joints
        for depth, side in SIDES:
            # ---- the hand ----
            hand = pose.hands.get(side) or self.rest.rest_hand(side)
            pre = f"{depth}_hand"
            chain = self.chains.get(pre)
            if chain is None:
                continue
            up, lo = chain["upper"], chain["lower"]
            l1, l2 = self.bone_len[up], self.bone_len[lo]
            sw = world[up].origin
            sgn = -1.0 if side == "right" else 1.0
            out_dir = v.project((sgn, 0.0, 0.0))
            o0 = v.project((0.0, 0.0, 0.0))

            od = (out_dir[0] - o0[0], out_dir[1] - o0[1])
            three_quarter = abs(v.s) > 0.3 and abs(v.c) > 0.3
            facing_x = math.copysign(1.0, v.s * v.c)

            def seen(vec3: Vec3, key: str) -> Point:
                """The direction a 3D segment is drawn in this view (a unit
                vector). A segment pointing toward (or away from) the camera
                barely shows, so it is swung off the view axis by part of its
                depth, as an animator cheats a punch at the viewer: toward
                the character's outer side, or, in a view with no outer side
                (the side view looks along it), the way it was last drawn.
                The swing is added to the projection (never chosen in its
                place), so the drawn direction turns smoothly as a segment
                passes the view axis."""
                p = v.project(vec3)
                p = (p[0] - o0[0], p[1] - o0[1])
                length = math.sqrt(sum(c * c for c in vec3))
                lean_out = min(1.0, math.hypot(*od))
                prev = self._last.get((pre, "seen", key))
                if prev is None:
                    prev = _unit(p, None) if math.hypot(*p) > 0.05 * length else (_unit(od, None) if lean_out > 0.3 else (0.0, 1.0))
                if three_quarter:
                    # A three-quarter view: toward the camera is swung the way
                    # the character faces on screen, away from it the other
                    # way (the view turned a little toward the side view).
                    k = CAMERA_CHEAT * v.depth(vec3)
                    drawn = (p[0] + k * facing_x, p[1])
                else:
                    k = CAMERA_CHEAT * abs(v.depth(vec3))
                    way = (od[0] + prev[0] * (1.0 - lean_out), od[1] + prev[1] * (1.0 - lean_out) - 0.2)
                    drawn = (p[0] + k * way[0], p[1] + k * way[1])
                    k = abs(k)
                # Where the swing and the projection nearly cancel, the last
                # drawn way carries the segment through.
                shown = math.hypot(*drawn) / max(1e-6, length)
                short = max(0.0, 0.4 * abs(k) - math.hypot(*drawn))
                drawn = (drawn[0] + prev[0] * short * 2.0, drawn[1] + prev[1] * short * 2.0)
                drawn = _unit(drawn, prev)
                # A direction the view barely shows (a segment near the view
                # axis, or where the swing and projection nearly cancel)
                # turns only so far from the last frame's: what the
                # projection says there is mostly noise.
                if (pre, "seen", key) in self._last:
                    limit = 30.0 + 150.0 * min(1.0, shown / 0.6) ** 2
                    turn = _wrap(_angle(drawn) - _angle(prev))
                    if abs(turn) > limit:
                        drawn = _unit(_rot2(prev, math.copysign(limit, turn)), prev)
                self._last[(pre, "seen", key)] = drawn
                return drawn

            ua3, fa3 = self.rest.ua[side], self.rest.fa[side]
            reach = math.sqrt(sum(c * c for c in hand.at))
            at = hand.at if reach <= 0.95 * (ua3 + fa3) else scale3(hand.at, 0.95 * (ua3 + fa3) / reach)
            E3 = _ik3((0.0, 0.0, 0.0), at, ua3, fa3, hand.pole, self._last.get((pre, "pole")))
            self._last[(pre, "pole")] = norm3(E3)
            # The hand: in the direction the shoulder->hand reach is drawn,
            # at the same fraction of the drawn arm's reach as the 3D hand is
            # of the 3D arm's (the rig's bones keep their length, so a reach
            # at the camera is drawn as reach, swung off the view axis, not
            # as a folded elbow), kept between the elbow's furthest fold and
            # nearly straight.
            hdir = _rot2(seen(at, "h"), trunk_rot)
            frac = math.sqrt(sum(c * c for c in at)) / (ua3 + fa3)
            r_min = math.sqrt(l1 * l1 + l2 * l2 - 2 * l1 * l2 * math.cos(math.radians(180.0 - ELBOW_FOLD)))
            r = min(0.97 * (l1 + l2), max(r_min, frac * (l1 + l2)))
            target = (sw[0] + hdir[0] * r, sw[1] + hdir[1] * r)
            # The elbow's side: where the 3D elbow shows. It changes sides
            # only where that is cheap (the arm near straight, both sides
            # close), so a bent elbow never jumps across its arm.
            e_seen = _rot2(seen(E3, "u"), trunk_rot)
            mids = {bb: _ik2_middle(sw, target, l1, l2, bb) for bb in (1.0, -1.0)}
            want = (sw[0] + e_seen[0] * l1, sw[1] + e_seen[1] * l1)
            raw = min(mids, key=lambda bb: math.dist(mids[bb], want))
            prev_bend = self._last.get((pre, "bend"))
            if prev_bend is None or raw == prev_bend:
                bend = raw
            else:
                cheap = math.dist(mids[1.0], mids[-1.0]) < 0.45 * l1
                bend = raw if cheap else prev_bend
            self._last[(pre, "bend")] = bend
            e2 = mids[bend]
            out[f"{pre}_x"] = target[0] - cx
            out[f"{pre}_y"] = target[1] - gy
            out[f"{pre}_bend"] = bend
            if hand.item is not None:
                out[f"{pre}_item"] = self.item_angle(hand.item, trunk_rot)
                if hand.two_hand:
                    out[f"{pre}_two"] = hand.two_hand * self.px
            elif hand.wrist:
                out[f"{pre}_wrist"] = hand.wrist
            # ---- the foot ----
            foot = pose.feet.get(side) or Foot()
            fpre = f"{depth}_foot"
            leg = self.legs.get(fpre)
            if leg is None:
                continue
            A0 = j[f"{side}_ankle"]
            H3 = j[f"{side}_hip"]
            if foot.body:
                rel3 = foot.at
                hip2 = world[leg["upper"]].origin
                fv = v.project(rel3)
                f0 = v.project((0.0, 0.0, 0.0))
                frel = _rot2((fv[0] - f0[0], fv[1] - f0[1]), body["pelvis"])
                tgt = (hip2[0] + frel[0] * self.px, hip2[1] + frel[1] * self.px)
                A3 = add3(H3, rel3)
            else:
                A3 = add3(A0, foot.at)
                tgt = (cx + self.to_frame(v.project(A3))[0], gy + self.to_frame(v.project(A3))[1])
            ankle_h = float(self.frame.get("ankle_h", 0.0))
            hip2 = world[leg["upper"]].origin
            l1, l2 = self.bone_len[leg["upper"]], self.bone_len[leg["lower"]]
            dx, dy = tgt[0] - hip2[0], tgt[1] - hip2[1]
            dist = math.hypot(dx, dy)
            hi_r = (l1 + l2) * 0.995
            if dist > hi_r:
                tgt = (hip2[0] + dx * hi_r / dist, hip2[1] + dy * hi_r / dist)
            knee3 = _ik3(H3, A3, self.rest.th[side], self.rest.sh[side], foot.pole)
            k_rel = _rot2((v.project(knee3)[0] - v.project(H3)[0], v.project(knee3)[1] - v.project(H3)[1]),
                          body["pelvis"] if foot.body else 0.0)
            k2 = (hip2[0] + k_rel[0] * self.px, hip2[1] + k_rel[1] * self.px)
            bend = self._keep_bend(fpre, hip2, tgt, l1, l2, k2)
            out[f"{fpre}_x"] = tgt[0] - cx
            out[f"{fpre}_lift"] = (gy - ankle_h) - tgt[1]
            out[f"{fpre}_bend"] = bend
            toe_rest = sub3(j[f"{side}_toe"], A0)
            r = math.radians(-foot.toe)
            toe = (toe_rest[0], toe_rest[1] * math.cos(r) - toe_rest[2] * math.sin(r), toe_rest[1] * math.sin(r) + toe_rest[2] * math.cos(r))
            tv = v.project(toe)
            t0 = v.project((0.0, 0.0, 0.0))
            tdir = (tv[0] - t0[0], tv[1] - t0[1])
            if foot.body:
                tdir = _rot2(tdir, body["pelvis"])
            if math.hypot(*tdir) > 0.2:
                out[f"{fpre}_pitch"] = _angle(tdir)
            else:
                out[f"{fpre}_pitch"] = float(leg["rest_pitch"])
        out.update(pose.face)
        out.update(pose.extra)
        return out


def _wrap(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


__all__ = ["Foot", "Hand", "Pose", "RestFrame", "ViewSolver", "blend"]
