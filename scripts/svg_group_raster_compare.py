#!/usr/bin/env python3
"""Render two SVG groups in isolation and compare them up to translation.

This is intentionally lightweight and generic enough to reuse for sprite SVGs.
It reports raster-space bbox extents, translation between bbox origins, and a
simple alpha-mask mismatch score after aligning the second image to the first.
"""
from __future__ import annotations
import argparse
import copy
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import cairosvg
from PIL import Image, ImageChops

def isolate_group(svg_path: Path, target_id: str, out_svg: Path) -> None:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    ids = {n.get('id'): n for n in root.iter() if n.get('id')}
    if target_id not in ids:
        raise KeyError(target_id)
    out_root = ET.Element(root.tag, root.attrib)
    for child in root:
        tag = child.tag.split('}')[-1]
        if tag in {'defs', 'namedview'}:
            out_root.append(copy.deepcopy(child))
    out_root.append(copy.deepcopy(ids[target_id]))
    ET.ElementTree(out_root).write(out_svg)

def render(svg_path: Path, out_png: Path, width: int) -> Image.Image:
    cairosvg.svg2png(url=str(svg_path), write_to=str(out_png), output_width=width)
    return Image.open(out_png).convert('RGBA')

def alpha_bbox(img: Image.Image):
    alpha = img.getchannel('A')
    return alpha.getbbox()

def alpha_mask(img: Image.Image, bbox):
    if bbox is None:
        raise ValueError('empty render')
    return img.getchannel('A').crop(bbox)

def compare(a: Image.Image, b: Image.Image):
    bbox_a = alpha_bbox(a)
    bbox_b = alpha_bbox(b)
    if bbox_a is None or bbox_b is None:
        raise ValueError('one render was empty')
    w_a = bbox_a[2] - bbox_a[0]
    h_a = bbox_a[3] - bbox_a[1]
    w_b = bbox_b[2] - bbox_b[0]
    h_b = bbox_b[3] - bbox_b[1]
    dx = bbox_a[0] - bbox_b[0]
    dy = bbox_a[1] - bbox_b[1]
    mask_a = alpha_mask(a, bbox_a)
    mask_b = alpha_mask(b, bbox_b)
    canvas = Image.new('L', (max(mask_a.width, mask_b.width), max(mask_a.height, mask_b.height)), 0)
    placed_a = canvas.copy(); placed_a.paste(mask_a, (0, 0))
    placed_b = canvas.copy(); placed_b.paste(mask_b, (0, 0))
    diff = Image.eval(ImageChops.difference(placed_a, placed_b), lambda v: 255 if v else 0)
    total = canvas.width * canvas.height
    histogram = diff.histogram()
    mismatch = total - histogram[0]
    return {
        'bbox_a': bbox_a, 'bbox_b': bbox_b,
        'extent_a': (w_a, h_a), 'extent_b': (w_b, h_b),
        'bbox_origin_delta': (dx, dy),
        'mask_mismatch_pixels': mismatch,
        'mask_mismatch_fraction': mismatch / total if total else 0.0,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('svg_path', type=Path)
    ap.add_argument('--left', required=True)
    ap.add_argument('--right', required=True)
    ap.add_argument('--width', type=int, default=1200)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        left_svg = d / 'left.svg'
        right_svg = d / 'right.svg'
        left_png = d / 'left.png'
        right_png = d / 'right.png'
        isolate_group(args.svg_path, args.left, left_svg)
        isolate_group(args.svg_path, args.right, right_svg)
        a = render(left_svg, left_png, args.width)
        b = render(right_svg, right_png, args.width)
        info = compare(a, b)
        print(f'left id: {args.left}')
        print(f'right id: {args.right}')
        print(f'left bbox:  {info["bbox_a"]}')
        print(f'right bbox: {info["bbox_b"]}')
        print(f'left extent:  {info["extent_a"][0]} x {info["extent_a"][1]}')
        print(f'right extent: {info["extent_b"][0]} x {info["extent_b"][1]}')
        print(f'bbox-origin delta (left - right): {info["bbox_origin_delta"]}')
        print(f'mask mismatch pixels: {info["mask_mismatch_pixels"]}')
        print(f'mask mismatch fraction: {info["mask_mismatch_fraction"]:.6f}')

if __name__ == '__main__':
    main()
