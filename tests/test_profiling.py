from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ambition_sprite2d_renderer import profiling


def test_optional_profile_decorator_is_safe_when_disabled():
    def sample(value: int) -> int:
        return value + 1

    wrapped = profiling.profile(sample)
    assert wrapped(3) == 4


def test_env_truthy_matches_shell_toggle_convention():
    for value in [None, "", "0", "false", "FALSE", "no", "off"]:
        assert not profiling._env_truthy(value)
    for value in ["1", "true", "yes", "on", "anything"]:
        assert profiling._env_truthy(value)


def test_profile_checkpoint_is_always_inert():
    assert not profiling.profile_checkpoint("unit-test", force=True)


def test_renderer_does_not_override_line_profiler_output_policy():
    source = Path(profiling.__file__).read_text(encoding="utf8")
    assert "profile.enable(" not in source
    assert "profile.write_config" not in source
    assert "AMBITION_LINE_PROFILE_OUTPUT" not in source
    assert "AMBITION_LINE_PROFILE_TEXT" not in source
    assert "AMBITION_LINE_PROFILE_CHECKPOINT_SECONDS" not in source


def test_line_profile_uses_upstream_default_cwd_output(tmp_path):
    if importlib.util.find_spec("line_profiler") is None:
        pytest.skip("optional line_profiler dependency is not installed")

    code = """
from ambition_sprite2d_renderer.profiling import profile

@profile
def sample():
    total = 0
    for value in range(100):
        total += value
    return total

assert sample() == 4950
"""
    env = os.environ.copy()
    env["LINE_PROFILE"] = "1"
    env.pop("AMBITION_LINE_PROFILE_OUTPUT", None)
    env.pop("AMBITION_LINE_PROFILE_TEXT", None)
    env.pop("AMBITION_LINE_PROFILE_CHECKPOINT_SECONDS", None)
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    # Do not prescribe the upstream filename; merely require that its normal
    # managed-profiler text output lands in the process working directory.
    assert list(tmp_path.glob("*.txt"))
