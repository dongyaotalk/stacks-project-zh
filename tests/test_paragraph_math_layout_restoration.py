"""Independent synthetic histories; no fixture claims actual model generation."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_preceding_statement_paragraphs import after_fixture
from test_source_container_boundaries import PLAIN
from test_source_containers import selector
from test_group_derivations import commit, run_for, save, write
import test_split_preceding_statement_paragraphs as split_tests
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.records import RecordError, load_jsonl, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, load_source_containers, lower_container, verify_old_group, write_container_package
from stacks_zh.source_paragraph_layout import paragraph_layout_pair
from stacks_zh.source_reextractions import byte_hash, source_tex

NATIVE_MATH = '$F(\\phi \\circ \\psi)\n= F(\\psi) \\circ F(\\phi)$'
OLD_MATH = '$$ F(\\phi \\circ \\psi) = F(\\psi) \\circ F(\\phi) $$'
INTRO = '\\noindent\nAn introductory paragraph with ' + NATIVE_MATH + '.'


def layout_fixture(base, *, old_math=OLD_MATH, native_math=NATIVE_MATH, native=None):
    intro = '\\noindent\nAn introductory paragraph with ' + native_math + '.'
    root, harvest, units, plan, output = after_fixture(base, native=native or PLAIN + '\n\n' + intro)
    paragraph = copy.deepcopy(units[-1])
    paragraph['source_text'] = 'An introductory paragraph with <MATH_0001>.'
    paragraph['placeholders'] = {'MATH_0001': old_math}
    units[-1] = stamp_unit_hashes(paragraph)
    data = json.loads(plan.read_text())
    candidates = load_jsonl(root / data['candidates_file'])
    candidates[-1]['source_text_hash'] = units[-1]['source_text_hash']
    save(root, data['units_file'], units)
    save(root, data['candidates_file'], candidates)
    write(root / 'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates, units[0]['source_commit'], 'translation', 'fixture-boundary-run'))
    commit(root)
    return root, harvest, units, plan, output


class ParagraphMathLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = Policy((Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text())

    def pair(self, old, native, **kwargs):
        return paragraph_layout_pair('A ' + old + '.', 'A ' + native + '.', self.policy, **kwargs)

    def witness(self, containers, units, ids=None):
        selected = containers.select(selector('paragraph', owner='0000'))
        return verify_old_group(units, containers.english.tags, ids or [units[-1]['unit_id']], selected,
            native_containers=containers, allow_preceding_paragraph=True, allow_paragraph_math_layout=True)

    def test_explicit_operations_replay_exact_bytes_with_offsets_and_hashes(self):
        cases = [('$x$', '$$ x $$', ['inline-to-display']),
                 ('$F(x)\n= x$', '$F(x) = x$', ['linebreak-to-space']),
                 ('$F(x)\r\n= x$', '$F(x) = x$', ['linebreak-to-space']),
                 (NATIVE_MATH, OLD_MATH, ['inline-to-display', 'linebreak-to-space']),
                 ('$F : \\Ob(\\mathcal{C}) \\to\n\\Ob(\\mathcal{S})$',
                  '$$ F : \\Ob(\\mathcal{C}) \\to\n\\Ob(\\mathcal{S}) $$', ['inline-to-display'])]
        for native, old, operations in cases:
            with self.subTest(native=native):
                result = self.pair(old, native)['math_layout_differences'][0]
                self.assertEqual(result['operations'], operations)
                self.assertEqual(result['native_math'], native)
                self.assertEqual(result['historical_math'], old)
                self.assertEqual(result['native_math_hash'], byte_hash(native))
                self.assertEqual(result['historical_math_hash'], byte_hash(old))
                raw = native
                for item in reversed(result['linebreaks']):
                    offset = item['native_byte_offset']
                    self.assertEqual(raw[offset:offset + len(item['source'])], item['source'])
                    raw = raw[:offset] + ' ' + raw[offset + len(item['source']):]
                if 'inline-to-display' in operations:
                    raw = '$$' + result['display_prefix_spaces'] + raw[1:-1] + result['display_suffix_spaces'] + '$$'
                self.assertEqual(raw, old)

    def test_math_mutations_unknown_text_and_unsafe_positions_remain_blocked(self):
        cases = [('$x$', '$x$'), ('$x$', '$y$'), ('$x=y$', '$x = y$'),
                 ('$x = y$', '$x\t= y$'), ('$$x$$', '$x$'), ('$ x$', '$$ x$$'),
                 ('$ x\n=y$', '$ x =y$'), ('$x\n=y $', '$x =y $'),
                 ('$x\n = y$', '$x  = y$'), ('$x\n\n=y$', '$x =y$'),
                 ('$x\ry$', '$x y$'), ('$F(x\n=y)$', '$F(x =y)$'),
                 ('$\\mathcal{C\n}$', '$\\mathcal{C }$'),
                 ('$\\ph\ni$', '$\\ph i$'), ('$x\\\n=y$', '$x\\ =y$'),
                 ('$x$ $y$', '$$x$$'), ('$x$', '$$$x$$$'), ('$x$', '$$\tx$$'),
                 ('$x$', '$$x\n$$'), ('$x\n=y$', '$x=y$'),
                 ('$x\\%\n=y$', '$x\\% =y$'), ('$x% hidden\n=y$', '$x% hidden =y$')]
        for command in [r'\text{word}', r'\textit{word}', r'\textbf{word}',
                        r'\textrm{word}', r'\mathrm{word}', r'\operatorname{word}',
                        r'\mbox{word}', r'\hbox{word}', r'\verb|word|',
                        r'\unknown{x}', r'\mathcal{AB}', r'\begin{math}x\end{math}',
                        r'\$', 'two words', 'é', '{x}', 'x_{y}', 'x^y']:
            cases.append(('$' + command + '$', '$$' + command + '$$'))
        for native, old in cases:
            with self.subTest(native=native, old=old), self.assertRaises(RecordError):
                self.pair(old, native)
        for unchanged in [r'$\textrm{word}$', r'$\operatorname{word}$', r'$\unknown{x}$']:
            with self.subTest(unchanged=unchanged), self.assertRaises(RecordError):
                self.pair('$$x$$ ' + unchanged, '$x$ ' + unchanged)
        for opaque in ['% comment\n', r'\verb|literal|', r'\begin{enumerate}\item x\end{enumerate}']:
            with self.subTest(opaque=opaque), self.assertRaises(RecordError):
                paragraph_layout_pair(opaque + ' $$x$$', opaque + ' $x$', self.policy)

    def test_complete_git_witness_and_all_earlier_permissions_remain_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = layout_fixture(Path(tmp))
            containers = Containers(root, harvest)
            chosen = containers.select(selector('paragraph', owner='0000'))
            flags = {'native_containers': containers}
            for feature in [None, 'allow_preceding_paragraph', 'allow_nested_preceding_paragraph',
                            'allow_section_title_paragraph', 'allow_split_preceding_paragraph']:
                if feature: flags[feature] = True
                with self.subTest(feature=feature), self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, [units[-1]['unit_id']], chosen, **flags)
            anchor = self.witness(containers, units)['paragraph_anchor']
            self.assertEqual(anchor['preceding_statement_input_unit_ids'], [units[0]['unit_id']])
            self.assertEqual(anchor['preceding_statement_selector'], selector('lemma'))
            self.assertEqual(anchor['preceding_statement_fragment_hash'], byte_hash(PLAIN))
            self.assertEqual(anchor['math_layout_differences'][0]['operations'], ['inline-to-display', 'linebreak-to-space'])
            self.assertEqual(source_tex(lower_container(chosen, containers.policy)[0]), chosen['fragment'])
            for fault in ['prose', 'math', 'unknown', 'unicode', 'blank', 'parent', 'chapter', 'source',
                          'prefix', 'suffix', 'kind', 'v2', 'statement-text', 'statement-label',
                          'statement-prefix', 'statement-close', 'order', 'duplicate', 'partial', 'missing']:
                changed = copy.deepcopy(units); old = changed[-1]; ids = None
                if fault == 'prose': old['source_text'] += ' Added.'
                if fault == 'math': old['placeholders']['MATH_0001'] = OLD_MATH.replace('=', ':')
                if fault == 'unknown': old['source_text'] += r'\unknown{value}'
                if fault == 'unicode': old['source_text'] = old['source_text'].replace(' ', '\u00a0', 1)
                if fault == 'blank': old['source_text'] += '\n\nExtra.'
                if fault == 'parent': old['parent_tag'] = '0001'
                if fault == 'chapter': old['chapter'] = 'other'
                if fault == 'source': old['source_commit'] = 'f' * 40
                if fault == 'prefix': old['render']['prefix'] = r'\medskip'
                if fault == 'suffix': old['render']['suffix'] += r'\ref{test-lemma-one}'
                if fault == 'kind': old['node_kind'] = 'display_math'
                if fault == 'v2': old['schema_version'] = 2
                if fault == 'statement-text': changed[0]['source_text'] += ' Added.'
                if fault == 'statement-label': changed[0]['render']['prefix'] = r'\begin{lemma}\label{test-lemma-two}'
                if fault == 'statement-prefix': changed[0]['render']['prefix'] = '$' + changed[0]['render']['prefix'] + '$'
                if fault == 'statement-close': changed[0]['render']['suffix'] += ' Extra.'
                if fault == 'order': changed.reverse()
                if fault == 'duplicate': changed.insert(0, copy.deepcopy(changed[0]))
                if fault == 'partial': ids = [u['unit_id'] for u in changed]
                if fault == 'missing': changed = changed[1:]
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    self.witness(containers, changed, ids)

    def test_native_uniqueness_and_full_adjacent_section_are_required(self):
        variants = [PLAIN + '\n\n' + INTRO + '\n\n' + INTRO,
                    PLAIN + '\n\n' + INTRO + '\n\n' + INTRO.replace(NATIVE_MATH, OLD_MATH),
                    PLAIN + '\n% Intervening.\n' + INTRO,
                    PLAIN + '\n\\section{Other}\\label{lemma-two}\n' + INTRO,
                    PLAIN + '\n\\begin{proof}Intervening.\\end{proof}\n' + INTRO]
        for native in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = layout_fixture(Path(tmp), native=native)
                with self.subTest(native=native), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)

    def test_package_readonly_check_and_every_witness_field_are_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = layout_fixture(Path(tmp))
            before = {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()}
            manifest = write_container_package(root, harvest, plan, output)
            self.assertEqual(manifest['state'], 'PREPARED')
            stamps = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            self.assertEqual(write_container_package(root, harvest, plan, output, check=True), manifest)
            self.assertEqual(stamps, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()})
            records = json.loads((output / 'restorations.json').read_text())
            record = next(r for r in records if r['tool']['version'] == 'source-container-v9')
            split_tests.SplitPrecedingParagraphTests.install(self, root, output, records)
            self.assertEqual(load_source_containers(root, harvest)[1], [])
            path = root / f"translation-data/source-container-restorations/{record['restoration_id']}.json"
            mutations = []
            anchor = record['legacy_boundary_witness']['paragraph_anchor']
            for key in anchor:
                row = copy.deepcopy(record); row['legacy_boundary_witness']['paragraph_anchor'].pop(key); mutations.append(row)
            for version in range(1, 9):
                row = copy.deepcopy(record); row['tool']['version'] = f'source-container-v{version}'; mutations.append(row)
            for key in anchor['math_layout_differences'][0]:
                row = copy.deepcopy(record); row['legacy_boundary_witness']['paragraph_anchor']['math_layout_differences'][0].pop(key); mutations.append(row)
            paths = [('historical_parent_tag', '0001'), ('paragraph_input_unit_id', 'wrong'),
                     ('historical_paragraph_signature_hash', 'sha256:' + '0' * 64),
                     ('native_paragraph_signature_hash', 'sha256:' + '0' * 64),
                     ('preceding_statement_signature_hash', 'sha256:' + '0' * 64),
                     ('preceding_statement_fragment_hash', 'sha256:' + '0' * 64),
                     ('preceding_statement_input_unit_ids', []), ('preceding_statement_selector', selector('lemma', owner='0002'))]
            for key, value in paths:
                row = copy.deepcopy(record); row['legacy_boundary_witness']['paragraph_anchor'][key] = value; mutations.append(row)
            for key, value in [('math_ordinal', 2), ('historical_math', '$x$'), ('native_math', '$x$'),
                               ('historical_math_hash', 'sha256:' + '0' * 64), ('native_math_hash', 'sha256:' + '0' * 64),
                               ('operations', ['inline-to-display']), ('display_prefix_spaces', ''),
                               ('display_suffix_spaces', ''), ('linebreaks', [{'native_byte_offset': 1, 'source': '\n'}])]:
                row = copy.deepcopy(record); row['legacy_boundary_witness']['paragraph_anchor']['math_layout_differences'][0][key] = value; mutations.append(row)
            for row in mutations:
                write(path, row)
                self.assertTrue(load_source_containers(root, harvest)[1])
            row = copy.deepcopy(record); row['new_units'][0]['schema_version'] = 2
            self.assertTrue(validate_named_schema(row, 'source-container-restoration.schema.json', 'synthetic'))

    def test_v4_replay_still_requires_all_five_fields_full_old_group_and_no_approval(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = layout_fixture(Path(tmp))
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'], 'PREPARED')
            records = json.loads((output / 'restorations.json').read_text())
            split_tests.SplitPrecedingParagraphTests.install(self, root, output, records)
            restored, errors = load_source_containers(root, harvest)
            self.assertEqual(errors, [])
            candidates = load_jsonl(output / 'input-candidates.jsonl')
            record = {k: records[0][k] for k in ['derivation_id', 'source_commit', 'origin_commit', 'created_at', 'files']}
            record['unit_groups'] = []; corrections = {}
            for source in records:
                group = {k: source[k] for k in ['group_id', 'input_unit_ids', 'output_unit_ids', 'reason']}
                group.update(identity_anchor=group['input_unit_ids'][0], output_units=source['new_units'],
                    source_container_restoration_id=source['restoration_id'], model_correction_id='synthetic-layout')
                record['unit_groups'].append(group)
                old = [u for u in units if u['unit_id'] in group['input_unit_ids']]
                oldc = [c for c in candidates if c['unit_id'] in group['input_unit_ids']]
                for unit in group['output_units']:
                    raw = copy.deepcopy(oldc[0]); context = {'revision_input': revision_group(record, group, old, oldc)}
                    raw.update(unit_id=unit['unit_id'], context=context, context_hash=sha256_value(context),
                        translation=''.join('<' + n + '>' for n in placeholder_names(unit['source_text'])) + '合成测试。',
                        allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic; never model output.'])
                    raw['translation_hash'] = sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'], unit['unit_id'])] = {'unit': unit, 'candidate': raw,
                        'record': {'derivation_ids': {unit['unit_id']: record['derivation_id']}, 'source_commit': record['source_commit']}}
            tags = Containers(root, harvest).english.tags
            new, newc = replay_groups(record, units, candidates, corrections, None, restored, tags)
            self.assertEqual(len(new), 2)
            self.assertTrue(all(c['publication_status'] == 'CANDIDATE' for c in newc))
            key = next(k for k, v in corrections.items() if v['unit']['node_kind'] == 'paragraph')
            for fault in [*sorted(FIELDS), 'missing', 'old-units', 'old-candidates', 'approval']:
                changed = copy.deepcopy(corrections)
                if fault in FIELDS: changed[key]['candidate'].pop(fault)
                if fault == 'missing': changed.pop(key)
                if fault == 'old-units': changed[key]['candidate']['context']['revision_input']['source_units'].clear()
                if fault == 'old-candidates': changed[key]['candidate']['context']['revision_input']['candidates'].clear()
                if fault == 'approval': changed[key]['candidate']['stage'] = 'MATH_REVIEWED'
                with self.subTest(fault=fault), self.assertRaises((RecordError, KeyError)):
                    replay_groups(record, units, candidates, changed, None, restored, tags)


if __name__ == '__main__':
    unittest.main()
