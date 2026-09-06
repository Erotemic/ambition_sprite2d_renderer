"""The Officer's duty sidearm and the holster it comes out of, as SVG paths.

⭐ A GUN THAT APPEARS FROM NOWHERE IS WORSE THAN NO GUN. The holster is
permanent art on his belt, bound to `pelvis`, so the draw has somewhere to come
from and every other frame of him carries the reason he is armed. The pistol
itself is an ALTERNATE -- drawn, but at zero opacity until a clip asks for it --
which is the same mechanism as his fist.

Coordinates are in the Officer's ART space (millimetres, inside the view's scale
group). The pistol is authored in the near hand bone's own frame: `s` runs along
wrist -> handtip so the BORE points wherever the hand points, and `t` runs across
it. An authored aim therefore points the muzzle by pointing the hand, exactly as
the Author's pen and the Pointed Polygon's sword do.
"""
import math

# Near hand bone: wrist -> handtip, in the Officer's own art units.
WRIST = (129.0, 142.0)
TIP = (131.0, 162.0)
#: The web of the hand, a little distal of the wrist: a fist closes AROUND a
#: grip, it does not hold it at the wrist joint.
GRIP_ORIGIN = (130.0, 148.5)

ANGLE = math.degrees(math.atan2(TIP[1] - WRIST[1], TIP[0] - WRIST[0]))
U = (math.cos(math.radians(ANGLE)), math.sin(math.radians(ANGLE)))
V = (-U[1], U[0])

STEEL = "#2b2f36"
STEEL_LIT = "#4a515c"
STEEL_DARK = "#171a1f"
GRIP_POLY = "#22252a"
HOLSTER = "#241d18"
HOLSTER_LIT = "#3a2f26"


def p(s, t):
    """Point at `s` along the bore and `t` across it."""
    return (GRIP_ORIGIN[0] + s * U[0] + t * V[0],
            GRIP_ORIGIN[1] + s * U[1] + t * V[1])


def poly(*pairs):
    pts = [p(s, t) for s, t in pairs]
    return "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts) + " Z"


def line(style, width, *pairs):
    pts = [p(s, t) for s, t in pairs]
    return "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in pts), \
        f"fill:none;stroke:{style};stroke-width:{width};stroke-linecap:round"


#: ⛔ THE BORE SITS OFF THE HAND AXIS, NOT ON IT. Drawn centred, the slide runs
#: through his own knuckles and the pistol reads as a rod skewering the fist.
#: `BORE_T` is how far to the thumb side it sits; the grip fills the gap.
BORE_T = -3.4
MUZZLE = 17.5

PATHS = [
    # Slide: the long top mass, square at the back, tapering to the muzzle.
    ("officer-sidearm-slide",
     poly((-7.6, BORE_T - 2.4), (MUZZLE, BORE_T - 2.4), (MUZZLE, BORE_T + 1.0),
          (-7.6, BORE_T + 1.0)),
     f"fill:{STEEL};stroke:{STEEL_DARK};stroke-width:0.4;stroke-linejoin:round"),
    # The lit top edge, so the slide reads as a block rather than a bar.
    ("officer-sidearm-slide-lit",
     poly((-6.8, BORE_T - 2.1), (MUZZLE - 0.8, BORE_T - 2.1), (MUZZLE - 0.8, BORE_T - 1.3),
          (-6.8, BORE_T - 1.3)),
     f"fill:{STEEL_LIT};stroke:none"),
    # Muzzle: a darker face so the business end is legible at 128px.
    ("officer-sidearm-muzzle",
     poly((MUZZLE - 1.6, BORE_T - 2.2), (MUZZLE, BORE_T - 2.2), (MUZZLE, BORE_T + 0.8),
          (MUZZLE - 1.6, BORE_T + 0.8)),
     f"fill:{STEEL_DARK};stroke:none"),
    # Rear sight.
    ("officer-sidearm-sight",
     poly((-6.4, BORE_T - 3.4), (-4.8, BORE_T - 3.4), (-4.8, BORE_T - 2.3),
          (-6.4, BORE_T - 2.3)),
     f"fill:{STEEL_DARK};stroke:none"),
    # Frame under the slide, forward of the trigger.
    ("officer-sidearm-frame",
     poly((-2.2, BORE_T + 1.0), (9.4, BORE_T + 1.0), (9.4, BORE_T + 2.6),
          (-2.2, BORE_T + 2.6)),
     f"fill:{STEEL};stroke:{STEEL_DARK};stroke-width:0.4;stroke-linejoin:round"),
    # Trigger guard.
    ("officer-sidearm-guard",
     poly((-1.4, BORE_T + 2.4), (5.2, BORE_T + 2.4), (5.8, BORE_T + 4.4),
          (3.6, BORE_T + 6.0), (-0.4, BORE_T + 6.0), (-1.4, BORE_T + 4.4)),
     f"fill:{STEEL};stroke:{STEEL_DARK};stroke-width:0.4;stroke-linejoin:round"),
    ("officer-sidearm-guard-hole",
     poly((-0.2, BORE_T + 3.2), (4.2, BORE_T + 3.2), (4.4, BORE_T + 4.3),
          (2.8, BORE_T + 5.0), (0.2, BORE_T + 5.0), (-0.6, BORE_T + 4.2)),
     "fill:#000000;fill-opacity:0.55;stroke:none"),
    # Grip, raked back the way a service pistol's is.
    ("officer-sidearm-grip",
     poly((-6.8, BORE_T + 1.4), (-1.6, BORE_T + 1.4), (-2.6, BORE_T + 11.6),
          (-8.6, BORE_T + 11.6)),
     f"fill:{GRIP_POLY};stroke:{STEEL_DARK};stroke-width:0.4;stroke-linejoin:round"),
    ("officer-sidearm-grip-check",
     poly((-6.2, BORE_T + 4.0), (-2.6, BORE_T + 4.0), (-3.2, BORE_T + 9.6),
          (-7.4, BORE_T + 9.6)),
     "fill:#000000;fill-opacity:0.28;stroke:none"),
    # Magazine base, so the grip does not end in a point.
    ("officer-sidearm-magbase",
     poly((-8.8, BORE_T + 11.2), (-2.4, BORE_T + 11.2), (-2.6, BORE_T + 12.6),
          (-9.0, BORE_T + 12.6)),
     f"fill:{STEEL_DARK};stroke:none"),
]

#: The holster, in the Officer's ART space directly (it rides the PELVIS, not a
#: hand, so it is not authored in the bore frame). A flapped duty holster on the
#: near hip, hanging off the belt line his shirt hem already draws.
HOLSTER_PATHS = [
    ("officer-holster-body",
     "M 118.6,150.4 L 128.4,150.4 L 128.9,163.2 "
     "C 128.9,165.2 127.6,166.4 125.4,166.4 "
     "L 121.4,166.4 C 119.2,166.4 118.0,165.2 118.0,163.2 Z",
     f"fill:{HOLSTER};stroke:#0d0b09;stroke-width:0.45;stroke-linejoin:round"),
    ("officer-holster-flap",
     "M 117.9,148.2 L 129.1,148.2 L 129.4,153.6 "
     "C 129.4,154.6 128.6,155.2 127.4,155.2 "
     "L 119.4,155.2 C 118.2,155.2 117.6,154.6 117.6,153.6 Z",
     f"fill:{HOLSTER_LIT};stroke:#0d0b09;stroke-width:0.45;stroke-linejoin:round"),
    ("officer-holster-stud",
     "M 122.6,152.0 L 124.4,152.0 L 124.4,153.8 L 122.6,153.8 Z",
     "fill:#8d7a48;stroke:none"),
    ("officer-holster-belt-loop",
     "M 119.4,146.0 L 121.4,146.0 L 121.4,149.6 L 119.4,149.6 Z",
     f"fill:{HOLSTER_LIT};stroke:#0d0b09;stroke-width:0.4"),
]

if __name__ == "__main__":
    print(f"hand bone angle = {ANGLE:.3f}")
    for eid, d, style in PATHS + HOLSTER_PATHS:
        print(f'<path id="{eid}" style="{style}" d="{d}" />')
