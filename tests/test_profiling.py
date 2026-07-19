from __future__ import annotations

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


def test_explicit_profile_output_is_quiet_and_lprof_only_by_default(tmp_path):
    import os
    import subprocess
    import sys

    output_prefix = tmp_path / "profile"
    code = """
from ambition_sprite2d_renderer.profiling import profile

@profile
def sample():
    total = 0
    for value in range(10):
        total += value
    return total

assert sample() == 45
"""
    env = os.environ.copy()
    env.update(
        {
            "LINE_PROFILE": "1",
            "AMBITION_LINE_PROFILE_OUTPUT": str(output_prefix),
        }
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Timer unit:" not in proc.stdout
    assert output_prefix.with_suffix(".lprof").exists()
    assert not output_prefix.with_suffix(".txt").exists()
    assert not list(tmp_path.glob("profile_*.txt"))

def test_explicit_profile_text_sidecar_is_opt_in(tmp_path):
    import os
    import subprocess
    import sys

    output_prefix = tmp_path / "profile"
    code = """
from ambition_sprite2d_renderer.profiling import profile

@profile
def sample():
    return sum(range(10))

assert sample() == 45
"""
    env = os.environ.copy()
    env.update(
        {
            "LINE_PROFILE": "1",
            "AMBITION_LINE_PROFILE_OUTPUT": str(output_prefix),
            "AMBITION_LINE_PROFILE_TEXT": "1",
        }
    )
    subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_prefix.with_suffix(".lprof").exists()
    assert output_prefix.with_suffix(".txt").exists()
    assert not list(tmp_path.glob("profile_*.txt"))
