"""The publication pipeline shared by SVG-rigged fighters with AUTHORED swings.

The Officer, the Medic and the Actor differ in exactly three things: which rig
they bind, which motion library they bind it to, and what their swings do to the
air. Everything between -- measuring the overscan a pose needs, measuring the
FURTHER overscan its effect needs, compositing that effect per CLIP rather than
per frame, and publishing the hit volume built from the same spec the effect was
drawn from -- is one pipeline, and it was copied three times before it was
written down once.

⛔ **the effect is composited per CLIP, not per FRAME.** The streaks on frame 4
are drawn from where the fist was on frames 1-3, so a `render_fn` that only ever
sees one frame cannot draw them -- which is how a published sheet ends up
carrying none of its own effects.

⛔ **and the danger axis comes from the SKELETON.** `swing_effects` can infer it
from brightness, which holds for a dark fighter carrying bright steel and fails
for anything else: on a woman with skin and pale hands it reads her face as the
weapon. Every character here names the striking limb in its spec instead.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ...authoring import strike_axis, swing_effects
from ...authoring.motion_ir import CharacterMotionBinding
from ...authoring.rig_gameplay_body import gameplay_body_metrics
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet

DATA = Path(__file__).resolve().parents[2] / "data" / "characters"


class AuthoredSwingFighter:
    """One SVG-rigged fighter, published with its authored effects and volumes."""

    def __init__(self, target: str, *, collision_scale: float = 1.8):
        self.target = target
        self.motion_path = DATA / target / f"{target}.motion.json"
        self.collision_scale = collision_scale

    # ── sources ───────────────────────────────────────────────────────────────
    @lru_cache(maxsize=1)
    def prepared(self):
        return CharacterMotionBinding.load(self.motion_path).load_prepared()

    @lru_cache(maxsize=1)
    def doc(self) -> RigDocument:
        # RigDocument is a temporary renderer projection. The editable sources
        # are the SVG static rig plus the shared pose/clip library this
        # character binds.
        return self.prepared().to_rig_document()

    @lru_cache(maxsize=1)
    def _spec_dir(self) -> Path:
        """Where the swing specs live -- asked of the LIBRARY this character binds.

        The specs sit beside the clips they describe, so a medic's discharge
        cannot be read for a swordsman's clip of the same name.
        """
        return Path(self.prepared().library.path).parent / "specs"

    def spec_for(self, animation: str) -> dict | None:
        path = self._spec_dir() / f"{animation}.spec.json"
        return json.loads(path.read_text()) if path.exists() else None

    # ── sampling ──────────────────────────────────────────────────────────────
    def _sample_times(self, animation: str, frame_count: int) -> list[float]:
        clip = self.prepared().library.clips[animation]
        return [
            round(i * clip.frame_duration_ms / 1000.0 / max(clip.duration_s, 1e-9), 9)
            for i in range(frame_count)
        ]

    def _strike_axes(self, animation: str, frame_count: int, padding):
        """Where the danger is on each frame, read off the solved skeleton.

        Measured at the SAME padding as the frames it describes: an axis is a
        coordinate, and a coordinate in another frame is a wrong answer.
        """
        spec = self.spec_for(animation)
        if not spec:
            return None
        return strike_axis.for_spec(
            self.doc(), animation, self._sample_times(animation, frame_count),
            spec, padding=padding,
        )

    def _raw_frame(self, animation: str, frame_idx: int, frame_count: int):
        clip = self.prepared().library.clips[animation]
        if frame_count != clip.frame_count:
            raise ValueError(
                f"{animation}: requested {frame_count} publication frames, "
                f"source declares {clip.frame_count}")
        at_s = frame_idx * clip.frame_duration_ms / 1000.0
        normalized = round(at_s / max(clip.duration_s, 1e-9), 9)
        return self.doc().render_at(animation, normalized, padding=self.padding())

    @lru_cache(maxsize=None)
    def _clip_frames(self, animation: str, frame_count: int) -> tuple:
        raw = [self._raw_frame(animation, i, frame_count) for i in range(frame_count)]
        spec = self.spec_for(animation)
        if not spec:
            return tuple(raw)
        axes = self._strike_axes(animation, frame_count, self.padding())
        return tuple(swing_effects.composite_authored_effect(raw, spec, axes=axes))

    def render_frame(self, animation: str, frame_idx: int, frame_count: int):
        return self._clip_frames(animation, frame_count)[frame_idx]

    # ── overscan ──────────────────────────────────────────────────────────────
    @lru_cache(maxsize=1)
    def padding(self) -> tuple[int, int, int, int]:
        """Minimal overscan for the exact poses this sheet publishes.

        The rig's logical frame is an authoring coordinate system, not a
        clipping promise: measure the publication samples cheaply at 1x, then
        render the real sheet with enough transparent room to keep every
        transformed part.
        """
        prepared = self.prepared()
        samples = []
        for animation, frame_count, _ms in self.doc().rows():
            clip = prepared.library.clips[animation]
            for i in range(frame_count):
                at_s = i * clip.frame_duration_ms / 1000.0
                samples.append((animation, round(at_s / max(clip.duration_s, 1e-9), 9)))
        pose = self.doc().measure_render_padding(samples, margin=4)
        # ⛔ AND THE EFFECT REACHES FURTHER THAN THE POSE. A smash's plume opens
        # well past the fist that throws it; measure the poses alone and the
        # publish clips it flat at the frame edge.
        return tuple(max(a, b) for a, b in zip(pose, self._effect_padding()))

    def _effect_padding(self) -> tuple[int, int, int, int]:
        doc = self.doc()
        width, height = int(doc.frame["width"]), int(doc.frame["height"])
        probe = max(width, height)
        required = [0, 0, 0, 0]
        for animation, frame_count, _ms in doc.rows():
            spec = self.spec_for(animation)
            if not spec:
                continue
            frames = [doc.render_at(animation, t, supersample=1, scale=1, padding=probe)
                      for t in self._sample_times(animation, frame_count)]
            axes = self._strike_axes(animation, frame_count, probe)
            for image in swing_effects.composite_authored_effect(frames, spec, axes=axes):
                bbox = image.getchannel("A").getbbox()
                if bbox is None:
                    continue
                required[0] = max(required[0], probe - bbox[0])
                required[1] = max(required[1], probe - bbox[1])
                required[2] = max(required[2], bbox[2] - (probe + width))
                required[3] = max(required[3], bbox[3] - (probe + height))
        return tuple(max(0, value) + 4 for value in required)

    def frame_size(self) -> tuple[int, int]:
        doc = self.doc()
        left, top, right, bottom = self.padding()
        scale = max(1, int(doc.frame.get("render_scale", 1)))
        return ((int(doc.frame["width"]) + left + right) * scale,
                (int(doc.frame["height"]) + top + bottom) * scale)

    # ── published gameplay facts ──────────────────────────────────────────────
    @lru_cache(maxsize=1)
    def attack_hitboxes(self) -> dict:
        """The authored hit volume for every swing that has a spec.

        Built from the same axes and the same spec as the effect, so the shape a
        player is shown IS the shape that hits them. Without it every attack
        falls back to a rectangle nobody has reviewed.
        """
        out = {}
        padding = self.padding()
        for animation, frame_count, _ms in self.doc().rows():
            spec = self.spec_for(animation)
            if not spec:
                continue
            raw = [self._raw_frame(animation, i, frame_count) for i in range(frame_count)]
            axes = self._strike_axes(animation, frame_count, padding)
            poly = swing_effects.authored_hit_volume(raw, spec, axes=axes)
            if poly:
                out[animation] = {"poly": poly}
        return out

    def body_metrics(self, _fw: int, _fh: int):
        """The gameplay body: the TRUNK, crown of the head to the feet.

        Without this the box is the alpha bbox of the sheet's FIRST frame, and a
        rig publishes its rows alphabetically -- so it would be `aim`, arm
        extended, and she would collide with the world using her aiming pose.
        """
        metrics = gameplay_body_metrics(self.doc(), padding=self.padding(),
                                        frame_size=self.frame_size())
        if metrics is None:
            raise ValueError(f"{self.target}: no trunk parts to measure a body from")
        return metrics

    # ── publication ───────────────────────────────────────────────────────────
    def render(self, out_dir, actor_metadata: dict):
        doc = self.doc()
        outputs = build_sheet(
            target=self.target,
            rows=doc.rows(),
            render_fn=self.render_frame,
            out_dir=Path(out_dir),
            frame_size=self.frame_size(),
            auto_crop=True,
            crop_margin=4,
            actor_metadata=actor_metadata,
            body_metrics_fn=self.body_metrics,
            animation_key_map={name: name for name, _f, _d in doc.rows()},
            attack_hitboxes=self.attack_hitboxes(),
            pose_bodies="authored",
            sheet_tuning=doc.sprite_tuning or {"collision_scale": self.collision_scale},
            authored_faces_left=doc.authored_faces_left,
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical",
                "canonical_transparent", "preview")
        return [Path(outputs[key]) for key in keys if outputs.get(key)]
