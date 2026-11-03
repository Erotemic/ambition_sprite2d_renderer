"""Publish selected scene and terrain products with the shared bundle store.

    python -m ambition_sprite2d_renderer.scenery_publication --theme art --skin art
    python -m ambition_sprite2d_renderer.scenery_publication --missing-only

`--missing-only` keeps every product that is already published, stale and
partial ones too, as the sprite publication's flag does. With no `--theme` or
`--skin` it selects every scene, skin and sky part, so it builds only what is
not published at all."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from . import publication
from .products import describe, Digests
from .publication_store import Store, identity


#: The kinds of product this module draws, and the command that draws each.
#: A sky part is drawn by `backgrounds parts`, which draws all the parts at
#: once; the unit keeps only its own files.
SCENERY_KINDS = ('theme', 'skin', 'sky')


def _command(prefix, name, output):
    if prefix == 'skin':
        return ['terrain', 'draw', '--out-dir', str(output), name]
    if prefix == 'sky':
        return ['backgrounds', 'parts', '--out-dir', str(output)]
    return ['backgrounds', 'draw', '--out-dir', str(output), name]


def every_unit(definitions):
    """Every scenery product that this module can draw."""
    return [uid for uid in definitions if uid.split(':', 1)[0] in SCENERY_KINDS]


def _draw(uid, plan, renderer, snapshot):
    """Draw one unit in its own work folder, and return the folder and the
    files to accept (published path -> (file, collection, tier)). The caller
    removes the folder."""
    prefix, name = uid.split(':', 1)
    work = Path(tempfile.mkdtemp(prefix='ambition-scenery-'))
    output = work / 'runtime/full' / plan['root']
    environment = dict(os.environ, PYTHONPATH=str(renderer), AMBITION_REPO_ROOT=str(snapshot),
                       AMBITION_CONTENT_LIBRARY=publication.library_path().relative_to(publication.repo_root()).as_posix(),
                       AMBITION_GENERATION_ROOT=str(work / 'runtime/full'),
                       AMBITION_ART_PROVENANCE_ROOT=str(work / 'provenance'))
    module, *arguments = _command(prefix, name, output)
    subprocess.run([sys.executable, '-m', 'ambition_sprite2d_renderer.' + module, *arguments],
                   cwd=renderer, env=environment, check=True)
    files = {}
    from PIL import Image
    for relative in plan['required']:
        path = output / relative
        with Image.open(path) as image:
            image.verify()
        files[plan['root'] + '/' + relative] = (path, 'runtime', 'full')
    if plan['tiers']:
        from .quality import VARIANTS, resize_png, resampling_for_variant
        for variant in VARIANTS:
            tier = {'0_5x': 'half', '0_25x': 'quarter', 'potato': 'potato'}[variant.suffix]
            for relative in plan['required']:
                logical = plan['root'] + '_' + variant.suffix + '/' + relative
                path = work / 'runtime' / tier / logical
                resize_png(output / relative, path, variant.nominal_scale,
                           min_px=variant.min_frame_px, resampling=resampling_for_variant(variant))
                files[logical] = (path, 'runtime', tier)
    for path in (work / 'provenance').rglob('*.json'):
        files['review/provenance/' + path.relative_to(work / 'provenance').as_posix()] = (path, 'review', 'full')
    return work, files


def build(units, *, missing_only=False, jobs=1):
    """Draw the pending units, `jobs` at a time (each draw is its own
    process), accept each into the store, and publish them all at once."""
    definitions, warnings = describe({})
    if not units:
        units = every_unit(definitions)
    unknown = set(units) - definitions.keys()
    if unknown:
        raise ValueError(f"Unknown scenery products: {sorted(unknown)}. {warnings}")
    store = Store(publication.store_root())
    selected = store.selected()
    pending = []
    hashes = Digests()
    sources, chain = publication.source_files(), publication.toolchain()
    for uid in dict.fromkeys(units):
        plan = definitions[uid]
        paths = [plan['root'] + '/' + name for name in plan['required']]
        present = [name in selected['files'] for name in paths]
        key = selected['bundles'].get(uid)
        if missing_only and (key or any(present)):
            continue
        if key and publication.recipe_state(store.bundle(key)['recipe'], sources, chain, hashes)[0] == 'current' and not store.integrity(key):
            continue
        pending.append(uid)
    if not pending:
        print('scenery: no missing products' if missing_only else 'scenery: selected products are current')
        return selected
    replacements = {}
    with publication.source_snapshot(sources) as (snapshot, original):
        renderer = snapshot / publication.RENDERER.relative_to(publication.repo_root())
        recipe = {'inputs': original, 'membership': identity(sorted(original)), 'toolchain': chain, 'scenery': True}
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            drawn = {uid: pool.submit(_draw, uid, definitions[uid], renderer, snapshot) for uid in pending}
            try:
                for uid, future in drawn.items():
                    work, files = future.result()
                    try:
                        replacements[uid] = store.accept(uid, files, dict(recipe, tiers=definitions[uid]['tiers']),
                                                         roots=['backgrounds', 'room_dressing'])
                    finally:
                        shutil.rmtree(work, ignore_errors=True)
            except BaseException:
                # A failed draw stops the run: drop the draws not yet started.
                for future in drawn.values():
                    future.cancel()
                raise
            finally:
                # Here the pool has not shut down yet, so wait for the draws
                # that are running, then remove the folders they made.
                for future in drawn.values():
                    if not future.cancelled() and future.exception() is None:
                        shutil.rmtree(future.result()[0], ignore_errors=True)
    return store.publish(replacements, selected, only_missing=missing_only)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', action='append', default=[])
    parser.add_argument('--skin', action='append', default=[])
    parser.add_argument('--missing-only', action='store_true',
                        help='keep every published product, stale and partial ones too; with no --theme or --skin, '
                             'select every scene, skin and sky part')
    parser.add_argument('--jobs', type=int, default=min(6, max(1, (os.cpu_count() or 2) // 2)),
                        help='draws at a time (each is its own process)')
    args = parser.parse_args(argv)
    units = ['theme:' + name for name in args.theme] + ['skin:' + name for name in args.skin]
    if not units and not args.missing_only:
        parser.error('select --theme or --skin, or --missing-only')
    try:
        build(units, missing_only=args.missing_only, jobs=args.jobs)
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'scenery publication: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
