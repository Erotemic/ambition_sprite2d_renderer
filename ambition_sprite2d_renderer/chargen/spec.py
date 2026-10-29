"""The character record: what a generated character IS, as plain data.

A :class:`CharacterSpec` is small and serializable (JSON or YAML). The same
spec always draws the same character; :func:`generate` makes one from a base
and a seed, and :func:`crowd` makes many. A spec is also edited by hand: an
author changes a field and draws it again.

Generation draws EVERY field, in a fixed order, from the seed, and then
applies the fields an author gave (``overrides``). So an override changes only
the field it names: the rest of the character stays the same.

Bases: a body type (slim, average, broad, heavy) in each sex. A base gives the
range each body number is drawn from and the odds of each style; it never
limits what a hand-edited spec may say, only :data:`BOUNDS` does.

Families (``family.py``): the look a spec is drawn in (``standard``, the
default, or ``crew``). A family does not change what the seed draws: it
changes how the body numbers become a drawing. A standard spec does not
write its family, so its record (and its SVG) stays as it was.

Overlays (``overlay.py``): ``overlay`` names hand-drawn art that draws over
or replaces parts of the generated drawing, in every view. The figure
places it and the art draws it. A spec without one does not write the field.
"""

from __future__ import annotations

import copy
import json
import random
import re
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "ambition-chargen-v1"

# ---- vocabulary -------------------------------------------------------------------

SEXES = ("female", "male")
BUILDS = ("slim", "average", "broad", "heavy")

EYE_SHAPES = ("almond", "round", "narrow", "hooded", "downturned", "upturned")
BROWS = ("straight", "arched", "angled", "soft", "heavy")
NOSES = ("straight", "button", "long", "hooked", "broad", "upturned")
MOUTHS = ("neutral", "smile", "frown", "smirk")
JAWS = ("round", "square", "pointed", "long", "wide")
#: ``nihongami`` is the geisha's wig-like up-do (a shimada): it is a worn
#: thing, so it sits on any head, an animal's too. ``center_part`` is flat
#: hair parted in the middle and combed back; generation does not pick it.
HAIR_STYLES = ("bald", "balding", "buzz", "short", "side_part", "curly", "afro", "bob", "pixie", "long", "ponytail", "bun", "braid",
               "nihongami", "center_part")
FACIAL_HAIR = ("none", "stubble", "mustache", "goatee", "full_beard", "chops")

TOPS = ("tshirt", "shirt", "tunic", "blouse", "sweater")
SLEEVES = ("short", "long", "rolled")
NECKLINES = ("crew", "v", "collar", "scoop")
#: A ``kimono`` is ankle long, wrapped left over right, with wide hanging
#: sleeves; ``outer_length`` does not apply to it.
OUTERS = ("none", "vest", "jacket", "coat", "robe", "apron", "cardigan", "field_jacket", "kimono")
OUTER_LENGTHS = ("hip", "knee", "ankle")
BOTTOMS = ("trousers", "shorts", "skirt", "long_skirt")
#: ``geta``: tabi socks on raised wooden sandals (two teeth, a thong strap),
#: ``outfit.geta_height`` tall. Geta raise the whole figure.
SHOES = ("shoes", "boots", "geta")
#: ``helmet``, ``beret``, ``garrison_cap``, ``peaked_cap`` and ``campaign`` (a
#: drill instructor's brimmed hat with a pinched crown) are military.
HATS = ("none", "cap", "flat_cap", "brimmed", "beanie", "headscarf", "top_hat", "bowler", "helmet", "beret", "garrison_cap", "peaked_cap",
        "campaign")
#: ``obi``: the wide sash of a kimono, knotted at the back (``outfit.obi_knot``).
ACCESSORIES = ("glasses", "scarf", "belt", "necklace", "suspenders", "webbing", "dog_tags", "obi", "bow_tie")
SPECIES = ("human", "horse", "dog", "cat", "bird", "pigeon", "sea_lion", "alligator")
EAR_STYLES = ("default", "floppy", "pointed")
#: Face paint: ``geisha`` is white face paint (oshiroi) with red lips; on an
#: animal, a pale painted face and red on the jaw line.
MAKEUPS = ("none", "geisha")
#: A drawn motif on a kimono, near its hem and on its sleeves.
MOTIFS = ("none", "blossom", "dot")
OBI_KNOTS = ("taiko", "bow")
#: The slots a wardrobe item swaps in, and the kinds each slot takes.
SLOTS = {"hat": HATS, "outer": OUTERS, "top": TOPS, "legwear": BOTTOMS, "footwear": SHOES, "hair": HAIR_STYLES, "acc": ACCESSORIES}

# ---- palettes ----------------------------------------------------------------------

#: Skin tones, light to deep. The last three (2026-10-25) carry the range to
#: the deepest human skin; deep skin is drawn with a sheen (``drawkit.sheen``).
SKIN_TONES = ("#f6d9c6", "#efc6a8", "#e6b592", "#d9a17b", "#c68b63", "#ae7451", "#94603f", "#7b4e32", "#643d26", "#4f2f1e",
              "#432819", "#382114", "#2d1a10")
HAIR_COLORS = {
    "black": "#26201c", "dark_brown": "#3f2b1f", "brown": "#5f4029", "chestnut": "#7b4a2b", "auburn": "#8d3f23",
    "ginger": "#b4612d", "dark_blonde": "#9f7b47", "blonde": "#cfa964", "platinum": "#e2d2a6", "grey": "#9b9690", "white": "#dddad5",
}
EYE_COLORS = {"brown": "#5b3a22", "dark": "#2f2520", "hazel": "#7a6a33", "green": "#4e7a4a", "blue": "#4f7fae", "grey": "#7b8995"}
#: Cloth: earthy, workaday colours for townsfolk, and a few strong ones.
CLOTH = (
    "#7a4b2e", "#a4683a", "#5b6b3a", "#3f5a6e", "#6e3b3b", "#c9b28a", "#e6dec9", "#2f3440", "#4a3f5c", "#8a8f4a",
    "#b0453a", "#2e5e5a", "#c99a3c", "#5a5f66", "#24304a", "#9a7b5a", "#7d8f9e", "#8e5a78", "#3d4a2c", "#d8cfb8",
)
LEATHER = ("#4a3123", "#5e3b26", "#3a2a22", "#2c2522", "#6b4a33", "#7a5a3a")
#: Uniform cloth and metal of the Faction of Steel. ``webbing`` is the
#: canvas of a duty belt and its straps; ``brass`` is buttons and badges.
UNIFORM = {"olive_drab": "#5b6136", "khaki": "#b7a77a", "dark_olive": "#3d4a2c", "field_grey": "#6b6e60", "webbing": "#958b5c",
           "brass": "#b8913e"}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# ---- the record --------------------------------------------------------------------


@dataclass
class Body:
    height_cm: float = 172.0
    #: Head height (crown to chin) as a part of the height: 0.155 is 6.5
    #: heads, the cast's adult proportion (a cartoon head, not a child's).
    head: float = 0.155
    shoulders: float = 1.0
    chest: float = 1.0
    waist: float = 1.0
    hips: float = 1.0
    belly: float = 0.0
    bust: float = 0.0
    legs: float = 1.0
    arms: float = 1.0
    neck: float = 1.0
    limbs: float = 1.0
    #: 0 young adult .. 1 old: grey hair, a receding line, lines on the face.
    age: float = 0.3


@dataclass
class Face:
    eye_shape: str = "almond"
    eye_size: float = 1.0
    eye_spacing: float = 1.0
    brow: str = "straight"
    brow_weight: float = 1.0
    nose: str = "straight"
    nose_size: float = 1.0
    mouth: str = "neutral"
    mouth_width: float = 1.0
    lips: float = 1.0
    jaw: str = "round"
    jaw_width: float = 1.0
    chin: float = 1.0
    ears: float = 1.0
    ear_angle: float = 0.3
    #: Face paint (``MAKEUPS``).
    makeup: str = "none"


@dataclass
class Hair:
    style: str = "short"
    facial: str = "none"
    #: Hair volume: 0 flat .. 1 full.
    volume: float = 0.5
    #: How long ``long`` / ``braid`` / ``ponytail`` hang: 0 shoulder .. 1 mid-back.
    length: float = 0.5
    #: Hair ornaments (kanzashi) in a ``nihongami``: how many (0 .. 6), and
    #: their colour ("": the outfit's accent colour).
    ornaments: int = 0
    ornament_color: str = ""


@dataclass
class Head:
    #: The head on the humanoid body: a person, or an anthropomorphic animal.
    species: str = "human"
    #: How far an animal's muzzle (or beak) reaches.
    muzzle: float = 1.0
    #: A dog's ears: floppy or pointed (``default`` is the species' own).
    ears: str = "default"


@dataclass
class Palette:
    skin: str = SKIN_TONES[3]
    hair: str = HAIR_COLORS["brown"]
    eyes: str = EYE_COLORS["brown"]


@dataclass
class Outfit:
    top: str = "shirt"
    sleeves: str = "long"
    neckline: str = "collar"
    top_color: str = CLOTH[6]
    tucked: bool = True
    outer: str = "none"
    outer_length: str = "hip"
    outer_color: str = CLOTH[0]
    outer_open: bool = True
    bottom: str = "trousers"
    bottom_color: str = CLOTH[7]
    shoes: str = "shoes"
    shoe_color: str = LEATHER[0]
    hat: str = "none"
    hat_color: str = CLOTH[2]
    accessories: List[str] = field(default_factory=list)
    accent_color: str = CLOTH[10]
    #: Alternates drawn into the rig but hidden: ``"slot:kind"`` items
    #: (``"hat:bowler"``, ``"outer:coat"``) a clip or a game can swap in.
    wardrobe: List[str] = field(default_factory=list)
    #: The outer garment's second colour: a kimono's collar, lining and hem
    #: ("": a light tone of ``outer_color``).
    trim_color: str = ""
    #: A kimono's drawn motif (``MOTIFS``), in the trim colour.
    motif: str = "none"
    #: The obi's colour ("": the accent colour) and its knot at the back.
    obi_color: str = ""
    obi_knot: str = "taiko"
    #: How tall geta are, in cm (sole of the foot to the ground).
    geta_height: float = 9.0


@dataclass
class CharacterSpec:
    name: str = "Townsperson"
    base: str = "average_female"
    seed: int = 0
    body: Body = field(default_factory=Body)
    face: Face = field(default_factory=Face)
    hair: Hair = field(default_factory=Hair)
    palette: Palette = field(default_factory=Palette)
    outfit: Outfit = field(default_factory=Outfit)
    head: Head = field(default_factory=Head)
    #: The family the spec is drawn in (``family.FAMILIES``).
    family: str = "standard"
    #: Hand-drawn art over its parts (``overlay.py``: the name of a file in
    #: ``data/overlays``), or "" for none. The seed does not draw it.
    overlay: str = ""

    @property
    def sex(self) -> str:
        return BASES[self.base].sex

    def to_dict(self) -> Dict[str, Any]:
        d = {"schema": SCHEMA, **asdict(self)}
        if d["family"] == "standard":
            # The default is not written: a standard record stays as it was.
            del d["family"]
        if not d["overlay"]:
            del d["overlay"]
        for (section, name), default in OPTIONAL_DEFAULTS.items():
            if d[section][name] == default:
                del d[section][name]
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CharacterSpec":
        data = dict(data)
        schema = data.pop("schema", SCHEMA)
        if schema != SCHEMA:
            raise ValueError(f"not a {SCHEMA} record: schema={schema!r}")
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"unknown spec fields: {sorted(unknown)}")
        kw: Dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            sub = _SECTIONS.get(f.name)
            if sub is not None:
                kw[f.name] = _section_from_dict(sub, value, f.name)
            else:
                kw[f.name] = value
        return cls(**kw)

    @classmethod
    def from_json(cls, text: str) -> "CharacterSpec":
        return cls.from_dict(json.loads(text))

    @classmethod
    def load(cls, path: Path | str) -> "CharacterSpec":
        """Read a JSON or YAML spec. A partial file (some fields left out) is
        completed from its ``base`` and ``seed`` by :func:`generate`."""
        text = Path(path).read_text(encoding="utf8")
        if str(path).endswith((".yaml", ".yml")):
            import yaml

            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
        return complete(data)

    def save(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if str(path).endswith((".yaml", ".yml")):
            import yaml

            path.write_text(yaml.safe_dump(self.to_dict(), sort_keys=False), encoding="utf8")
        else:
            path.write_text(self.to_json(), encoding="utf8")
        return path


_SECTIONS = {"body": Body, "face": Face, "hair": Hair, "palette": Palette, "outfit": Outfit, "head": Head}
#: Fields added after the first records: a record writes one only when it is
#: not at its default, so an older record (and its SVG) stays as it was.
OPTIONAL_DEFAULTS: Dict[Tuple[str, str], Any] = {
    ("face", "makeup"): "none",
    ("hair", "ornaments"): 0,
    ("hair", "ornament_color"): "",
    ("outfit", "trim_color"): "",
    ("outfit", "motif"): "none",
    ("outfit", "obi_color"): "",
    ("outfit", "obi_knot"): "taiko",
    ("outfit", "geta_height"): 9.0,
}


def _section_from_dict(kind, value: Mapping[str, Any], where: str):
    if not isinstance(value, Mapping):
        raise ValueError(f"{where} must be a mapping")
    unknown = set(value) - {f.name for f in fields(kind)}
    if unknown:
        raise ValueError(f"unknown {where} fields: {sorted(unknown)}")
    return kind(**dict(value))


# ---- bounds ---------------------------------------------------------------------------

#: The hard limits a spec, generated or hand-edited, must keep (inclusive).
BOUNDS: Dict[str, Tuple[float, float]] = {
    "body.height_cm": (145.0, 205.0),
    "body.head": (0.135, 0.185),
    "body.shoulders": (0.8, 1.25),
    "body.chest": (0.8, 1.35),
    "body.waist": (0.8, 1.6),
    "body.hips": (0.85, 1.4),
    "body.belly": (0.0, 1.0),
    "body.bust": (0.0, 1.0),
    "body.legs": (0.9, 1.1),
    "body.arms": (0.9, 1.1),
    "body.neck": (0.8, 1.2),
    "body.limbs": (0.8, 1.4),
    "body.age": (0.0, 1.0),
    "face.eye_size": (0.75, 1.2),
    "face.eye_spacing": (0.85, 1.15),
    "face.brow_weight": (0.5, 1.6),
    "face.nose_size": (0.75, 1.3),
    "face.mouth_width": (0.8, 1.2),
    "face.lips": (0.5, 1.4),
    "face.jaw_width": (0.85, 1.18),
    "face.chin": (0.5, 1.5),
    "face.ears": (0.8, 1.2),
    "face.ear_angle": (0.0, 1.0),
    "hair.volume": (0.0, 1.0),
    "hair.length": (0.0, 1.0),
    "head.muzzle": (0.6, 1.4),
    "outfit.geta_height": (3.0, 16.0),
}

CHOICES: Dict[str, Sequence[str]] = {
    "face.eye_shape": EYE_SHAPES,
    "face.brow": BROWS,
    "face.nose": NOSES,
    "face.mouth": MOUTHS,
    "face.jaw": JAWS,
    "hair.style": HAIR_STYLES,
    "hair.facial": FACIAL_HAIR,
    "outfit.top": TOPS,
    "outfit.sleeves": SLEEVES,
    "outfit.neckline": NECKLINES,
    "outfit.outer": OUTERS,
    "outfit.outer_length": OUTER_LENGTHS,
    "outfit.bottom": BOTTOMS,
    "outfit.shoes": SHOES,
    "outfit.hat": HATS,
    "head.species": SPECIES,
    "head.ears": EAR_STYLES,
    "face.makeup": MAKEUPS,
    "outfit.motif": MOTIFS,
    "outfit.obi_knot": OBI_KNOTS,
}
#: Colours that may be "" (derived from another colour).
OPTIONAL_COLORS = ("hair.ornament_color", "outfit.trim_color", "outfit.obi_color")
COLORS = ("palette.skin", "palette.hair", "palette.eyes", "outfit.top_color", "outfit.outer_color", "outfit.bottom_color",
          "outfit.shoe_color", "outfit.hat_color", "outfit.accent_color")


def _get(spec: CharacterSpec, dotted: str):
    section, name = dotted.split(".")
    return getattr(getattr(spec, section), name)


def validate(spec: CharacterSpec) -> List[str]:
    """Every way ``spec`` breaks the schema; an empty list is a valid spec."""
    errors: List[str] = []
    if spec.base not in BASES:
        errors.append(f"base {spec.base!r} is not one of {sorted(BASES)}")
    from .family import FAMILIES

    if spec.family not in FAMILIES:
        errors.append(f"family {spec.family!r} is not one of {sorted(FAMILIES)}")
    if spec.overlay:
        from .overlay import available

        if spec.overlay not in available():
            errors.append(f"overlay {spec.overlay!r} is not one of {available()}")
    for key, (lo, hi) in BOUNDS.items():
        v = _get(spec, key)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            errors.append(f"{key} must be a number, not {v!r}")
        elif not lo <= float(v) <= hi:
            errors.append(f"{key}={v} is outside [{lo}, {hi}]")
    for key, allowed in CHOICES.items():
        v = _get(spec, key)
        if v not in allowed:
            errors.append(f"{key}={v!r} is not one of {list(allowed)}")
    for key in COLORS:
        v = _get(spec, key)
        if not isinstance(v, str) or not _HEX.match(v):
            errors.append(f"{key}={v!r} is not a #rrggbb colour")
    for acc in spec.outfit.accessories:
        if acc not in ACCESSORIES:
            errors.append(f"outfit.accessories: {acc!r} is not one of {list(ACCESSORIES)}")
    if len(set(spec.outfit.accessories)) != len(spec.outfit.accessories):
        errors.append("outfit.accessories repeats an item")
    for item in spec.outfit.wardrobe:
        slot, _, kind = item.partition(":")
        if slot not in SLOTS or kind not in SLOTS[slot]:
            errors.append(f"outfit.wardrobe: {item!r} is not slot:kind with a slot of {sorted(SLOTS)}")
    for key in ("outfit.tucked", "outfit.outer_open"):
        if not isinstance(_get(spec, key), bool):
            errors.append(f"{key} must be true or false")
    for key in OPTIONAL_COLORS:
        v = _get(spec, key)
        if v != "" and (not isinstance(v, str) or not _HEX.match(v)):
            errors.append(f"{key}={v!r} is not a #rrggbb colour or empty")
    n = spec.hair.ornaments
    if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 6:
        errors.append(f"hair.ornaments={n!r} is not a whole number in [0, 6]")
    # Geta raise the whole figure, so the rig's bones differ from a figure in
    # shoes: geta and other footwear cannot be swapped in one rig.
    shoes = {spec.outfit.shoes} | {i.partition(":")[2] for i in spec.outfit.wardrobe if i.startswith("footwear:")}
    if "geta" in shoes and len(shoes) > 1:
        errors.append("outfit.wardrobe: geta and other footwear cannot be alternates of each other (geta raise the figure)")
    return errors


def check(spec: CharacterSpec) -> CharacterSpec:
    errors = validate(spec)
    if errors:
        raise ValueError("invalid character spec:\n  " + "\n  ".join(errors))
    return spec


# ---- bases ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Base:
    """A body type in one sex: the range of each body number, and style odds."""

    key: str
    sex: str
    build: str
    ranges: Mapping[str, Tuple[float, float]]
    hair_odds: Mapping[str, float]
    facial_odds: Mapping[str, float]

    @property
    def display_name(self) -> str:
        return f"{self.build.title()} ({self.sex.title()})"


def _ranges(sex: str, build: str) -> Dict[str, Tuple[float, float]]:
    female = sex == "female"
    r: Dict[str, Tuple[float, float]] = {
        "height_cm": (152.0, 178.0) if female else (160.0, 194.0),
        "head": (0.148, 0.166),
        "legs": (0.95, 1.05),
        "arms": (0.96, 1.04),
        "neck": (0.9, 1.1) if female else (0.88, 1.06),
        "age": (0.0, 1.0),
        "bust": (0.55, 0.95) if female else (0.0, 0.0),
        "belly": (0.0, 0.12),
    }
    r.update({
        "slim": {"shoulders": (0.88, 0.97), "chest": (0.86, 0.95), "waist": (0.84, 0.93), "hips": (0.9, 0.98), "limbs": (0.84, 0.94)},
        "average": {"shoulders": (0.95, 1.04), "chest": (0.96, 1.04), "waist": (0.95, 1.05), "hips": (0.97, 1.05), "limbs": (0.95, 1.05),
                    "belly": (0.0, 0.25)},
        "broad": {"shoulders": (1.07, 1.18), "chest": (1.06, 1.16), "waist": (0.98, 1.08), "hips": (0.98, 1.06), "limbs": (1.08, 1.2),
                  "belly": (0.0, 0.2), "height_cm": (162.0, 180.0) if female else (172.0, 196.0)},
        "heavy": {"shoulders": (1.0, 1.1), "chest": (1.12, 1.26), "waist": (1.22, 1.48), "hips": (1.12, 1.3), "limbs": (1.14, 1.3),
                  "belly": (0.5, 1.0), "neck": (0.86, 0.98)},
    }[build])
    return r


_HAIR_FEMALE = {"bob": 3, "long": 4, "ponytail": 3, "bun": 3, "short": 1, "curly": 2, "afro": 1, "pixie": 2, "braid": 2, "side_part": 1}
_HAIR_MALE = {"short": 4, "side_part": 3, "buzz": 2, "bald": 1, "balding": 1, "curly": 2, "afro": 1, "long": 1, "ponytail": 1}
_FACIAL_MALE = {"none": 5, "stubble": 2, "mustache": 2, "goatee": 1, "full_beard": 2, "chops": 1}

BASES: Dict[str, Base] = {
    f"{build}_{sex}": Base(
        key=f"{build}_{sex}",
        sex=sex,
        build=build,
        ranges=_ranges(sex, build),
        hair_odds=_HAIR_FEMALE if sex == "female" else _HAIR_MALE,
        facial_odds={"none": 1} if sex == "female" else _FACIAL_MALE,
    )
    for build in BUILDS
    for sex in SEXES
}


# ---- generation ---------------------------------------------------------------------------


def _pick(rng: random.Random, odds: Mapping[str, float]) -> str:
    names = sorted(odds)
    total = sum(odds[n] for n in names)
    x = rng.random() * total
    for n in names:
        x -= odds[n]
        if x <= 0.0:
            return n
    return names[-1]


def _uniform(rng: random.Random, lo: float, hi: float, nd: int = 3) -> float:
    return round(lo + (hi - lo) * rng.random(), nd)


def _draw(base: Base, seed: int) -> CharacterSpec:
    """Every field of a character of ``base``, drawn from ``seed`` in a fixed
    order (an added field goes at the END, so old seeds keep their looks)."""
    rng = random.Random(f"{SCHEMA}:{base.key}:{seed}")
    female = base.sex == "female"
    body = Body(**{k: _uniform(rng, *base.ranges[k], nd=1 if k == "height_cm" else 3) for k in (
        "height_cm", "head", "shoulders", "chest", "waist", "hips", "belly", "bust", "legs", "arms", "neck", "limbs", "age")})
    face = Face(
        eye_shape=_pick(rng, {s: 1 for s in EYE_SHAPES}),
        eye_size=_uniform(rng, 0.85, 1.1),
        eye_spacing=_uniform(rng, 0.92, 1.08),
        brow=_pick(rng, {"straight": 3, "arched": 3 if female else 1, "angled": 2, "soft": 2, "heavy": 0.5 if female else 2}),
        brow_weight=_uniform(rng, 0.7, 1.05) if female else _uniform(rng, 0.95, 1.45),
        nose=_pick(rng, {n: 1 for n in NOSES}),
        nose_size=_uniform(rng, 0.85, 1.05) if female else _uniform(rng, 0.92, 1.22),
        mouth=_pick(rng, {"neutral": 4, "smile": 3, "frown": 1, "smirk": 1}),
        mouth_width=_uniform(rng, 0.88, 1.12),
        lips=_uniform(rng, 0.85, 1.3) if female else _uniform(rng, 0.6, 1.05),
        jaw=_pick(rng, {"round": 3, "pointed": 2 if female else 1, "square": 1 if female else 3, "long": 1, "wide": 1 if female else 2}),
        jaw_width=_uniform(rng, 0.88, 1.02) if female else _uniform(rng, 0.96, 1.14),
        chin=_uniform(rng, 0.7, 1.3),
        ears=_uniform(rng, 0.85, 1.15),
        ear_angle=_uniform(rng, 0.0, 0.8),
    )
    style = _pick(rng, base.hair_odds)
    facial = _pick(rng, base.facial_odds)
    hair = Hair(style=style, facial=facial, volume=_uniform(rng, 0.2, 0.9), length=_uniform(rng, 0.0, 1.0))
    old = body.age > 0.72
    hair_name = _pick(rng, {"black": 3, "dark_brown": 4, "brown": 4, "chestnut": 2, "auburn": 1, "ginger": 1, "dark_blonde": 2,
                            "blonde": 2, "platinum": 0.5, "grey": 0.3, "white": 0.2})
    aged_name = _pick(rng, {"grey": 3, "white": 2, hair_name: 1})
    if old:
        hair_name = aged_name
    palette = Palette(
        skin=SKIN_TONES[rng.randrange(len(SKIN_TONES))],
        hair=HAIR_COLORS[hair_name],
        eyes=EYE_COLORS[_pick(rng, {"brown": 4, "dark": 3, "hazel": 2, "green": 1, "blue": 2, "grey": 1})],
    )
    recede = rng.random()
    if old and style not in ("bald", "balding") and not female and recede < 0.35:
        hair.style = "balding"
    top = _pick(rng, {"tshirt": 2, "shirt": 4, "tunic": 2, "blouse": 3 if female else 0, "sweater": 2})
    outer = _pick(rng, {"none": 5, "vest": 2, "jacket": 2, "coat": 2, "robe": 0.4, "apron": 1.2, "cardigan": 1.2 if female else 0.5})
    bottom = _pick(rng, {"trousers": 4, "shorts": 0.6, "skirt": 2.5, "long_skirt": 2.5} if female else {"trousers": 8, "shorts": 1})
    cloth = list(CLOTH)
    colors = rng.sample(cloth, 4)
    outfit = Outfit(
        top=top,
        sleeves=_pick(rng, {"long": 4, "short": 2, "rolled": 2}),
        neckline=_pick(rng, {"crew": 3, "v": 2, "collar": 3 if top in ("shirt", "blouse") else 0.5, "scoop": 1.5 if female else 0.2}),
        top_color=colors[0],
        tucked=rng.random() < (0.7 if top in ("shirt", "blouse") else 0.25),
        outer=outer,
        outer_length=_pick(rng, {"hip": 3, "knee": 2, "ankle": 1}),
        outer_color=colors[1],
        outer_open=rng.random() < 0.7,
        bottom=bottom,
        bottom_color=colors[2],
        shoes=_pick(rng, {"shoes": 3, "boots": 2}),
        shoe_color=LEATHER[rng.randrange(len(LEATHER))],
        hat=_pick(rng, {"none": 9, "cap": 1, "flat_cap": 1.2, "brimmed": 1, "beanie": 0.8, "headscarf": 0.8 if female else 0.1,
                        "top_hat": 0.3, "bowler": 0.5}),
        hat_color=colors[3],
        accessories=sorted(a for a, p in (("glasses", 0.22), ("scarf", 0.12), ("belt", 0.35), ("necklace", 0.15 if female else 0.03),
                                          ("suspenders", 0.0 if female else 0.1)) if rng.random() < p),
        accent_color=cloth[rng.randrange(len(cloth))],
    )
    coat_pick = rng.random()
    muzzle = _uniform(rng, 0.85, 1.2)
    ears = _pick(rng, {"floppy": 1, "pointed": 1})
    if outfit.outer == "robe":
        outfit.outer_length = "ankle"
        outfit.outer_open = False
    if outfit.outer == "apron":
        outfit.outer_length = "knee" if outfit.outer_length == "hip" else outfit.outer_length
    spec = CharacterSpec(name=f"{base.display_name} #{seed}", base=base.key, seed=int(seed), body=body, face=face, hair=hair,
                         palette=palette, outfit=outfit, head=Head("human", muzzle, ears))
    spec._coat_pick = coat_pick  # type: ignore[attr-defined]
    return spec


def _merge(dst: Dict[str, Any], src: Mapping[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, Mapping) and isinstance(dst.get(k), dict):
            _merge(dst[k], v)
        else:
            dst[k] = copy.deepcopy(v)
    return dst


def generate(base: Optional[str] = None, seed: int = 0, overrides: Optional[Mapping[str, Any]] = None) -> CharacterSpec:
    """A character of ``base`` (one of :data:`BASES`; drawn from the seed when
    ``None``) for ``seed``, with ``overrides`` (a partial spec mapping) applied
    on top. The same arguments always give the same spec. The family
    (``overrides["family"]``) does not change what the seed draws."""
    if base is None:
        base = sorted(BASES)[random.Random(f"{SCHEMA}:base:{seed}").randrange(len(BASES))]
    if base not in BASES:
        raise ValueError(f"unknown base {base!r}; one of {sorted(BASES)}")
    first = _draw(BASES[base], seed)
    drawn = first.to_dict()
    over: Dict[str, Any] = {}
    if overrides:
        over = dict(overrides)
        over.pop("schema", None)
        over.pop("base", None)
        over.pop("seed", None)
        _merge(drawn, over)
    species = drawn["head"]["species"]
    if species != "human" and "skin" not in over.get("palette", {}):
        # An animal's skin is its coat, drawn from the species' coats.
        from .species import COATS, COATS_BY_SEX

        coats = COATS_BY_SEX.get(species, {}).get(BASES[first.base].sex, COATS[species])
        drawn["palette"]["skin"] = coats[int(first._coat_pick * len(coats)) % len(coats)]  # type: ignore[attr-defined]
    return check(CharacterSpec.from_dict(drawn))


def complete(data: Mapping[str, Any]) -> CharacterSpec:
    """A spec from a mapping that may leave fields out: they are drawn from
    its ``base`` and ``seed``."""
    data = dict(data)
    return generate(data.get("base"), int(data.get("seed", 0)), data)


def crowd(count: int, seed: int = 0, bases: Optional[Sequence[str]] = None, species: Optional[str] = None,
          family: Optional[str] = None) -> List[CharacterSpec]:
    """``count`` characters, one per seed ``seed*1000 + i``, cycling through
    ``bases`` (every base by default) so a crowd has every body type; all of
    ``species`` when it is given, all in ``family`` when it is given."""
    keys = list(bases) if bases else sorted(BASES, key=lambda k: (BASES[k].build != "average", k))
    out = []
    for i in range(count):
        s = int(seed) * 1000 + i
        over: Dict[str, Any] = {}
        if species:
            over["head"] = {"species": species}
        if family:
            over["family"] = family
        spec = generate(keys[i % len(keys)], s, over or None)
        spec.name = f"Townsfolk {i + 1:02d}"
        out.append(spec)
    return out


def spec_vector(spec: CharacterSpec) -> List[float]:
    """Every field as a number in [0, 1] (choices as one-hot), for measuring
    how far apart two characters are."""
    vec: List[float] = []
    for key, (lo, hi) in sorted(BOUNDS.items()):
        vec.append((float(_get(spec, key)) - lo) / (hi - lo))
    for key, allowed in sorted(CHOICES.items()):
        v = _get(spec, key)
        vec.extend(1.0 if v == a else 0.0 for a in allowed)
    for key in COLORS:
        h = _get(spec, key)
        vec.extend(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    vec.extend(1.0 if a in spec.outfit.accessories else 0.0 for a in ACCESSORIES)
    vec.append(1.0 if spec.sex == "female" else 0.0)
    return vec


def spec_distance(a: CharacterSpec, b: CharacterSpec) -> float:
    va, vb = spec_vector(a), spec_vector(b)
    return sum((x - y) ** 2 for x, y in zip(va, vb)) ** 0.5


__all__ = [
    "BASES", "BOUNDS", "Base", "Body", "CHOICES", "CharacterSpec", "Face", "Hair", "Outfit", "Palette", "SCHEMA", "check", "complete",
    "crowd", "generate", "spec_distance", "spec_vector", "validate",
]
