"""Independent synthetic Git boundaries; no production facts or model output."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_containers import (INTRODUCTION, NAMED, git, paragraph_package_fixture, selector)
from test_group_derivations import commit, run_for, save, write
from stacks_zh.records import RecordError, load_jsonl, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers, lower_container,
    verify_old_group, write_container_package)
from stacks_zh.source_reextractions import source_tex

INTRO = '\\noindent\nAn introductory\nparagraph with $x$.'


def intro_fixture(base, *, native=INTRO):
    root, harvest, plan, output = paragraph_package_fixture(base)
    text = harvest / 'test.tex'
    text.write_text(text.read_text().replace(INTRODUCTION, native))
    git(harvest, 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '--allow-empty', '-qm', 'synthetic first paragraph')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    data = json.loads(plan.read_text())
    units = load_jsonl(root / data['units_file'])
    candidates = load_jsonl(root / data['candidates_file'])
    for unit, candidate in zip(units, candidates, strict=True):
        unit['source_commit'] = source
        unit.update(stamp_unit_hashes(unit))
        candidate.update(source_commit=source, source_text_hash=unit['source_text_hash'])
        candidate['context']['source_commit'] = source
        candidate['context_hash'] = sha256_value(candidate['context'])
    save(root, data['units_file'], units); save(root, data['candidates_file'], candidates)
    write(root / 'translation-data/runs/fixture-paragraph-run.json',
          run_for(candidates, source, 'translation', 'fixture-paragraph-run'))
    commit(root)
    return root, harvest, units, plan, output


def install_records(root, output):
    records = json.loads((output / 'restorations.json').read_text())
    for record in records:
        for role, name in [('input_units', 'input-units.jsonl'), ('input_candidates', 'input-candidates.jsonl')]:
            path = root / record['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((output / name).read_bytes())
        write(root / f"translation-data/source-container-restorations/{record['restoration_id']}.json", record)
    return records


class SectionTitleParagraphTests(unittest.TestCase):
    def witness(self, containers, units, *, enabled=True, selected=None, ids=None):
        selected = selected or containers.select(selector('paragraph', owner='0000'))
        return verify_old_group(units, containers.english.tags, ids or ['tag:0000:p001'], selected,
            native_containers=containers, allow_preceding_paragraph=True,
            allow_nested_preceding_paragraph=True, allow_section_title_paragraph=enabled)

    def test_complete_first_paragraph_has_explicit_permission_and_exact_title_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = intro_fixture(Path(tmp)); c = Containers(root, harvest)
            with self.assertRaises(RecordError): self.witness(c, units, enabled=False)
            anchor = self.witness(c, units)['paragraph_anchor']
            self.assertEqual(anchor['preceding_section_title_input_unit_id'], 'tag:0000:title')
            self.assertEqual(anchor['preceding_section_title_selector'], selector('section_title', owner='0000'))
            self.assertEqual(anchor['historical_parent_tag'], '0000')
            native = c.select(selector('paragraph', owner='0000'))
            self.assertEqual(source_tex(lower_container(native, c.policy)[0]), INTRO)
            self.assertIn('\\label{test-section-basic}', source_tex(units[0]))
            self.assertIn('\\label{section-basic}', c.select(anchor['preceding_section_title_selector'])['fragment'])

    def test_full_old_title_scope_prose_and_protected_bytes_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = intro_fixture(Path(tmp)); c = Containers(root, harvest)
            faults = ['missing-title', 'order', 'duplicate', 'title-kind', 'parent', 'chapter', 'source',
                      'title-words', 'title-space', 'title-math', 'wrong-label', 'old-local-label', 'fake-opening',
                      'fake-closing', 'comment-closing', 'unicode-wrapper', 'second-label', 'slice', 'words',
                      'math', 'reference', 'unknown', 'unicode-prose', 'blank', 'partial-group']
            for fault in faults:
                units = copy.deepcopy(original); h, p = units; ids = None
                if fault == 'missing-title': units.pop(0)
                if fault == 'order': units.reverse()
                if fault == 'duplicate': units.insert(0, copy.deepcopy(h))
                if fault == 'title-kind': h['node_kind'] = 'paragraph'
                if fault == 'parent': h['parent_tag'] = '0001'
                if fault == 'chapter': h['chapter'] = 'other'
                if fault == 'source': h['source_commit'] = '1' * 40
                if fault == 'title-words': h['source_text'] = 'Other basics'
                if fault == 'title-space': h['source_text'] = ' Basics'
                if fault == 'title-math': h['source_text'] = '$x$'
                if fault == 'wrong-label': h['render']['suffix'] = '}\\label{test-lemma-one}'
                if fault == 'old-local-label': h['render']['suffix'] = '}\\label{section-basic}'
                if fault == 'fake-opening': h['render']['prefix'] = '$\\section{'
                if fault == 'fake-closing': h['render']['suffix'] += '$'
                if fault == 'comment-closing': h['render']['suffix'] = '}% forged\n\\label{test-section-basic}'
                if fault == 'unicode-wrapper': h['render']['suffix'] = h['render']['suffix'].replace('\n', '\u00a0')
                if fault == 'second-label': h['render']['suffix'] += '\\label{test-section-basic}'
                if fault == 'slice': p['source_text'] = 'paragraph with <MATH_0001>.'
                if fault == 'words': p['source_text'] += ' Added.'
                if fault == 'math': p['placeholders']['MATH_0001'] = '$y$'
                if fault == 'reference': p['render']['suffix'] += '\\ref{lemma-one}'
                if fault == 'unknown': p['render']['prefix'] = '\\unknownCommand '
                if fault == 'unicode-prose': p['source_text'] = p['source_text'].replace(' ', '\u00a0', 1)
                if fault == 'blank': p['source_text'] = p['source_text'].replace('paragraph', '\n\nparagraph')
                if fault == 'partial-group': ids = [h['unit_id'], p['unit_id']]
                with self.subTest(fault=fault), self.assertRaises(RecordError): self.witness(c, units, ids=ids)

    def test_native_first_adjacency_uniqueness_and_unknown_syntax_are_required(self):
        variants = [INTRO + '\n\n' + INTRO, '% intervening\n' + INTRO,
                    NAMED + '\n\n' + INTRO, '\\section{Other}\\label{lemma-two}\n' + INTRO,
                    'Earlier paragraph.\n\n' + INTRO, '\u00a0\n' + INTRO,
                    INTRO.replace('$x$', '$\\text{unclassified prose}$'),
                    INTRO.replace('introductory', '\\unknownCommand introductory')]
        for native in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = intro_fixture(Path(tmp), native=native)
                with self.subTest(native=native), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = intro_fixture(Path(tmp), native='Earlier.\n\n' + INTRO)
            c = Containers(root, harvest)
            with self.assertRaises(RecordError):
                self.witness(c, units, selected=c.select(selector('paragraph', ordinal=2, owner='0000')))

    def test_v7_readonly_packages_replay_and_reject_version_or_witness_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, plan, out = intro_fixture(Path(tmp))
            before = {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()}
            manifest = write_container_package(root, harvest, plan, out)
            self.assertEqual(manifest['state'], 'PREPARED')
            stamps = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir() if p.is_file()}
            self.assertEqual(write_container_package(root, harvest, plan, out, check=True), manifest)
            self.assertEqual(stamps, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir() if p.is_file()})
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()})
            records = install_records(root, out)
            boundary = next(r for r in records if r['tool']['version'] == 'source-container-v7')
            self.assertEqual(load_source_containers(root, harvest)[1], [])
            path = root / f"translation-data/source-container-restorations/{boundary['restoration_id']}.json"
            for fault in ['v4', 'v5', 'v6', 'missing', 'extra', 'id', 'parent', 'selector', 'ordinal',
                          'title-hash', 'paragraph-hash', 'typed-unit', 'source-byte']:
                b = copy.deepcopy(boundary); a = b['legacy_boundary_witness']['paragraph_anchor']
                if fault in ['v4', 'v5', 'v6']: b['tool']['version'] = 'source-container-' + fault
                if fault == 'missing': a.pop('preceding_section_title_input_unit_id')
                if fault == 'extra': a['preceding_statement_selector'] = selector('lemma')
                if fault == 'id': a['preceding_section_title_input_unit_id'] = 'tag:0001:title'
                if fault == 'parent': a['historical_parent_tag'] = '0001'
                if fault == 'selector': a['preceding_section_title_selector']['owner_tag'] = '0001'
                if fault == 'ordinal': a['preceding_section_title_selector']['ordinal'] = 2
                if fault == 'title-hash': a['preceding_section_title_fragment_hash'] = 'sha256:' + '0' * 64
                if fault == 'paragraph-hash': a['paragraph_signature_hash'] = 'sha256:' + '0' * 64
                if fault == 'typed-unit': b['new_units'][0]['schema_version'] = 2
                if fault == 'source-byte': b['new_units'][0]['source_text'] += ' Added.'
                write(path, b)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root, harvest)[1])
                    if fault in ['v4', 'v5', 'v6', 'missing', 'extra', 'ordinal', 'typed-unit']:
                        self.assertTrue(validate_named_schema(b, 'source-container-restoration.schema.json', 'fixture'))

    def test_prior_outer_whitespace_permission_stays_byte_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, out = paragraph_package_fixture(Path(tmp))
            self.assertEqual(write_container_package(root, harvest, plan, out)['state'], 'PREPARED')
            self.assertEqual([r['tool']['version'] for r in json.loads((out / 'restorations.json').read_text())],
                             ['source-container-v2', 'source-container-v2'])

    def test_group_revision_requires_all_fields_full_inputs_and_no_human_approval(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        from stacks_zh.records import placeholder_names
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, out = intro_fixture(Path(tmp))
            self.assertEqual(write_container_package(root, harvest, plan, out)['state'], 'PREPARED')
            records = install_records(root, out); restored, errors = load_source_containers(root, harvest)
            self.assertEqual(errors, [])
            candidates = load_jsonl(out / 'input-candidates.jsonl')
            record = {k: records[0][k] for k in ['derivation_id', 'source_commit', 'origin_commit', 'created_at', 'files']}
            record['unit_groups'] = []; corrections = {}
            for source in records:
                group = {k: source[k] for k in ['group_id', 'input_unit_ids', 'output_unit_ids', 'reason']}
                group.update(identity_anchor=group['input_unit_ids'][0], output_units=source['new_units'],
                    source_container_restoration_id=source['restoration_id'], model_correction_id='synthetic-section-revision')
                record['unit_groups'].append(group)
                old = [u for u in units if u['unit_id'] in group['input_unit_ids']]
                oldc = [c for c in candidates if c['unit_id'] in group['input_unit_ids']]
                for unit in group['output_units']:
                    raw = copy.deepcopy(oldc[0]); context = {'revision_input': revision_group(record, group, old, oldc)}
                    raw.update(unit_id=unit['unit_id'], context=context, context_hash=sha256_value(context),
                        translation=''.join('<' + n + '>' for n in placeholder_names(unit['source_text'])) + '合成测试。',
                        allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic, never model output.'])
                    raw['translation_hash'] = sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'], unit['unit_id'])] = {'unit': unit, 'candidate': raw,
                        'record': {'derivation_ids': {unit['unit_id']: record['derivation_id']}, 'source_commit': record['source_commit']}}
            tags = Containers(root, harvest).english.tags
            new, newc = replay_groups(record, units, candidates, corrections, None, restored, tags)
            self.assertEqual(len(new), 2); self.assertTrue(all(c['publication_status'] == 'CANDIDATE' for c in newc))
            key = next(k for k, v in corrections.items() if v['unit']['node_kind'] == 'paragraph')
            for fault in [*sorted(FIELDS), 'missing-revision', 'partial-inputs', 'human-approval']:
                changed = copy.deepcopy(corrections)
                if fault in FIELDS: changed[key]['candidate'].pop(fault)
                if fault == 'missing-revision': changed.pop(key)
                if fault == 'partial-inputs': changed[key]['candidate']['context']['revision_input']['candidates'].clear()
                if fault == 'human-approval': changed[key]['candidate']['stage'] = 'MATH_REVIEWED'
                with self.subTest(fault=fault), self.assertRaises((RecordError, KeyError)):
                    replay_groups(record, units, candidates, changed, None, restored, tags)


if __name__ == '__main__':
    unittest.main()
