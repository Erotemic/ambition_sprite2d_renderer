"""Independently authored frontal imp anatomy for the facing-change row.

The endpoints of the row use the ordinary side artwork. The middle frame is
constructed from front-view landmarks, not a warp or compression of that art.
Both species have their own landmarks and proportions. Coordinates are sprite
pixels relative to the body's authored horizontal pivot and normal origin.
"""
from __future__ import annotations

import math

from ._magic_character_art import bezier, unit, sub, perp, add, mul, mix
from ._imp_parts import ImpScene, chain


def paint_front(target, size, origin, *, adult=False, quarter=False):
    if quarter:
        return paint_quarter(target,size,origin,adult=adult)
    c = ImpScene(target,size,origin)
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
        tail_end = (-24, 57)
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
        tail_end = (-14,30)
        lw = 1.8

    def P(pt): return pt
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
    k=1.45 if adult else 1.
    tx,ty=tail_end
    with c.part('front_tail',(0,hip_y),key='front'):
        tail=path((0,hip_y),((-pelvis*.6,hip_y+12),(tx*.6,ty+13),(tx,ty+6)),
                  ((tx-7*k,ty),(tx-5*k,ty-5*k),(tx,ty)))
        root=8.5 if adult else 3.5
        limb(tail,[root*(1-j/(len(tail)-1))+(2.0 if adult else 1.5) for j in range(len(tail))],shade,light)
        poly([(tx-4*k,ty-5*k),(tx+10*k,ty-8*k),(tx+6*k,ty+5*k),(tx+1*k,ty+2*k)],horn_dark if adult else skin)

    # Wings: both shoulders visible from the front, with a full wrist, thumb,
    # finger fan and curved membrane for each wing. Spars behind the arms.
    for s in (-1,1):
        with c.part('front_'+('left' if s<0 else 'right')+'_wing',key='front'):
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
        with c.part('front_'+('left' if s<0 else 'right')+'_leg',key='front'):
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
    with c.part('front_torso',key='front'):
        shape((-shoulder,sy),((-shoulder*.88,sy-13*k),(-shoulder*.32,sy-14*k),(0,sy-10*k)),
              ((shoulder*.32,sy-14*k),(shoulder*.88,sy-13*k),(shoulder,sy)),
              ((shoulder*1.07,sy+15*k),(waist,sy+23*k),(waist,hip_y-9*k)),
              ((pelvis,hip_y-3*k),(pelvis*.95,hip_y+5*k),(0,hip_y+7*k)),
              ((-pelvis*.95,hip_y+5*k),(-pelvis,hip_y-3*k),(-waist,hip_y-9*k)),
              ((-waist,sy+23*k),(-shoulder*1.07,sy+15*k),(-shoulder,sy)),fill=skin)

    for s in (-1,1):
        with c.part('front_'+('left' if s<0 else 'right')+'_arm',key='front'):
            if adult:
                poly(side([(2,sy+1),(shoulder*.8,sy-3),(shoulder*.87,sy+10),(shoulder*.44,sy+19),(2,sy+13)],s),light,None)
            sh=(shoulder*.91,sy+2*k); el=arm_elbow; wa=arm_wrist
            limb(side([sh,el,wa],s),[arm_top,arm_top*.75,arm_top*.47],skin,light)
            x,y=wa[0]*s,wa[1]
            oval(x,y+2*k,4.7*k,5.4*k,skin)
            for j in (-1,0,1):
                xj=x+j*2.6*k
                poly([(xj-1.15*k,y+3*k),(xj+1.15*k,y+3*k),(xj+1.6*k,y+8.6*k),(xj,y+10*k)],claw,ink,.7*k)

    with c.part('front_belly',key='front'):
        shape((-waist*.75,sy+13*k),((-waist*.4,sy+10*k),(waist*.4,sy+10*k),(waist*.75,sy+13*k)),
              ((waist*.95,sy+22*k),(waist*.65,hip_y-1*k),(0,hip_y+2*k)),
              ((-waist*.65,hip_y-1*k),(-waist*.95,sy+22*k),(-waist*.75,sy+13*k)),fill=light if not adult else '#655e69',edge=None)
        for j in range(2 if not adult else 3):
            y=sy+17*k+j*8*k
            line([(-waist*.56,y),(0,y+2*k),(waist*.56,y)],shade,lw*.7)

    # Horns and ears form paired silhouettes behind the skull. Horns have
    # independent curved profiles and ridge marks, not stretched side shapes.
    for s in (-1,1):
        with c.part('front_'+('left' if s<0 else 'right')+'_horn_ear',key='front'):
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
    with c.part('front_head',key='front'):
        shape((-hx,head_y-4*k),((-hx,head_y-hy*.78),(-hx*.57,head_y-hy),(0,head_y-hy)),
              ((hx*.57,head_y-hy),(hx,head_y-hy*.78),(hx,head_y-4*k)),
              ((hx*1.03,head_y+hy*.5),(hx*.58,head_y+hy),(0,head_y+hy)),
              ((-hx*.58,head_y+hy),(-hx*1.03,head_y+hy*.5),(-hx,head_y-4*k)),fill=skin,w=lw*1.2)
        shape((-hx*.78,head_y-hy*.65),((-hx*.5,head_y-hy*.95),(hx*.5,head_y-hy*.95),(hx*.78,head_y-hy*.65)),
              ((hx*.38,head_y-hy*.76),(-hx*.38,head_y-hy*.76),(-hx*.78,head_y-hy*.65)),fill=light,edge=None)

    with c.part('front_face',key='front'):
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


def paint_quarter(target,size,origin,*,adult=False):
    """An oblique front view, between the existing front and side landmarks.

    The cheek planes, paired horns, nose bridge, shoulders, wings and feet
    have their own projected coordinates. No image or profile is squeezed.
    """
    c=ImpScene(target,size,origin)
    if adult:
        ink,skin,shade,light,far='#1e1924','#514c5c','#363140','#77717e','#3e3949'
        horn,hd,claw='#b6a18a','#796b67','#bead99'
        membrane,deep='#443446','#312638'
        eye='#f3cb61'; k=1.45; lw=2.3
        hy=-55; hips=40; sy=-27; knee_y=65; foot_y=95
        shoulder_l=(-28,-25); shoulder_r=(25,-27)
        elbow_l=(-47,3); hand_l=(-41,33)
        elbow_r=(41,0); hand_r=(43,24)
        leg_l=[(-15,37),(-7,66),(-16,96)]
        leg_r=[(13,37),(27,63),(20,91)]
        wings=[((18,-30),(64,-78),[(119,-66),(107,-3),(77,35),(42,40),(18,5)]),
               ((-20,-27),(-76,-85),[(-143,-66),(-126,-5),(-94,42),(-57,47),(-19,8)])]
        tail=[(-12,40),(-44,65),(-93,78),(-105,50),(-92,37)]
    else:
        ink,skin,shade,light,far='#21191f','#514042','#31242d','#77615e','#44343a'
        horn,hd,claw='#a89477','#88745d','#a89477'
        membrane,deep='#2d202d','#231a24'
        eye='#e9d16e'; k=1.; lw=1.7
        hy=-25; hips=19; sy=-13; knee_y=29; foot_y=40
        shoulder_l=(-15,-12); shoulder_r=(13,-13)
        elbow_l=(-27,0); hand_l=(-24,14)
        elbow_r=(25,-2); hand_r=(28,8)
        leg_l=[(-9,17),(-4,29),(-8,40)]
        leg_r=[(8,17),(17,28),(12,37)]
        wings=[((8,-15),(35,-42),[(65,-31),(58,1),(34,20),(9,7)]),
               ((-11,-13),(-48,-47),[(-84,-37),(-73,1),(-44,25),(-12,9)])]
        tail=[(-8,20),(-31,35),(-57,41),(-67,25),(-57,17)]

    def poly(pts,col,edge=ink,w=lw):c.poly(pts,col,edge,w)
    def line(pts,col=ink,w=lw):c.line(pts,col,w)
    def oval(x,y,rx,ry,col,edge=ink,w=lw,angle=0.):c.oval((x,y),rx,ry,col,edge,w,angle)
    def path(start,*segments):
        pts=[start]
        for a,b,d in segments:pts.extend(bezier(pts[-1],a,b,d,16)[1:])
        return pts
    def shape(start,*segments,fill,edge=ink,w=lw):poly(path(start,*segments),fill,edge,w)
    # Tail curls away behind the hip, with its barb following the curve.
    with c.part('quarter_tail',tail[0],key='quarter'):
        a,b,d,e,f=tail
        pts=path(a,(b,d,e),(add(e,(-5*k,-10*k)),add(f,(-6*k,-5*k)),f))
        line(pts,ink,8.2*k);line(pts,shade,5.8*k);line(pts[:-3],light,1.7*k)
        x,y=f
        poly([(x-4*k,y-6*k),(x+10*k,y-4*k),(x+4*k,y+5*k),(x,y+2*k)],hd if adult else skin)
    # Oblique wing anatomy: the landmarks above are already projected,
    # including the shorter far-side fingers. Keep each complete wing a
    # reusable local raster; the ribs share its exact membrane endpoints.
    for wing_index,(sh,wr,tips) in enumerate(wings):
        far_side=wing_index==0
        side=1 if far_side else -1
        with c.part('quarter_'+('far' if far_side else 'near')+'_wing',sh,key='quarter'):
            # The wrist has a hooked free thumb and a fleshy knuckle. A bent
            # upper arm joins it to the shoulder rather than a straight spar.
            elbow=add(mix(sh,wr,.49),(-side*3.8*k,2.8*k))
            thumb_base=add(wr,(-side*2*k,-3.0*k))
            thumb_tip=add(wr,(-side*1.3*k,-12.0*k))
            leading=add(wr,(side*6*k,-4.0*k))
            scallops=[]
            for a,b in zip(tips,tips[1:]):
                ca=mix(wr,a,.68); cb=mix(wr,b,.63)
                scallops.append(bezier(a,ca,cb,b,18))
            outline=[sh,elbow,wr,thumb_base,thumb_tip,leading,tips[0]]
            for arc in scallops:
                outline.extend(arc[1:])
            # Preserve the original dark hide and membrane palettes. The
            # far wing is recessed, but retains its full set of visible ribs.
            if adult:
                base=deep if far_side else membrane
                bays=('#48384c','#403044','#49374b','#392c3d') if far_side else ('#695365','#584457','#654d61','#513e51')
                facet='#5b465b' if far_side else '#806879'
                rib='#514052' if far_side else '#675065'
                ridge='#756071' if far_side else '#9a8291'
            else:
                base=deep if far_side else membrane
                bays=('#38262d','#30222d','#3a2b34') if far_side else ('#5d4a50','#493940','#554148')
                facet='#47343e' if far_side else '#766068'
                rib='#433139' if far_side else '#503a43'
                ridge='#61505a' if far_side else '#8a7267'
            poly(outline+[sh],base,ink,lw*1.15)
            # Broad membrane panels follow the *curved* trailing edge.
            # Inset the colored panel from the silhouette and form a small
            # lighter plane along the tensioned leading side of each bay.
            for j,arc in enumerate(scallops):
                a,b=arc[0],arc[-1]
                panel_arc=[mix(wr,p,.88) for p in arc]
                poly([wr]+panel_arc,bays[j%len(bays)],None)
                inner_a=mix(wr,a,.72)
                inner_b=mix(wr,b,.53)
                facet_edge=mix(wr,arc[6],.69)
                poly([mix(wr,a,.15),inner_a,facet_edge,inner_b],facet,None)
                # A subtle dark trailing rim remains between the facet and
                # the scallop. Avoid arbitrary markings outside the membrane.
            for j,tip in enumerate(tips[:-1]):
                # Ribs narrow toward the tips. Add a small knuckle bend,
                # then a thin highlight on the proximal half, as in profile.
                d=sub(tip,wr)
                n=perp(unit(d))
                joint=add(mix(wr,tip,.48),mul(n,side*(.9 if far_side else 1.5)*k))
                end=mix(wr,tip,.98)
                rib_width=(2.0 if j==0 else 1.55)*k*(.80 if far_side else 1.)
                line([wr,joint,end],ink,rib_width+1.0*k)
                line([wr,joint,mix(joint,end,.76)],rib,rib_width)
                hi=mul(n,-side*.45*k)
                line([add(mix(wr,joint,.15),hi),add(joint,hi),add(mix(joint,end,.20),hi)],ridge,.73*k)
            # The innermost finger attaches to the flank, not the wrist tip.
            line([wr,mix(wr,tips[-1],.56),tips[-1]],rib,1.45*k)
            # The wing arm sits above the membrane; taper the contour from
            # the upper arm down to the wrist and retain the dorsal ridge.
            arm=[sh,elbow,wr]
            normals=[perp(unit(sub(arm[min(i+1,2)],arm[max(0,i-1)]))) for i in range(3)]
            widths=[3.0*k,2.35*k,1.65*k]
            if far_side: widths=[v*.84 for v in widths]
            left=[add(p,mul(n,w)) for p,n,w in zip(arm,normals,widths)]
            right=[add(p,mul(n,-w)) for p,n,w in zip(arm,normals,widths)]
            poly(left+right[::-1],far if far_side else skin,ink,1.25*k)
            line([mix(a,b,.27 if side<0 else .73) for a,b in zip(left,right)],ridge,.85*k)
            # A genuine wrist claw, not the flat triangle of the old pose.
            shape(add(wr,(-side*2.8*k,1*k)),
                  (add(thumb_base,(-side*2*k,0)),add(thumb_tip,(-side*1.4*k,1.7*k)),thumb_tip),
                  (add(thumb_tip,(side*2.7*k,3.8*k)),add(wr,(side*3.0*k,-2.3*k)),add(wr,(side*3.7*k,.2*k))),
                  (add(wr,(side*2*k,2*k)),add(wr,(-side*1.2*k,2*k)),add(wr,(-side*2.8*k,1*k))),
                  fill=hd if far_side else horn,edge=ink,w=1.05*k)
            line([add(thumb_tip,(0,2.5*k)),add(wr,(side*.9*k,-3.5*k))],
                 horn if far_side else ('#d0bba0' if adult else '#c5ae8e'),.65*k)

    def leg(is_far,joints):
        label='quarter_'+('far' if is_far else 'near')+'_leg'
        col=far if is_far else skin
        x,y=joints[-1]
        with c.part(label+'_foot',(x,y),key='quarter'):
            if adult:
                shape((x-6*k,y-2*k),((x-4*k,y-5*k),(x+2*k,y-4*k),(x+6*k,y)),
                      ((x+9*k,y+5*k),(x+1*k,y+7*k),(x-5*k,y+5*k)),
                      ((x-8*k,y+4*k),(x-8*k,y),(x-6*k,y-2*k)),fill=col)
                for j in (-1,0,1):
                    u=x+1.5*k+j*3.5*k
                    poly([(u-1.2*k,y+3*k),(u+1.7*k,y+3*k),(u+2.8*k,y+7*k),(u,y+6*k)],hd if is_far else claw,ink,.8*k)
            else:
                poly([(x-5,y-1),(x-2,y-4),(x+4,y-2),(x+9,y+3),(x+8,y+7),(x+2,y+6),(x,y+4),(x-2,y+6),(x-6,y+5)],shade)
                line([(x+2,y+1),(x+2,y+5)],ink,1.)
        chain(c,label,joints,(7.4*k,5.2*k,3.5*k) if adult else (5.4,4.3,3.4),col,None if is_far else light,ink,bulk=1.23)

    def arm(is_far,joints):
        label='quarter_'+('far' if is_far else 'near')+'_arm'
        col=far if is_far else skin
        x,y=joints[-1]
        with c.part(label+'_hand',(x,y),key='quarter'):
            oval(x,y+2*k,5.1*k,5.5*k,col)
            for j in (-1,0,1):
                u=x+j*3.2*k
                poly([(u-1.4*k,y+3*k),(u+1.1*k,y+3*k),(u+2.3*k,y+8.8*k),(u-.8*k,y+10*k)],hd if is_far else claw,ink,.8*k)
        chain(c,label,joints,(7.5*k,5.5*k,3.9*k) if adult else (5.,4.2,3.1),col,None if is_far else light,ink,bulk=1.35)
    leg(True,leg_r);arm(True,[shoulder_r,elbow_r,hand_r])
    with c.part('quarter_torso',key='quarter'):
        if adult:
            shape((-28,-35),((-10,-48),(14,-43),(28,-33)),((38,-19),(28,0),(20,17)),
                  ((16,30),(22,40),(13,46)),((0,51),(-18,51),(-24,41)),
                  ((-30,25),(-21,14),(-29,1)),((-37,-14),(-39,-28),(-28,-35)),fill=skin)
            shape((-23,-27),((-14,-36),(4,-35),(12,-23)),((13,-14),(5,-7),(-7,-6)),
                  ((-20,-8),(-28,-17),(-23,-27)),fill=light,edge=None)
            shape((15,-26),((23,-32),(30,-25),(29,-18)),((27,-8),(18,-8),(13,-13)),((11,-19),(12,-23),(15,-26)),fill='#655d6e',edge=None)
            shape((-5,-1),((6,-4),(16,1),(14,12)),((12,26),(12,36),(2,41)),(( -9,42),(-16,13),(-5,-1)),fill='#655e69',edge=None)
            for y in (8,19,30):line([(-8,y),(3,y+2),(11,y)],shade,1.8)
        else:
            shape((-15,-20),((-5,-28),(10,-24),(17,-14)),((23,-4),(14,7),(11,15)),
                  ((16,22),(8,25),(-1,24)),((-14,25),(-19,15),(-19,3)),((-23,-8),(-22,-17),(-15,-20)),fill=skin)
            shape((-6,-15),((2,-21),(13,-15),(13,-6)),((12,2),(7,8),(8,17)),((0,23),(-9,12),(-10,2)),((-12,-4),(-10,-12),(-6,-15)),fill=light,edge=None)
            for y in (0,8):line([(-7,y),(1,y+2),(7,y)],shade,1.2)
    leg(False,leg_l);arm(False,[shoulder_l,elbow_l,hand_l])

    # Facial landmarks use local head pixels. The far eye sits around the
    # brow ridge and the central muzzle points right, not straight out.
    def F(x,y):return (x*k,hy+y*k)
    def fp(pts,col,edge=ink,w=lw):poly([F(*p) for p in pts],col,edge,w)
    def fl(pts,col=ink,w=lw):line([F(*p) for p in pts],col,w)
    def fo(x,y,rx,ry,col,edge=ink,w=lw,angle=0):oval(*F(x,y),rx*k,ry*k,col,edge,w,angle)
    def fs(start,*segments,fill,edge=ink,w=lw):
        shape(F(*start),*((F(*a),F(*b),F(*d)) for a,b,d in segments),fill=fill,edge=edge,w=w)
    def horn_piece(label,x,y,far_side):
        with c.part(label,F(x,y),key='quarter'):
            def H(a,b):return (x+a,y+b)
            # The near horn sweeps back, the far horn is foreshortened by
            # its own tip/base landmarks rather than rescaling a horn image.
            tip=(-20,-31) if adult and not far_side else (-12,-23)
            if far_side:tip=(-6,-25 if adult else -19)
            fs(H(-6,4),(H(-10,-7),H(tip[0]-3,tip[1]+7),H(*tip)),
               (H(tip[0]+7,tip[1]+8),H(7,-12),H(6,2)),
               (H(3,7),H(-3,8),H(-6,4)),fill=hd if far_side else horn)
            for t in (.28,.52,.73):
                u=tip[0]*t;v=tip[1]*t
                fl([H(u-4*(1-t),v+2),H(u+6*(1-t),v-1)],hd if not far_side else '#655248',1.05*k)
    horn_piece('quarter_far_horn',15,-17,True)
    with c.part('quarter_far_ear',F(24,-8),key='quarter'):
        fp([(20,-11),(38,-20),(32,-4),(24,5)],far)
        fp([(24,-10),(33,-15),(29,-3)],shade,None)
    horn_piece('quarter_near_horn',-12,-20,False)
    with c.part('quarter_head',F(0,0),key='quarter'):
        # Wide cranial vault, near cheek with jaw taper, far cheek closer
        # to the nose bridge. The chin sits below the projecting muzzle.
        fs((-24,-9),((-22,-23),(-8,-25),(8,-23)),((21,-22),(28,-15),(29,-7)),
           ((29,-3),(27,-1),(31,2)),((36,6),(32,11),(24,12)),
           ((19,20),(6,23),(-5,20)),((-18,17),(-25,9),(-26,-1)),
           ((-26,-4),(-25,-7),(-24,-9)),fill=skin,w=lw*1.2)
        fs((-20,-10),((-16,-20),(-2,-23),(11,-19)),((4,-19),(-6,-16),(-11,-11)),
           ((-17,-7),(-20,-8),(-20,-10)),fill=light,edge=None)
        fp([(-20,2),(-12,8),(2,11),(-3,16),(-16,13)],shade,None)
        fp([(21,-5),(28,-3),(30,2),(23,5),(19,1)],light,None)
    with c.part('quarter_near_ear',F(-23,-4),key='quarter'):
        fp([(-21,-8),(-44,-20),(-38,3),(-23,9)],skin)
        fp([(-25,-6),(-38,-14),(-34,0),(-25,4)],shade,None)
        fl([(-39,-15),(-33,-3),(-25,2)],light,1.0*k)
    with c.part('quarter_face',F(0,0),key='quarter'):
        # Near and far eyes follow different brow planes; pupils point
        # along the same forward direction. Keep the fangs of each species.
        if adult:
            fp([(-14,-9),(9,-2),(5,3),(-10,1)],eye,ink,1.4*k)
            fp([(16,-3),(27,-10),(26,-2),(19,2)],eye,ink,1.25*k)
        else:
            fp([(-13,-8),(8,-3),(5,4),(-9,3)],eye,ink,1.4*k)
            fp([(16,-4),(26,-9),(26,-2),(18,3)],eye,ink,1.25*k)
        fo(2,-1,1.9,3.7,'#302231',None)
        fo(23,-3,1.15,2.9,'#302231',None)
        fl([(-15,-11),(-3,-9),(9,-4)],shade,3.0*k)
        fl([(15,-6),(26,-11)],shade,2.5*k)
        fs((13,5),((15,1),(25,0),(29,3)),((34,6),(29,10),(23,10)),
           ((17,10),(11,9),(13,5)),fill=skin,edge=shade,w=1.1*k)
        fo(27,5,1.8,1.2,shade,None);fo(19,5.8,1.5,1.1,shade,None)
        fl([(1,13),(10,15),(18,13),(27,11)],ink,2.2*k)
        fp([(9,14),(13,14),(11,19)],claw,ink,.8*k)
        fp([(22,12),(26,11),(24,17)],claw,ink,.8*k)
        if adult:fp([(16,14),(19,13),(17,18)],claw,ink,.7*k)
        fl([(-8,13),(-3,14)],shade,1.2*k)
        if adult:
            fp([(-19,4),(-8,8),(3,10),(-1,13),(-14,11)],'#655b6c',None)
            fl([(-15,10),(-7,13),(-4,12)],shade,1.3*k)
    return c.finish()
