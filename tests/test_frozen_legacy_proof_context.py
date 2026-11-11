"""Synthetic read-only context replay, with a synthetic accepted code witness."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_source_containers import fixture, git
from test_math_text import BASE_POLICY
from stacks_zh.source_containers import Containers, clean
from stacks_zh.source_adoptions import (_context_sources, _context_sources_full,
    _legacy_proof_inventory_origin, _legacy_prose_boundary_equal, _DAILY)
from stacks_zh.records import RecordError

FUNCTION = 'def chapter_inventory(chapter):\n    return []\n'
FUNCTION_HASH = hashlib.sha256(FUNCTION.rstrip('\n').encode()).hexdigest()


class FrozenLegacyProofContextTests(unittest.TestCase):
    def context_fixture(self, temp, *, typed=False, ordinal=1):
        statement = ('\\begin{lemma}\\label{lemma-one}A claim.\\end{lemma}\n\n'
                     'A complete explanatory paragraph.\n\n')
        proof = ('\\begin{proof}Take $x\\quad\\text{and}\\quad y$.\\end{proof}'
                 if typed else '\\begin{proof}Take $x$.\\end{proof}')
        other = 'A following paragraph.\n\n\\begin{lemma}\\label{lemma-two}Another claim.\\end{lemma}'
        root, harvest, _ = fixture(Path(temp), statement=statement, proof=proof, other=other)
        (root / 'config/macro-policy.yml').write_text(BASE_POLICY + ('''
translatable_math_text:
  proof-and:
    literal: "and"
    command: "text"
    usage: "quad-connector"
    source_label: "test-section-basic"
    witness_kind: "section"
    witness_ordinal: 1
''' if typed else ''))
        (root / 'stacks_zh').mkdir()
        (root / 'stacks_zh/extraction.py').write_text(FUNCTION)
        git(root, 'init', '-q')
        git(root, 'add', '.')
        git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
            'commit', '-qm', 'synthetic original code')
        origin = git(root, 'rev-parse', 'HEAD')
        git(root, 'update-ref', 'refs/remotes/origin/main', origin)
        native = Containers(root, harvest)
        flat = Containers(root, harvest, hierarchical_prose=False, natural_text_enabled=False)
        row = [r for r in flat.document('test')[1] if r['unit']['node_kind'] == 'proof'][ordinal-1]
        current = next(r for r in native.document('test')[1] if r['location'] == row['location'])
        self.assertIsNone(row['owner_tag'])
        self.assertEqual(current['owner_tag'], '0001')
        value = dict(kind='locked-English-neighbor', source_commit=native.english.commit,
                     source_unit=clean(row['unit']), location=clean(row['location']),
                     owner_tag=None, parent_tag=row['parent_tag'])
        frozen = dict(tool_version='source-adoption-input-v1', origin_commit=origin,
                      source_commit=native.english.commit, contexts=[dict(value=value)])
        return native, frozen, current

    def test_exact_original_schema1_proof_and_current_owner_replay(self):
        for typed, ordinal in ((False,1),(True,1),(False,2)):
            with self.subTest(typed=typed,ordinal=ordinal), tempfile.TemporaryDirectory() as temp:
                native, frozen, current = self.context_fixture(temp,typed=typed,ordinal=ordinal)
                original = copy.deepcopy(frozen)
                with patch('stacks_zh.source_adoptions._LEGACY_PROOF_RESET_FUNCTION_HASH',FUNCTION_HASH):
                    nodes, refs = _context_sources_full(frozen,native)
                self.assertEqual(nodes,{('test',current['unit']['unit_id'])})
                self.assertEqual(refs,set())
                self.assertEqual(frozen,original)
                self.assertFalse((native.root/'translation-data').exists())

    def test_unrecognized_or_unaccepted_original_code_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            native, frozen, _ = self.context_fixture(temp)
            self.assertFalse(_legacy_proof_inventory_origin(native.root,frozen['origin_commit']))
            with self.assertRaises(RecordError):_context_sources_full(frozen,native)
            with patch('stacks_zh.source_adoptions._LEGACY_PROOF_RESET_FUNCTION_HASH',FUNCTION_HASH):
                self.assertTrue(_legacy_proof_inventory_origin(native.root,frozen['origin_commit']))
                git(native.root,'update-ref','-d','refs/remotes/origin/main')
                # The fixture's local branch is not named main either.
                git(native.root,'branch','-M','synthetic-unaccepted')
                self.assertFalse(_legacy_proof_inventory_origin(native.root,frozen['origin_commit']))

    def test_modified_complete_proof_context_fields_are_rejected(self):
        for field in ('source_text','unit_id','source_math_hash','owner_tag','parent_tag','location','schema_version','kind'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                native,frozen,_=self.context_fixture(temp)
                value=frozen['contexts'][0]['value']
                if field=='source_text':value['source_unit'][field]+=' Extra.'
                elif field=='unit_id':value['source_unit'][field]='inventory:test:untagged:proof/9999'
                elif field=='source_math_hash':value['source_unit'][field]='sha256:'+'0'*64
                elif field=='location':value[field]['byte_end']-=1
                elif field=='schema_version':value['source_unit'][field]=3
                elif field=='kind':value[field]='locked-English-reference'
                else:value[field]='9999'
                with patch('stacks_zh.source_adoptions._LEGACY_PROOF_RESET_FUNCTION_HASH',FUNCTION_HASH):
                    with self.assertRaises(RecordError):_context_sources_full(frozen,native)

    def test_direct_boundary_cache_binds_original_code_and_tool_version(self):
        with tempfile.TemporaryDirectory() as temp:
            native,frozen,_=self.context_fixture(temp)
            token=_DAILY.set(SimpleNamespace(cache={}))
            try:
                with patch('stacks_zh.source_adoptions._LEGACY_PROOF_RESET_FUNCTION_HASH',FUNCTION_HASH):
                    _context_sources(frozen,native)
                    changed=copy.deepcopy(frozen);changed['origin_commit']='0'*40
                    with self.assertRaises(RecordError):_context_sources(changed,native)
                    changed=copy.deepcopy(frozen);changed['tool_version']='source-adoption-input-v2'
                    with self.assertRaises(RecordError):_context_sources(changed,native)
            finally:_DAILY.reset(token)

    def test_complete_prose_boundary_requires_its_exact_original_proof_neighbor(self):
        for side, ordinal, block in (('before',2,2),('after',1,1)):
            with self.subTest(side=side), tempfile.TemporaryDirectory() as temp:
                native,frozen,current=self.context_fixture(temp,ordinal=ordinal)
                selected=native.select(dict(file='test.tex',kind='prose_block',ordinal=block,
                    owner_tag='0000',parent_tag='0000',owner_label='test-section-basic'))
                original=copy.deepcopy(selected)
                old_id=frozen['contexts'][0]['value']['source_unit']['unit_id']
                original['boundary_witness'][side]=dict(kind='proof',owner_tag=None,
                    ordinal=int(old_id.rsplit('/',1)[1]))
                with patch('stacks_zh.source_adoptions._LEGACY_PROOF_RESET_FUNCTION_HASH',FUNCTION_HASH):
                    self.assertTrue(_legacy_prose_boundary_equal(frozen,native,original,selected))
                    bad=copy.deepcopy(original);bad['fragment']+=' Extra.'
                    self.assertFalse(_legacy_prose_boundary_equal(frozen,native,bad,selected))
                    bad=copy.deepcopy(original);bad['boundary_witness'][side]['ordinal']=9999
                    self.assertFalse(_legacy_prose_boundary_equal(frozen,native,bad,selected))
                    missing=copy.deepcopy(frozen);missing['contexts']=[]
                    self.assertFalse(_legacy_prose_boundary_equal(missing,native,original,selected))
