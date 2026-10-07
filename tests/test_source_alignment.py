"""Independent synthetic source fixtures; no fixture is an actual model run."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from stacks_zh.cli import main
from stacks_zh.extraction import Policy, chapter_inventory, write_inventory
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_alignment import (Corpus, _labels, _proof_diagnostics, _read_facts,
    align_batches, build_alignment, canonical_tokens, verified_inventory, write_alignment)
from stacks_zh.source_reextractions import byte_hash, source_tex

POLICY_RAW = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text()
POLICY = Policy(POLICY_RAW)
TAGS = {'alpha-section-phantom': 'AAAA', 'alpha-section-first': 'BBBB',
        'alpha-lemma-one': 'CCCC', 'alpha-item-one': 'DDDD', 'other-lemma-one': 'EEEE'}
COMMIT = 'a' * 40


def keys(text):
    return [t.key for t in canonical_tokens(text, 'alpha', TAGS, POLICY)]


def unit(text, identifier='tag:BBBB:p001', prefix='', suffix='', kind='paragraph'):
    return {'unit_id': identifier, 'chapter': 'alpha', 'parent_tag': 'BBBB',
            'source_commit': COMMIT, 'source_text': text, 'placeholders': {},
            'render': {'prefix': prefix, 'suffix': suffix}, 'node_kind': kind}


def corpus(body):
    raw = ('\\begin{document}\n\\section{First}\\label{section-first}\n' + body + '\n\\end{document}\n').encode()
    rows, _, errors = chapter_inventory('alpha', raw, COMMIT, TAGS, POLICY)
    if errors:
        raise AssertionError(errors)
    return Corpus(rows, TAGS, POLICY), raw


class AlignmentTests(unittest.TestCase):
    def complete_prose_fixture(self, base, body=None):
        root, harvest, inventory, tags_raw = self.fixture(base)
        body = body or ('First paragraph $X$.\n\nSecond paragraph '
            '\\footnote{Natural words $Y$ and \\ref{lemma-one}.}.\n'
            '\\begin{enumerate}\n\\item A condition $Z$.\n\\end{enumerate}\n'
            '\nLast paragraph.\n')
        text = ('\\begin{document}\n\\section{First}\\label{section-first}\n' + body
            + '\\begin{lemma}\\label{lemma-one}Claim.\\end{lemma}\n'
            + '\\begin{proof}Omitted.\\end{proof}\n\\end{document}\n')
        (harvest / 'alpha.tex').write_text(text)
        subprocess.run(['git', '-C', str(harvest), 'add', 'alpha.tex'], check=True)
        subprocess.run(['git', '-C', str(harvest), '-c', 'user.name=Synthetic Fixture',
            '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Complete prose fixture'], check=True)
        commit = subprocess.check_output(['git', '-C', str(harvest), 'rev-parse', 'HEAD'], text=True).strip()
        (root / 'upstream.lock').write_text(f'commit = "{commit}"\n')
        write_inventory(root, harvest, inventory)
        native = Containers(root, harvest)
        selected = native.select({'file': 'alpha.tex', 'owner_tag': 'BBBB',
            'owner_label': 'alpha-section-first', 'parent_tag': 'BBBB',
            'kind': 'prose_block', 'ordinal': 1})
        current = lower_container(selected, native.policy)[0]
        english, policy, entries, _ = verified_inventory(root, harvest, inventory, {'alpha'})
        return root, harvest, inventory, tags_raw, current, selected, Corpus(
            entries, english.tags, policy, source_containers=native)

    def test_complete_prose_spans_paragraphs_list_footnote_and_keeps_outer_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, current, selected, source = self.complete_prose_fixture(Path(tmp))
            self.assertIn('<FOOTNOTEOPEN_', current['source_text'])
            self.assertIn('\\begin{enumerate}', source_tex(current))
            match = source.match(current, current['unit_id'])
            self.assertEqual(match['status'], 'BYTE_EXACT')
            self.assertEqual(match['location'], selected['location'])
            self.assertEqual(match['native_container']['boundary_witness'], selected['boundary_witness'])
            self.assertTrue(selected['fragment'].startswith('\n'))
            self.assertEqual(match['current_source_tex_hash'], byte_hash(selected['fragment']))

    def test_complete_prose_changed_text_math_reference_and_outer_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, current, selected, source = self.complete_prose_fixture(Path(tmp))
            variants = []
            for old, new in [('First', 'Changed'), ('$X$', '$Q$'),
                             ('\\ref{lemma-one}', '\\ref{other-lemma-one}')]:
                changed = copy.deepcopy(current)
                if old in changed['source_text']:
                    changed['source_text'] = changed['source_text'].replace(old, new)
                else:
                    changed['placeholders'] = {k: v.replace(old, new) for k, v in changed['placeholders'].items()}
                variants.append(changed)
            clipped = copy.deepcopy(current); clipped['source_text'] = clipped['source_text'].strip()
            variants.append(clipped)
            for changed in variants:
                with self.subTest(tex=source_tex(changed)):
                    self.assertNotEqual(source_tex(changed), selected['fragment'])
                    self.assertEqual(source.match(changed, changed['unit_id'])['status'], 'SOURCE_DIFFERENCE')

    def test_complete_prose_wrong_identity_parent_kind_ordinal_commit_and_no_git_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            *_, current, selected, source = self.complete_prose_fixture(Path(tmp))
            for key, value in [('unit_id', 'tag:CCCC:prose-0001'), ('parent_tag', 'CCCC'),
                    ('node_kind', 'proof'), ('unit_id', 'tag:BBBB:prose-0000'),
                    ('unit_id', 'tag:BBBB:prose-0002'), ('source_commit', COMMIT)]:
                changed = {**current, key: value}
                with self.subTest(key=key, value=value):
                    self.assertEqual(source.match(changed, changed['unit_id'])['status'], 'UNSUPPORTED')
            self.assertEqual(source.match(current, 'tag:CCCC:prose-0001')['status'], 'UNSUPPORTED')
            unbound = Corpus([], TAGS, POLICY)
            self.assertEqual(unbound.match(current, current['unit_id'])['status'], 'UNSUPPORTED')

    def test_complete_prose_dirty_worktree_cannot_change_git_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, inventory, tags, current, selected, source = self.complete_prose_fixture(Path(tmp))
            (harvest / 'alpha.tex').write_text('dirty replacement')
            (harvest / 'tags/tags').write_text('CCCC,alpha-section-first\n')
            match = source.match(current, current['unit_id'])
            self.assertEqual(match['status'], 'BYTE_EXACT')
            self.assertEqual(match['native_container']['blob_hash'], selected['blob_hash'])

    def test_complete_prose_blocked_macro_and_duplicate_real_anchor_fail(self):
        for fault, expected in [('macro', 'blocked'), ('anchor', 'duplicate')]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root, harvest, inventory, _, current, _, _ = self.complete_prose_fixture(Path(tmp))
                path = harvest / 'alpha.tex'; text = path.read_text()
                if fault == 'macro':
                    text = text.replace('First paragraph', r'\unreviewedmacro{First paragraph}')
                else:
                    text = text.replace(r'\begin{lemma}',
                        '\\section{Duplicate}\\label{section-first}\n\\begin{lemma}', 1)
                path.write_text(text)
                subprocess.run(['git', '-C', str(harvest), 'add', 'alpha.tex'], check=True)
                subprocess.run(['git', '-C', str(harvest), '-c', 'user.name=Synthetic Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Blocked fixture'], check=True)
                commit = subprocess.check_output(['git', '-C', str(harvest), 'rev-parse', 'HEAD'], text=True).strip()
                (root / 'upstream.lock').write_text(f'commit = "{commit}"\n')
                current['source_commit'] = commit
                write_inventory(root, harvest, inventory)
                english, policy, entries, _ = verified_inventory(root, harvest, inventory, {'alpha'})
                source = Corpus(entries, english.tags, policy, source_containers=Containers(root, harvest))
                match = source.match(current, current['unit_id'])
                self.assertEqual(match['status'], 'UNSUPPORTED')
                self.assertIn(expected, match['reason'])

    def test_complete_prose_aggregation_does_not_waive_audits_and_checks_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, inventory, tags, current, selected, source = self.complete_prose_fixture(Path(tmp))
            write_jsonl(root / 'translation-data/units/alpha-bbbb.jsonl', [current])
            write_jsonl(root / 'translation-data/candidates/synthetic/alpha-bbbb.jsonl',
                        [{'unit_id': current['unit_id'], 'translation': 'synthetic'}])
            output = root / 'build/alignment'
            with self.audits(root, tags):
                report = write_alignment(root, harvest, inventory, output)
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                write_alignment(root, harvest, inventory, output, check=True)
            self.assertEqual(report['match_counts'], {'BYTE_EXACT': 1})
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            queue = json.loads((output / 'repair-queue.jsonl').read_text())
            self.assertNotIn('VERIFY_OR_RESTORE_SOURCE', queue['actions'])
            self.assertIn('ACTUAL_MODEL_TERM_REVISION', queue['actions'])
            self.assertIn('RESOLVE_SOURCE_STRUCTURE_OR_DISPLAY', queue['actions'])
            self.assertFalse(queue['adoption_or_review_approval'])

    def test_v1_owned_package_is_rebuilt_but_old_check_and_unknown_version_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, inventory, tags = self.fixture(Path(tmp)); output = root / 'build/alignment'
            with self.audits(root, tags):
                write_alignment(root, harvest, inventory, output)
                marker = output / 'alignment.json'; value = json.loads(marker.read_text())
                value['version'] = 'source-alignment-v1'; marker.write_text(json.dumps(value))
                with self.assertRaisesRegex(RecordError, 'out of date'):
                    write_alignment(root, harvest, inventory, output, check=True)
                write_alignment(root, harvest, inventory, output)
                self.assertEqual(json.loads(marker.read_text())['version'], 'source-alignment-v2')
                value['version'] = 'unrelated'; marker.write_text(json.dumps(value))
                with self.assertRaisesRegex(RecordError, 'unrelated'):
                    write_alignment(root, harvest, inventory, output)

    def fixture(self, base):
        root, harvest = base / 'chinese', base / 'english'
        (root / 'config').mkdir(parents=True); (harvest / 'tags').mkdir(parents=True)
        (root / 'config/macro-policy.yml').write_text(POLICY_RAW)
        (root / 'config/source-terms.json').write_text('{}')
        (root / 'config/glossary.yml').write_text('synthetic glossary')
        (harvest / 'chapters.tex').write_text(r'\item \hyperref[alpha-section-phantom]{Alpha}' + '\n')
        (harvest / 'alpha.tex').write_text('\\begin{document}\n\\section{First}\\label{section-first}\nA category.\n\\end{document}\n')
        tags_raw = ''.join(tag + ',' + label + '\n' for label, tag in TAGS.items())
        (harvest / 'tags/tags').write_text(tags_raw)
        subprocess.run(['git', 'init', '-q', str(harvest)], check=True)
        subprocess.run(['git', '-C', str(harvest), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(harvest), '-c', 'user.name=Synthetic Fixture',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Synthetic source fixture'], check=True)
        commit = subprocess.check_output(['git', '-C', str(harvest), 'rev-parse', 'HEAD'], text=True).strip()
        (root / 'upstream.lock').write_text(f'commit = "{commit}"\n')
        inventory = root / 'source-ir/extraction'
        write_inventory(root, harvest, inventory)
        rows = [json.loads(line) for line in (inventory / 'units.jsonl').read_text().splitlines()]
        current = copy.deepcopy(rows[-1]['unit']); current['unit_id'] = 'tag:BBBB:p001'
        facts = root / 'translation-data/units'; facts.mkdir(parents=True)
        (facts / 'alpha-bbbb.jsonl').write_text(json.dumps(current) + '\n')
        candidates = root / 'translation-data/candidates/synthetic'; candidates.mkdir(parents=True)
        (candidates / 'alpha-bbbb.jsonl').write_text('{"unit_id":"tag:BBBB:p001","translation":"synthetic"}\n')
        return root, harvest, inventory, tags_raw

    @contextlib.contextmanager
    def audits(self, root, expected_tags=None):
        # Synthetic audit results exercise aggregation without asserting QA for
        # nonexistent model runs or treating a test glossary as approved.
        def source_audit(actual_root, tags_path):
            self.assertEqual(actual_root.resolve(), root.resolve())
            if expected_tags is not None:
                self.assertEqual(tags_path.read_text(), expected_tags)
            return {'schema_version': 1}, ['tag:BBBB:p001: synthetic source finding',
                                        'alpha-bbbb.jsonl: incomplete unit coverage']
        terms = {'candidates': [{'path': 'translation-data/candidates/synthetic/alpha-bbbb.jsonl',
                                'errors': ['synthetic term finding']}]}
        with patch('stacks_zh.source_alignment.audit_repository_terms', return_value=(terms, ['synthetic term finding'])), \
             patch('stacks_zh.source_alignment.audit_repository_source', side_effect=source_audit), \
             patch('stacks_zh.source_alignment.audit_repository_proofs', return_value=({'mismatched': 0, 'proofs': []}, [])):
            yield

    def test_presentation_equivalence_preserves_words_and_known_ref_targets(self):
        self.assertEqual(keys('A category % comment\nwith \\ref{lemma-one}.'),
                         keys('A  category with \\ref{alpha-lemma-one}.'))
        self.assertEqual(keys('cat% comment\negory'), keys('category'))
        self.assertNotEqual(keys('a b'), keys('ab'))
        self.assertNotEqual(keys(r'\ref{lemma-one}'), keys(r'\ref{other-lemma-one}'))
        self.assertNotEqual(keys(r'\ref{unknown}'), keys(r'\ref{alpha-unknown}'))
        self.assertNotEqual(keys(r'\ref{lemma-one}'), keys(r'\eqref{lemma-one}'))

    def test_opaque_math_literal_citation_url_and_diagram_are_exact(self):
        for before, after in [('$x + y$', '$x+y$'),
            (r'$\ref{lemma-one}$', r'$\ref{alpha-lemma-one}$'),
            (r'\begin{align}x &= y\end{align}', r'\begin{align}x&=y\end{align}'),
            (r'\cite{a-b}', r'\cite{a - b}'), (r'\url{https://a/b}', r'\url{https://a / b}'),
            (r'\href{https://a/b}{a link}', r'\href{https://a / b}{a link}'),
            (r'\xymatrix{x \ar[r] & y}', r'\xymatrix{x\ar[r]&y}'),
            (r"\'{e}", r"\'{ e }"),
            (r'\verb|a b|', r'\verb|ab|'),
            (r'\begin{verbatim}a b\end{verbatim}', r'\begin{verbatim}ab\end{verbatim}')]:
            with self.subTest(before=before):
                self.assertNotEqual(keys(before), keys(after))
        self.assertEqual(keys(r'\href{https://a/b}{a  link}'), keys(r'\href{https://a/b}{a link}'))

    def test_escaped_comment_and_structural_or_footnote_changes_remain_visible(self):
        self.assertNotEqual(keys(r'A \% literal.'), keys('A % literal.'))
        for before, after in [(r'A\footnote{Full words.}', 'A'),
            (r'A\footnote{Full words.}', r'A\footnote{Words.}'),
            (r'{\it A}', r'\it A'), (r'\begin{itemize}A\end{itemize}', 'A'),
            (r'A\space B', 'A B'), (r'A\\B', r'A\B')]:
            with self.subTest(before=before):
                self.assertNotEqual(keys(before), keys(after))

    def test_utf8_span_replays_git_bytes_and_exact_class_is_strict(self):
        source, raw = corpus('Café δ words.\n\nOther words.')
        exact = source.match(unit('Café δ words.'), 'tag:BBBB:p001')
        self.assertEqual(exact['status'], 'BYTE_EXACT')
        loc = exact['location']
        self.assertEqual(raw[loc['byte_start']:loc['byte_end']], 'Café δ words.'.encode())
        self.assertEqual(loc['fragment_hash'], byte_hash(raw[loc['byte_start']:loc['byte_end']]))
        equivalent = source.match(unit('Café  δ words.\n'), 'tag:BBBB:p001')
        self.assertEqual(equivalent['status'], 'PRESENTATION_EQUIVALENT')
        self.assertEqual(equivalent['current_source_tex_hash'], byte_hash('Café  δ words.\n'))

    def test_owner_scope_forbids_global_fallback_and_secondary_label_is_verified(self):
        source, _ = corpus('Section words.\n\\begin{lemma}\\label{lemma-one}Unique lemma.\\end{lemma}')
        self.assertEqual(source.match(unit('Unique lemma.'), 'tag:BBBB:p001')['status'], 'SOURCE_DIFFERENCE')
        self.assertEqual(source.match(unit('Unique lemma.'), 'tag:EEEE:p001')['status'], 'UNSUPPORTED')
        self.assertEqual(source.match(unit('Unique lemma.'), 'tag:CCCC:p001')['status'], 'BYTE_EXACT')
        self.assertEqual(_labels(r'\verb|\label{lemma-one}|\begin{verbatim}\label{item-one}\end{verbatim}'
                                 r'\begin{reference}\label{lemma-one}\end{reference}'
                                 r'\url{https://example/\label{lemma-one}}'
                                 r'\href{https://example/\label{item-one}}{visible words}', 'alpha', TAGS, POLICY), set())
        source, _ = corpus(r'\begin{lemma}\label{lemma-one}\begin{enumerate}\item\label{item-one}Item words.\end{enumerate}\end{lemma}')
        self.assertEqual(source.match(unit('Item words.'), 'tag:DDDD:p001')['status'], 'BYTE_EXACT')

    def test_duplicate_short_text_is_ambiguous_and_does_not_select_first(self):
        source, _ = corpus('Repeated words.\n\nRepeated words.')
        match = source.match(unit('Repeated words.'), 'tag:BBBB:p001')
        self.assertEqual(match['status'], 'AMBIGUOUS')
        self.assertEqual(len(match['matches']), 2)
        self.assertNotIn('location', match)

    def test_same_physical_span_in_overlapping_verified_frames_is_deduplicated(self):
        source, _ = corpus('Unique words.')
        row = copy.deepcopy(list(source.entries.values())[-1])
        second = copy.deepcopy(row); second['inventory_id'] += '-second'
        merged = Corpus([row, second], TAGS, POLICY)
        match = merged.match(unit('Unique words.'), 'tag:BBBB:p001')
        self.assertEqual(match['status'], 'BYTE_EXACT')
        self.assertEqual(len(match['container_witnesses']), 2)

    def test_current_reordering_and_overlapping_spans_are_not_accepted(self):
        source, _ = corpus('First words.\n\nSecond words.')
        rows = [unit('Second words.'), unit('First words.', 'tag:BBBB:p002')]
        matches, _ = align_batches({'synthetic': rows}, source)
        self.assertEqual([r['status'] for r in matches], ['BYTE_EXACT', 'AMBIGUOUS'])
        rows = [unit('First words.'), unit('First words.', 'tag:BBBB:p002')]
        matches, _ = align_batches({'synthetic': rows}, source)
        self.assertEqual(matches[1]['status'], 'AMBIGUOUS')

    def test_multiple_proofs_split_chain_and_wrong_proof_selector(self):
        statement = r'\begin{lemma}\label{lemma-one}Claim.\end{lemma}'
        body = statement + '\n' + r'\begin{proof}First words.' + '\n\n' + r'Second words.\end{proof}'
        body += '\n' + r'\begin{proof}Other proof.\end{proof}'
        source, _ = corpus(body)
        rows = [unit('Claim.', 'tag:BBBB:statement', r'\begin{lemma}\label{lemma-one}', r'\end{lemma}', 'lemma'),
                unit('First words.', 'tag:BBBB:proof-p001', r'\begin{proof}', kind='proof'),
                unit('Second words.', 'tag:BBBB:proof-p002', suffix=r'\end{proof}', kind='proof'),
                unit('Other proof.', 'tag:BBBB:proof2', r'\begin{proof}', r'\end{proof}', 'proof')]
        matches, mapping = align_batches({'synthetic': rows}, source)
        self.assertTrue(all(r['status'] == 'BYTE_EXACT' for r in matches), matches)
        self.assertEqual(mapping['synthetic']['tag:BBBB:proof2'], 'tag:CCCC:proof2')
        wrong = source.match(unit('Other proof.'), 'tag:CCCC:proof2', {'statement_tag': 'CCCC', 'proof_index': 1})
        self.assertEqual(wrong['status'], 'SOURCE_DIFFERENCE')
        self.assertEqual(source.match(unit('Other proof.'), 'tag:CCCC:p001')['status'], 'SOURCE_DIFFERENCE')
        rows[2]['render']['suffix'] = ''
        matches, _ = align_batches({'synthetic': rows}, source)
        self.assertTrue(all(r['status'] == 'UNSUPPORTED' for r in matches))

    def test_inventory_commit_policy_and_content_tampering_are_rejected(self):
        for field, value in [('owner_tag', 'EEEE'), ('state', 'BLOCKED'),
                             ('location', {'file': 'alpha.tex', 'byte_start': 0}),
                             ('math_text_classifications', [{'notation': 'invented', 'usage': 'symbol'}])]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root, harvest, inventory, _ = self.fixture(Path(temp))
                rows = [json.loads(line) for line in (inventory / 'units.jsonl').read_text().splitlines()]
                rows[-1][field] = value
                path = inventory / 'units.jsonl'; path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
                manifest = json.loads((inventory / 'manifest.json').read_text())
                manifest['files']['units.jsonl'] = byte_hash(path.read_bytes())
                (inventory / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaisesRegex(RecordError, 'locked Git extraction'):
                    verified_inventory(root, harvest, inventory, {'alpha'})
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp))
            manifest = json.loads((inventory / 'manifest.json').read_text()); manifest['source_commit'] = COMMIT
            (inventory / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RecordError, 'version/commit/macro'):
                verified_inventory(root, harvest, inventory, {'alpha'})
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp))
            (root / 'config/macro-policy.yml').write_text(POLICY_RAW + '\n')
            with self.assertRaisesRegex(RecordError, 'version/commit/macro'):
                verified_inventory(root, harvest, inventory, {'alpha'})

    def test_cache_existing_id_is_not_matching_evidence_and_dirty_source_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, tags_raw = self.fixture(Path(temp))
            rows = [json.loads(line) for line in (inventory / 'units.jsonl').read_text().splitlines()]
            rows[-1]['existing_unit_id'] = 'tag:EEEE:untrusted'
            path = inventory / 'units.jsonl'; path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            manifest = json.loads((inventory / 'manifest.json').read_text())
            manifest['files']['units.jsonl'] = byte_hash(path.read_bytes())
            (inventory / 'manifest.json').write_text(json.dumps(manifest))
            (harvest / 'alpha.tex').write_text('untrusted dirty replacement')
            (harvest / 'tags/tags').write_text('EEEE,alpha-section-first\n')
            with self.audits(root, tags_raw):
                report, queue, audits = build_alignment(root, harvest, inventory)
            self.assertEqual(report['unit_count'], 1)
            self.assertEqual(report['matches'][0]['owner_tag'], 'BBBB')
            self.assertFalse(report['adopted']); self.assertFalse(report['all_translation_repairs_complete'])
            self.assertEqual(report['term_candidate_failures'], 1)
            self.assertEqual(queue[0]['source_findings'], audits['source-audit.json']['errors'])
            self.assertIn('ACTUAL_MODEL_TERM_REVISION', queue[0]['actions'])
            self.assertIn('config/source-terms.json', report['input_hashes'])

    def test_locked_term_audit_receives_the_actual_harvest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, inventory, tags = self.fixture(Path(tmp))
            with self.audits(root, tags), patch('stacks_zh.source_alignment.audit_repository_terms',
                                               return_value=({'candidates': []}, [])) as terms:
                build_alignment(root, harvest, inventory)
                terms.assert_called_once_with(root, harvest)

    def test_fact_duplicates_and_changed_fact_snapshot_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp))
            facts = root / 'translation-data/units/alpha-bbbb.jsonl'
            original = facts.read_bytes(); facts.write_bytes(original * 2)
            with self.assertRaisesRegex(RecordError, 'duplicate current'):
                _read_facts(root)
            facts.write_bytes(original)
            original_read = _read_facts
            calls = []
            def changing(path):
                calls.append(path)
                if len(calls) == 2:
                    (root / 'config/glossary.yml').write_text('changed synthetic policy')
                return original_read(path)
            with self.audits(root), patch('stacks_zh.source_alignment._read_facts', side_effect=changing):
                with self.assertRaisesRegex(RecordError, 'facts changed'):
                    build_alignment(root, harvest, inventory)

    def test_inventory_change_during_audits_and_current_wrong_commit_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp))
            with self.audits(root), patch('stacks_zh.source_alignment.audit_repository_proofs') as audit:
                def change(*_):
                    with (inventory / 'diagnostics.jsonl').open('a') as stream:
                        stream.write('{}\n')
                    return {'mismatched': 0, 'proofs': []}, []
                audit.side_effect = change
                with self.assertRaisesRegex(RecordError, 'inventory changed'):
                    build_alignment(root, harvest, inventory)
            write_inventory(root, harvest, inventory)
            facts = root / 'translation-data/units/alpha-bbbb.jsonl'
            row = json.loads(facts.read_text()); row['source_commit'] = COMMIT
            facts.write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(RecordError, 'locked English commit'):
                build_alignment(root, harvest, inventory)

    def test_missing_cache_container_and_manifest_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp))
            (inventory / 'units.jsonl').write_text('')
            manifest = json.loads((inventory / 'manifest.json').read_text())
            manifest['files']['units.jsonl'] = byte_hash(b'')
            (inventory / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RecordError, 'locked Git extraction'):
                verified_inventory(root, harvest, inventory, {'alpha'})
            marker = inventory / 'manifest.json'; saved = inventory / 'saved-manifest'
            marker.rename(saved); marker.symlink_to(saved)
            with self.assertRaisesRegex(RecordError, 'symlink'):
                verified_inventory(root, harvest, inventory, {'alpha'})

    def test_proof_differences_are_retained_even_for_known_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'translation-data/units').mkdir(parents=True)
            current = unit(r'Use \ref{lemma-one}.', 'tag:CCCC:proof', r'\begin{proof}', r'\end{proof}', 'proof')
            (root / 'translation-data/units/synthetic.jsonl').write_text(json.dumps(current) + '\n')
            proof = {'proofs': [{'batch': 'synthetic', 'status': 'mismatch',
                                'unit_ids': [current['unit_id']], 'selector': {'fixture': True}}]}
            english = SimpleNamespace(tags=TAGS, select=lambda _: source_tex(current).replace('{lemma-one}', '{alpha-lemma-one}'))
            details = _proof_diagnostics(root, english, POLICY, proof)
            self.assertEqual(details[0]['classification'], 'PRESENTATION_EQUIVALENT')
            self.assertEqual(details[0]['audit_status'], 'mismatch'); self.assertFalse(details[0]['waived'])
            self.assertTrue(details[0]['node_changes'])
            english.select = lambda _: r'\begin{proof}Use $x$.\end{proof}'
            self.assertEqual(_proof_diagnostics(root, english, POLICY, proof)[0]['classification'], 'SOURCE_DIFFERENCE')

    def test_deterministic_check_invalidates_changed_candidates_and_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp)); output = root / 'build/source-alignment'
            with self.audits(root):
                first = write_alignment(root, harvest, inventory, output)
                before = {p.name:p.read_bytes() for p in output.iterdir()}
                self.assertEqual(first, write_alignment(root, harvest, inventory, output, check=True))
                self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
                path = root / 'translation-data/candidates/synthetic/alpha-bbbb.jsonl'
                path.write_text(path.read_text().replace('synthetic', 'changed'))
                with self.assertRaisesRegex(RecordError, 'out of date'):
                    write_alignment(root, harvest, inventory, output, check=True)
                write_alignment(root, harvest, inventory, output)
                (root / 'config/glossary.yml').write_text('changed glossary')
                with self.assertRaisesRegex(RecordError, 'out of date'):
                    write_alignment(root, harvest, inventory, output, check=True)

    def test_output_safety_failed_write_and_swap_preserve_complete_previous_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, inventory, _ = self.fixture(Path(temp)); output = root / 'build/source-alignment'
            with self.audits(root):
                write_alignment(root, harvest, inventory, output)
                before = {p.name:p.read_bytes() for p in output.iterdir()}
                for forbidden in (root / 'build', root / 'translation-data/units', root.parent / 'outside'):
                    with self.assertRaises(RecordError):
                        write_alignment(root, harvest, inventory, forbidden)
                link = root / 'build/link'; link.symlink_to(output, target_is_directory=True)
                with self.assertRaises(RecordError):write_alignment(root, harvest, inventory, link)
                (output / 'extra').write_text('unrelated')
                with self.assertRaises(RecordError):write_alignment(root, harvest, inventory, output)
                with self.assertRaises(RecordError):write_alignment(root, harvest, inventory, output, check=True)
                (output / 'extra').unlink()
                original_write = Path.write_bytes
                def failing_write(path, data):
                    if path.parent.name.startswith('.alignment-') and path.name == 'repair-queue.jsonl':
                        raise OSError('synthetic partial-package write failure')
                    return original_write(path, data)
                with patch.object(Path, 'write_bytes', failing_write):
                    with self.assertRaises(OSError):write_alignment(root, harvest, inventory, output)
                self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
                original, calls = Path.rename, []
                def failing_swap(path, target):
                    calls.append(path)
                    if len(calls) == 2:raise OSError('synthetic swap failure')
                    return original(path, target)
                with patch.object(Path, 'rename', failing_swap):
                    with self.assertRaises(OSError):write_alignment(root, harvest, inventory, output)
                self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
                racing = root / 'build/racing'
                def unrelated_directory(*args):
                    result = build_alignment(*args)
                    racing.mkdir(); (racing / 'unrelated').write_text('preserve this')
                    return result
                with patch('stacks_zh.source_alignment.build_alignment', side_effect=unrelated_directory):
                    with self.assertRaisesRegex(RecordError, 'unrelated'):
                        write_alignment(root, harvest, inventory, racing)
                self.assertEqual((racing / 'unrelated').read_text(), 'preserve this')

    def test_cli_queue_success_does_not_claim_findings_resolved(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _, _ = self.fixture(Path(temp))
            args = ['source-alignment', '--root', str(root), '--harvest', str(harvest)]
            out = io.StringIO()
            with self.audits(root), contextlib.redirect_stdout(out):
                self.assertEqual(main(args), 0); self.assertEqual(main(args + ['--check']), 0)
            self.assertIn('Adopted: false. Repairs complete: false.', out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(args + ['--inventory', 'missing']), 1)


if __name__ == '__main__':
    unittest.main()
