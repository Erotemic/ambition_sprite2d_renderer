"""Maintained looks use current source data without history access."""
from pathlib import Path
import subprocess

from PIL import Image
import pytest

from ambition_sprite2d_renderer import lineage_variants as variants


def test_a_normalized_variant_renders_without_git_or_the_archive(tmp_path, monkeypatch):
    original = subprocess.run
    def no_git(command, *args, **kwargs):
        if Path(str(command[0])).name == 'git':
            raise AssertionError('Maintained looks must not run Git')
        return original(command, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'run', no_git)
    monkeypatch.setenv('AMBITION_HISTORY_STORE', str(tmp_path / 'no-archive'))
    monkeypatch.setenv('AMBITION_DESIGN_HISTORY_CACHE', str(tmp_path / 'no-history-cache'))
    row = variants.recipes()['alice.toon_placeholder']
    result = variants.render('alice.toon_placeholder', row, tmp_path / 'out')
    assert result['state'] == 'ready', result
    with Image.open(result['image']) as image:
        assert image.mode == 'RGBA' and image.getbbox()
    assert not (tmp_path / 'no-archive').exists() and not (tmp_path / 'no-history-cache').exists()


def test_missing_current_sources_fail_without_falling_back_to_history(tmp_path):
    result = variants.render('missing', {'lineage': 'missing', 'source': {'kind': 'target', 'name': 'unregistered_fixture'}}, tmp_path)
    assert result['state'] == 'failed' and 'not registered' in result['failure']


def test_selection_names_a_lineage_or_a_specific_variant():
    book = {'one.old': {'lineage': 'one'}, 'one.new': {'lineage': 'one'}, 'two.old': {'lineage': 'two'}}
    assert set(variants.select(book, ['one'])) == {'one.old', 'one.new'}
    assert set(variants.select(book, ['one.old'])) == {'one.old'}
    with pytest.raises(ValueError):
        variants.select(book, ['unknown'])
