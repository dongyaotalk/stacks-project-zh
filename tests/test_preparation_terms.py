"""Synthetic original inventories; no real model or accepted generation."""
import ast
import copy
import hashlib
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_adoptions import synthetic_fixture, write
from test_source_containers import git
from test_source_terms import unit, catalog
from stacks_zh import preparation_terms as original, source_terms
from stacks_zh.current_qa import InputSnapshot
from stacks_zh.records import write_jsonl


def fixture(base):
    root, harvest, fp, rp, frozen, raw = synthetic_fixture(base)
    text = inspect.getsource(source_terms)
    node = next(n for n in ast.parse(text).body
                if isinstance(n, ast.FunctionDef) and n.name == '_qualified_declaration_parts')
    old = inspect.getsource(original._qualified_declaration_parts).rstrip('\n')
    text = text.replace(ast.get_source_segment(text, node), old, 1)
    path = root / 'stacks_zh/source_terms.py'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    git(root, 'add', 'stacks_zh/source_terms.py')
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=test@example.invalid',
        'commit', '-qm', 'Synthetic recognized reader; no model generation')
    frozen['origin_commit'] = git(root, 'rev-parse', 'HEAD')
    git(root, 'update-ref', 'refs/heads/main', frozen['origin_commit'])
    return root, frozen, path


def records(rows, words):
    # Independent full current inventory reader with just the static old
    # declaration recognizer. Never alter production candidates or records.
    with patch.object(source_terms, '_qualified_declaration_parts', original._qualified_declaration_parts):
        return [source_terms.source_inventory(row, words) for row in rows]


def samples():
    phrases = ['category <MATH_0001> of formal objects of <MATH_0002>',
               'tangent space of <MATH_0001> at <MATH_0002>',
               'lift of <MATH_0001> along <MATH_0002>',
               'morphism <MATH_0001> of groupoids in functors on <MATH_0002>',
               'presentation of <MATH_0001> by <MATH_0002>']
    rows = []
    for index, phrase in enumerate(phrases):
        row = unit('A <TEXTITOPEN_0003>' + phrase + '<TEXTITCLOSE_0003>.',
                   {'MATH_0001': '$x$', 'MATH_0002': '$y$',
                    'TEXTITOPEN_0003': '{\\it ', 'TEXTITCLOSE_0003': '}'})
        row['unit_id'] = 'fixture:term-' + str(index)
        rows.append(row)
    words = catalog(rows[0]); words['terms'] = []
    return rows, words


class PreparationTermInventoryTests(unittest.TestCase):
    def test_complete_original_inventory_and_bytes_without_generation_authority(self):
        with tempfile.TemporaryDirectory() as d:
            root, frozen, path = fixture(Path(d))
            rows, words = samples(); old = records(rows, words)
            self.assertNotEqual(old, [source_terms.source_inventory(row, words) for row in rows])
            immutable = copy.deepcopy((frozen, rows, words, old))
            before = path.read_bytes()
            for version in ('source-adoption-input-v1', 'source-adoption-input-v4'):
                frozen['tool_version'] = version
                result = original.original_inventory(root, frozen, rows, words, old, InputSnapshot(root))
                self.assertEqual(result['generation_validation'], 'not_claimed')
                self.assertEqual(result['origin_commit'], frozen['origin_commit'])
            frozen['tool_version'] = immutable[0]['tool_version']
            self.assertEqual((frozen, rows, words, old), immutable)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((root / f"translation-data/runs/{frozen['run_id']}.json").exists())

    def test_original_helper_is_the_exact_reviewed_static_function(self):
        text = inspect.getsource(original._qualified_declaration_parts).rstrip('\n')
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), original.KNOWN_QUALIFIED_SHA256)

    def test_every_inventory_field_and_complete_unit_coverage_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root, frozen, path = fixture(Path(d)); rows, words = samples()
            old = records(rows, words)
            variants = [old[:-1], old[::-1]]
            for key, value in [('source_text_hash', 'sha256:' + '0' * 64),
                               ('source_structure_hash', 'sha256:' + '0' * 64),
                               ('catalog_hash', 'sha256:' + '0' * 64),
                               ('unit_id', 'fixture:wrong'), ('source_commit', '0' * 40),
                               ('occurrences', [])]:
                value_copy = copy.deepcopy(old); value_copy[0][key] = value; variants.append(value_copy)
            value_copy = copy.deepcopy(old)
            value_copy[0]['occurrences'][0]['projection_start'] += 1; variants.append(value_copy)
            for observed in variants:
                self.assertIsNone(original.original_inventory(root, frozen, rows, words, observed, InputSnapshot(root)))

    def test_installed_or_predecessor_identity_and_unaccepted_origin_are_rejected(self):
        for mutation in ('run', 'adoption', 'candidate-run', 'candidate-adoption',
                         'prior', 'shared', 'attempt', 'v2', 'origin'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as d:
                root, frozen, path = fixture(Path(d)); rows, words = samples()
                old = records(rows, words)
                if mutation == 'run': write(root / f"translation-data/runs/{frozen['run_id']}.json", {})
                elif mutation == 'adoption': write(root / f"translation-data/source-adoptions/{frozen['adoption_id']}.json", {})
                elif mutation.startswith('candidate'):
                    key = 'run_id' if mutation == 'candidate-run' else 'source_adoption_id'
                    value = frozen['run_id'] if key == 'run_id' else frozen['adoption_id']
                    write_jsonl(root / frozen['batches'][0]['candidates_path'], [{key: value}])
                elif mutation == 'prior': frozen['prior_adoptions'] = []
                elif mutation == 'shared': frozen['shared_run_histories'] = []
                elif mutation == 'attempt': frozen['batches'][0]['prior_attempts'] = [{}]
                elif mutation == 'v2': frozen['tool_version'] = 'source-adoption-input-v2'
                else: frozen['origin_commit'] = '0' * 40
                self.assertIsNone(original.original_inventory(root, frozen, rows, words, old, InputSnapshot(root)))

    def test_duplicate_function_definitions_cannot_supply_a_known_reader(self):
        text = inspect.getsource(source_terms)
        self.assertEqual(original._functions(text + '\n' + inspect.getsource(source_terms.source_inventory)), {})

    def test_unknown_helper_or_any_other_inventory_algorithm_change_is_rejected(self):
        for name in ('_qualified_declaration_parts', *original.UNCHANGED_READERS):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                root, frozen, path = fixture(Path(d)); rows, words = samples()
                old = records(rows, words); text = path.read_text()
                node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
                segment = ast.get_source_segment(text, node)
                lines = segment.splitlines(); lines.insert(1, '    pass  # unrecognized synthetic original')
                path.write_text(text.replace(segment, '\n'.join(lines), 1))
                git(root, 'add', 'stacks_zh/source_terms.py')
                git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'Synthetic unrecognized original')
                frozen['origin_commit'] = git(root, 'rev-parse', 'HEAD')
                git(root, 'update-ref', 'refs/heads/main', frozen['origin_commit'])
                self.assertIsNone(original.original_inventory(root, frozen, rows, words, old, InputSnapshot(root)))


if __name__ == '__main__':
    unittest.main()
