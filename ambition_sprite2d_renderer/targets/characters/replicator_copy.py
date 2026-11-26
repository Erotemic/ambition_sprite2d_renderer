"""The Replicator's smaller, finite offspring. Same HighLife seed art."""
from __future__ import annotations
from pathlib import Path
from . import replicator as R
from ._replicator_radical_art import floating_actor, publish

TARGET_NAME='replicator_copy'
FRAME_SIZE=R.FRAME_SIZE
ROWS=[(a,20 if a=='death' else n,ms) for a,n,ms in R.ROWS]
ACTOR_METADATA=floating_actor(TARGET_NAME,'Replicator Copy','automaton',['cellular_automaton','highlife','replicator','offspring'],
    'A smaller instance of the HighLife replicator seed. A separate finite combat identity, so defeating it does not cause further multiplication.',
    'One of the two offspring of a defeated Replicator; a small aerial attacker with no death split.')

def _render_frame(anim,i,n):return R._render_common(anim,i,n,child=True)

def render(out_dir: str|Path, **opts):
    return publish(TARGET_NAME,ROWS,_render_frame,FRAME_SIZE,ACTOR_METADATA,R._body_metrics,out_dir,**opts)
