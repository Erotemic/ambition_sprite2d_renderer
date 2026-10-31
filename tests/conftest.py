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

import os
import re
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
#
# ⛔ AND IT MOVED AGAIN (superproject 58ba17f4a): `sprites.sh` now runs the
# publication tool and lists no targets. The roster is the collections in
# `authored/sprites.yaml`, and a publish drops a target that is not listed.
_ROSTER_RELATIVE = Path("game/ambition_content_library/authored/sprites.yaml")


@pytest.fixture(scope="session")
def regen_roster() -> frozenset[str]:
    """The targets the superproject's sprite roster lists, or skip if standalone."""
    superproject = Path(__file__).resolve().parents[3]
    roster = superproject / _ROSTER_RELATIVE
    if not roster.is_file():
        pytest.skip(
            f"no superproject roster at {roster} — this renderer is checked out "
            "standalone, so there is no regen roster to check against"
        )
    listed = re.findall(r"^\s*-\s*([A-Za-z0-9_]+)\s*$", roster.read_text(encoding="utf8"), re.MULTILINE)
    return frozenset(listed)


#: Workers for a run of a directory of tests. Six, not one per CPU: the box is
#: shared. ``-n 0`` (or any ``-n``) on the command line overrides it.
DEFAULT_WORKERS = 6


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config: pytest.Config) -> None:
    """Run the suite on ``DEFAULT_WORKERS`` xdist workers when it is run whole.

    Only when pytest-xdist is installed, no ``-n``/``--dist`` was given, and a
    path asked for is a directory (``pytest`` alone runs ``testpaths``): a run
    of one file or one test stays in this process, where starting six workers
    would cost more than it saves. It sets ``tx`` as xdist's own hook would, so
    it holds whichever of the two runs first.
    """
    if not config.pluginmanager.hasplugin("xdist") or os.environ.get("PYTEST_XDIST_WORKER"):
        return
    if config.option.numprocesses is not None or config.option.dist != "no" or config.option.tx:
        return
    if not any(Path(arg.split("::")[0]).is_dir() for arg in config.args):
        return
    config.option.numprocesses = DEFAULT_WORKERS
    config.option.dist = "worksteal"
    config.option.tx = ["popen"] * DEFAULT_WORKERS


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
