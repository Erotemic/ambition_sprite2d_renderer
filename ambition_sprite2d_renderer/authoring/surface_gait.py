"""Plan foot contacts for a part-based 2D walking rig.

A support foot stays at one world point. A swing foot moves to the next
contact point. A caller supplies the body's path and a surface probe.
The probe can return a floor, a slope, a wall, or a ceiling contact.

The gait supplies only IK goals. It does not select body poses, eye targets,
or attacks. The caller can combine those actions with the leg goals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Callable, Mapping

Point = tuple[float, float]


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _unit(a: Point) -> Point:
    length = math.hypot(*a)
    if length < 1e-8:
        raise ValueError("surface direction has zero length")
    return (a[0] / length, a[1] / length)


@dataclass(frozen=True)
class SurfacePose:
    """The rig floor anchor and its world-space travel direction."""

    anchor: Point
    tangent: Point

    @property
    def down(self) -> Point:
        t = _unit(self.tangent)
        return (-t[1], t[0])

    def world(self, local: Point) -> Point:
        t = _unit(self.tangent)
        d = self.down
        return (self.anchor[0] + t[0] * local[0] + d[0] * local[1],
                self.anchor[1] + t[1] * local[0] + d[1] * local[1])

    def local(self, world: Point) -> Point:
        v = (world[0] - self.anchor[0], world[1] - self.anchor[1])
        return (_dot(v, _unit(self.tangent)), _dot(v, self.down))


@dataclass(frozen=True)
class SurfaceContact:
    point: Point
    normal: Point  # Points away from the surface.


@dataclass(frozen=True)
class Leg:
    name: str
    rest_tip: Point  # At the end of the claw, in rig floor-anchor coordinates.
    tarsus_length: float
    tarsus_pitch: float  # Local degrees, positive clockwise.
    phase: float


@dataclass
class ContactCache:
    """Keep landing points until a new step needs a new point.

    Make one cache per moving body. Clear it if the body teleports or the
    surface changes. This keeps the surface probe out of the frame loop.
    """

    landings: dict[tuple[str, int], SurfaceContact] = field(default_factory=dict)

    def get(
        self,
        key: tuple[str, int],
        get_contact: Callable[[], SurfaceContact],
    ) -> SurfaceContact:
        contact = self.landings.get(key)
        if contact is not None:
            return contact
        contact = get_contact()
        self.landings[key] = contact
        if len(self.landings) > 64:
            # Discard old landings. Each step keeps only a few recent points.
            cycle = key[1]
            self.landings = {
                k: value for k, value in self.landings.items()
                if k[1] >= cycle - 2
            }
        return contact

    def clear(self) -> None:
        self.landings.clear()


@dataclass(frozen=True)
class Gait:
    stride: float = 26.0
    stance: float = 0.68
    lift: float = 18.0

    def __post_init__(self) -> None:
        if not (0.0 < self.stance < 1.0):
            raise ValueError("stance must be between zero and one")
        if self.stride <= 0.0 or self.lift < 0.0:
            raise ValueError("stride must be positive and lift must not be negative")

    def phase_at(self, time: float, offset: float) -> float:
        return (time + offset) % 1.0

    def foot_offset(self, time: float, offset: float) -> Point:
        """Return a local stride offset and the foot's positive lift."""
        phase = self.phase_at(time, offset)
        if phase < self.stance:
            return (self.stride * (0.5 - phase / self.stance), 0.0)
        u = (phase - self.stance) / (1.0 - self.stance)
        sweep = u * u * (3.0 - 2.0 * u)
        return (self.stride * (sweep - 0.5), self.lift * math.sin(math.pi * u) ** 2)

    def expressions(self, offset: float) -> tuple[str, str]:
        """Emit the same trajectory for a RigDocument math channel."""
        p = f"((t+{offset:.6f})%1)"
        u = f"(({p}-{self.stance:.6f})/{1.0-self.stance:.6f})"
        s = f"({u}*{u}*(3-2*{u}))"
        x = (f"({self.stride / 2:.6f}-{self.stride / self.stance:.6f}*{p} "
             f"if {p} < {self.stance:.6f} else "
             f"{-self.stride/2:.6f}+{self.stride:.6f}*{s})")
        lift = (f"(0 if {p} < {self.stance:.6f} else "
                f"{self.lift:.6f}*sin(pi*{u})**2)")
        return x, lift

    def planar_channels(self, leg: Leg) -> dict[str, dict]:
        """Bake a local flat-floor gait into ordinary IK channel expressions."""
        x, lift = self.expressions(leg.phase)
        prefix = f"{leg.name}_contact"
        tip_rad = math.radians(leg.tarsus_pitch)
        ankle_x = leg.rest_tip[0] - leg.tarsus_length * math.cos(tip_rad)
        ankle_y = leg.rest_tip[1] - leg.tarsus_length * math.sin(tip_rad)
        return {
            f"{prefix}_x": {"expr": f"{ankle_x:.8f}+{x}"},
            f"{prefix}_y": {"expr": f"{ankle_y:.8f}-{lift}"},
        }

    def contact_channels(
        self,
        time: float,
        legs: Mapping[str, Leg],
        frame_at: Callable[[float], SurfacePose],
        probe: Callable[[Point, Point], SurfaceContact],
        *,
        cache: ContactCache | None = None,
    ) -> dict[str, float]:
        """Return external IK goals for contacts on any probed surface.

        ``time`` counts walk cycles and can exceed one. ``frame_at`` returns
        the body floor anchor for any cycle time. A support contact uses the
        same world point until that leg begins its next swing. The caller can
        change the surface path and probe without changing the leg rig.
        """
        now = frame_at(time)
        goals: dict[str, float] = {}
        for leg in legs.values():
            whole = math.floor(time + leg.phase)
            start = whole - leg.phase
            phase = self.phase_at(time, leg.phase)

            def landing(when: float) -> SurfaceContact:
                def find() -> SurfaceContact:
                    frame = frame_at(when)
                    tip = frame.world((leg.rest_tip[0] + self.stride / 2.0,
                                       leg.rest_tip[1]))
                    return probe(tip, frame.down)
                if cache is None:
                    return find()
                cycle = round(when + leg.phase)
                return cache.get((leg.name, cycle), find)

            old = landing(start)
            if phase < self.stance:
                contact = old.point
                outward = _unit(old.normal)
            else:
                next_contact = landing(start + 1.0)
                u = (phase - self.stance) / (1.0 - self.stance)
                sweep = u * u * (3.0 - 2.0 * u)
                n = _unit((old.normal[0] * (1 - sweep) + next_contact.normal[0] * sweep,
                           old.normal[1] * (1 - sweep) + next_contact.normal[1] * sweep))
                height = self.lift * math.sin(math.pi * u) ** 2
                contact = (
                    old.point[0] * (1-sweep) + next_contact.point[0] * sweep + n[0] * height,
                    old.point[1] * (1-sweep) + next_contact.point[1] * sweep + n[1] * height,
                )
                outward = n
            # Match the claw's local pitch to the surface normal.
            d = (-outward[0], -outward[1])
            local_down = (_dot(d, _unit(now.tangent)), _dot(d, now.down))
            pitch = leg.tarsus_pitch + math.degrees(math.atan2(-local_down[0], local_down[1]))
            p = math.radians(pitch)
            rel_x, rel_y = now.local(contact)
            prefix = f"{leg.name}_contact"
            goals[f"{prefix}_x"] = rel_x - leg.tarsus_length * math.cos(p)
            goals[f"{prefix}_y"] = rel_y - leg.tarsus_length * math.sin(p)
            goals[f"{prefix}_pitch"] = pitch
        return goals
