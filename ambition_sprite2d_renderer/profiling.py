"""Optional line-level profiling hooks for the sprite renderer.

The instrumentation is inert during ordinary rendering. Set ``LINE_PROFILE=1``
to enable the managed profiler provided by :mod:`line_profiler`.

Deliberately do not customize line_profiler's output prefix, output directory,
write modes, or checkpoint behavior here. The upstream managed ``profile``
decorator already honors ``LINE_PROFILE`` and writes its configured/default
report at interpreter exit. Keeping that behavior intact means a developer can
run a command from the repository root and find the ordinary line-profiler
output in the current working directory, without renderer-specific flags or
output conventions.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def _env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


PROFILE_REQUESTED = _env_truthy(os.environ.get("LINE_PROFILE"))
PROFILE_ACTIVE = False
# Kept as a compatibility export for callers/tests from the earlier profiling
# shim. We no longer impose an output prefix; line_profiler owns that policy.
PROFILE_OUTPUT_PREFIX = None

try:
    from line_profiler import profile as profile
except ImportError:

    def profile(func: Callable[P, R]) -> Callable[P, R]:
        """No-op fallback used when the optional profiler is unavailable."""

        return func

    if PROFILE_REQUESTED:
        print(
            "[profiling] LINE_PROFILE=1 was requested, but line_profiler is not "
            f"installed in {sys.executable}; no line profile will be produced.",
            file=sys.stderr,
            flush=True,
        )
else:
    if PROFILE_REQUESTED:
        # The imported GlobalProfiler reads LINE_PROFILE itself. Do not call
        # enable(), alter write_config, or choose an output_prefix: those would
        # replace line_profiler's normal cwd/default-output behavior.
        PROFILE_ACTIVE = True
        print(
            "[profiling] LINE_PROFILE=1; using line_profiler's default output "
            "configuration in the current working directory",
            file=sys.stderr,
            flush=True,
        )


def profile_checkpoint(
    label: str = "",
    *,
    min_interval_seconds: float = 30.0,
    force: bool = False,
) -> bool:
    """Compatibility no-op for the former renderer-managed checkpoints.

    Progress reporting may still call this function, but line_profiler now owns
    report emission completely. In particular, we do not repeatedly serialize
    a growing profile during a long 900-frame sheet build.
    """

    del label, min_interval_seconds, force
    return False


__all__ = [
    "PROFILE_ACTIVE",
    "PROFILE_OUTPUT_PREFIX",
    "PROFILE_REQUESTED",
    "profile",
    "profile_checkpoint",
]
