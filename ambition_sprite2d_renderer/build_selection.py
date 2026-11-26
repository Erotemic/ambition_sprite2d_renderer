"""Select published asset units from their freshness status."""
from enum import Enum


class BuildMode(Enum):
    DEFAULT = "default"
    LOOSE = "loose"
    MISSING = "only-missing"
    POSSIBLY_STALE = "only-possibly-stale"
    FORCE = "force"

    @classmethod
    def from_flags(cls, *, loose=False, missing_only=False, possibly_stale_only=False, force=False):
        active = [mode for mode, enabled in (
            (cls.LOOSE, loose), (cls.MISSING, missing_only),
            (cls.POSSIBLY_STALE, possibly_stale_only), (cls.FORCE, force),
        ) if enabled]
        if len(active) > 1:
            raise ValueError(" and ".join(f"--{mode.value}" for mode in active) + " cannot be combined")
        return active[0] if active else cls.DEFAULT

    def includes(self, state: str, scope: str | None = None) -> bool:
        shared = state == "stale" and scope == "shared"
        if self == BuildMode.MISSING:
            return state == "missing"
        if self == BuildMode.POSSIBLY_STALE:
            return shared
        if self == BuildMode.FORCE:
            return True
        return state != "current" and (not shared or self != BuildMode.LOOSE)

    def check(self) -> "BuildMode":
        if self not in {BuildMode.DEFAULT, BuildMode.LOOSE}:
            raise ValueError("--check accepts only --loose as a selection option")
        return self
