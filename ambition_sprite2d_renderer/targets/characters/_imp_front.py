"""Independently authored frontal imp anatomy for the facing-change row.

The endpoints of the row use the ordinary side artwork. The middle frame is
constructed from front-view landmarks, not a warp or compression of that art.
Both species have their own landmarks and proportions. Coordinates are sprite
pixels relative to the body's authored horizontal pivot and normal origin.
"""
from __future__ import annotations

from PIL import Image

from ._magic_character_art import Canvas, bezier, unit, sub, perp, add, mul


def turn_frame(i, n, idle, front, box):
    """The engine has already flipped its facing; end in canonical facing."""
    assert n == 3
    if i == 1:
        return front()
    im = idle()
    if i == 2:
        return im
    # Reflect around the authored body anchor, not the padded canvas centre.
    dx = box[0] + box[2] - im.width
    out = Image.new('RGBA', im.size)
    out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (dx, 0))
    return out


def paint_front(size, origin, *, adult=False):
    c = Canvas(size)
    cx, cy = origin
    if adult:
        ink, skin, shade, light = '#1e1924', '#514c5c', '#363140', '#77717e'
        horn, horn_dark, claw = '#b6a18a', '#796b67', '#bead99'
        membrane, panel, panel_dark = '#443446', '#695365', '#584457'
        eye = '#f3cb61'
        # Landmarks: frontal head, torso, hips, fingers and feet.
        head_y, hx, hy = -52, 37, 29
        shoulder, chest_y, waist, pelvis, hip_y = 30, -28, 17, 20, 42
        knee_y, ankle_y, foot_y = 66, 95, 103
        arm_elbow, arm_wrist, arm_top = (43, 3), (38, 32), 10
        wing_hinge, wrist = (23,-29), (79,-85)
        wing_tips = [(147,-65),(132,-5),(97,42),(61,49),(24,8)]
        ear_tip, horn_tip = (62,-72),(32,-110)
        tail_end = (-91, 49)
        lw = 2.5
    else:
        ink, skin, shade, light = '#21191f', '#514042', '#31242d', '#77615e'
        horn, horn_dark, claw = '#a89477', '#88745d', '#a89477'
        membrane, panel, panel_dark = '#2d202d', '#5d4a50', '#493940'
        eye = '#e9d16e'
        head_y, hx, hy = -24, 26, 22
        shoulder, chest_y, waist, pelvis, hip_y = 15, -12, 10, 12, 19
        knee_y, ankle_y, foot_y = 29, 40, 47
        arm_elbow, arm_wrist, arm_top = (25, 0), (22, 13), 4.8
        wing_hinge, wrist = (11,-13), (47,-46)
        wing_tips = [(86,-35),(74,1),(44,25),(17,9)]
        ear_tip, horn_tip = (45,-41),(20,-70)
        tail_end = (-60,24)
        lw = 1.8

    def P(pt): return (cx + pt[0], cy + pt[1])
    def poly(pts, color, edge=ink, w=lw): c.poly([P(p) for p in pts], color, edge, w)
    def line(pts, color=ink, w=lw): c.line([P(p) for p in pts], color, w)
    def oval(x,y,rx,ry,color,edge=ink,w=lw): c.oval(P((x,y)),rx,ry,color,edge,w)
    def path(start, *segments):
        pts=[start]
        for a,b,d in segments: pts.extend(bezier(pts[-1],a,b,d,16)[1:])
        return pts
    def shape(start, *segments, fill, edge=ink, w=lw):
        poly(path(start,*segments),fill,edge,w)
    def side(pts,s): return [(s*x,y) for x,y in pts]
    def limb(joints, widths, color, highlight=None):
        normals=[]
        for i,p in enumerate(joints):
            d=sub(joints[min(i+1,len(joints)-1)], joints[max(0,i-1)])
            normals.append(perp(unit(d)))
        a=[add(p,mul(v,w)) for p,v,w in zip(joints,normals,widths)]
        b=[add(p,mul(v,-w)) for p,v,w in zip(joints,normals,widths)]
        outline=a+b[::-1]
        if len(joints)<8:
            pts=[]
            for j,v in enumerate(outline):
                prev,nxt=outline[j-1],outline[(j+1)%len(outline)]
                start=add(mul(v,.78),mul(prev,.22)); end=add(mul(v,.78),mul(nxt,.22))
                pts.extend(bezier(start,v,v,end,6))
            outline=pts
        poly(outline,color)
        if highlight:
            line([add(p,mul(v,w*.48)) for p,v,w in zip(joints,normals,widths)],highlight,lw*.7)

    # Tail is projected behind the pelvis and loops out to one side. Its root
    # is occluded by the body; it is not a flat mirror of a side-view tail.
    tx,ty=tail_end
    tail=path((0,hip_y),((-pelvis,hip_y+20),(tx*.8,ty+29),(tx,ty+13)),
              ((tx-12,ty-4),(tx-5,ty-12),(tx,ty)))
    root=8.5 if adult else 3.5
    limb(tail,[root*(1-j/(len(tail)-1))+(2.0 if adult else 1.5) for j in range(len(tail))],shade,light)
    k=1.45 if adult else 1.
    poly([(tx-4*k,ty-5*k),(tx+10*k,ty-8*k),(tx+6*k,ty+5*k),(tx+1*k,ty+2*k)],horn_dark if adult else skin)

    # Wings: both shoulders visible from the front, with a full wrist, thumb,
    # finger fan and curved membrane for each wing. Spars behind the arms.
    for s in (-1,1):
        sh=wing_hinge; wr=wrist; tips=wing_tips
        thumb=(wr[0]-2*k,wr[1]-12*k)
        outline=[sh,wr,thumb,(wr[0]+5*k,wr[1]-4*k),tips[0]]
        for a,b in zip(tips,tips[1:]):
            ca=add(mul(a,.67),mul(wr,.33)); cb=add(mul(b,.67),mul(wr,.33))
            outline.extend(bezier(a,ca,cb,b,16)[1:])
        outline.append(sh)
        poly(side(outline,s),membrane)
        for j,(a,b) in enumerate(zip(tips,tips[1:])):
            pa=add(mul(a,.67),mul(wr,.33)); pb=add(mul(b,.67),mul(wr,.33))
            poly(side([wr,pa,pb],s),panel if j%2==0 else panel_dark,None)
        limb(side([sh,add(mul(sh,.52),mul(wr,.48)),wr],s),[arm_top*.64,arm_top*.48,arm_top*.35],skin,light)
        for t in tips[:-1]: line(side([wr,t],s),ink,lw*.88)
        poly(side([wr,thumb,(wr[0]+5*k,wr[1]-4*k)],s),horn,ink,lw*.65)

    # Two legs, viewed straight on, with independent knees and feet. No leg
    # overlays the opposite thigh. The torso hides the hip sockets below.
    for s in (-1,1):
        h=(pelvis*.56,hip_y-3*k); kn=(pelvis*.76,knee_y); an=(pelvis*.68,ankle_y)
        limb(side([h,kn,an],s),[pelvis*.46,pelvis*.38,pelvis*.27],skin,light)
        fx=an[0]*s
        oval(fx,foot_y-4*k,7.6*k,4.3*k,shade)
        if adult:
            for j in (-1,0,1):
                x=fx+j*3.7*k
                poly([(x-1.5*k,foot_y-4*k),(x+1.5*k,foot_y-4*k),(x+1.9*k,foot_y+.4*k),(x,foot_y+1.4*k)],claw,ink,.8*k)
        else:
            line([(fx,foot_y-5),(fx,foot_y)],ink,1.2)

    # Frontal torso: paired shoulders/pectoral planes and a narrow waist.
    sy=chest_y
    shape((-shoulder,sy),((-shoulder*.88,sy-13*k),(-shoulder*.32,sy-14*k),(0,sy-10*k)),
          ((shoulder*.32,sy-14*k),(shoulder*.88,sy-13*k),(shoulder,sy)),
          ((shoulder*1.07,sy+15*k),(waist,sy+23*k),(waist,hip_y-9*k)),
          ((pelvis,hip_y-3*k),(pelvis*.95,hip_y+5*k),(0,hip_y+7*k)),
          ((-pelvis*.95,hip_y+5*k),(-pelvis,hip_y-3*k),(-waist,hip_y-9*k)),
          ((-waist,sy+23*k),(-shoulder*1.07,sy+15*k),(-shoulder,sy)),fill=skin)
    for s in (-1,1):
        if adult:
            poly(side([(2,sy+1),(shoulder*.8,sy-3),(shoulder*.87,sy+10),(shoulder*.44,sy+19),(2,sy+13)],s),light,None)
        sh=(shoulder*.91,sy+2*k); el=arm_elbow; wa=arm_wrist
        limb(side([sh,el,wa],s),[arm_top,arm_top*.75,arm_top*.47],skin,light)
        x,y=wa[0]*s,wa[1]
        oval(x,y+2*k,4.7*k,5.4*k,skin)
        for j in (-1,0,1):
            xj=x+j*2.6*k
            poly([(xj-1.15*k,y+3*k),(xj+1.15*k,y+3*k),(xj+1.6*k,y+8.6*k),(xj,y+10*k)],claw,ink,.7*k)
    shape((-waist*.75,sy+13*k),((-waist*.4,sy+10*k),(waist*.4,sy+10*k),(waist*.75,sy+13*k)),
          ((waist*.95,sy+22*k),(waist*.65,hip_y-1*k),(0,hip_y+2*k)),
          ((-waist*.65,hip_y-1*k),(-waist*.95,sy+22*k),(-waist*.75,sy+13*k)),fill=light if not adult else '#655e69',edge=None)
    for j in range(2 if not adult else 3):
        y=sy+17*k+j*8*k
        line([(-waist*.56,y),(0,y+2*k),(waist*.56,y)],shade,lw*.7)

    # Horns and ears form paired silhouettes behind the skull. Horns have
    # independent curved profiles and ridge marks, not stretched side shapes.
    for s in (-1,1):
        x0=hx*.48; y0=head_y-hy+5*k; xt,yt=horn_tip
        horn_pts=path((x0-6*k,y0+3*k),((x0-9*k,y0-12*k),(xt-3*k,yt+12*k),(xt,yt)),
                      ((xt+8*k,yt+10*k),(x0+13*k,y0-12*k),(x0+8*k,y0+3*k)),
                      ((x0+4*k,y0+9*k),(x0-3*k,y0+9*k),(x0-6*k,y0+3*k)))
        poly(side(horn_pts,s),horn)
        for f in (.22,.46,.69):
            y=y0+(yt-y0)*f; x=x0+(xt-x0)*f
            line(side([(x-5*k*(1-f),y),(x+7*k*(1-f),y-2*k)],s),horn_dark,lw*.65)
        ex,ey=ear_tip
        poly(side([(hx*.77,head_y-7*k),(ex,ey),(ex-7*k,head_y+8*k),(hx*.78,head_y+11*k)],s),skin)
        poly(side([(hx*.90,head_y-5*k),(ex-5*k,ey+5*k),(ex-10*k,head_y+5*k)],s),shade,None)

    # Frontal skull, two fully visible eyes, central muzzle and paired fangs.
    shape((-hx,head_y-4*k),((-hx,head_y-hy*.78),(-hx*.57,head_y-hy),(0,head_y-hy)),
          ((hx*.57,head_y-hy),(hx,head_y-hy*.78),(hx,head_y-4*k)),
          ((hx*1.03,head_y+hy*.5),(hx*.58,head_y+hy),(0,head_y+hy)),
          ((-hx*.58,head_y+hy),(-hx*1.03,head_y+hy*.5),(-hx,head_y-4*k)),fill=skin,w=lw*1.2)
    shape((-hx*.78,head_y-hy*.65),((-hx*.5,head_y-hy*.95),(hx*.5,head_y-hy*.95),(hx*.78,head_y-hy*.65)),
          ((hx*.38,head_y-hy*.76),(-hx*.38,head_y-hy*.76),(-hx*.78,head_y-hy*.65)),fill=light,edge=None)
    for s in (-1,1):
        eye_pts=[(hx*.16,head_y-3*k),(hx*.78,head_y-9*k),(hx*.68,head_y+2*k),(hx*.30,head_y+4*k)]
        poly(side(eye_pts,s),eye,ink,lw*.8)
        oval(s*hx*.43,head_y-1.4*k,1.8*k,3.7*k,'#302231',None)
        line(side([(hx*.12,head_y-5*k),(hx*.48,head_y-10*k),(hx*.82,head_y-12*k)],s),shade,lw*1.6)
        if adult:
            poly(side([(hx*.9,head_y+4*k),(hx*.55,head_y+7*k),(hx*.28,head_y+10*k),(hx*.62,head_y+13*k)],s),'#655b6c',None)
    # Broad nostrils and muzzle, rather than the side view's protruding snout.
    shape((-9*k,head_y+5*k),((-7*k,head_y+1*k),(7*k,head_y+1*k),(9*k,head_y+5*k)),
          ((11*k,head_y+10*k),(5*k,head_y+11*k),(0,head_y+10*k)),
          ((-5*k,head_y+11*k),(-11*k,head_y+10*k),(-9*k,head_y+5*k)),fill=skin,edge=shade,w=lw*.65)
    for s in (-1,1): oval(s*4*k,head_y+7*k,2.0*k,1.3*k,shade,None)
    line([(-hx*.57,head_y+13*k),(-hx*.26,head_y+12*k),(0,head_y+13.5*k),(hx*.26,head_y+12*k),(hx*.57,head_y+13*k)],ink,lw*1.2)
    for s in (-1,1):
        x=s*hx*.38; y=head_y+12*k
        poly([(x-2.1*k,y),(x+2.1*k,y),(x-s*.7*k,y+5*k)],claw,ink,lw*.45)
    return c.finish()
