"""Recorded looks can be prepared from history with an empty image cache."""
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

from design_history import cli, prepare, stills, store


@pytest.fixture
def recorded_source(tmp_path):
    root = tmp_path / 'history'
    root.mkdir()
    store.git(root, 'init', '-q')
    store.git(root, 'config', 'user.name', 'Fixture')
    store.git(root, 'config', 'user.email', 'fixture@example.com')
    package = root / 'ambition_sprite2d_renderer'
    package.mkdir()
    (package / '__init__.py').write_text('')
    code = '''from pathlib import Path
import sys
from PIL import Image
# person is the registered target in this historical fixture.
out = Path(sys.argv[sys.argv.index('--out-dir') + 1])
Image.new('RGBA', (8, 12), 'blue').save(out / 'person.png')
'''
    (package / '__main__.py').write_text(code)
    store.git(root, 'add', '.')
    store.git(root, 'commit', '-qm', 'First drawing')
    first = store.git(root, 'rev-parse', 'HEAD').strip()
    (package / '__main__.py').write_text(code.replace("'blue'", "'red'"))
    store.git(root, 'add', '.')
    store.git(root, 'commit', '-qm', 'New drawing')
    store.git(root, 'update-ref', store.SEGMENTS[-1].ref, 'HEAD')
    return root, first, tmp_path / 'cache'


def records(sha):
    lineages = {'person': {'ids': ['person'], 'eras': [{'commit': sha[:7], 'label': 'First'}]}}
    variations = {'person': {'tracks': {'person': {'ids': ['person'], 'variations': [
        {'commit': sha[:12], 'segment': 'R1', 'target': 'person'}]}}}}
    return lineages, variations


def test_preparation_resolves_aliases_renders_old_code_and_reuses_a_cold_cache(recorded_source):
    root, sha, cache = recorded_source
    lineages, variations = records(sha)
    rows = prepare.plan(lineages, variations, ['person'], root, cache)
    assert len(rows) == 1 and rows[0]['commit'] == sha
    assert rows[0]['origins'] == ['milestone', 'variation']
    assert rows[0]['state'] == 'missing' and not cache.exists()
    ready = prepare.prepare(rows, python=sys.executable, store=root, cache=cache, jobs=1)
    assert ready[0]['state'] == 'ready', ready
    with Image.open(ready[0]['path']) as image:
        assert image.getpixel((0, 0)) == (0, 0, 255, 255)
    assert not list((cache / 'worktrees').glob('*/.git'))
    again = prepare.plan(lineages, variations, ['person'], root, cache)
    assert again[0]['state'] == 'cached'
    # A cache hit does not need the selected interpreter to run.
    reused = prepare.prepare(again, python='/no/interpreter', store=root, cache=cache, jobs=1)
    assert reused[0]['state'] == 'ready'


def test_cached_failure_can_be_retried_and_pixel_drift_is_reported(recorded_source):
    root, sha, cache = recorded_source
    lineages, variations = records(sha)
    variations['person']['tracks']['person']['variations'][0]['pixels'] = 'old-pixels'
    marker = cache / 'stills' / (stills.still_key(sha, ['person']) + '.failed')
    marker.parent.mkdir(parents=True)
    marker.write_text('Old dependency failure')
    rows = prepare.plan(lineages, variations, ['person'], root, cache)
    skipped = prepare.prepare(rows, python=sys.executable, store=root, cache=cache, jobs=1)
    assert skipped[0]['state'] == 'failed' and marker.read_text() == 'Old dependency failure'
    retried = prepare.prepare(rows, python=sys.executable, store=root, cache=cache, jobs=1, retry=True)
    assert retried[0]['state'] == 'different' and retried[0]['path']
    assert not marker.exists()


def test_unavailable_sources_have_an_actionable_plan_without_fetching(tmp_path):
    lineages, variations = records('b' * 40)
    result = prepare.plan(lineages, variations, ['person'], tmp_path / 'absent', tmp_path / 'cache')
    assert result[0]['state'] == 'missing-source'
    assert 'Fetch history' in result[0]['source_error']
    assert not (tmp_path / 'absent').exists() and not (tmp_path / 'cache').exists()


def test_cli_writes_a_report_and_returns_failure_for_unresolved_looks(tmp_path, monkeypatch, capsys):
    lineages, variations = records('b' * 40)
    monkeypatch.setattr(cli, 'load_lineages', lambda: lineages)
    monkeypatch.setattr(cli.variations_mod, 'load', lambda: variations)
    monkeypatch.setenv('AMBITION_DESIGN_HISTORY_CACHE', str(tmp_path / 'cache'))
    result = cli.main(['--store', str(tmp_path / 'absent'), 'prepare', '--offline', '--json'])
    report = json.loads(capsys.readouterr().out)
    assert result == 1 and report['summary'] == {'missing-source': 2}
    assert json.loads((tmp_path / 'cache/prepared.json').read_text()) == report


def test_a_new_history_store_can_fetch_sources_and_prepare_a_recorded_look(recorded_source, monkeypatch):
    source, sha, cache = recorded_source
    for segment in store.SEGMENTS[:3]:
        store.git(source, 'update-ref', segment.ref, sha)
    monkeypatch.setattr(store, 'HISTORY_URL', str(source))
    destination = cache.parent / 'fresh-store'
    store.fetch(destination, active_ambition=source, active_renderer=source)
    lineages, variations = records(sha)
    rows = prepare.plan(lineages, variations, ['person'], destination, cache)
    result = prepare.prepare(rows, python=sys.executable, store=destination, cache=cache, jobs=1)
    assert result[0]['state'] == 'ready', result
    assert result[0]['commit'] == sha and Path(result[0]['path']).is_file()


def test_a_merge_revision_without_renderer_edits_still_resolves_its_source_layout(recorded_source):
    root, _, cache = recorded_source
    store.git(root, 'commit', '--allow-empty', '-qm', 'A revision without source edits')
    sha = store.git(root, 'rev-parse', 'HEAD').strip()
    store.git(root, 'update-ref', store.SEGMENTS[-1].ref, sha)
    lineages, variations = records(sha)
    rows = prepare.plan(lineages, {}, ['person'], root, cache)
    assert rows[0]['commit'] == sha and rows[0]['segment'] == 'R1'
    assert rows[0]['state'] == 'missing'


def test_a_historical_module_can_draw_its_canonical_without_a_registered_cli(tmp_path):
    root = tmp_path / 'renderer'
    package = root / 'ambition_sprite2d_renderer'
    targets = package / 'targets'
    targets.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (targets / '__init__.py').write_text('')
    (package / '__main__.py').write_text('raise SystemExit(2)')
    (targets / 'person.py').write_text("from PIL import Image\ndef canonical_preview():\n    return Image.new('RGBA', (8, 12), 'blue')\n")
    image, target, failure = stills.render_still(sys.executable, root, ['person'])
    assert image and target == 'person' and not failure
    with Image.open(image) as pixels:
        assert pixels.getpixel((0, 0)) == (0, 0, 255, 255)
    import shutil
    shutil.rmtree(stills.scratch_root(image))


def test_a_historical_family_requires_an_explicit_pick(tmp_path):
    root = tmp_path / 'renderer'
    package = root / 'ambition_sprite2d_renderer'
    targets = package / 'targets'
    targets.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (targets / '__init__.py').write_text('')
    (package / '__main__.py').write_text('raise SystemExit(2)')
    (targets / 'family.py').write_text("""from PIL import Image
def render(out, variant='all'):
    Image.new('RGBA', (8, 12), 'blue').save(out / 'blue.png')
    Image.new('RGBA', (8, 12), 'red').save(out / 'red.png')
""")
    missing, _, reason = stills.render_still(sys.executable, root, ['family'])
    assert missing is None and 'Multiple historical variants' in reason
    image, target, reason = stills.render_still(sys.executable, root, ['family'], pick='file:blue.png')
    assert image and target == 'family' and not reason
    with Image.open(image) as pixels:
        assert pixels.getpixel((0, 0)) == (0, 0, 255, 255)
    import shutil
    shutil.rmtree(stills.scratch_root(image))
