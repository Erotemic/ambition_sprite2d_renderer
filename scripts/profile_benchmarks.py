#!/usr/bin/env python3
"""Profile representative sprite targets and materialize readable reports.

This runner is intentionally local to the sprite renderer repository. It runs
one target per Python process so every target receives an isolated line-profiler
database, converts that database to a stable text report, and writes a summary
that is convenient for before/after comparisons.

Examples:
    ./scripts/profile_benchmarks.py
    ./scripts/profile_benchmarks.py --suite representative
    ./scripts/profile_benchmarks.py --target oiler --target ninja_heavy
    ./scripts/profile_benchmarks.py --repeat 3 --target oiler
"""

from __future__ import annotations

import argparse
import datetime as datetime_mod
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Iterable, Sequence


BENCHMARK_SUITES: dict[str, tuple[str, ...]] = {
    # Small enough for the normal edit/profile loop while covering an SVG rig
    # and a substantial bespoke procedural character.
    "quick": (
        "oiler",
        "ninja_heavy",
    ),
    # Cross-section of the main character authoring families. Keep this list
    # deliberately small: the goal is actionable profiles, not another full
    # roster regeneration.
    "representative": (
        "oiler",
        "m_leblanc",
        "ninja_heavy",
        "stochastic_parrot_v2",
        "perfect_cellular_automaton",
    ),
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_python(root: Path) -> Path:
    local_python = root / ".venv" / "bin" / "python"
    if local_python.is_file():
        return local_python
    return Path(sys.executable)


def absolute_path_preserving_symlinks(path: Path) -> Path:
    """Return an absolute path without resolving a virtualenv interpreter.

    Virtualenv ``bin/python`` entries are commonly symlinks to the base Python.
    Resolving that symlink changes interpreter startup semantics: Python no
    longer discovers the virtualenv's ``pyvenv.cfg`` and therefore loses the
    environment's site-packages. Keep the executable path exactly inside the
    selected environment while still making relative ``--python`` values
    independent of the subprocess working directory.
    """
    return Path(os.path.abspath(os.path.expanduser(os.fspath(path))))


def local_timestamp() -> str:
    """Filesystem-safe timestamp in the machine's configured local timezone."""
    return datetime_mod.datetime.now().astimezone().strftime("%Y-%m-%dT%H%M%S%z")


def iso_now() -> str:
    return datetime_mod.datetime.now().astimezone().isoformat(timespec="seconds")


def shell_join(command: Sequence[str | os.PathLike[str]]) -> str:
    return shlex.join([os.fspath(item) for item in command])


def unique_ordered(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run isolated line-profiler captures for representative sprite "
            "targets and write both .lprof and .txt reports."
        )
    )
    parser.add_argument(
        "--suite",
        choices=sorted(BENCHMARK_SUITES),
        default="quick",
        help="Curated benchmark suite used when --target is not supplied.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        metavar="NAME",
        help="Profile this target. Repeat to override the selected suite.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of isolated captures per target (default: 1).",
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=None,
        help="Python interpreter with this package and line_profiler installed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Capture directory. Default: "
            ".profiles/benchmarks/<local-timestamp>."
        ),
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue profiling later targets after a failed target.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write command output to .log files without echoing it live.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved benchmark commands without running them.",
    )
    parser.add_argument(
        "--list-suites",
        action="store_true",
        help="Print curated suites and exit.",
    )
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    return args


def check_profiler(python: Path, root: Path) -> None:
    command = [os.fspath(python), "-c", "import line_profiler"]
    proc = subprocess.run(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise SystemExit(
            "line_profiler is not available to the selected interpreter.\n"
            f"Python: {python}\n"
            "Install it with:\n"
            f"  uv pip install --python {shlex.quote(os.fspath(python))} line_profiler"
            + (f"\nDetails: {detail}" if detail else "")
        )


def stream_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
    quiet: bool,
) -> int:
    with log_path.open("w", encoding="utf8") as log_file:
        log_file.write(f"$ {shell_join(command)}\n")
        log_file.flush()
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        try:
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
                if not quiet:
                    print(line, end="", flush=True)
        except KeyboardInterrupt:
            process.send_signal(2)
            process.wait()
            raise
        return process.wait()


def render_text_report(python: Path, root: Path, lprof: Path, text: Path) -> int:
    command = [
        os.fspath(python),
        "-m",
        "line_profiler",
        "--sort",
        "yes",
        "--summarize",
        "yes",
        "--skip-zero",
        "yes",
        os.fspath(lprof),
    ]
    with text.open("w", encoding="utf8") as file:
        proc = subprocess.run(
            command,
            cwd=root,
            stdout=file,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return proc.returncode


def run_capture(
    *,
    root: Path,
    python: Path,
    output_dir: Path,
    target: str,
    ordinal: int,
    repeat_index: int,
    repeat_count: int,
    quiet: bool,
) -> dict[str, object]:
    suffix = f"-r{repeat_index:02d}" if repeat_count > 1 else ""
    stem = f"{ordinal:02d}-{target}{suffix}"
    prefix = output_dir / stem
    lprof_path = prefix.with_suffix(".lprof")
    text_path = prefix.with_suffix(".txt")
    log_path = prefix.with_suffix(".log")

    command = [
        os.fspath(python),
        "-m",
        "ambition_sprite2d_renderer",
        "sheet",
        target,
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "LINE_PROFILE": "1",
            "AMBITION_LINE_PROFILE_OUTPUT": os.fspath(prefix),
            # The runner performs the conversion explicitly so every report has
            # a predictable filename and the command used is recorded here.
            "AMBITION_LINE_PROFILE_TEXT": "0",
            "PYTHONUNBUFFERED": "1",
        }
    )

    print(f"\n[{ordinal:02d}] profiling {target}", flush=True)
    print(f"     command: {shell_join(command)}", flush=True)
    print(f"     output:  {prefix}.[lprof|txt|log]", flush=True)
    started_at = iso_now()
    started = time.perf_counter()
    return_code = stream_command(
        command,
        cwd=root,
        env=environment,
        log_path=log_path,
        quiet=quiet,
    )
    elapsed = time.perf_counter() - started

    conversion_code: int | None = None
    if lprof_path.is_file():
        conversion_code = render_text_report(python, root, lprof_path, text_path)
    status = "ok"
    if return_code != 0:
        status = "render-failed"
    elif not lprof_path.is_file():
        status = "missing-lprof"
    elif conversion_code != 0:
        status = "conversion-failed"
    elif not text_path.is_file() or text_path.stat().st_size == 0:
        status = "missing-text"

    print(
        f"     {status}: {elapsed:.2f}s; "
        f"text={text_path if text_path.exists() else 'missing'}",
        flush=True,
    )
    return {
        "target": target,
        "repeat": repeat_index,
        "status": status,
        "started_at": started_at,
        "elapsed_seconds": round(elapsed, 6),
        "return_code": return_code,
        "conversion_return_code": conversion_code,
        "command": command,
        "lprof": os.fspath(lprof_path),
        "text": os.fspath(text_path),
        "log": os.fspath(log_path),
    }


def write_summary(
    *,
    output_dir: Path,
    root: Path,
    python: Path,
    suite: str,
    targets: Sequence[str],
    started_at: str,
    results: Sequence[dict[str, object]],
) -> None:
    finished_at = iso_now()
    payload = {
        "schema_version": 1,
        "repository": os.fspath(root),
        "python": os.fspath(python),
        "suite": suite,
        "targets": list(targets),
        "started_at": started_at,
        "finished_at": finished_at,
        "results": list(results),
    }
    (output_dir / "profile-summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf8"
    )

    rows = [
        "Sprite line-profile benchmark",
        "=============================",
        f"Repository: {root}",
        f"Python:     {python}",
        f"Suite:      {suite}",
        f"Started:    {started_at}",
        f"Finished:   {finished_at}",
        "",
        "Status               Seconds  Target",
        "-------------------  -------  ------------------------------",
    ]
    for result in results:
        rows.append(
            f"{str(result['status']):19}  "
            f"{float(result['elapsed_seconds']):7.2f}  "
            f"{result['target']} r{int(result['repeat']):02d}"
        )
    rows.extend(
        [
            "",
            "Each target has matching .lprof, .txt, and .log files.",
            "The .txt report is sorted by total time, summarizes functions,",
            "and omits instrumented functions that received no calls.",
            "",
        ]
    )
    (output_dir / "profile-index.txt").write_text("\n".join(rows), encoding="utf8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_suites:
        for name, targets in BENCHMARK_SUITES.items():
            print(f"{name}: {', '.join(targets)}")
        return 0

    root = repository_root()
    python = absolute_path_preserving_symlinks(args.python or default_python(root))
    targets = unique_ordered(args.target or BENCHMARK_SUITES[args.suite])
    output_dir = (
        args.output_dir.expanduser()
        if args.output_dir is not None
        else root / ".profiles" / "benchmarks" / local_timestamp()
    ).resolve()

    commands = [
        [
            os.fspath(python),
            "-m",
            "ambition_sprite2d_renderer",
            "sheet",
            target,
        ]
        for target in targets
        for _repeat in range(args.repeat)
    ]
    if args.dry_run:
        print(f"repository: {root}")
        print(f"python:     {python}")
        print(f"output:     {output_dir}")
        for command in commands:
            print(shell_join(command))
        return 0

    if not python.is_file():
        raise SystemExit(f"selected Python interpreter does not exist: {python}")
    check_profiler(python, root)
    output_dir.mkdir(parents=True, exist_ok=False)

    started_at = iso_now()
    results: list[dict[str, object]] = []
    ordinal = 0
    failed = False
    for target in targets:
        for repeat_index in range(1, args.repeat + 1):
            ordinal += 1
            result = run_capture(
                root=root,
                python=python,
                output_dir=output_dir,
                target=target,
                ordinal=ordinal,
                repeat_index=repeat_index,
                repeat_count=args.repeat,
                quiet=args.quiet,
            )
            results.append(result)
            if result["status"] != "ok":
                failed = True
                if not args.keep_going:
                    write_summary(
                        output_dir=output_dir,
                        root=root,
                        python=python,
                        suite=args.suite,
                        targets=targets,
                        started_at=started_at,
                        results=results,
                    )
                    print(f"\nStopped after failure. Reports: {output_dir}")
                    return 1

    write_summary(
        output_dir=output_dir,
        root=root,
        python=python,
        suite=args.suite,
        targets=targets,
        started_at=started_at,
        results=results,
    )
    print(f"\nProfile reports: {output_dir}")
    print(f"Index:           {output_dir / 'profile-index.txt'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
