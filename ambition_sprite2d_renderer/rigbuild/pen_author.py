"""The Author's held pen, as SVG paths in root user units.

⛔⛔ IT WAS ONLY EVER IN THE GENERATED RIG. `build_author` authored a SWORD --
the one he put down in "The Author puts down the sword and picks up the pen" --
so the pen existed in exactly one place: the rig file the builder overwrites.
Rebuilding him from source handed him the sword back. Art in a generated file is
art one rebuild from gone; this is where it lives now.

One rigid part bound to `near_arm_hand`, drawn along that bone's axis so an
authored swing points the nib where the hand points. The coordinates are the
authored ones, recovered verbatim -- do not re-derive them from a formula, or the
nib moves.
"""

# (element id, path data, style)
PATHS = [
    ("author-pen-barrel",
     "M 108.9923,161.0329 L 107.5412,162.0488 L 95.5772,183.3145 L 88.4123,196.4957 L 91.8904,198.4712 L 99.5422,185.5667 L 111.6801,164.3997 L 111.8095,162.6331 Z",
     "fill:#a3202f;stroke:#141a24;stroke-width:0.5;stroke-linejoin:round"),
    ("author-pen-sheen",
     "M 110.6409,165.4195 L 92.1992,197.0366 L 91.4166,196.5921 L 109.7192,164.8959 Z",
     "fill:#d9556a;stroke:none"),
    ("author-pen-shade",
     "M 107.1628,163.4439 L 89.3820,195.4364 L 89.9211,195.7426 L 107.8236,163.8193 Z",
     "fill:#5e0f1a;stroke:none"),
    ("author-pen-band",
     "M 95.7754,182.2771 L 93.3581,186.6543 L 97.8101,189.1831 L 100.3317,184.8651 Z",
     "fill:#d9a441;stroke:#141a24;stroke-width:0.5;stroke-linejoin:round"),
    ("author-pen-band-lit",
     "M 99.4845,185.3039 L 97.7211,188.3274 L 96.7646,187.7842 L 98.5454,184.7705 Z",
     "fill:#ffe6a6;stroke:none"),
    ("author-pen-clip",
     "M 107.7728,162.4104 L 105.2081,163.4837 L 96.3639,179.6212 L 96.5879,181.8185 L 97.6341,179.6526 L 97.6293,178.7298 L 105.1601,165.0665 L 106.2682,164.7759 Z",
     "fill:#d9a441;stroke:#141a24;stroke-width:0.5;stroke-linejoin:round"),
    ("author-pen-collar",
     "M 88.6856,195.7309 L 87.1574,198.5430 L 90.7746,200.5976 L 92.4072,197.8448 Z",
     "fill:#8f6420;stroke:#141a24;stroke-width:0.5;stroke-linejoin:round"),
    ("author-pen-nib",
     "M 87.4885,198.0410 L 86.0645,200.9124 L 84.0472,205.5169 L 82.4654,209.6786 L 81.6140,212.3923 L 81.7184,212.4515 L 83.6131,210.3305 L 86.3775,206.8405 L 89.2992,202.7497 L 91.0361,200.0561 Z",
     "fill:#d9a441;stroke:#141a24;stroke-width:0.5;stroke-linejoin:round"),
    ("author-pen-nib-lit",
     "M 90.1596,200.7083 L 86.4130,206.1706 L 83.5846,209.8543 L 82.6671,210.9432 L 82.9057,210.1587 L 86.0019,205.4771 L 89.4119,200.2836 Z",
     "fill:#ffe6a6;stroke:none"),
    ("author-pen-breather",
     "M 87.3173,200.9340 L 86.4283,202.4991 L 87.7500,203.2498 L 88.6390,201.6847 Z",
     "fill:#4a3210;stroke:none"),
    ("author-pen-slit",
     "M 86.8923,202.5327 L 81.9732,211.6992 L 82.1471,211.7979 L 87.4836,202.8685 Z",
     "fill:#4a3210;stroke:none"),
]
