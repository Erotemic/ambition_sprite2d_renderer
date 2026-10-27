"""Accepted bundles report missing members and changes to their actual inputs."""
import json
from pathlib import Path

from ambition_sprite2d_renderer import products as p, provenance


def bundle(tmp_path, name, inputs):
    root = tmp_path / name
    root.mkdir()
    output = root / 'sheet.png'
    output.write_bytes(b'pixels')
    evidence = p.generation([{'path': str(path), 'sha256': provenance.digest(path)} for path in inputs], [], {}, complete=True)
    plan = {'root': name, 'required': ['sheet.png'], 'tiers': [], 'repair': 'publish ' + name}
    record = {'generation': evidence, 'outputs': [{'path': 'sheet.png', 'sha256': provenance.digest(output)}]}
    return root, plan, record


def test_shared_inputs_and_one_spec_affect_only_their_consumers(tmp_path):
    common = tmp_path / 'draw.py'; common.write_text('draw')
    spec = tmp_path / 'one.yaml'; spec.write_text('one')
    one = bundle(tmp_path, 'one', [common, spec])
    two = bundle(tmp_path, 'two', [common])
    decide = lambda b: p.evaluate(b[1], b[2], b[0], tmp_path, p.Digests(), tiers=False)['state']
    assert decide(one) == decide(two) == 'current'
    spec.write_text('changed')
    assert decide(one) == 'stale' and decide(two) == 'current'
    common.write_text('changed')
    assert decide(two) == 'stale'
    (one[0] / 'sheet.png').unlink()
    assert decide(one) == 'missing'


def test_incomplete_receipts_stay_unknown_but_known_changes_are_reported(tmp_path):
    source = tmp_path / 'source'; source.write_text('source')
    root, plan, record = bundle(tmp_path, 'one', [source])
    record['generation']['complete'] = False
    assert p.evaluate(plan, record, root, tmp_path, p.Digests())['state'] == 'unknown'
    source.write_text('new')
    assert p.evaluate(plan, record, root, tmp_path, p.Digests())['state'] == 'stale'


def test_conversion_acceptance_and_failure_keep_the_last_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv(provenance.ENV, str(tmp_path / 'records'))
    source = tmp_path / 'source.png'; source.write_bytes(b'source')
    root = tmp_path / 'tier'; root.mkdir()
    output = root / 'sheet.png'; output.write_bytes(b'tier')
    evidence = p.conversion_evidence([source], {'scale': 0.5})
    p.accept_conversion(root, 'sheet', evidence, [output])
    path = tmp_path / 'records/sheet.quality.json'
    accepted = path.read_bytes()
    assert p.conversion_current(root, 'sheet', evidence)
    try:
        p.accept_conversion(root, 'sheet', evidence, [root / 'missing.png'])
    except ValueError:
        pass
    else:
        assert False, 'A missing output cannot be accepted'
    assert path.read_bytes() == accepted
    source.write_bytes(b'new source')
    assert p.conversion_status(root, 'sheet', p.Digests())['state'] == 'stale'


def test_full_generation_state_does_not_become_its_last_tier_state(tmp_path):
    source = tmp_path / 'source'; source.write_text('source')
    root, plan, record = bundle(tmp_path, 'sprites', [source])
    plan['tiers'] = ['half', 'quarter', 'potato']
    status = p.evaluate(plan, record, root, tmp_path, p.Digests())
    assert status['state'] == 'current'
    assert all(tier['state'] == 'missing' for tier in status['tiers'].values())


def test_a_new_accepted_parent_bundle_invalidates_its_conversion(tmp_path, monkeypatch):
    root = tmp_path / 'tier'; root.mkdir()
    records = tmp_path / 'records'
    (records / 'sprites').mkdir(parents=True)
    parent = records / 'sprites/body.json'
    parent_record = {'schema': provenance.SCHEMA, 'generation': {'key': 'first'}, 'outputs': []}
    parent.write_text(json.dumps(parent_record))
    monkeypatch.setenv('AMBITION_ART_PROVENANCE_ROOT', str(records))
    monkeypatch.setenv(provenance.ENV, str(records / 'tier'))
    output = root / 'sheet.png'; output.write_bytes(b'pixels')
    evidence = p.conversion_evidence([], {'parents':[{'path':'sprites/body.json','key':'first','outputs':p.output_key(parent_record)}]})
    p.accept_conversion(root, 'sheet', evidence, [output])
    assert p.conversion_current(root, 'sheet', evidence)
    parent_record['generation']['key'] = 'second'
    parent.write_text(json.dumps(parent_record))
    status = p.conversion_status(root, 'sheet', p.Digests())
    assert status['state'] == 'stale'
    assert status['reasons'][0]['code'] == 'stale-parent-bundle'
