"""Emit the Author's held sword as SVG paths in root user units.

Follows the Pointed Polygon sword template: one rigid part bound to
``near_arm_hand`` whose blade continues the hand bone's axis distally, so every
authored swing points the blade where the hand points.
"""
import math

# Near hand bone: wrist -> handtip (root SVG user units, mm).
WRIST = (108.06, 161.92)
TIP = (101.78, 174.02)
# The fist grips the sword off the wrist centre, the way a hand closes around a
# grip rather than skewering it.
GRIP_ORIGIN = (105.5, 166.5)

ANGLE = math.degrees(math.atan2(TIP[1] - WRIST[1], TIP[0] - WRIST[0]))
U = (math.cos(math.radians(ANGLE)), math.sin(math.radians(ANGLE)))
V = (-U[1], U[0])


def p(s, t):
    """Point at ``s`` along the blade axis and ``t`` across it."""
    return (
        GRIP_ORIGIN[0] + s * U[0] + t * V[0],
        GRIP_ORIGIN[1] + s * U[1] + t * V[1],
    )


def poly(*pairs):
    pts = [p(s, t) for s, t in pairs]
    return "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts) + " Z"


# Blade length, measured from the face of the guard. His arm is the ruler: a
# sword reads as a sword when the reach it adds is the reach he already has.
ARM_LENGTH = 36.99  # near_shoulder -> near_elbow -> near_wrist
GUARD_FACE = 9.2
BLADE_TIP = GUARD_FACE + ARM_LENGTH * 1.15

PATHS = [
    # Blade: a long tapered leaf with a straight back edge.
    ("author-sword-blade",
     poly((9.0, -3.0), (BLADE_TIP - 7.7, -1.9), (BLADE_TIP, 0.0), (BLADE_TIP - 7.7, 1.9), (9.0, 3.0)),
     "fill:#c8ced8;stroke:#141a24;stroke-width:0.45;stroke-linejoin:round"),
    # Fuller: the bright facet down the blade's near face.
    ("author-sword-fuller",
     poly((10.5, -1.5), (BLADE_TIP - 8.7, -0.85), (BLADE_TIP - 4.7, 0.0), (BLADE_TIP - 8.7, 0.75), (10.5, 1.4)),
     "fill:#eef2f8;stroke:none"),
    # Crossguard.
    ("author-sword-guard", poly((6.6, -6.2), (GUARD_FACE, -5.8), (GUARD_FACE, 5.8), (6.6, 6.2)),
     "fill:#b8813a;stroke:#141a24;stroke-width:0.45;stroke-linejoin:round"),
    # Grip, wrapped.
    ("author-sword-grip", poly((-3.4, -1.5), (6.8, -1.7), (6.8, 1.7), (-3.4, 1.5)),
     "fill:#4a3020;stroke:#141a24;stroke-width:0.45;stroke-linejoin:round"),
    ("author-sword-wrap-1", poly((-1.2, -1.6), (-0.2, -1.6), (-0.2, 1.6), (-1.2, 1.6)),
     "fill:#6a4630;stroke:none"),
    ("author-sword-wrap-2", poly((2.0, -1.65), (3.0, -1.65), (3.0, 1.65), (2.0, 1.65)),
     "fill:#6a4630;stroke:none"),
    # Pommel.
    ("author-sword-pommel", poly((-6.4, -2.2), (-3.2, -2.4), (-3.2, 2.4), (-6.4, 2.2)),
     "fill:#b8813a;stroke:#141a24;stroke-width:0.45;stroke-linejoin:round"),
]

if __name__ == "__main__":
    print(f"hand bone angle = {ANGLE:.3f}")
    for eid, d, style in PATHS:
        print(f'<path id="{eid}" style="{style}" d="{d}" />')
