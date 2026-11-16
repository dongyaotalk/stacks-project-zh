"""Source-only finite primitive grammar: no TeX execution or data acceptance."""
import json,os,subprocess,unittest
from pathlib import Path
from stacks_zh.numeric_item_labels import LABELS,label_end,label_metadata,validate_literals
from stacks_zh.extraction import Policy,Scanner
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers
from stacks_zh.source_reextractions import byte_hash,LockedEnglish
from stacks_zh.source_reextractions import source_tex
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.loads((ROOT/'tests/fixtures/defos-numeric-item-labels.json').read_text())
class NumericItemLabelsTests(unittest.TestCase):
 def test_complete_labels_require_explicit_opt_in(self):
  expected=tuple(r'\item[(\romannumeral'+str(i)+')]' for i in range(1,5))
  self.assertEqual(LABELS,expected);self.assertEqual(validate_literals(list(expected)),expected)
  for literal in expected:
   self.assertIsNone(label_end(literal,0))
   self.assertEqual(label_end(literal,0,allowed=expected),len(literal))
   self.assertIsNone(label_end(literal,0,end=len(literal)-1,allowed=expected))
  for bad in ([],['romannumeral'],[expected[0],expected[0]],['\\item[(\\romannumeral5)]']):
   with self.assertRaises(ValueError):validate_literals(bad)
 def test_no_missing_integer_or_expression_or_context_guessing(self):
  for bad in (r'\romannumeral1',r'\item[(\romannumeral)]',r'\item[(\romannumeral0)]',
              r'\item[(\romannumeral5)]',r'\item[(\romannumeral12)]',r'\item[(\romannumeral-1)]',
              r'\item[(\romannumeral+1)]',r'\item[(\romannumeral{1})]',r'\item[(\romannumeral 1)]',
              r'\item[(\romannumeral1\relax)]',r'\item[(\romannumeral1+2)]',
              r'\item [(\romannumeral1)]',r'\item[(\romannumeral1) ]',r'\item[(\romannumeral1]',
              r'\item[(\Romannumeral1)]',r'\item[\romannumeral1]'):
   self.assertIsNone(label_end(bad,0,allowed=LABELS),bad)
  self.assertIsNone(label_end(LABELS[0],True,allowed=LABELS))
  self.assertIsNone(label_end(LABELS[0],-1,allowed=LABELS))
 def test_metadata_locks_whole_optional_argument_and_utf8_boundaries(self):
  for i,literal in enumerate(LABELS,1):
   text='汉字 '+literal+'\nbody';start=3;finish=start+len(literal)
   self.assertEqual(label_end(text,start,allowed=LABELS),finish)
   meta=label_metadata(text,start,finish)
   self.assertEqual(meta['source'],literal);self.assertEqual(meta['integer_source'],str(i))
   span=meta['source_byte_span'];self.assertEqual(text.encode()[span['start']:span['end']].decode(),literal)
   with self.assertRaises(ValueError):label_metadata(text,start,finish-1)
 def test_current_policy_keeps_four_unknown_macros_blocked(self):
  policy=Policy((ROOT/'config/macro-policy.yml').read_text())
  self.assertNotIn('romannumeral',policy.commands)
  _,_,errors=Scanner(FIXTURE['full_source_container'],policy).protect(0,len(FIXTURE['full_source_container']))
  self.assertEqual(len([e for e in errors if e['kind']=='unknown-command' and 'romannumeral' in e['message']]),4)
 @unittest.skipUnless(os.environ.get('HARVEST_DIR'),'requires explicit locked read-only harvest')
 def test_complete_locked_git_container_and_all_literal_occurrences(self):
  harvest=Path(os.environ['HARVEST_DIR']);english=LockedEnglish(ROOT,harvest)
  raw=subprocess.check_output(['git','show',FIXTURE['source_commit']+':defos.tex'],cwd=harvest)
  self.assertEqual(byte_hash(raw),FIXTURE['blob_hash'])
  loc=FIXTURE['inventory_coordinate']['location'];source=raw[loc['byte_start']:loc['byte_end']].decode()
  self.assertEqual(source,FIXTURE['full_source_container']);self.assertEqual(byte_hash(source),loc['fragment_hash'])
  self.assertEqual(english.tags['defos-lemma-lift-complex'],'0DIT')
  self.assertTrue(FIXTURE['source_only']);self.assertFalse(FIXTURE['candidate_generation'])
  self.assertEqual([w['source'] for w in FIXTURE['witnesses']],list(LABELS))
  for witness in FIXTURE['witnesses']:
   span=witness['git_byte_span'];self.assertEqual(raw[span['start']:span['end']].decode(),witness['source'])
  with self.assertRaisesRegex(RecordError,'unknown command or unsupported scoped command: romannumeral'):
   Containers(ROOT,harvest).select(FIXTURE['selector'])


import copy,hashlib,re,types
from stacks_zh.numeric_item_labels import policy_registry,resolve_policy_witnesses
from stacks_zh.extraction import resolve_natural_math_witnesses
from stacks_zh.records import _validate_candidate,placeholder_names,sha256_value
from stacks_zh.source_containers import lower_container
PRODUCTION=(ROOT/'config/macro-policy.yml').read_text()
SECTION=('\nlocked_numeric_item_labels:\n  defos-lift-complex:\n'
         '    literals: '+json.dumps(list(LABELS))+'\n'
         '    usage: "finite-roman-item-label"\n'
         '    source_label: "defos-lemma-lift-complex"\n')

@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
class NumericItemLabelIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.english = LockedEnglish(ROOT, Path(os.environ['HARVEST_DIR']))
        cls.policy = Policy(PRODUCTION + SECTION)
        resolve_natural_math_witnesses(cls.policy, cls.english)

    def scan(self, source, policy=None, end=None):
        return Scanner(source, policy or self.policy).protect(0, len(source) if end is None else end)

    def test_unresolved_policy_does_not_grant_numeric_permission(self):
        policy = Policy(PRODUCTION + SECTION)
        _, _, errors = self.scan(FIXTURE['full_source_container'], policy)
        self.assertEqual(sum('romannumeral' in e['message'] for e in errors), 4)
        self.assertEqual(policy_registry(PRODUCTION), {})

    def test_default_source_and_diagnostics_match_original_implementation(self):
        # Replay the real accepted implementation, never compare the patched module with itself.
        baseline = types.ModuleType('stacks_zh._numeric_baseline')
        baseline.__package__ = 'stacks_zh'
        baseline_source = subprocess.check_output(
            ['git', 'show', FIXTURE['accepted_base'] + ':stacks_zh/extraction.py'], cwd=ROOT)
        exec(compile(baseline_source, 'accepted-extraction-baseline', 'exec'), baseline.__dict__)
        baseline_policy = subprocess.check_output(
            ['git', 'show', FIXTURE['accepted_base'] + ':config/macro-policy.yml'], cwd=ROOT).decode()
        source = FIXTURE['full_source_container']
        old = baseline.Scanner(source, baseline.Policy(baseline_policy)).protect(0, len(source))
        new = self.scan(source, Policy(PRODUCTION))
        self.assertEqual(new, old)

    def test_complete_native_container_ready_with_exact_original_replay(self):
        native = Containers(ROOT, self.english.harvest, policy_bytes=(PRODUCTION + SECTION).encode())
        selected = native.select(FIXTURE['selector'])
        units = lower_container(selected, native.policy)
        self.assertEqual(len(units), 1)
        unit = units[0]
        self.assertEqual(unit['unit_id'], 'tag:0DIT:statement')
        self.assertEqual(source_tex(unit), FIXTURE['full_source_container'])
        labels = [v for v in unit['placeholders'].values() if v in LABELS]
        self.assertEqual(labels, list(LABELS))
        self.assertTrue(all(k.startswith('STRUCT_') for k, v in unit['placeholders'].items() if v in LABELS))
        self.assertNotIn('romannumeral', re.sub(r'<[^>]*>', '', unit['source_text']))
        native.assert_unchanged()
        self.__class__.unit = unit

    def test_source_witness_matches_all_four_original_locked_git_spans(self):
        witness = self.policy.numeric_item_witnesses['defos-lift-complex']
        self.assertEqual(witness['source_commit'], FIXTURE['source_commit'])
        self.assertEqual(witness['blob_hash'], FIXTURE['blob_hash'])
        self.assertEqual(witness['location'], FIXTURE['inventory_coordinate']['location'])
        self.assertEqual([w['source'] for w in witness['witnesses']], list(LABELS))
        self.assertEqual([w['git_byte_span'] for w in witness['witnesses']],
                         [w['git_byte_span'] for w in FIXTURE['witnesses']])
        policy = Policy(PRODUCTION + SECTION.replace('defos-lemma-lift-complex', 'defos-lemma-nonexistent'))
        with self.assertRaisesRegex(RecordError, 'real permanent Tag'):
            resolve_policy_witnesses(policy, self.english)
        self.assertEqual(policy.numeric_item_witnesses, {})
        policy = Policy(PRODUCTION + SECTION.replace('defos-lemma-lift-complex', 'defos-lemma-tor-aux'))
        with self.assertRaises(RecordError):
            resolve_policy_witnesses(policy, self.english)

    def test_malformed_label_and_non_enumerate_context_remain_blocked(self):
        malformed = [r'\item[(\romannumeral)]', r'\item[(\romannumeral0)]',
                     r'\item[(\romannumeral5)]', r'\item[(\romannumeral12)]',
                     r'\item[(\romannumeral-1)]', r'\item[(\romannumeral{1})]',
                     r'\item[(\romannumeral 1)]', r'\item[(\romannumeral1\relax)]',
                     r'\item [(\romannumeral1)]', r'\item[(\romannumeral1) ]']
        for label in malformed:
            with self.subTest(label=label):
                source = r'\begin{enumerate}' + label + r' body\end{enumerate}'
                _, _, errors = self.scan(source)
                self.assertTrue(any('romannumeral' in e['message'] for e in errors))
        for source in [LABELS[0], r'\romannumeral1',
                       r'\begin{itemize}' + LABELS[0] + r'\end{itemize}',
                       r'\begin{enumerate}\textit{' + LABELS[0] + r'}\end{enumerate}',
                       r'\unknown{' + LABELS[0] + '}']:
            with self.subTest(source=source):
                _, payloads, errors = self.scan(source)
                self.assertTrue(errors)
                self.assertFalse(any(v in LABELS for v in payloads.values()))

    def test_math_literal_comments_and_partial_walk_never_invoke_numeric_lock(self):
        for source in ['$' + LABELS[0] + '$', '% ' + LABELS[0] + '\n',
                       r'\begin{verbatim}' + LABELS[0] + r'\end{verbatim}']:
            with self.subTest(source=source):
                _, payloads, _ = self.scan(source)
                self.assertFalse(any(v in LABELS for v in payloads.values()))
        source = r'\begin{enumerate}' + LABELS[0] + r' body\end{enumerate}'
        stop = source.index(LABELS[0]) + len(LABELS[0]) - 1
        with self.assertRaises(RecordError):
            self.scan(source, end=stop)

    def test_registry_rejects_invalid_duplicate_and_incomplete_inputs(self):
        malformed = [SECTION + SECTION, SECTION + '  duplicate:\n',
                     SECTION.replace('    usage:', '    unknown:'),
                     SECTION.replace('    usage: "finite-roman-item-label"\n', ''),
                     SECTION.replace('finite-roman-item-label', 'generic-roman'),
                     SECTION.replace(json.dumps(list(LABELS)), 'true'),
                     SECTION.replace(json.dumps(list(LABELS)), json.dumps(list(LABELS[:-1]))),
                     SECTION.replace(json.dumps(list(LABELS)), json.dumps(list(reversed(LABELS)))),
                     SECTION.replace(json.dumps(list(LABELS)), json.dumps([LABELS[0]] * 4)),
                     SECTION.replace('    usage:', '\tusage:'),
                     SECTION.replace('locked_numeric_item_labels:', ' locked_numeric_item_labels:'),
                     SECTION.replace('locked_numeric_item_labels:', 'locked_numeric_item_labels :'),
                     SECTION.replace('"defos-lemma-lift-complex"', '"../source"'),
                     SECTION.replace('"defos-lemma-lift-complex"', 'false'),
                     '\nlocked_numeric_item_labels:\n']
        for text in malformed:
            with self.subTest(text=text):
                with self.assertRaises(RecordError):
                    Policy(PRODUCTION + text)

    def test_existing_candidate_guard_rejects_whole_label_token_mutations(self):
        protected, payloads, errors = self.scan(FIXTURE['full_source_container'])
        self.assertEqual(errors, [])
        unit = {'unit_id': 'fixture:numeric-protection', 'schema_version': 1,
                'source_commit': FIXTURE['source_commit'], 'source_text': protected,
                'source_text_hash': 'sha256:' + '0' * 64, 'placeholders': payloads}
        candidate = {k: 'fixture' for k in ['model_id', 'model_lane', 'reasoning_effort',
                     'prompt_version', 'glossary_revision', 'stage', 'source_status',
                     'qa_status', 'term_status', 'publication_status', 'created_at']}
        candidate.update(schema_version=1, unit_id=unit['unit_id'], source_commit=unit['source_commit'],
                         source_text_hash=unit['source_text_hash'], context={}, context_hash=sha256_value({}),
                         term_occurrences=[], unknown_terms=[], notes=[], allowed_english=[])
        tokens = placeholder_names(protected)
        good = ''.join('<' + name + '>' for name in tokens) + '合成保护测试。\n'
        self.assertFalse(any('protected placeholders changed' in e
                             for e in _validate_candidate({**candidate, 'translation': good}, unit, unit['source_commit'])))
        labels = [name for name in tokens if payloads[name] in LABELS]
        first, second = ['<' + name + '>' for name in labels[:2]]
        variants = [good.replace(first, '', 1), good.replace(first, first + first, 1),
                    good.replace(first, '<STRUCT_9999>', 1),
                    good.replace(first, '\x00', 1).replace(second, first, 1).replace('\x00', second, 1)]
        for translation in variants:
            with self.subTest(translation=translation):
                self.assertTrue(any('protected placeholders changed' in e
                                    for e in _validate_candidate({**candidate, 'translation': translation}, unit, unit['source_commit'])))


if __name__=='__main__':unittest.main()
