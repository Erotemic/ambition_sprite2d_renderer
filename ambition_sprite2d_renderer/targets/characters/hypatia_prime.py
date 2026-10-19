"""Hypatia Prime: an old scholar of Alexandria in future plate over a blue himation, with an armillary tech-lance.

An SVG rig. The drawing is ``data/characters/hypatia_prime/hypatia_prime.svg``
(``scripts/svg_art/hypatia_prime_art.py``), and the skeleton and the rows are
``rigged/hypatia_prime/hypatia_prime.rig.json``
(``scripts/build_hypatia_prime_rig.py``).

Hypatia Prime is a science-fantasy mystery character inspired by Hypatia of
Alexandria: mathematician, astronomer, philosopher, teacher, and historical
person whose surviving record is fragmentary and heavily refracted through
later retellings. The design does not pretend to reveal a definitive private
personality or appearance.

Jon, 2026-10-18: "this is hypatia prime, not literal hypatia, so maybe give
her some future techno space armor, with the alexandria vibe. Also I think she
was supposed to be an old woman." Her look (``prime``) is an old woman, silver
hair under a crown braid, a lined face, a slight stoop, commanding still: sleek
plate (a breastplate with an armillary ring at its heart, a pauldron, a
vambrace, a belt and tasset, greaves) over the ivory chiton and the blue
himation, Greek-key meanders running as lit circuitry along their borders, an
armillary ring on her back, and her staff an armillary tech-lance. The literal
reconstruction he chose first (``alexandria``), today's midnight mantle and
bronze (``guardian``) and a library keeper (``library``) are drawn by the art
script and cast nowhere. Her mystery is in her moves: the alternate
silhouettes of ``library_of_shadows`` behind her that never settle, the
folios with pieces missing, the revelation that aligns the fragments.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
from typing import List

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "hypatia_prime"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "hypatia_prime.rig.json"
PORTRAIT_SIZE = (192, 192)
#: Her head in the rig's 288x256 frame: the portrait's crop.
PORTRAIT_BOX = (84, 82, 152, 150)

AUTHORING_DESCRIPTION = {
    "parody_of": "Hypatia of Alexandria",
    "character_name": "Hypatia Prime",
    "concept": (
        "An enigmatic scholar-guardian inspired by Hypatia of Alexandria. The character "
        "is intentionally presented through incomplete records and competing reconstructions: "
        "a mathematician, astronomer, philosopher, teacher, librarian, and possibly something "
        "more within the game's fiction, but never reduced to a single definitive legend."
    ),
    "name_origin": (
        "Prime suggests a primary or ideal reconstruction among many later versions, while also "
        "giving the character a mathematical and science-fiction title. The game should never "
        "confirm that this reconstruction is the uniquely true one."
    ),
    "historical_mystery": (
        "Much of Hypatia's own work is lost and the surviving evidence is indirect, sparse, and "
        "filtered through later political, religious, literary, and philosophical narratives. "
        "The character's mystery should reflect that problem of historical reconstruction rather "
        "than inventing secret facts about the real person."
    ),
    "visual_inspiration": [
        "A bronze astrolabe halo identifies astronomy and instrument-making while hiding part of the head silhouette.",
        "A layered midnight mantle and palimpsest veil make the figure look copied, revised, and partially erased.",
        "An armillary staff functions as a spear, pointer, measuring instrument, and portable celestial model.",
        "Faint alternate silhouettes appear during special moves but never resolve into one canonical appearance.",
        "Scroll fragments carry conic curves, star positions, and incomplete geometric constructions rather than legible modern formulas.",
    ],
    "gameplay_inspiration": [
        "astrolabe_guard rotates a bronze instrument into a precise defensive alignment.",
        "conic_lance traces ellipse, parabola, and hyperbola arcs before the staff commits to one line of attack.",
        "epicycle_orbit surrounds the character with small nested celestial paths that redirect projectiles.",
        "library_of_shadows calls several incompatible reconstructed silhouettes into the arena.",
        "missing_folio scatters incomplete pages whose gaps become dangerous zones.",
        "prime_revelation aligns the fragments into a momentary radiant model, but still leaves the face obscured.",
    ],
    "gameplay_description": (
        "A precise midrange scholar-knight built around counterplay, orbiting defenses, and delayed "
        "geometric attacks. Hypatia Prime controls space with the armillary staff and astrolabe, then "
        "uses missing fragments to create ambiguity about where the real strike will land. Her strongest "
        "moves briefly align several incomplete reconstructions without ever resolving the character's mystery."
    ),
    "suggested_barks": {
        "idle": [
            "The record is incomplete. That is not permission to stop reading.",
            "A copy of a copy can still preserve an angle.",
            "You expected certainty from fragments?",
        ],
        "combat": [
            "Observe before you conclude.",
            "The orbit closes.",
            "Choose your reconstruction carefully.",
            "The missing line still has consequences.",
        ],
        "on_hit": [
            "Add that to the surviving testimony.",
            "An inelegant correction.",
        ],
        "victory": [
            "One account survives. Not the only one.",
            "The diagram is clearer than the legend.",
        ],
    },
    "fallback_dialogue": [
        "You are speaking to a reconstruction. Whether I am the first, the best, or merely the latest is another question.",
        "Most people remember the ending because endings travel easily. I am more interested in the work that did not survive.",
        "A missing book is not an empty book. It leaves citations, students, arguments, and strangely shaped absences.",
        "Every age redraws me in its own clothing. I have learned to keep several wardrobes.",
        "Mystery is not magic. Sometimes it is simply what remains after the documents do not.",
    ],
    "boundaries": [
        "Do not claim that the game's mysterious details are newly discovered facts about the historical Hypatia.",
        "Do not define her primarily by the violence of her death; center teaching, mathematics, astronomy, philosophy, and lost work.",
        "Avoid flattening complex late-antique history into a single modern culture-war allegory.",
        "The obscured face and conflicting silhouettes should communicate incomplete evidence, not shame or passivity.",
        "Keep Hypatia Prime formidable, intellectually active, and capable of correcting the legends projected onto her.",
    ],
}

ACTOR_METADATA = {
    "actor": {"character_id": "npc_hypatia_prime", "display_name": "Hypatia Prime"},
    "authoring_description": AUTHORING_DESCRIPTION,
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story", "humanoid", "mathematician", "astronomer", "philosopher",
            "scholar_guardian", "mystery", "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True, "jump": True, "climb": True, "fly": None,
            "swim": True, "crawl": True, "use_lifts": True,
            "door_access": ["public", "archive"],
        },
        "interactions": {
            "talk": True, "trade": None, "carry": True,
            "open_doors": ["public", "archive"],
        },
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {"face_guide": {
            "center": {"x": 118.0, "y": 118.0},
            "size": {"w": 30.0, "h": 34.0},
            "source_size": {"w": 288.0, "h": 256.0},
        }},
    },
    "tags": [
        "story", "humanoid", "mathematician", "astronomer", "philosopher",
        "scholar_guardian", "mystery", "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.hypatia_prime", "point": {"x": 116.1, "y": 120.5}},
        "chest": {"source": "explicit.hypatia_prime", "point": {"x": 111.4, "y": 150.0}},
        "hand_l": {"source": "explicit.hypatia_prime", "point": {"x": 97.8, "y": 178.8}},
        "hand_r": {"source": "explicit.hypatia_prime", "point": {"x": 132.3, "y": 159.7}},
        "staff_tip": {"source": "explicit.hypatia_prime", "point": {"x": 132.3, "y": 72.2}},
        "speech_bubble": {"source": "explicit.hypatia_prime", "point": {"x": 116.1, "y": 95.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "conic_lance", "events": []},
        "action.special.primary": {"animation": "epicycle_orbit", "events": []},
        "action.special.secondary": {"animation": "library_of_shadows", "events": []},
        "action.special.tertiary": {"animation": "missing_folio", "events": []},
        "action.defense.block": {"animation": "astrolabe_guard", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "svg_rig_prime_2026_10_18",
        "lineage": [
            {
                "revision_id": "hypatia_prime_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "selected_hypatia_prime_and_requested_mystery_reflecting_the_fragmentary_historical_person",
            },
            {
                "revision_id": "hypatia_prime_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "hypatia_prime_concept_direction",
                "contribution": "procedural_full_action_mysterious_scholar_guardian_with_portraits_barks_and_historical_boundaries",
            },
            {
                "revision_id": "hypatia_prime_svg_rig_alexandria",
                "creator_kind": "model",
                "creator": "claude-opus-5.5",
                "parent_revision_id": "hypatia_prime_procedural_sprite_v1",
                "contribution": "svg_rig_redraw_of_three_looks_alexandria_guardian_library_each_row_reauthored",
            },
            {
                "revision_id": "hypatia_prime_look_a_chosen",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "parent_revision_id": "hypatia_prime_svg_rig_alexandria",
                "contribution": "chose_look_a_alexandria_and_kept_the_other_two_looks",
            },
            {
                "revision_id": "hypatia_prime_prime_look",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "parent_revision_id": "hypatia_prime_look_a_chosen",
                "contribution": "asked_for_an_old_woman_in_future_techno_space_armor_with_the_alexandria_vibe",
            },
            {
                "revision_id": "hypatia_prime_prime_drawn",
                "creator_kind": "model",
                "creator": "claude-opus-5.5",
                "parent_revision_id": "hypatia_prime_prime_look",
                "contribution": "drew_the_prime_look_on_the_same_rig_and_reauthored_death_as_a_prone_fall",
            },
        ],
    },
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


ROWS = _doc().rows()


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    return _doc().render_frame(anim, frame_idx, nframes)


def _render_native_portrait(expression: str = "default", phase: float = 0.0) -> Image.Image:
    anim = {"default": "idle", "talk": "talk", "shadow": "library_of_shadows", "folio": "missing_folio", "reveal": "prime_revelation"}.get(expression, "idle")
    n = dict((name, frames) for name, frames, _ms in ROWS)[anim]
    frame = render_frame(anim, int(phase * n) % n, n)
    return frame.crop(PORTRAIT_BOX).resize(PORTRAIT_SIZE, Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips = {
        "default": PortraitClip.still(_render_native_portrait("default")),
        "talk": PortraitClip(tuple(_render_native_portrait("talk", i / 8) for i in range(8)), duration_ms=104, looping=True),
        "shadow": PortraitClip(tuple(_render_native_portrait("shadow", i / 8) for i in range(8)), duration_ms=90, looping=True),
        "folio": PortraitClip.still(_render_native_portrait("folio", 0.6)),
        "reveal": PortraitClip.still(_render_native_portrait("reveal", 0.5)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


#: Where each attack reaches, in the rig's frame, measured off its active
#: frames: the lance is the staff and its beam ahead of her body, the folios
#: are what she flings ahead, the rest fill the space round her.
ATTACK_HITBOXES = {
    "conic_lance": {"bbox": {"x": 130, "y": 142, "w": 133, "h": 23}},
    "epicycle_orbit": {"bbox": {"x": 72, "y": 70, "w": 82, "h": 171}},
    "library_of_shadows": {"bbox": {"x": 70, "y": 67, "w": 83, "h": 178}},
    "missing_folio": {"bbox": {"x": 140, "y": 81, "w": 38, "h": 119}},
    "prime_revelation": {"bbox": {"x": 70, "y": 28, "w": 86, "h": 210}},
}


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    doc = _doc()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME, rows=ROWS, render_fn=render_frame, out_dir=Path(out_dir),
        frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
        auto_crop=True, crop_margin=4, actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes=ATTACK_HITBOXES,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    doc = _doc()
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir),
                           frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])))


__all__ = ["ACTOR_METADATA", "AUTHORING_DESCRIPTION", "TARGET_NAME", "render", "render_canonical", "render_frame", "render_portraits"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args()
    for path in render(args.out_dir):
        print(path)
    for path in render_portraits(args.out_dir):
        print(path)
