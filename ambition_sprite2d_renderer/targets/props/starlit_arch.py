"""Magical's portal arch (WORLD-LAYERS MG-2): the portal arch's assembly
(``_portal_arch``) in pale starlit stone, gold stars set in alternate
voussoirs and in its jambs, glints twinkling about its head that all
brighten as it opens. Mary-O's dimension draws its arches where the Jungle
grows moss on its own.
"""

from __future__ import annotations

from . import _portal_arch as arch

TARGETS = {"starlit_arch": arch.render_targets("starlit_arch", arch.STARLIT)}
