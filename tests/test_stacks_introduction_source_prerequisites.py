"""Independent synthetic English/Git fixtures, never actual model translations."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_math_text import BASE_POLICY
from test_source_containers import fixture as english_fixture, git, selector
from test_source_adoptions import synthetic_fixture, write
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions, validate_translation
from stacks_zh.records import RecordError, write_jsonl, sha256_value
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_adoptions import POLICIES, assemble_source_adoption, load_repository_source_adoptions
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from stacks_zh.workflow import render_batch

ROOT_CONDITION = r'$$\mathcal{X}\to\Spec(k)\text{ is smooth}\Leftrightarrow W\text{ is smooth}$$'
MATRIX_CONDITION = r'$$\begin{matrix}X\text{ is compact}\Leftarrow W\text{ is compact}\\Y\text{ is compact}\end{matrix}$$'
SET_CONDITION = (r'$$\left\{\left(\begin{matrix}u&r\\0&1\end{matrix}\right)'
                 r'\middle|\begin{matrix}u\text{ unit}\\s,r,t\text{ arbitrary}'
                 r'\end{matrix}\right\}\subset G_{2}$$')
HYPHEN = r'$$\QCoh(X)=H\text{-equivariant modules on }W$$'


def policy_text():
    text = BASE_POLICY + '\ntranslatable_math_text:\n'
    for key, literal, role in [
        ('smooth-condition', ' is smooth', 'root-condition'),
        ('compact-condition', ' is compact', 'matrix-row-condition'),
        ('unit-condition', ' unit', 'matrix-row-condition'),
        ('free-condition', ' arbitrary', 'matrix-row-condition'),
        ('module-phrase', '-equivariant modules on ', 'root-hyphen-phrase'),
    ]:
        text += (f'  {key}:\n    literal: {json.dumps(literal)}\n    command: "text"\n'
                 f'    usage: "{role}"\n    source_label: "test-lemma-one"\n'
                 '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text


def math_fixture(base):
    proof = '\\begin{proof}\n' + '\n'.join([
        ROOT_CONDITION, MATRIX_CONDITION, SET_CONDITION, HYPHEN]) + '\n\\end{proof}'
    root, harvest, _ = english_fixture(base, proof=proof)
    (root / 'config/macro-policy.yml').write_text(policy_text())
    native = Containers(root, harvest)
    selected = native.select(selector())
    return root, harvest, lower_container(selected, native.policy)[0], proof


def header_fixture(base, *, version='source-adoption-input-v4', old_origin=False):
    root, harvest, fp, rp, frozen, _ = synthetic_fixture(base, typed=False)
    source_path = harvest / 'test.tex'
    source_path.write_text(source_path.read_text().replace('\\begin{document}\n',
        '\\begin{document}\n\\title{A synthetic chapter}\n\\maketitle\n'
        '\\phantomsection\n\\label{section-phantom}\n\\tableofcontents\n\n', 1))
    tags = harvest / 'tags/tags'
    tags.write_text('000Z,test-section-phantom\n' + tags.read_text())
    git(harvest, 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic complete document header')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    for batch in frozen['batches']:
        (root / batch['units_path']).unlink()
    witness = Containers(root, harvest).select(selector('prose_block', owner='0000'))
    write(root / 'config/source-terms.json', dict(schema_version=1, source_commit=source,
        nonmathematical_declarations={}, terms=[dict(id='category', forms=['category'],
        chapters=[], evidence=[dict(kind='locked-source-container', chapter='test',
            source_commit=source, selector=witness['selector'],
            fragment_hash=witness['location']['fragment_hash'], source_term='category')])]))
    if old_origin:
        for name in ['source-adoption-input.schema.json', 'source-adoption.schema.json']:
            path = root / 'schema' / name
            value = json.loads(path.read_text())
            value['properties']['tool_version']['enum'] = [v for v in
                value['properties']['tool_version']['enum'] if not v.endswith('-v4')]
            write(path, value)
    git(root, 'add', '--', *POLICIES)
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic policy origin; no translation adopted')
    origin = git(root, 'rev-parse', 'HEAD')
    native = Containers(root, harvest)
    selected = native.select(dict(file='test.tex', owner_tag='000Z',
        owner_label='test-section-phantom', parent_tag='000Z', kind='title_title', ordinal=1))
    unit = lower_container(selected, native.policy)[0]
    up = 'translation-data/units/test-header.jsonl'
    cp = 'translation-data/candidates/synthetic/test-header.jsonl'
    write_jsonl(root / up, [unit])
    contexts = []
    for row in native.document('test')[1]:
        value = dict(kind='locked-English-neighbor', location=row['location'], source_commit=source,
            source_unit=row['unit'], owner_tag=row['owner_tag'], parent_tag=row['parent_tag'])
        contexts.append(dict(context_id=row['unit']['unit_id'], value=value, hash=sha256_value(value)))
    batch = dict(units_path=up, candidates_path=cp, units=[unit],
        containers=[dict(selector=selected['selector'], selected=selected, unit_ids=[unit['unit_id']])],
        prior_attempts=[])
    scope_path = root / frozen['task']['scope_manifest']
    scope = json.loads(scope_path.read_text())
    scope['source_commit'] = source
    scope['allowed_write_files'] += [up, cp]
    child = scope['data_scopes'][0]
    child.update(parent_tags=['000Z'], unit_ids=[unit['unit_id']], input_unit_ids=[],
                 output_unit_ids=[unit['unit_id']])
    child['allowed_write_files'] += [up, cp]
    write(scope_path, scope)
    frozen.update(tool_version=version, origin_commit=origin, source_commit=source,
        unit_ids=[unit['unit_id']], parent_tags=['000Z'], contexts=contexts, batches=[batch],
        policies=[dict(path=name, hash=byte_hash((root / name).read_bytes())) for name in POLICIES])
    frozen['task'].update(scope_manifest_sha256=byte_hash(scope_path.read_bytes()),
                          scope_bytes=scope_path.read_text())
    write(fp, frozen)
    write_jsonl(rp, [dict(unit_id=unit['unit_id'], translation='合成章标题', allowed_english=[],
        term_occurrences=[], unknown_terms=[], notes=['Synthetic fixture; no model output.'])])
    return root, harvest, fp, rp, frozen, unit


class BoundedConditionTests(unittest.TestCase):
    def test_independent_literal_expected_slots_in_all_three_positions(self):
        rules = Policy(policy_text()).math_text_rules
        for source, expected in [(ROOT_CONDITION, [' is smooth', ' is smooth']),
                                 (MATRIX_CONDITION, [' is compact'] * 3),
                                 (SET_CONDITION, [' unit', ' arbitrary']),
                                 (SET_CONDITION.replace('$$', '$$H=', 1), [' unit', ' arbitrary']),
                                 (HYPHEN, ['-equivariant modules on '])]:
            with self.subTest(source=source):
                self.assertEqual([slot['value'] for slot in find_slots(source, rules)], expected)

    def test_nested_ungrouped_commands_scripts_fake_frames_and_columns_are_not_new_roles(self):
        rules = Policy(policy_text()).math_text_rules
        cases = [
            r'$x_\text{ is smooth}$', r'$\frac x\text{ is smooth}$',
            r'$\foo x\text{ is smooth}$', r'$\mathrm\text{ is smooth}$',
            r'$x^{y\text{ is smooth}}$', r'$\text{ is smooth}$',
            r'$x\text{ is smooth}+y$', r'$x\text{ is smooth}\Leftrightarrow$',
            r'$\begin{matrix}\text{ unit}\\\end{matrix}$',
            r'$\begin{matrix}x&\text{ unit}\\\end{matrix}$',
            r'$\begin{matrix}x\text{ unit}&y\end{matrix}$',
            r'$\foo\begin{matrix}x\text{ unit}\end{matrix}$',
            r'$\begin{unknown}\begin{matrix}x\text{ unit}\end{matrix}\end{unknown}$',
            r'$x^{\begin{matrix}x\text{ unit}\end{matrix}}$',
            SET_CONDITION.replace(r'\middle|', '|'),
            SET_CONDITION.replace(r'\right\}', r'\right)'),
            SET_CONDITION.replace('$$', '$$HX=', 1),
            SET_CONDITION.replace('$$', '$$H+X=', 1),
            HYPHEN.replace('H\\text', 'H \\text'), HYPHEN.replace('}W', '}w'),
            HYPHEN.replace('}W', '} W'), HYPHEN.replace('-equivariant', 'equivariant'),
            r'$\url{H\text{-equivariant modules on }W}$',
            r'$\verb|H\text{-equivariant modules on }W|$',
            '$x % \\text{ is smooth}\n y$',
        ]
        for source in cases:
            with self.subTest(source=source):
                try:
                    slots = find_slots(source, rules)
                except ValueError:
                    slots = []
                self.assertEqual(slots, [])

    def test_old_roles_still_reject_terminal_matrix_and_hyphen_source_forms(self):
        old_rules = Policy(BASE_POLICY + '''
translatable_math_text:
  old-root:
    literal: " is smooth"
    command: "text"
    usage: "root-phrase"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
''').math_text_rules
        self.assertEqual(find_slots(r'$x\text{ is smooth}$', old_rules), [])
        with self.assertRaises(RecordError):
            Policy(policy_text().replace('usage: "root-hyphen-phrase"', 'usage: "root-phrase"'))

    def test_complete_git_lowering_regions_and_all_embedded_schemas_agree(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, unit, proof = math_fixture(Path(temp))
            self.assertEqual(unit['schema_version'], 2)
            self.assertEqual(source_tex(unit), proof)
            self.assertEqual(validate_named_schema(unit, 'unit.schema.json', 'synthetic'), [])
            self.assertEqual(validate_regions(unit), [])
            self.assertEqual(validate_translation(unit, unit['source_text']), [])
            for kind in ['math-text-regions.schema.json', 'math-text-components.schema.json']:
                self.assertEqual(validate_named_schema(unit['math_text_regions'], kind, 'synthetic'), [])

    def test_actual_translation_preserves_new_conditions_math_and_hyphen(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, unit, _ = math_fixture(Path(temp))
            target = (unit['source_text'].replace(' is smooth', '为光滑（smooth）')
                .replace(' is compact', '为紧的（compact）').replace(' unit', '为单位（unit）')
                .replace(' arbitrary', '任意（arbitrary）')
                .replace('-equivariant modules on ', '-等变（equivariant）模（modules）定义于 '))
            self.assertEqual(validate_translation(unit, target), [])
            self.assertTrue(validate_translation(unit, target.replace('-等变', '等变')))
            self.assertTrue(validate_translation(unit, target.replace('-等变', '--等变')))
            self.assertTrue(validate_translation(unit, target.replace('-等变', r'-\alpha')))
            changed = copy.deepcopy(unit)
            first = next(iter(changed['placeholders']))
            changed['placeholders'][first] += 'x'
            self.assertTrue(validate_regions(changed))


class ChapterHeaderAdoptionTests(unittest.TestCase):
    def test_new_public_header_adoption_replays_the_complete_header_and_five_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, unit = header_fixture(Path(temp))
            self.assertEqual(unit['parent_tag'], '000Z')
            self.assertIn(r'\label{section-phantom}', source_tex(unit))
            record = assemble_source_adoption(root, fp, [rp], harvest)
            self.assertEqual(record['tool_version'], 'source-adoption-v4')
            self.assertEqual(record['parent_tags'], ['000Z'])
            adopted, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(len(adopted), 1)
            self.assertEqual(next(iter(adopted.values()))['candidate']['translation'], '合成章标题')
            batch = frozen['batches'][0]
            render_batch(root / batch['units_path'], root / batch['candidates_path'],
                root / 'upstream.lock', root / 'preview', 'synthetic', 'Synthetic fixture',
                chapter_source_dir=harvest, tags_path=harvest / 'tags/tags')
            self.assertIn(r'\chapter{合成章标题}', (root / 'preview/chapters/test.tex').read_text())

    def test_earlier_input_versions_still_reject_header_parent(self):
        for version in ['source-adoption-input-v1', 'source-adoption-input-v2', 'source-adoption-input-v3']:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = header_fixture(Path(temp), version=version)
                if version.endswith('-v2'):
                    frozen['prior_adoptions'] = []
                elif version.endswith('-v3'):
                    frozen['shared_run_histories'] = []
                write(fp, frozen)
                with self.assertRaisesRegex(RecordError, 'actual Section parent'):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions/synthetic-first.json').exists())

    def test_v4_cannot_claim_an_origin_that_did_not_have_the_header_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, _, _ = header_fixture(Path(temp), old_origin=True)
            with self.assertRaisesRegex(RecordError, 'origin does not permit'):
                assemble_source_adoption(root, fp, [rp], harvest)

    def test_v4_rejects_normal_section_packages_and_any_generation_ancestry(self):
        for kind in ['section', 'prior-attempts', 'prior-adoptions', 'shared']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                if kind == 'section':
                    root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp), typed=False)
                else:
                    root, harvest, fp, rp, frozen, _ = header_fixture(Path(temp))
                frozen['tool_version'] = 'source-adoption-input-v4'
                if kind == 'prior-attempts':
                    frozen['batches'][0]['prior_attempts'] = [{}]
                elif kind == 'prior-adoptions':
                    frozen['prior_adoptions'] = None
                elif kind == 'shared':
                    frozen['shared_run_histories'] = None
                write(fp, frozen)
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/runs/run-synthetic-first.json').exists())

    def test_header_parent_selector_full_source_and_raw_drift_fail_without_outputs(self):
        for fault in ['parent', 'selector', 'source', 'raw']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = header_fixture(Path(temp))
                if fault == 'parent':
                    frozen['batches'][0]['units'][0]['parent_tag'] = '0000'
                elif fault == 'selector':
                    frozen['batches'][0]['containers'][0]['selector']['ordinal'] = 2
                elif fault == 'source':
                    frozen['batches'][0]['containers'][0]['selected']['fragment'] += '\n'
                else:
                    rp.write_text('{"unit_id":"wrong"}\n')
                write(fp, frozen)
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions/synthetic-first.json').exists())
                self.assertFalse((root / 'translation-data/candidates/synthetic/test-header.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
