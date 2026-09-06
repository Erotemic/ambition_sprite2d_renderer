from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "profile_benchmarks.py"


def test_profile_benchmark_suites_are_discoverable():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--list-suites"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "quick: oiler, ninja_heavy" in proc.stdout
    assert "representative:" in proc.stdout
    assert "stochastic_parrot_v2" in proc.stdout


def test_profile_benchmark_dry_run_uses_isolated_sheet_processes(tmp_path):
    output_dir = tmp_path / "capture"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "oiler",
            "--target",
            "ninja_heavy",
            "--repeat",
            "2",
            "--python",
            sys.executable,
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout.count("ambition_sprite2d_renderer sheet oiler") == 2
    assert proc.stdout.count("ambition_sprite2d_renderer sheet ninja_heavy") == 2
    assert str(output_dir) in proc.stdout
    assert not output_dir.exists()

def _load_profile_benchmark_module():
    spec = importlib.util.spec_from_file_location(
        "profile_benchmarks_under_test", SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selected_virtualenv_python_symlink_is_not_resolved(tmp_path):
    module = _load_profile_benchmark_module()
    root = tmp_path / "renderer"
    interpreter = root / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(Path(sys.executable))

    selected = module.absolute_path_preserving_symlinks(
        module.default_python(root)
    )

    assert selected == interpreter
    assert os.path.islink(selected)
    assert selected != interpreter.resolve()


def test_explicit_relative_python_becomes_absolute_without_resolving(tmp_path):
    module = _load_profile_benchmark_module()
    interpreter = tmp_path / "venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(Path(sys.executable))

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        selected = module.absolute_path_preserving_symlinks(
            Path("venv/bin/python")
        )
    finally:
        os.chdir(old_cwd)

    assert selected == interpreter
    assert os.path.islink(selected)

