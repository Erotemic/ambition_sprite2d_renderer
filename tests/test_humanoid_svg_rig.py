from pathlib import Path

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    LimbPoseHint,
    _bend_for_side,
)

ROOT = Path(__file__).resolve().parent.parent


def test_pose_hint_controls_ik_branch_independent_of_svg_splay():
    hints = {
        "near": LimbPoseHint(target=(-12.0, -57.0), joint=(2.5, -64.0)),
    }
    common = dict(
        pose_hints=hints,
        overrides=None,
        side="near",
        center_x=88.0,
        ground_y=150.0,
        root=(102.8304, 72.0839),
        l1=18.4378,
        l2=16.1966,
    )

    first = _bend_for_side(
        joint=(140.0, 60.0),
        target=(160.0, 50.0),
        **common,
    )
    second = _bend_for_side(
        joint=(60.0, 120.0),
        target=(35.0, 135.0),
        **common,
    )

    assert first == second == 1.0


def test_svg_joint_layout_remains_fallback_without_pose_authority():
    common = dict(
        pose_hints=None,
        overrides=None,
        side="near",
        center_x=88.0,
        ground_y=150.0,
        root=(102.8304, 72.0839),
        l1=18.4378,
        l2=16.1966,
        target=(76.0, 93.0),
    )

    left_joint = _bend_for_side(joint=(90.5, 85.8), **common)
    right_joint = _bend_for_side(joint=(86.5, 80.7), **common)

    assert left_joint == 1.0
    assert right_joint == -1.0


def test_a_part_nested_inside_another_belongs_to_the_deeper_one():
    """Nested recognized parts belong to the deepest matching owner.

    Containers retain only descendants not claimed by a recognized child part,
    allowing ordinary nested Inkscape structure without duplicate ownership.
    """

    import xml.etree.ElementTree as ET

    from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import _collect_parts

    root = ET.parse(ROOT / "assets" / "carl-stargan.svg").getroot()
    parts = _collect_parts(root, "Carl Stargan - Side Left")

    owners: dict[str, list[str]] = {}
    for part in parts:
        for drawable in part.include:
            owners.setdefault(drawable, []).append(part.name)
    doubled = {k: v for k, v in owners.items() if len(v) > 1}
    assert not doubled, f"a drawable may have exactly one owner: {doubled}"

    by_name = {part.name: set(part.include) for part in parts}
    # ⛔ the non-vacuity: the nesting this is about must actually be present, or
    # the assertion above is a statement about an SVG with no nested parts.
    assert by_name.get("hair_front"), "Carl's hair is a part in its own right"
    assert by_name.get("hair_back"), "…both halves of it"
    assert by_name.get("head"), "…and the head still owns its leftovers"
    assert not (by_name["head"] & (by_name["hair_front"] | by_name["hair_back"])), (
        "the head must not also claim the hair it contains"
    )


def test_standard_humanoid_leftovers_split_at_intervening_svg_layers():
    """A semantic body part may occupy several foreground/background slices."""

    import xml.etree.ElementTree as ET

    from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import _collect_parts

    root = ET.fromstring(
        """
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
  <g inkscape:label="Side">
    <g inkscape:label="Head">
      <g inkscape:label="Glasses - Level 3">
        <path id="far-glasses" d="M 0 0 L 1 0 L 1 1 Z" />
      </g>
      <g inkscape:label="Head Base">
        <path id="head-base" d="M 0 0 L 2 0 L 2 2 Z" />
      </g>
      <g inkscape:label="Nose">
        <path id="nose" d="M 0 0 L 3 0 L 3 3 Z" />
      </g>
      <g inkscape:label="Facial Features">
        <path id="features" d="M 0 0 L 4 0 L 4 4 Z" />
      </g>
    </g>
  </g>
</svg>
"""
    )

    parts = _collect_parts(root, "Side", binding_mode="standard-humanoid")

    assert [(part.name, part.include) for part in parts] == [
        ("head_misc", ("far-glasses",)),
        ("head_base", ("head-base",)),
        ("head_misc__zslice_2", ("nose",)),
        ("head_features", ("features",)),
    ]
    assert parts[0].bone == parts[2].bone == "head"
