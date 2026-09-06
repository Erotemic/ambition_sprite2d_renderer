#!/usr/bin/env python3
"""Validate the Fire Mary-O front normalization invariants."""
from __future__ import annotations

import argparse
from pathlib import Path

from lxml import etree

from svg_geometry_tools import (
    collect_paths, compare_path_geometry, element_by_id, max_matrix_delta,
    multiply, parse_transform,
)


def check_pivot(root, tall_prefix: str, fire_prefix: str, failures: list[str]) -> None:
    tall = element_by_id(root, tall_prefix + "_pivot")
    fire = element_by_id(root, fire_prefix + "_pivot")
    if (tall.get("cx"), tall.get("cy")) != (fire.get("cx"), fire.get("cy")):
        failures.append(
            f"pivot mismatch {fire_prefix}: {(fire.get('cx'),fire.get('cy'))} != {(tall.get('cx'),tall.get('cy'))}"
        )


def head_common_matrix(root, fire: bool):
    if not fire:
        head=element_by_id(root,"maryo_tall_front_head")
        art=element_by_id(root,"maryo_tall_front_head_art")
        source=next(c for c in art if etree.QName(c).localname=="g")
        use=next(c for c in source if etree.QName(c).localname=="use")
        authoring=element_by_id(root,"maryo_authoring_tall_front_head")
        m=parse_transform(head.get("transform"))
        for e in (art,source,use,authoring):
            m=multiply(m,parse_transform(e.get("transform")))
        return m
    head=element_by_id(root,"maryo_fire_front_head")
    art=element_by_id(root,"maryo_fire_front_head_art")
    source=next(c for c in art if etree.QName(c).localname=="g")
    use=next(c for c in source if etree.QName(c).localname=="use")
    authoring=element_by_id(root,"maryo_authoring_fire_front_head")
    clone=element_by_id(root,"maryo_fire_front_tall_head_clone")
    tall_authoring=element_by_id(root,"maryo_authoring_tall_front_head")
    m=parse_transform(head.get("transform"))
    for e in (art,source,use,authoring,clone,tall_authoring):
        m=multiply(m,parse_transform(e.get("transform")))
    return m


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("svg", type=Path)
    args=ap.parse_args()
    root=etree.parse(str(args.svg)).getroot()
    failures=[]

    head_delta=max_matrix_delta(head_common_matrix(root,False),head_common_matrix(root,True))
    print(f"assembled tall/fire front common-head matrix delta: {head_delta:.3g}")
    if head_delta > 1e-8:
        failures.append(f"assembled fire front head misaligned: matrix delta {head_delta}")

    for tall_id,fire_id in [
        ("maryo_tall_front_character_right_arm","maryo_fire_front_character_right_arm"),
        ("maryo_tall_front_character_left_arm","maryo_fire_front_character_left_arm"),
    ]:
        tall=element_by_id(root,tall_id); fire=element_by_id(root,fire_id)
        if tall.get("transform") != fire.get("transform"):
            failures.append(f"outer arm transform mismatch: {fire_id}")

    pairs=[
        ("maryo_tall_front_character_right_arm_art", "maryo_fire_front_character_right_arm_common"),
        ("maryo_tall_front_character_left_arm_art", "maryo_fire_front_character_left_arm_common"),
    ]
    for tall_id, fire_id in pairs:
        tall_paths=[p for p in collect_paths(root,tall_id) if p.label != "sleeve-spike"]
        fire_paths=[p for p in collect_paths(root,fire_id) if p.label != "sleeve-spike"]
        ok,msgs=compare_path_geometry(tall_paths,fire_paths)
        print(f"{tall_id} <-> {fire_id}: {'PASS' if ok else 'FAIL'} ({len(tall_paths)} common paths)")
        for msg in msgs:
            print("  "+msg)
        if not ok:
            failures.extend(msgs)
        fire_art_id = fire_id.replace("_common", "_art")
        spikes=[p for p in collect_paths(root,fire_art_id) if p.label == "sleeve-spike"]
        print(f"  fire-only shoulder spikes: {len(spikes)}")
        if len(spikes)!=1:
            failures.append(f"{fire_art_id} expected 1 spike, got {len(spikes)}")

    for tall,fire in [
        ("maryo_tall_front_head","maryo_fire_front_head"),
        ("maryo_tall_front_character_right_arm","maryo_fire_front_character_right_arm"),
        ("maryo_tall_front_character_left_arm","maryo_fire_front_character_left_arm"),
    ]:
        check_pivot(root,tall,fire,failures)

    torso=element_by_id(root,"maryo_fire_front_torso_art")
    hrefs=[c.get("href") or c.get("{http://www.w3.org/1999/xlink}href") for c in torso]
    torso_ok="#maryo_fire_side_torso" in hrefs
    print(f"fire front torso restored from side torso: {'PASS' if torso_ok else 'FAIL'}")
    if not torso_ok:
        failures.append("fire front torso is not linked to fire side torso")

    if failures:
        raise SystemExit("validation failed:\n- " + "\n- ".join(failures))
    print("all Fire Mary-O front normalization checks passed")

if __name__=='__main__':
    main()
