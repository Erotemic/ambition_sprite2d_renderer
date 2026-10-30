"""Which knobs of a spec change the drawing.

Two things decide it.

``REQUIRES``: a field draws only when another field allows it (a kimono's
motif needs a kimono). The table is MEASURED, not read from the docs
(2026-10-25: ``outer_length`` draws for a jacket, coat or cardigan only), and
``tests/test_chargen_applies.py`` measures every rule again by drawing.

``measure(species)``: what a head species draws. Each field is drawn at its
values on one character of that species (with its ``REQUIRES`` met) and
compared by its SVG: a field whose values all draw the same picture does
nothing for that species, and a choice keeps one value of each distinct
picture (an alligator draws no hair, so of the hair styles only ``bald``
and the ``nihongami`` wig remain). It costs about a second a value; the
studio measures once per version of this package and caches it.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

from . import spec as S

#: ``field -> (other field, the values of the other that let it draw)``. For
#: ``outfit.accessories`` the value is an item the list must hold.
REQUIRES: Dict[str, Tuple[str, Tuple[Any, ...]]] = {
    "hair.length": ("hair.style", ("long", "ponytail", "braid")),
    "hair.volume": ("hair.style", ("short", "side_part", "curly", "afro", "bob", "pixie", "long", "bun", "center_part")),
    "hair.ornaments": ("hair.style", ("nihongami",)),
    "hair.ornament_color": ("hair.style", ("nihongami",)),
    "outfit.outer_color": ("outfit.outer", tuple(o for o in S.OUTERS if o != "none")),
    "outfit.outer_length": ("outfit.outer", ("jacket", "coat", "cardigan")),
    "outfit.outer_open": ("outfit.outer", ("jacket", "coat", "cardigan", "field_jacket")),
    "outfit.trim_color": ("outfit.outer", ("kimono",)),
    "outfit.motif": ("outfit.outer", ("kimono",)),
    "outfit.obi_color": ("outfit.accessories", ("obi",)),
    "outfit.obi_knot": ("outfit.accessories", ("obi",)),
    "outfit.geta_height": ("outfit.shoes", ("geta",)),
    "outfit.hat_color": ("outfit.hat", tuple(h for h in S.HATS if h != "none")),
    "outfit.tucked": ("outfit.top", ("tshirt", "shirt", "blouse", "sweater")),
}

#: The views a measure draws: a field that shows only from the back (an obi's
#: knot) or the side still counts.
VIEW_KEYS = ("front_3q", "side", "back")
_TWO_COLORS = ("#1f77b4", "#d62728")


def _get(d: Mapping[str, Any], dotted: str) -> Any:
    section, name = dotted.split(".")
    return (d.get(section) or {}).get(name)


def _set(d: Dict[str, Any], dotted: str, value: Any) -> Dict[str, Any]:
    d = json.loads(json.dumps(d))
    section, name = dotted.split(".")
    d.setdefault(section, {})[name] = value
    return d


def allowed(spec_dict: Mapping[str, Any], dotted: str) -> bool:
    """Whether ``dotted`` draws, given the rest of ``spec_dict`` (``REQUIRES``)."""
    rule = REQUIRES.get(dotted)
    if rule is None:
        return True
    other, values = rule
    have = _get(spec_dict, other)
    if other == "outfit.accessories":
        return any(v in (have or []) for v in values)
    return have in values


def enable(spec_dict: Dict[str, Any], dotted: str) -> Dict[str, Any]:
    """``spec_dict`` with ``dotted``'s requirement met."""
    rule = REQUIRES.get(dotted)
    if rule is None or allowed(spec_dict, dotted):
        return spec_dict
    other, values = rule
    if other == "outfit.accessories":
        return _set(spec_dict, other, sorted(set(_get(spec_dict, other) or []) | {values[0]}))
    return _set(spec_dict, other, values[0])


def fingerprint(spec_dict: Mapping[str, Any]) -> str:
    """The identity of what ``spec_dict`` draws in ``VIEW_KEYS``."""
    from .geometry import VIEW_BY_KEY
    from .rig import character_svg

    svg = character_svg(S.complete(spec_dict), [VIEW_BY_KEY[k] for k in VIEW_KEYS], joints=False)
    svg = re.sub(r"<metadata.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    return hashlib.sha1(svg.encode()).hexdigest()[:16]


def base(species: str) -> Dict[str, Any]:
    """The character a measure varies: plain clothes, no hat, short hair, so
    that no other field hides the one measured."""
    d = S.generate("average_female", 1, {"head": {"species": species}}).to_dict()
    d["hair"].update(style="short", facial="none")
    d["outfit"].update(hat="none", outer="none", accessories=[], shoes="shoes", top="shirt")
    return d


def knobs() -> List[Tuple[str, List[Any]]]:
    """Every field a measure varies, with the values it draws."""
    out: List[Tuple[str, List[Any]]] = []
    for key, values in S.CHOICES.items():
        if key != "head.species":
            out.append((key, list(values)))
    for key, (lo, hi) in S.BOUNDS.items():
        out.append((key, [lo, hi]))
    for key in (*S.COLORS, *S.OPTIONAL_COLORS):
        out.append((key, list(_TWO_COLORS)))
    out.append(("hair.ornaments", [0, 6]))
    for key in ("outfit.tucked", "outfit.outer_open"):
        out.append((key, [False, True]))
    for acc in S.ACCESSORIES:
        out.append((f"accessory:{acc}", [False, True]))
    return out


def variant(species: str, key: str, value: Any) -> Dict[str, Any]:
    """The measured character with ``key`` at ``value``."""
    d = base(species)
    if key.startswith("accessory:"):
        acc = key.split(":", 1)[1]
        return _set(d, "outfit.accessories", [acc] if value else [])
    return _set(enable(d, key), key, value)


def tasks(species: Iterable[str]) -> List[Tuple[str, str, Any]]:
    return [(sp, key, v) for sp in species for key, values in knobs() for v in values]


def summarize(results: Mapping[Tuple[str, str, Any], str]) -> Dict[str, Dict[str, Any]]:
    """``species -> {"fields": {key: draws}, "values": {choice: kept values}}``
    from ``(species, key, value) -> fingerprint``.

    A field that draws nothing for EVERY species measured is not the head's
    doing: it waits on something the measured character lacks (the accent
    colour of an item it does not wear), so it counts as drawing. The same
    holds for a choice's values."""
    species = sorted({k[0] for k in results})
    raw: Dict[str, Dict[str, Any]] = {}
    for sp in species:
        fields: Dict[str, bool] = {}
        values: Dict[str, List[Any]] = {}
        for key, vals in knobs():
            prints = [results[(sp, key, v)] for v in vals]
            fields[key] = len(set(prints)) > 1
            if key in S.CHOICES:
                seen, kept = set(), []
                for v, p in zip(vals, prints):
                    if p not in seen:
                        seen.add(p)
                        kept.append(v)
                values[key] = kept
        raw[sp] = {"fields": fields, "values": values}
    if len(species) > 1:
        for key, vals in knobs():
            if not any(raw[sp]["fields"][key] for sp in species):
                for sp in species:
                    raw[sp]["fields"][key] = True
            if key in S.CHOICES:
                somewhere = {v for sp in species for v in raw[sp]["values"][key]}
                for sp in species:
                    kept = set(raw[sp]["values"][key]) | (set(vals) - somewhere)
                    raw[sp]["values"][key] = [v for v in vals if v in kept]
    return raw


def measure(species: Sequence[str], mapper: Callable = map) -> Dict[str, Dict[str, Any]]:
    """Measure ``species`` (``mapper`` may be a process pool's ``map``)."""
    todo = tasks(species)
    prints = mapper(_fingerprint_task, todo)
    return summarize(dict(zip(todo, prints)))


def _fingerprint_task(task: Tuple[str, str, Any]) -> str:
    return fingerprint(variant(*task))


#: Modules of the package that do not draw: editing them keeps a measure.
_NOT_DRAWING = {"studio.py", "cli.py", "__main__.py"}


def version() -> str:
    """The version of the drawing code: a measure is valid for it alone."""
    h = hashlib.sha1()
    for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
        if path.name not in _NOT_DRAWING:
            h.update(path.read_bytes())
    return h.hexdigest()[:16]
