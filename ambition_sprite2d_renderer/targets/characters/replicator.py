"""HighLife Replicator: actual B36/S23 generations in a rotated cell grid.

Seed: 2b3o$bo2bo$o3bo$o2bo$3o! (LifeWiki, HighLife/Replicator).
The pattern does not have a period-12 return to a single seed: at generation
12 it has two seeds. The regular poses hold the seed; the complete one-way
replication is reserved for the death row. The engine spawns two non-dividing
replicator_copy actors at the end of that row. No unbounded spawning.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
from ._replicator_radical_art import Canvas, INK, add, mul, rot, phase, track, clamp, smooth, lerp, rgbmix, floating_actor, publish

TARGET_NAME='replicator'
FRAME_SIZE=(256,208)
CENTER=(128.,104.)
S=17.
WINDUP_S,ACTIVE_S,RECOVER_S=.48,.20,.52
ROWS=[('idle',16,100),('walk',16,80),('notice',8,75),('windup',12,60),('attack_side',40,30),('hit',8,75),('death',47,45)]
LOOPS={'idle','walk','windup'}
SEED=frozenset((x-2,y-2) for y,row in enumerate(('..###','.#..#','#...#','#..#.','###..')) for x,c in enumerate(row) if c=='#')


def step(live):
    """HighLife: B36/S23, not B3/S23. B6 only applies to dead cells."""
    count=Counter((x+dx,y+dy) for x,y in live for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy)
    return frozenset(p for p,n in count.items() if (n in (2,3) if p in live else n in (3,6)))


def translate(live,dx,dy):return frozenset((x+dx,y+dy) for x,y in live)


def generations(n):
    out=[SEED]
    for _ in range(n):out.append(step(out[-1]))
    return tuple(out)


GENS=generations(36)
assert GENS[12]==translate(SEED,-2,-2)|translate(SEED,2,2)
assert GENS[36]==frozenset.union(*(translate(SEED,k,k) for k in (-6,-2,2,6)))
ACTOR_METADATA=floating_actor(TARGET_NAME,'Replicator','automaton',['cellular_automaton','highlife','replicator'],
    'The actual 12-cell HighLife B36/S23 replicator, drawn on a grid rotated forty-five degrees. The death row steps twelve exact generations, ending in two translated seeds. Glowing mineral-like square cells, not a biological organism.',
    'An aerial lunge enemy which divides into two smaller non-dividing copies when defeated.')


def _at(cell,origin,scale=1.,angle=0.):
    return add(origin,mul(rot(cell,-45+angle),S*scale))


def _tile(d,c,size,heat=0.,alpha=1.,new=False,angle=0.):
    """A beveled square centered on the rotated lattice, with a cell core."""
    dark=rgbmix((20,71,65),(82,46,37),heat)
    rim=rgbmix((104,231,164),(255,182,75),heat)
    light=rgbmix((212,255,209),(255,242,166),heat)
    low=rgbmix((42,132,114),(162,74,42),heat)
    core=rgbmix((43,163,126),(236,126,59),heat)
    if new:rim=rgbmix(rim,(245,255,218),.53);light=(255,255,226)
    def rgba(c):return (*c,round(255*clamp(alpha)))
    def square(r):return [add(c,rot(p,angle)) for p in [(0,-r),(r,0),(0,r),(-r,0)]]
    r=size*.65
    q=square(r);inside=square(r*.68)
    # Side bevels are integral to the cell, not a drop shadow.
    d.poly(q,rgba(dark),rgba((20,44,46)),1.25)
    d.poly([q[0],q[1],inside[1],inside[0]],rgba(rim),None)
    d.poly([q[0],q[3],inside[3],inside[0]],rgba(light),None)
    d.poly([q[1],q[2],inside[2],inside[1]],rgba(low),None)
    d.poly([q[3],q[2],inside[2],inside[3]],rgba(dark),None)
    d.poly(inside,rgba(core),rgba(dark),.7)
    d.poly(square(r*.26),rgba(light),None)
    d.line([add(c,rot(p,angle)) for p in [(-r*.52,0),(0,-r*.52),(r*.52,0)]],rgba(rim),.7)


def _draw(d,live,origin,heat=0.,old=None,scale=1.,alpha=1.,angle=0.):
    for p in sorted(live,key=lambda p:(p[1]-p[0],p[0]+p[1])):
        _tile(d,_at(p,origin,scale,angle),S*scale,heat,alpha,old is not None and p not in old,angle)


def _render_common(anim,i,n,child=False):
    t=phase(i,n,anim in LOOPS);p=math.tau*t
    d=Canvas(FRAME_SIZE);origin=CENTER;heat=0.;scale=1.;angle=0.
    if anim=='idle':
        origin=add(CENTER,(0,2*math.sin(p)));heat=.08+.05*math.sin(p)
    elif anim=='walk':
        origin=add(CENTER,(3*math.sin(p),2*math.cos(p)));heat=.18
    elif anim=='notice':
        origin=add(CENTER,(0,-3*math.sin(math.pi*t)));heat=track(t,[(0,0),(.35,.67),(1,.24)])
    elif anim=='windup':
        origin=add(CENTER,(-6,0));heat=.76+.08*math.sin(p);angle=-12
    elif anim=='attack_side':
        a=WINDUP_S/(WINDUP_S+ACTIVE_S+RECOVER_S);b=(WINDUP_S+ACTIVE_S)/(WINDUP_S+ACTIVE_S+RECOVER_S)
        x=track(t,[(0,-6),(a,-6),(a+.075,13),(b,13),(.88,0),(1,0)])
        heat=track(t,[(0,.8),(a,.8),(a+.07,1),(b,1),(.85,.1),(1,0)])
        origin=add(CENTER,(x,0))
        # Rigidly rotate the complete lattice into a horizontal attack
        # silhouette. No cell births/deaths are invented for the lunge.
        angle=track(t,[(0,-12),(a,-12),(a+.075,90),(b,90),(.88,0),(1,0)])
        if a<t<b+.1:
            strength=math.sin(math.pi*clamp((t-a)/(b+.1-a)))
            for p0 in sorted(SEED):
                c=_at(p0,origin,angle=angle)
                d.line([add(c,(-18*strength,0)),c],(109,229,170,round(100*strength)),1.5)
    elif anim=='hit':
        origin=add(CENTER,(-9*math.sin(math.pi*t),-2*math.sin(math.pi*t)));heat=.85*math.sin(math.pi*t);angle=-17*math.sin(math.pi*t)
    elif anim=='death':
        if child:
            # A copy is a finite combatant; its death removes cells instead
            # of simulating another true replication. It never spawns more.
            keep=sorted(SEED,key=lambda c:(c[0]+c[1],c[1]))[:max(0,math.ceil(len(SEED)*(1-t)))]
            _draw(d,keep,origin,.15,alpha=max(.04,1-t))
            return d.finish()
        # Three frames per generation, preserving exact live positions.
        # After the two-copy pattern is held for three frames, both intact
        # seeds resize and move to the runtime split offsets. This final
        # adjustment is game presentation, not an additional CA generation.
        if i<39:
            g=i//3;live=GENS[g];old=GENS[max(0,g-1)]
            _draw(d,live,origin,heat=.10,old=old)
        else:
            blend=smooth((i-38)/max(1,n-1-38))
            offset=lerp(2*math.sqrt(2)*S,18.,blend)
            size=lerp(1.,24/54,blend)
            for sign in (-1,1):
                _draw(d,SEED,add(origin,(sign*offset,0)),heat=.10,scale=size)
        return d.finish()
    else:raise ValueError(anim)
    _draw(d,SEED,origin,heat=heat,scale=scale,angle=angle)
    return d.finish()


def _render_frame(anim,i,n):return _render_common(anim,i,n)


def _body_metrics(fw,fh):
    from ...core.measure import body_metrics_for_box
    # Stable seed body; expansion during division must not alter scaling.
    return body_metrics_for_box((92,44,164,164),fw,fh)


def render(out_dir: str|Path, **opts):
    return publish(TARGET_NAME,ROWS,_render_frame,FRAME_SIZE,ACTOR_METADATA,_body_metrics,out_dir,**opts)
