"""The one place sprite-sheet packing / trim policy is decided.

Every build path — the adapter spine (``authoring/sheet.py``), the tack-on spine
(``authoring/tackon_sheet.py``), and the rigged-doc spine
(``authoring/rigdoc.py``) — used to carry its own ``trim`` default (adapter
True, tack-on False, rigged True) plus a per-config opt-out (``boss.yaml``'s
``trim: false``). That scattered policy is replaced by ``policy_for(target)``:
a declarative, per-target table that says how a target's frames are laid out
into page images.

The policy is expected to CHANGE as we learn each sheet's memory access pattern
(which sprites are resident together, which want their own pages), so it lives
here as data, not as defaults sprinkled through the builders.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


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
    # Targets sharing a `group` pack their frames onto the same page images
    # (one set of PNGs, one SheetRecord per target sharing the `images` list).
    # `None` ⇒ the target owns its own pages. Grouping is the lever for "these
    # sprites are always resident together" (e.g. a biome's cast); declared here
    # so the access pattern is data. Single-target (own pages) is today's
    # default — cross-target packing reads this field when it lands.
    group: Optional[str] = None


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


def policy_for(target: str) -> PackPolicy:
    """Pack policy for a sprite target (its sheet file-root / RON ``target``)."""
    return _POLICIES.get(target, PackPolicy())
