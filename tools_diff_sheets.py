#!/usr/bin/env python3
"""Differential harness for the sheet-pipeline unification.

Renders every discoverable target's sheet to a temp dir and captures a stable
fingerprint — the parsed manifest plus a hash of each page image — so a refactor
of the build pipeline can be proven output-stable (or its intended changes
re-baselined) target by target.

Usage:
    python tools_diff_sheets.py capture  baseline.json
    python tools_diff_sheets.py capture  after.json
    python tools_diff_sheets.py diff     baseline.json after.json
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import traceback
from pathlib import Path

from ambition_sprite2d_renderer.registry.discovery import discover_all_targets


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def capture(out_path: Path) -> None:
    report = discover_all_targets()
    targets = report.targets
    result: dict = {}
    for name in sorted(targets):
        target = targets[name]
        entry: dict = {}
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            try:
                paths = list(target.render_sheet(out_dir))
            except Exception as ex:  # noqa: BLE001
                entry["error"] = f"{type(ex).__name__}: {ex}"
                entry["trace"] = traceback.format_exc().splitlines()[-3:]
                result[name] = entry
                print(f"  {name}: ERROR {entry['error']}")
                continue
            # Fingerprint every emitted file: RON/YAML text verbatim, images by hash.
            files: dict = {}
            for p in sorted(out_dir.rglob("*")):
                if not p.is_file():
                    continue
                rel = str(p.relative_to(out_dir))
                if p.suffix in (".png",):
                    files[rel] = f"png:{_hash(p)}:{p.stat().st_size}"
                elif p.suffix in (".ron", ".yaml"):
                    files[rel] = p.read_text()
                else:
                    files[rel] = f"file:{_hash(p)}"
            entry["files"] = files
        result[name] = entry
        print(f"  {name}: {len(entry.get('files', {}))} files")
    out_path.write_text(json.dumps(result, indent=1, sort_keys=True))
    print(f"captured {len(result)} targets -> {out_path}")


def diff(a_path: Path, b_path: Path) -> int:
    a = json.loads(a_path.read_text())
    b = json.loads(b_path.read_text())
    names = sorted(set(a) | set(b))
    changed = 0
    for name in names:
        ea, eb = a.get(name), b.get(name)
        if ea is None:
            print(f"+ {name}: NEW"); changed += 1; continue
        if eb is None:
            print(f"- {name}: REMOVED"); changed += 1; continue
        if ea.get("error") != eb.get("error"):
            print(f"~ {name}: error {ea.get('error')!r} -> {eb.get('error')!r}"); changed += 1; continue
        fa, fb = ea.get("files", {}), eb.get("files", {})
        keys = sorted(set(fa) | set(fb))
        deltas = []
        for k in keys:
            if k not in fa:
                deltas.append(f"    + {k}")
            elif k not in fb:
                deltas.append(f"    - {k}")
            elif fa[k] != fb[k]:
                deltas.append(f"    ~ {k}")
        if deltas:
            changed += 1
            print(f"~ {name}:")
            print("\n".join(deltas))
    if changed == 0:
        print("IDENTICAL — every target's sheet fingerprint is unchanged.")
    else:
        print(f"\n{changed} target(s) changed.")
    return changed


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "capture":
        capture(Path(sys.argv[2]))
    elif cmd == "diff":
        sys.exit(1 if diff(Path(sys.argv[2]), Path(sys.argv[3])) else 0)
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
