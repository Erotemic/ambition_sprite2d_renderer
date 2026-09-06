"""Shared pytest setup for the sprite renderer test suite.

Adds a ``slow_render`` marker for tests that require full-resolution
rendering and have no low-resolution equivalent yet. Skipped by
default to keep the regression net fast (seconds, not minutes);
opt in with ``pytest --run-slow-render``.

See ``GOALS.md`` for the rationale — the long-term goal is to remove
this marker entirely once every target supports a ``scale`` parameter,
at which point every test is fast.
"""

from __future__ import annotations

from pathlib import Path

import pytest


# ⛔⛔ THE ROSTER LIVES IN THE SUPERPROJECT, AND IT MOVED.
#
# Four tests read the game repo's full sprite-regeneration roster by hard-coded
# path. The superproject grouped its dev scripts and the root `regen_sprites.sh`
# became `scripts/regen/sprites.sh`; the parent's own callers were updated and
# this submodule's were not, so the four went red with `FileNotFoundError` — a
# failure that says nothing about the renderer.
#
# ⭐ ONE PLACE KNOWS THE PATH NOW, and it also knows the honest answer for a
# STANDALONE clone: there is no superproject, so there is no roster to check and
# the test skips rather than inventing a verdict about a file it cannot see.
_ROSTER_RELATIVE = Path("scripts/regen/sprites.sh")


@pytest.fixture(scope="session")
def regen_roster() -> str:
    """The superproject's sprite-regeneration roster, or skip if standalone."""
    superproject = Path(__file__).resolve().parents[3]
    roster = superproject / _ROSTER_RELATIVE
    if not roster.is_file():
        pytest.skip(
            f"no superproject roster at {roster} — this renderer is checked out "
            "standalone, so there is no regen roster to check against"
        )
    return roster.read_text(encoding="utf8")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-slow-render",
        action="store_true",
        default=False,
        help=(
            "Run tests marked `slow_render` (full-resolution sprite renders, "
            "minutes of runtime). Skipped by default. See GOALS.md."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow_render: test requires full-resolution sprite rendering; "
        "skipped by default, opt in with --run-slow-render",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    if config.getoption("--run-slow-render"):
        return
    skip_slow = pytest.mark.skip(
        reason=(
            "slow_render: full-resolution sprite render. Opt in with "
            "--run-slow-render. See GOALS.md for the low-res-mode plan."
        ),
    )
    for item in items:
        if "slow_render" in item.keywords:
            item.add_marker(skip_slow)
