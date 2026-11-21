"""Render maintained lineage looks with the current authoring framework."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import shutil
import tempfile

from .yaml_io import safe_load

ROOT = Path(__file__).resolve().parent
RECIPES = ROOT / 'data/lineage_variants.yaml'
OUT = ROOT.parent / 'generated/review/lineage_variants'


def recipes(path: Path = RECIPES) -> dict:
    return safe_load(path.read_text())['variants']


def select(book: dict, names: list[str]) -> dict:
    if not names:
        return book
    found = {key: row for key, row in book.items() if key in names or row['lineage'] in names}
    unknown = set(names) - set(found) - {row['lineage'] for row in found.values()}
    if unknown:
        raise ValueError('Unknown lineage or variant: ' + ', '.join(sorted(unknown)))
    return found


def source_target(source: dict, targets: dict, root: Path = ROOT):
    from .registry.discovery import Target

    if source['kind'] == 'target':
        try:
            return targets[source['name']]
        except KeyError:
            raise ValueError('Current target is not registered: ' + source['name']) from None
    if source['kind'] == 'config':
        path = root / source['path']
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Maintained config is not in the authoring package: ' + source['path'])
        return Target.from_config(config_path=path, category='characters')
    raise ValueError('Unknown maintained render source: ' + str(source['kind']))


def render(key: str, row: dict, out: Path) -> dict:
    from .registry.discovery import discover_all_targets
    from .authoring.canonical import draw_canonical_of
    from .authoring.sheet_build import canonical_render_only

    result = dict(row, id=key)
    try:
        target = source_target(row['source'], discover_all_targets().targets)
        destination = out / key
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='lineage-', dir=out) as scratch:
            with canonical_render_only():
                source = draw_canonical_of(target, Path(scratch))
            image = destination / source.name
            partial = image.with_suffix('.partial.png')
            shutil.copyfile(source, partial)
            partial.replace(image)
        result.update(state='ready', target=target.name, image=str(image.resolve()))
    except Exception as error:
        result.update(state='failed', failure=f'{type(error).__name__}: {error}')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog="The repository wrapper accepts --archive-reference as its first argument for archive research.")
    parser.add_argument('names', nargs='*', help='lineage names or variant ids; default: all maintained variants')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--plan', action='store_true', help='resolve current sources without rendering')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--jobs', type=int, choices=range(1, 7), default=2)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args(argv)
    try:
        book = recipes()
        chosen = select(book, [] if args.all else args.names)
    except ValueError as error:
        parser.error(str(error))
    rows = []
    if args.plan:
        from .registry.discovery import discover_all_targets
        targets = discover_all_targets().targets
        for key, row in chosen.items():
            result = dict(row, id=key)
            try:
                result.update(state='available', target=source_target(row['source'], targets).name)
            except (ValueError, OSError) as error:
                result.update(state='failed', failure=str(error))
            rows.append(result)
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(render, key, row, args.out) for key, row in chosen.items()]
            for future in as_completed(futures):
                result = future.result()
                rows.append(result)
                print(result['id'] + ': ' + result['state'], file=sys.stderr, flush=True)
    rows.sort(key=lambda row: row['id'])
    report = {'schema': 'ambition.maintained_lineage_variants.v1', 'variants': rows,
              'scope': 'Current authored render sources. Historical refs are optional provenance, not render inputs.'}
    if not args.plan:
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / 'manifest.json'
        partial = path.with_suffix('.json.partial')
        try:
            previous = json.loads(path.read_text()).get('variants', [])
        except (OSError, ValueError):
            previous = []
        complete = {row['id']: row for row in previous if row['id'] in book and row.get('source') == book[row['id']]['source']}
        complete.update({row['id']: row for row in rows})
        stored = dict(report, variants=sorted(complete.values(), key=lambda row: row['id']))
        partial.write_text(json.dumps(stored, indent=2) + '\n')
        partial.replace(path)
        print('Maintained variant report: ' + str(path), file=sys.stderr)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{len(rows)} maintained variants; {sum(row['state'] == 'failed' for row in rows)} failures")
    return int(any(row['state'] == 'failed' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
