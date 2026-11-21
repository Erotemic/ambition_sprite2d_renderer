"""Prepare the recorded historical looks without a new survey."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import subprocess
import uuid

from .characters import era_ids
from .stills import Worktrees, still_for, still_key
from .store import SEGMENTS, git, have_ref, touching


def plan(lineages: dict, variations: dict, names: list[str], store: Path, cache: Path, *, curated_only=False) -> list[dict]:
    """Resolve source revisions and inspect the cache. Do not render or fetch."""
    index = {}
    if store.exists():
        for segment in SEGMENTS:
            if have_ref(store, segment.ref):
                for commit, _ in touching(store, segment):
                    index[commit.sha] = segment.name
    resolved = {}
    def revision(commit, hint=None):
        commit = str(commit)
        if commit not in resolved:
            matches = [sha for sha in index if sha.startswith(commit)]
            sha = matches[0] if len(matches) == 1 else ''
            if not sha and store.exists():
                sha = git(store, 'rev-parse', '--verify', '-q', f'{commit}^{{commit}}', check=False).strip()
            segment = index.get(sha, hint)
            if sha and not segment:
                for candidate in reversed(SEGMENTS):
                    package = candidate.prefix + 'ambition_sprite2d_renderer/__init__.py'
                    if git(store, 'cat-file', '-t', f'{sha}:{package}', check=False).strip() == 'blob':
                        segment = candidate.name
                        break
            resolved[commit] = (sha, segment)
        return resolved[commit]
    tasks = {}
    def add(name, spec, item, ids, origin):
        sha, segment = revision(item['commit'], item.get('segment'))
        pick = item.get('pick', spec.get('pick'))
        key = still_key(sha or str(item['commit']), ids, pick)
        row = tasks.setdefault(key, {'key': key, 'commit': sha or str(item['commit']), 'segment': segment,
                                     'ids': ids, 'pick': pick, 'lineages': [], 'origins': [], 'expected_pixels': []})
        if name not in row['lineages']:
            row['lineages'].append(name)
        if origin not in row['origins']:
            row['origins'].append(origin)
        if item.get('pixels') and item['pixels'] not in row['expected_pixels']:
            row['expected_pixels'].append(item['pixels'])
        image, failure = cache / 'stills' / (key + '.png'), cache / 'stills' / (key + '.failed')
        row['state'] = 'cached' if image.is_file() else 'failed' if failure.is_file() else 'missing' if sha and segment else 'missing-source'
        row['path'] = str(image) if image.is_file() else None
        row['failure'] = failure.read_text() if row['state'] == 'failed' else ''
        if not sha or not segment:
            row['source_error'] = 'The history store cannot resolve this renderer revision. Fetch history first.'
    for name in names:
        spec = lineages[name]
        for era in spec.get('eras', []):
            add(name, spec, era, era_ids(name, spec, era), 'milestone')
        if not curated_only:
            for track in variations.get(name, {}).get('tracks', {}).values():
                for item in track.get('variations', []):
                    add(name, spec, item, list(track['ids']), 'variation')
    return list(tasks.values())


def _draw(rows: list[dict], python: str, store: str, cache: str, slot: str, retry: bool, timeout: int) -> list[dict]:
    os.environ['AMBITION_DESIGN_HISTORY_RENDER_TIMEOUT'] = str(timeout)
    cache = Path(cache)
    trees = Worktrees(Path(store), cache, slot=slot)
    segments = {seg.name: seg for seg in SEGMENTS}
    results = []
    try:
        for index, row in enumerate(rows, 1):
            row = dict(row)
            marker = cache / 'stills' / (row['key'] + '.failed')
            print(f"[{slot} {index}/{len(rows)}] {row['key']}: preparing", file=sys.stderr, flush=True)
            try:
                if retry:
                    marker.unlink(missing_ok=True)
                still = still_for(python=python, worktrees=trees, cache=cache, seg=segments[row['segment']],
                                  sha=row['commit'], target_ids=row['ids'], pick=row['pick'])
                row.update(path=str(still.path) if still.path else None, target=still.target_id,
                           pixels=still.pixel_hash, failure=still.failure,
                           state='ready' if still.path else 'failed')
                if still.path and row['expected_pixels'] and still.pixel_hash not in row['expected_pixels']:
                    row['state'] = 'different'
                    row['failure'] = 'The image differs from the recorded pixel hash. Review it before use.'
            except Exception as error:
                row.update(state='failed', failure=f'{type(error).__name__}: {error}')
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(row['failure'])
            results.append(row)
            print(f"[{slot} {index}/{len(rows)}] {row['key']}: {row['state']}", file=sys.stderr, flush=True)
    finally:
        trees.remove()
        import shutil
        shutil.rmtree(cache / 'outputs' / slot, ignore_errors=True)
    return results


def prepare(rows: list[dict], *, python: str, store: Path, cache: Path, jobs=2, retry=False, timeout=120) -> list[dict]:
    """Resume the recorded recipes. Leave cached failures unless retry is set."""
    selected = [row for row in rows if not row.get('source_error') and (row['state'] != 'failed' or retry)]
    selected_keys = {row['key'] for row in selected}
    remaining = [row for row in rows if row['key'] not in selected_keys]
    if not selected:
        return rows
    cache.mkdir(parents=True, exist_ok=True)
    jobs = max(1, min(jobs, 6, len(selected)))
    run = 'prepare-' + uuid.uuid4().hex[:12]
    # All picks of a commit share one worker and its retained full render.
    commits = sorted({row['commit'] for row in selected})
    workers = {commit: index % jobs for index, commit in enumerate(commits)}
    chunks = [[row for row in selected if workers[row['commit']] == worker] for worker in range(jobs)]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(_draw, chunk, python, str(store), str(cache), f'{run}-{i}', retry, timeout)
                   for i, chunk in enumerate(chunks) if chunk]
        for future in as_completed(futures):
            remaining.extend(future.result())
    return sorted(remaining, key=lambda row: row['key'])


def report(rows: list[dict], *, store: Path, cache: Path, python: str) -> dict:
    probe = """import importlib.metadata as m, json, sys
versions = {}
for package in ('Pillow', 'PyYAML', 'numpy', 'resvg-py', 'lxml', 'rectpack'):
    try: versions[package] = m.version(package)
    except m.PackageNotFoundError: versions[package] = None
print(json.dumps({'python': sys.version, 'packages': versions}))
"""
    try:
        done = subprocess.run([python, '-c', probe], capture_output=True, text=True, timeout=30, check=True)
        environment = json.loads(done.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        environment = {'error': str(error)}
    return {'schema': 'ambition.lineage_preparation.v1', 'store': str(store), 'cache': str(cache),
            'python': python, 'environment': environment,
            'summary': dict(Counter(row['state'] for row in rows)), 'looks': rows,
            'scope': 'Historical stills for review. These are not published runtime skins.'}


def write_report(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.partial')
    partial.write_text(json.dumps(value, indent=2) + '\n')
    partial.replace(path)
