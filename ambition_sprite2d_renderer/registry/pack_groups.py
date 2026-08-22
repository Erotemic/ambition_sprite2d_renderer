"""Central sprite-sheet packing and trim policy.

All adapter, tack-on, and rig-document build paths ask `policy_for(target)` for
layout policy instead of carrying independent defaults. Per-target policy remains
data here so packing can evolve without diverging builders."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PackPolicy:
    """How a sprite target's frames become sheet page image(s)."""

    # Alpha-trim + MaxRects-pack the frames: reclaims the 84-97% transparent
    # margins and lets a tall sheet split across pages to stay within the GPU
    # texture limit. Requires a trim-aware runtime — the CharacterAnimator and
    # BossAnimator paths re-derive each frame's size + anchor from its trim
    # offset (every character / NPC / prop / boss spawn calls
    # `with_render_basis`). The few effect / item runtimes that sample the sheet
    # as a fixed grid can't, so they opt out (see `_UNTRIMMED`).
    trim: bool = True
    # Fixed square page size the packer fills before opening another page. Pages
    # are the RESIDENCY UNIT — the grain at which a future loader could stream a
    # sheet in or out — so this is a policy knob, not a hidden constant.
    page_size: int = 4096
    # GPU max texture dimension guard; the packer never emits a larger page.
    max_dim: int = 16384
    # NOTE: cross-target locality grouping landed as the ultrapack PackPlan
    # (authoring/ultrapack.py + data/pack_plan.yaml), not as a field here —
    # this policy stays per-target (trim + page geometry only).


# Targets whose runtime samples the sheet as a fixed, untrimmed grid with no
# per-frame size/anchor compensation, so their frames must NOT be trimmed:
#   - shrine                — ShrineVisualAnim (rendering/shrine_visuals.rs)
#   - robot_slash           — one-shot melee effect (rendering/slash_visuals.rs)
#   - glider                — projectile, sprite.rect sub-image (projectile_visuals.rs)
#   - lasersword            — wielded + projectile item sprite (item_visuals.rs)
#   - lasersword_with_guns  — pirate gun-sword overlay (pirate_weapon.rs)
# Everything else renders through a trim-aware runtime and packs by default.
_UNTRIMMED = (
    "shrine",
    "robot_slash",
    "glider",
    "lasersword",
    "lasersword_with_guns",
)

# Per-target overrides. Most targets take the default policy (trim=True, own
# pages); a target appears here only when it diverges.
_POLICIES: Dict[str, PackPolicy] = {target: PackPolicy(trim=False) for target in _UNTRIMMED}

# GNU-ton renders a split body/hands pair that must share ONE atlas layout (the
# runtime mirrors the body's flat index + trim onto the hands child). The shared
# record carries a single image per layer, so the pack must stay on ONE page —
# a `page_size` at the GPU cap keeps the single-bin packer from spilling.
_POLICIES["gnu_ton_boss"] = PackPolicy(page_size=16384)


def policy_for(target: str) -> PackPolicy:
    """Pack policy for a sprite target (its sheet file-root / RON ``target``)."""
    return _POLICIES.get(target, PackPolicy())
