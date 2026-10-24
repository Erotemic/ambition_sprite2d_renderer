"""The character generator: many distinct humanoid townsfolk from simple parts.

A :class:`~.spec.CharacterSpec` (a base body type, face, hair, palette and
clothes) is drawn in five views from one 3D description, written as a
multiview SVG in the humanoid rig contract, and bound to the common humanoid
skeleton, so a generated character is posed by the same tools as the
hand-made cast. See ``README.md`` (section "Generated characters") and
``python -m ambition_sprite2d_renderer.chargen --help``.
"""

from .spec import BASES, CharacterSpec, complete, crowd, generate, spec_distance, validate

__all__ = ["BASES", "CharacterSpec", "complete", "crowd", "generate", "spec_distance", "validate"]
