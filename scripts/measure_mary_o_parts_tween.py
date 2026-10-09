"""Is a world-space per-part lerp (pivot position + angle) a faithful in-between?
Truth: the renderer's own render of the lerped Pose. Rows whose consecutive frames
draw the same parts in the same order only."""
import dataclasses, math
from PIL import Image
import ambition_sprite2d_renderer.targets.characters.mary_o_v2_svg_poc as poc
from ambition_sprite2d_renderer.authoring import rigdoc
from ambition_sprite2d_renderer.authoring.part_flipbook import recorded_blits, parity
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import FIRE_FORM, SHORT_FORM, TALL_FORM, Pose
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document, render_pose_with_doc

docs = {}
for src in (SHORT_FORM, TALL_FORM, FIRE_FORM):
    docs[src.target_name] = build_rig_document(poc.ASSET_PATH, src, "side")

def lerp_pose(a, b, t):
    kw = {}
    for f in dataclasses.fields(Pose):
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            kw[f.name] = va + (vb - va) * t
        elif va == vb:
            kw[f.name] = va
        else:
            return None
    return Pose(**kw)

def draw(form, pose):
    with recorded_blits() as calls:
        img = render_pose_with_doc(docs[form.target_name], form, pose)
    return img, calls

def key(c): return (c[0].size, c[1], c[0].tobytes())
results = []
for form in (SHORT_FORM, TALL_FORM, FIRE_FORM):
    table = poc._poses_for(form)
    for row, count, ms in form.rows:
        poses = table.get(row)
        if not poses or len(poses) < 2 or row in ("grow","shrink","big_shrink","transform","death","shoot"): continue
        for i in range(len(poses)):
            a, b = poses[i], poses[(i+1) % len(poses)]
            mid = lerp_pose(a, b, 0.5)
            if mid is None: results.append((form.target_name,row,i,"pose not lerpable")); continue
            _, ca = draw(form, a); _, cb = draw(form, b); truth, cm = draw(form, mid)
            if [key(c) for c in ca] != [key(c) for c in cb]:
                results.append((form.target_name,row,i,"parts differ between frames")); continue
            canvas = Image.new("RGBA", truth.size, (0,0,0,0))
            maxmove = 0
            for x, y in zip(ca, cb):
                wx = (x[2][0]+y[2][0])/2; wy = (x[2][1]+y[2][1])/2
                d = (y[3]-x[3]+180) % 360 - 180
                maxmove = max(maxmove, abs(d))
                rigdoc.blit_rotated(canvas, x[0], x[1], (wx, wy), x[3]+d/2, 1.0)
            results.append((form.target_name,row,i,f"tween parity {parity(truth, canvas)*100:.2f}%  max joint swing {maxmove:.0f}deg"))
for r in results: print(*r)
