"""Synthetic pre-Git records; real current validator, no model or review data."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_chapter_validation import fixture, preparation_copy
from test_source_adoptions import write
from stacks_zh.chapter_validation import check_chapter
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_adoptions import assemble_source_adoption
from stacks_zh.source_reextractions import byte_hash


def inventory_fixture(folder, *, late=False, mutation=None):
    root, harvest, base, fp, rp, frozen = fixture(folder)
    aid = frozen['adoption_id']
    record = root/'translation-data/source-adoptions'/f'{aid}.json'
    run = root/'translation-data/runs'/f'run-{aid}.json'
    for path in (record, run, *(root/b['candidates_path'] for b in frozen['batches'])):
        path.unlink()
    earlier = root/'docs/evidence'/f'{aid}-discarded-raw.jsonl'
    scope = json.loads(frozen['task']['scope_bytes'])
    relative = earlier.relative_to(root).as_posix()
    scope['allowed_write_files'].append(relative)
    scope['data_scopes'][0]['allowed_write_files'].append(relative)
    sp = root/frozen['task']['scope_manifest']
    write(sp, scope)
    frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
    mp, rt = preparation_copy(root, frozen, fp, rp)
    rows = [json.loads(line) for line in rp.read_text().splitlines()]
    discarded = copy.deepcopy(rows)
    discarded[0]['translation'] = '<MATH_9999>'+discarded[0]['translation']
    if mutation=='foreign':
        discarded[0]['unit_id'] = 'tag:FFFF:foreign'
    if mutation=='schema':
        del discarded[0]['notes']
    write_jsonl(earlier, discarded)
    model = json.loads(mp.read_text())
    ordered = [rp, earlier] if late else [earlier, rp]
    model['raw_output_paths_reserved'] = [p.relative_to(root).as_posix() for p in ordered]
    write(mp, model)
    assemble_source_adoption(root, fp, [rp], harvest)
    return root, harvest, base, fp, rp, earlier, mp, rt, record, run


class UnselectedRawInventoryTests(unittest.TestCase):
    def test_earlier_rejected_raw_is_read_without_rewriting_installed_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, base, fp, rp, earlier, mp, rt, record, run = inventory_fixture(Path(directory))
            tracked = [fp, rp, earlier, mp, rt, record, run]
            tracked += list((root/'translation-data/candidates/synthetic').glob('*.jsonl'))
            before = {p:p.read_bytes() for p in tracked}
            result = check_chapter(root, harvest, 'test', 'synthetic', base)
            detail = result.report['preparations'][0]['unselected_raw_attempts']
            self.assertEqual([v['path'] for v in detail], [earlier.relative_to(root).as_posix()])
            self.assertEqual(detail[0]['hash'], byte_hash(before[earlier]))
            self.assertEqual(detail[0]['generation_validation'], 'not_claimed')
            self.assertEqual(before, {p:p.read_bytes() for p in before})
            self.assertEqual([v['path'] for v in json.loads(record.read_bytes())['raw_attempts']],
                [rp.relative_to(root).as_posix()])

    def test_foreign_units_schema_errors_and_later_outputs_remain_blocked(self):
        for mutation, late in [('foreign',False),('schema',False),(None,True)]:
            with self.subTest(mutation=mutation,late=late), tempfile.TemporaryDirectory() as directory:
                root, harvest, base, *_ = inventory_fixture(Path(directory),late=late,mutation=mutation)
                with self.assertRaises(RecordError):
                    check_chapter(root, harvest, 'test', 'synthetic', base)


if __name__=='__main__':
    unittest.main()
