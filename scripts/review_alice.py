"""Render Alice at inspection size, across poses, and through a walk cycle."""
from pathlib import Path
from PIL import Image, ImageDraw
from ambition_sprite2d_renderer.targets.characters.alice_cryptographer import AliceCryptographerGenerator, AliceSpec
out=Path(__file__).resolve().parents[1] / 'generated' / 'alice_review'
out.mkdir(parents=True, exist_ok=True)
g=AliceCryptographerGenerator(); spec=AliceSpec('alice',540,'alice','Alice','npc','ivory')
poses=[('idle',1),('idle_front',1),('idle_side',1),('walk',0),('walk',2),('run',3),('jump',3),('attack_side',3),('interact',3),('crouch',2),('celebrate',3),('death',5)]
board=Image.new('RGB',(1200,960),'#202735'); d=ImageDraw.Draw(board)
for i,(name,f) in enumerate(poses):
    n=g.ANIMATIONS[name]['frames']
    img=g.render_animation_frame(spec,name,f,n,(300,300),background=None,supersample=2,downsample='lanczos')
    x,y=(i%4)*300,(i//4)*320
    board.paste(img,(x,y),img); d.text((x+15,y+295),name,fill='#ead9b6')
board.save(out/'pose_review.png')
g.render_animation_frame(spec,'idle',1,8,(1024,1024),background=None,supersample=2,downsample='lanczos').save(out/'alice.png')
frames=[]
for i in range(8):
    img=g.render_animation_frame(spec,'walk',i,8,(384,384),background=(32,39,53,255),supersample=2,downsample='lanczos')
    frames.append(img.convert('RGB'))
frames[0].save(out/'walk.gif',save_all=True,append_images=frames[1:],duration=95,loop=0)
from rich.console import Console
Console().print(f"[link={ (out / 'pose_review.png').as_uri() }]Pose review[/link] · [link={out.as_uri()}]Artifact directory[/link]")
