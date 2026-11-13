"""The sheet of one of the bossofthegame's named agents (Geppetto, Clause,
Wren), drawn by the character generator in every view.

Each agent is a chargen spec (``data/characters/<name>/<name>.chargen.yaml``)
with its own parts (``_band_agents_gear.py``) and the band's instruments
(``_band_instruments.py``), so it has the five drawn views and their mirrors
(eight angles), the motion library's rows, and the rows that play each
instrument (``band_*``). The game's design is
``docs/planning/game/final-boss.md``.
"""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Sequence

import yaml

from ...chargen import extras
from ...chargen.body import build as build_figure
from ...chargen.motion import build_library, solve_clip
from ...chargen.pose3d import ViewSolver
from ...chargen.rig import PX_PER_CM, build_rigs, character_svg
from ...chargen.sheets import COMPOSED, PUBLISH_ROWS, publish_sheet
from ...chargen.spec import CharacterSpec, complete
from ._band_instruments import ROWS as BAND_ROWS
from ._band_instruments import band_clips, instrument_parts

DATA = Path(__file__).resolve().parents[2] / "data" / "characters"

#: The rows of an agent's sheet: a fighter's (moving, fighting, holding an
#: item), then the band's. Not the rows of sitting down and sleeping: a
#: sheet that can sit sits down when its body stands idle
#: (`request_actor_pose` in the game's animator), and an agent idles in the
#: fight while it waits for its turn at the player.
OFF_DUTY = ("sit_down", "sit_idle", "stand_up", "sleep")
ROWS = tuple(r for r in PUBLISH_ROWS if r not in OFF_DUTY) + BAND_ROWS


def spec_path(name: str) -> Path:
    return DATA / name / f"{name}.chargen.yaml"


def load_spec(name: str) -> CharacterSpec:
    return complete(yaml.safe_load(spec_path(name).read_text(encoding="utf8")))


def library(fig, grip: str, own_props: Dict[str, float]):
    """The motion library's clips posed for ``grip``, and the band's rows
    (with the agent's own prop put away while it plays)."""
    lib = dict(build_library(fig, grip))
    lib.update(band_clips(fig, {name: 0.0 for name in own_props}))
    return lib


def _clips(fig, view, doc, *, grip: str, own_props: Dict[str, float]) -> Dict[str, dict]:
    lib = library(fig, grip, own_props)
    solver = ViewSolver(fig, view, doc, PX_PER_CM)
    return {name: solve_clip(lib[name], solver) for name in ROWS if name in lib}


def build(name: str, parts: Callable, out_dir: Path, *, grip: str, own_props: Dict[str, float]) -> Dict[str, Path]:
    """The agent's multiview SVG and one rig per view in ``out_dir``; the
    rigs, by view key."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = load_spec(name)
    svg_path = out_dir / f"{name}.svg"
    with extras.using(parts, instrument_parts):
        svg_path.write_text(character_svg(spec), encoding="utf8")
        rigs = build_rigs(spec, svg_path, out_dir, clips=partial(_clips, grip=grip, own_props=own_props), grip=grip)
    views = {n: c.view for n, c in library(build_figure(spec), grip, own_props).items()}
    for path in rigs.values():
        doc = json.loads(path.read_text(encoding="utf8"))
        doc["chargen"]["publish_views"] = {n: views.get(n, "side") for n in doc["clips"]}
        path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    return rigs


def actor_metadata(name: str, character_id: str, display_name: str, description: str, traits: Sequence[str]) -> dict:
    return {
        "actor": {"character_id": character_id, "display_name": display_name, "actor_id": name},
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium",
                 "traits": ["story", "humanoid", "agent", "generated", *traits], "locomotion_hint": "Walk"},
        "brain": {"default_preset": "melee_brute_striker"},
        "actions": {"default_preset": "striker_swipe"},
        "visual": {"default_pose": "idle", "canonical_source": f"ambition_sprite2d_renderer/data/characters/{name}/{name}.chargen.yaml"},
        "tags": ["story", "agent", "enemy", "generated", "svg_rigged"],
        "animation_bindings": {"default": {"animation": "idle", "events": []}, "interaction.talk": {"animation": "talk", "events": []}},
        "authoring_description": description,
        "missing_information": ["The concept sheets show other forms (weight tiers, thinking modes); this sheet is one form."],
    }


def make_render(name: str, parts: Callable, metadata: dict, *, grip: str, own_props: Dict[str, float]):
    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        out_dir = Path(out_dir)
        rigs = build(name, parts, out_dir / "rig", grip=grip, own_props=own_props)
        rows = [r for r in ROWS if r in COMPOSED or r in json.loads(next(iter(rigs.values())).read_text(encoding="utf8"))["clips"]]
        return publish_sheet(load_spec(name), out_dir, rigs, target=name, metadata=metadata, rows=rows, grip=grip)

    return render


__all__ = ["ROWS", "actor_metadata", "build", "library", "load_spec", "make_render", "spec_path"]
