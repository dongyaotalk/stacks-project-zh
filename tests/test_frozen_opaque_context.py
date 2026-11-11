"""Read-only complete English context compatibility; no model/data fixtures."""
import copy
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture
from test_math_text import BASE_POLICY
from stacks_zh.source_containers import Containers, clean
from stacks_zh.source_adoptions import _context_sources_full
from stacks_zh.records import RecordError


class FrozenOpaqueContextTests(unittest.TestCase):
    def context_fixture(self, temp):
        root, harvest, _ = fixture(Path(temp), statement=(
            '\\begin{lemma}\n\\label{lemma-one}\n'
            'Take $x\\quad\\text{and}\\quad y$.\n\\end{lemma}'))
        policy = BASE_POLICY + '''
translatable_math_text:
  owner-and:
    literal: "and"
    command: "text"
    usage: "quad-connector"
    source_label: "test-lemma-one"
    witness_kind: "lemma"
    witness_ordinal: 1
'''
        (root / 'config/macro-policy.yml').write_text(policy)
        native = Containers(root, harvest)
        opaque = Containers(root, harvest, natural_text_enabled=False)
        row = next(r for r in opaque.document('test')[1] if r['unit']['node_kind'] == 'lemma')
        current = next(r for r in native.document('test')[1] if r['unit']['node_kind'] == 'lemma')
        self.assertEqual(row['unit']['schema_version'], 1)
        self.assertGreater(current['unit']['schema_version'], 1)
        value = dict(kind='locked-English-reference', source_commit=native.english.commit,
            source_unit=clean(row['unit']), location=clean(row['location']),
            owner_tag=row['owner_tag'], parent_tag=row['parent_tag'],
            requested_label='test-lemma-one', requested_tag=row['owner_tag'])
        frozen = dict(source_commit=native.english.commit, contexts=[dict(value=value)])
        return native, frozen

    def test_exact_original_context_replays_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            native, frozen = self.context_fixture(temp)
            original = copy.deepcopy(frozen)
            observed, refs = _context_sources_full(frozen, native)
            self.assertEqual(refs, {'test-lemma-one'})
            self.assertEqual(len(observed), 1)
            self.assertEqual(frozen, original)
            self.assertFalse((native.root / 'translation-data').exists())

    def test_modified_frozen_fields_remain_rejected(self):
        for field in ('source_text', 'placeholders', 'source_math_hash', 'owner_tag',
                      'parent_tag', 'location', 'requested_label'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                native, frozen = self.context_fixture(temp)
                value = frozen['contexts'][0]['value']
                if field == 'source_text': value['source_unit'][field] += ' Extra.'
                elif field == 'placeholders':
                    value['source_unit'][field]['MATH_0001'] = '$z$'
                elif field == 'source_math_hash': value['source_unit'][field] = 'sha256:' + '0' * 64
                elif field == 'location': value[field]['byte_end'] -= 1
                elif field == 'requested_label': value[field] = 'test-missing'
                else: value[field] = '9999'
                with self.assertRaises(RecordError): _context_sources_full(frozen, native)

    def test_forged_typed_context_has_no_opaque_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            native, frozen = self.context_fixture(temp)
            frozen['contexts'][0]['value']['source_unit']['schema_version'] = 3
            with self.assertRaises(RecordError): _context_sources_full(frozen, native)
