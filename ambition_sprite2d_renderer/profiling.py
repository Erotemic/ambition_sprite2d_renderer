"""Optional line-level profiling hooks for the sprite renderer.

The committed instrumentation is deliberately inert unless profiling is
requested.  Developers may install ``line_profiler`` into the renderer's local
virtualenv and run any normal command with ``LINE_PROFILE=1``; without the
optional package, :data:`profile` is a zero-overhead identity decorator.

``regen_sprites.sh`` sets ``AMBITION_LINE_PROFILE_OUTPUT`` per expensive Python
subprocess so a full regeneration writes separate reports instead of repeatedly
overwriting ``profile_output.lprof``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def _env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


try:
    from line_profiler import profile as profile
except ImportError:

    def profile(func: Callable[P, R]) -> Callable[P, R]:
        """No-op fallback used when the optional profiler is unavailable."""

        return func

else:
    output_prefix = os.environ.get("AMBITION_LINE_PROFILE_OUTPUT")
    if output_prefix and _env_truthy(os.environ.get("LINE_PROFILE")):
        prefix_path = Path(output_prefix)
        prefix_path.parent.mkdir(parents=True, exist_ok=True)

        # A full sprite regeneration launches several profiled Python processes.
        # line_profiler's defaults print the complete report to stdout and also
        # write two text copies plus the binary .lprof file at interpreter exit.
        # The terminal dump can be enormous and makes the next long-running
        # subprocess look hung. Keep the compact binary report as the default;
        # developers can request one detailed text sidecar explicitly.
        profile.write_config["stdout"] = False
        profile.write_config["lprof"] = True
        profile.write_config["timestamped_text"] = False
        profile.write_config["text"] = _env_truthy(
            os.environ.get("AMBITION_LINE_PROFILE_TEXT")
        )
        profile.enable(output_prefix=str(prefix_path))
