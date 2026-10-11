"""Stable, descriptive Inkscape object names for the GNU-ton scholar.

Every drawable is explicitly mapped to its artistic role, *not* numbered by
Inkscape. The rig-part ids remain intact. The generated SVG is both the
human-editable artwork and the sprite/rig input.

Mutually exclusive variants are sublayers of shared Eyes, Mouths, or Book
folders. Non-default variants are hidden in the SVG editor, but a marked
hidden variant is shown by the subset rasterizer when its rig part is sampled.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"
INK_LABEL = f"{{{INK}}}label"
INK_MODE = f"{{{INK}}}groupmode"
DRAWABLES = {"ellipse", "circle", "path", "rect", "polygon", "polyline", "line", "use"}

ET.register_namespace("", SVG)
ET.register_namespace("inkscape", INK)

# One precise purpose per primitive, in generator order. If a designer adds a
# new primitive, update this list instead of allowing another 'ellipse205'.
DRAWABLE_PURPOSES: dict[str, tuple[str, ...]] = {
    "far_foot_art": ("Rear shoe outline", "Rear shoe leather shine", "Rear shoe gold buckle", "Rear shoe sole seam"),
    "far_shin": ("Rear white stocking outline", "Rear stocking front highlight", "Rear stocking cuff seam"),
    "far_breeches": ("Rear upper trouser leg", "Rear trouser leg highlight", "Rear trouser knee seam"),
    "far_coat_tail": ("Rear coat tail outline", "Rear coat tail blue fold", "Rear coat tail gold hem piping"),
    "near_coat_tail": ("Front coat tail outline", "Front coat tail blue fold", "Front coat tail gold hem piping"),
    "wig_queue": ("Tied wig queue outer mass", "Tied wig queue cream highlight", "Queue curl shading line", "Queue ribbon left end", "Queue ribbon right end"),
    "far_arm_upper": ("Rear upper coat sleeve outline", "Rear upper sleeve blue fill", "Rear upper sleeve cuff trim"),
    "far_arm_lower": ("Rear forearm coat sleeve outline", "Rear forearm sleeve highlight", "Rear forearm gold cuff piping"),
    "far_cuff": ("Rear linen wrist cuff", "Rear wrist cuff fold"),
    "principia_open_cover": ("Opened book outer cover", "Opened book centre spine gold crease"),
    "principia_open_left": ("Opened book left paper page", "Left page top writing", "Left page middle writing", "Left page bottom writing"),
    "principia_open_right": ("Opened book right paper page", "Right page top writing", "Right page middle writing", "Right page bottom writing"),
    "principia_book": ("Closed book leather silhouette", "Closed book front leather panel", "Closed book exposed pages", "Closed book gold border", "Closed book central embossed emblem background", "Closed book embossed ornament", "Closed book bottom gold edge"),
    "far_hand_fist": ("Rear hand fist silhouette", "Rear hand knuckle highlight", "Rear hand finger crease"),
    "neck_base": ("Neck skin connecting head to torso", "Neck shadow behind cravat"),
    "torso_coat": ("Coat body and waist outer silhouette", "Left coat seam", "Right coat seam"),
    "pelvis_panel": ("Pelvis bridge outer silhouette", "Pelvis bridge inner panel", "Pelvis bridge central button"),
    "waistcoat": ("Burgundy waistcoat silhouette", "Waistcoat top gold button", "Waistcoat middle gold button", "Waistcoat bottom gold button"),
    "far_lapel": ("Rear jacket lapel outer shape", "Rear lapel gold piping"),
    "near_lapel": ("Front jacket lapel outer shape", "Front lapel gold piping"),
    "cravat": ("White neck cravat and jabot outline", "White cravat left fold", "Cravat fold-shadow line"),
    "coat_pin": ("Gold lapel pin diamond base", "Lapel pin inner diamond"),
    "near_breeches": ("Front upper trouser leg", "Front trouser highlight", "Front knee seam"),
    "near_shin": ("Front white stocking silhouette", "Front stocking highlight", "Front stocking cuff seam"),
    "near_shoe": ("Front shoe outer leather", "Front shoe leather shine", "Front shoe gold buckle", "Front shoe sole seam"),
    "wig_back_mass": ("Powdered wig rear volume silhouette", "Powdered wig rear cream mass", "Powdered wig rear light highlight"),
    "head_face": ("Face skin and round jaw outline", "Forehead skin highlight", "Rosy blush on cheek", "Small triangular nose", "Visible ear outer ellipse", "Inner ear fold line"),
    "wig_crown": ("Powdered wig crown outline", "Wig crown left cream highlight", "Wig crown right shaded section", "Wig crown left curl crease", "Wig crown right curl crease", "Wig crown back fold"),
    "wig_curl_0": ("Upper wig ringlet outer circle", "Upper ringlet cream inner highlight", "Upper ringlet spiral curl"),
    "wig_curl_1": ("Middle wig ringlet outer circle", "Middle ringlet cream inner highlight", "Middle ringlet spiral curl"),
    "wig_curl_2": ("Lower wig ringlet outer circle", "Lower ringlet cream inner highlight", "Lower ringlet spiral curl"),
    "eye_angry": (
        "Actor-right NEAR eye (canvas-left) focused sclera",
        "Actor-right NEAR eye focused pupil", "Actor-right NEAR eye pupil catchlight",
        "Actor-right NEAR eye stern brow",
        "Actor-left FAR eye (canvas-right) focused sclera",
        "Actor-left FAR eye focused pupil", "Actor-left FAR eye pupil catchlight",
        "Actor-left FAR eye stern brow"),
    "eye_open": (
        "Actor-right NEAR eye (canvas-left) neutral sclera",
        "Actor-right NEAR eye neutral pupil", "Actor-right NEAR eye pupil catchlight",
        "Actor-right NEAR eye natural brow",
        "Actor-left FAR eye (canvas-right) neutral sclera",
        "Actor-left FAR eye neutral pupil", "Actor-left FAR eye pupil catchlight",
        "Actor-left FAR eye natural brow"),
    "eye_surprised": (
        "Actor-right NEAR eye (canvas-left) surprised sclera",
        "Actor-right NEAR eye surprised pupil", "Actor-right NEAR eye pupil catchlight",
        "Actor-right NEAR eye raised brow",
        "Actor-left FAR eye (canvas-right) surprised sclera",
        "Actor-left FAR eye surprised pupil", "Actor-left FAR eye pupil catchlight",
        "Actor-left FAR eye raised brow"),
    "eye_shut": (
        "Actor-right NEAR closed eyelid", "Actor-left FAR closed eyelid",
        "Actor-right NEAR strained brow", "Actor-left FAR strained brow",
        "Actor-right NEAR outer crease"),
    "eye_dead": (
        "Actor-right NEAR knocked-out descending X stroke",
        "Actor-right NEAR knocked-out ascending X stroke",
        "Actor-left FAR knocked-out descending X stroke",
        "Actor-left FAR knocked-out ascending X stroke",
        "Actor-right NEAR knocked-out brow", "Actor-left FAR knocked-out brow"),
    "eye_dizzy": ("Actor-right NEAR large dazed spiral",
                   "Actor-left FAR small dazed spiral"),
    "mouth_closed": ("Closed mouth small expression line",),
    "mouth_smile": ("Smug smile curved expression line",),
    "mouth_open": ("Open mouth dark cavity", "Open mouth pale top teeth"),
    "mouth_wavy": ("Dazed mouth wavy contour",),
    "mouth_grit": ("Strained gritted teeth silhouette", "Gritted teeth centre crease"),
    "near_arm_upper": ("Front upper coat sleeve outline", "Front upper sleeve blue fold highlight", "Front sleeve elbow trim"),
    "near_arm_lower": ("Front forearm coat sleeve outline", "Front forearm blue highlight", "Front wrist gold cuff trim"),
    "near_cuff": ("Front white linen wrist cuff", "Front cuff fold seam"),
    "quill": ("Quill feather outer silhouette", "Quill vanes white highlight", "Quill brown shaft at grip", "Quill full central brown rib", "Feather lower barb crease", "Feather middle barb crease", "Feather upper barb crease", "Feather tip barb crease"),
    "near_hand_fist": ("Front hand fist outer silhouette", "Front hand knuckle highlight", "Front hand finger fold"),
    "dizzy_stars": ("Dizzy stars left five-point sparkle", "Dizzy stars upper five-point sparkle", "Dizzy stars right five-point sparkle"),
    "flying_apple": ("Flying apple red fruit body", "Apple skin red glint", "Apple brown stem", "Apple green leaf"),
}

# Each family becomes one collapsible Inkscape layer with one sublayer per
# variant. Names and opacity channels distinguish which can be visible in one
# pose. Non-expression props are NOT presented as exclusive choices.
FAMILIES: tuple[tuple[str, str, tuple[str, ...], frozenset[str]], ...] = (
    ("scholar-book-alternatives", "BOOK | choose CLOSED or OPEN (open = 3 page layers)",
     ("principia_book", "principia_open_cover", "principia_open_left", "principia_open_right"),
     frozenset({"principia_book"})),
    ("scholar-eye-alternatives", "FACE | EYES - mutually exclusive expression alternatives",
     ("eye_angry", "eye_open", "eye_surprised", "eye_shut", "eye_dead", "eye_dizzy"),
     frozenset({"eye_open"})),
    ("scholar-mouth-alternatives", "FACE | MOUTH - mutually exclusive expression alternatives",
     ("mouth_closed", "mouth_smile", "mouth_open", "mouth_wavy", "mouth_grit"),
     frozenset({"mouth_closed"})),
    ("scholar-optional-effects", "FX | OPTIONAL - orbiting stars and apple",
     ("dizzy_stars", "flying_apple"), frozenset()),
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def annotate_for_inkscape(source: str) -> str:
    """Apply stable identifiers, descriptive shape labels, and art-state folders.

    All original `data-rig-part`, `data-rig-opacity`, and bone assignments are
    retained. Hidden editor alternatives are deliberately marked so the
    sprite subset renderer can reveal them *only when that variant is sampled*.
    """
    root = ET.fromstring(source)
    view = next(
        (node for node in root.iter(f"{{{SVG}}}g")
         if node.get("id") == "scholar-three-quarter"),
        None,
    )
    if view is None:
        raise ValueError("Expected scholar-three-quarter SVG drawing layer")
    rig_parts = {child.get("data-rig-part"): child for child in view if child.get("data-rig-part")}
    if set(rig_parts) != set(DRAWABLE_PURPOSES):
        missing = sorted(set(rig_parts) - set(DRAWABLE_PURPOSES))
        stale = sorted(set(DRAWABLE_PURPOSES) - set(rig_parts))
        raise ValueError(f"Unlabelled or stale scholar rig parts: missing labels={missing}, stale entries={stale}")

    for name, part in rig_parts.items():
        purposes = DRAWABLE_PURPOSES[name]
        shapes = [child for child in part if child.tag.rsplit("}", 1)[-1] in DRAWABLES]
        if len(shapes) != len(purposes):
            raise ValueError(f"{name}: {len(shapes)} SVG shapes but {len(purposes)} purpose labels")
        # Keep the unmodified rig part id; improve its human-readable name.
        part.set(INK_LABEL, name.replace("_", " ").title() + " | " + purposes[0])
        for shape, purpose in zip(shapes, purposes):
            sid = f"{name}--{_slug(purpose)}"
            shape.set("id", sid)
            shape.set(INK_LABEL, purpose)
            shape.set("data-art-purpose", purpose)

    # A layer per family, with each alternative retained as a sublayer. Move
    # whole rig-part groups, never their individual shapes. The z-order used
    # during runtime comes from data-rig-z, not these editor folders.
    for gid, family_label, names, defaults in FAMILIES:
        nodes = [rig_parts[name] for name in names]
        insert_index = min(list(view).index(node) for node in nodes)
        layer = ET.Element(f"{{{SVG}}}g", {
            "id": gid,
            INK_MODE: "layer",
            INK_LABEL: family_label,
            "data-rig-editor-family": gid,
            "data-rig-editor-visibility": "editor-only",
        })
        for name in names:
            node = rig_parts[name]
            view.remove(node)
            node.set("data-rig-editor-variant", name)
            # Layer visibility is an editor convenience, not a rig visibility
            # channel. Even the default variant may be hidden temporarily by
            # an artist when comparing expressions in Inkscape.
            node.set("data-rig-editor-visibility", "editor-only")
            node.set(INK_LABEL,
                     name.replace("_", " ").title() + (" [DEFAULT]" if name in defaults else " [ALTERNATE]"))
            if name not in defaults:
                node.set("style", "display:none")
            layer.append(node)
        view.insert(insert_index, layer)

    # Preserve SVG geometry/IDs; deterministic serialization is important for
    # reviewing authored modifications and diffing generated SVGs.
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + '\n'


def label_generated_rig_guides(svg_path) -> None:
    """Label all hidden joints/bone guides added by the rig catalog builder.

    This is run *after* install_svg_catalog(), which recreates its marker
    subtree each time. It does not alter drawable character geometry.
    """
    from pathlib import Path

    svg_path = Path(svg_path)
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(svg_path, parser=parser).getroot()
    changed = False
    for layer in root:
        if layer.get("id") == "ambition-rig-markers":
            # Markers are still available in the Inkscape layer panel, but
            # should not obscure the character's eyes, blush or coat by
            # default. The actual joints/rig metadata remain untouched.
            layer.set("style", "display:none")
            changed = True
    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag not in DRAWABLES:
            continue
        meaning = None
        if joint := elem.get("data-joint"):
            meaning = f"Rig rest-pose joint marker: {joint.replace('_', ' ')}"
        elif bone := elem.get("data-rig-bone-guide"):
            meaning = f"Rig bone connection guide: {bone.replace('_', ' ')}"
        elif joint := elem.get("data-rig-joint"):
            meaning = f"Rig catalog joint marker: {joint.replace('_', ' ')}"
        elif part := elem.get("data-rig-bind-pivot"):
            meaning = f"Rig attachment pivot marker: {part.replace('_', ' ')}"
        if meaning:
            elem.set(INK_LABEL, meaning)
            changed = True
    if changed:
        svg_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' +
                            ET.tostring(root, encoding="unicode") + '\n',
                            encoding="utf8")


def write_object_inventory(svg_path, destination) -> None:
    """Write a searchable, user-facing index of the actual editable art."""
    import csv
    from pathlib import Path

    root = ET.parse(svg_path).getroot()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    view = next(el for el in root.iter(f"{{{SVG}}}g") if el.get('id') == 'scholar-three-quarter')
    for part in view.iter(f"{{{SVG}}}g"):
        name = part.get('data-rig-part')
        if not name:
            continue
        for el in part:
            if el.tag.rsplit('}', 1)[-1] not in DRAWABLES:
                continue
            rows.append({
                'object_id': el.get('id', ''),
                'purpose': el.get(INK_LABEL, ''),
                'rig_part': name,
                'bone': part.get('data-rig-bone', ''),
                'svg_type': el.tag.rsplit('}', 1)[-1],
                'cx': el.get('cx', ''), 'cy': el.get('cy', ''),
                'rx': el.get('rx', ''), 'ry': el.get('ry', ''),
                'expression_channel': part.get('data-rig-opacity', ''),
            })
    with destination.open('w', newline='', encoding='utf8') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
