from __future__ import annotations

import json
import copy
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from stacks_zh.pr_contract import ContractApiError, fetch_pr_contract, validate_pr_contract, _batch_blob_contents


REPOSITORY = "example/stacks-project-zh"
SOURCE_COMMIT = "a" * 40
UNIT_PATH = "translation-data/units/guide-04V1.jsonl"
UNIT_ID = "tag:04V1:title"
SECOND_UNIT_PATH = "translation-data/units/guide-04V2.jsonl"
SECOND_UNIT_ID = "tag:04V2:title"


def issue_body(*, branch: str = "tool/scope/guide-04v1/model") -> str:
    return f"""\
task_id: guide-04V1-scope
owner: @contributor
branch: {branch}
allowed_write_files:
- {UNIT_PATH}
source_commit: {SOURCE_COMMIT}
chapter: guide
parent_tag: 04V1
unit_ids:
- {UNIT_ID}
"""


def batch_issue_body(
    *,
    parent_tags: list[str] | None = None,
    unit_ids: list[str] | None = None,
    include_parent_tag: bool = False,
) -> str:
    parent_tags = parent_tags or ["04V1", "04V2"]
    unit_ids = unit_ids or [UNIT_ID, SECOND_UNIT_ID]
    single = "parent_tag: 04V1\n" if include_parent_tag else ""
    return f"""\
task_id: guide-batch-scope
owner: @contributor
branch: tool/scope/guide-04v1/model
allowed_write_files:
- {UNIT_PATH}
- {SECOND_UNIT_PATH}
source_commit: {SOURCE_COMMIT}
chapter: guide
{single}parent_tags:
{chr(10).join(f'- {tag}' for tag in parent_tags)}
unit_ids:
{chr(10).join(f'- {unit_id}' for unit_id in unit_ids)}
"""


def payload(*, issues: list[dict] | None = None) -> dict:
    if issues is None:
        issues = [
            {
                "number": 42,
                "state": "OPEN",
                "createdAt": "2026-08-29T01:00:00Z",
                "body": issue_body(),
                "repository": {"nameWithOwner": REPOSITORY},
                "labels": {"nodes": [{"name": "claimed"}]},
            }
        ]
    return {
        "number": 99,
        "body": f"Closes #42\n\nTask: guide-04V1-scope\nSource: {SOURCE_COMMIT}",
        "createdAt": "2026-08-29T02:00:00Z",
        "headRefName": "tool/scope/guide-04v1/model",
        "headRefOid": "b" * 40,
        "baseRefOid": "c" * 40,
        "author": {"login": "contributor"},
        "headRepository": {"nameWithOwner": REPOSITORY},
        "baseRepository": {"nameWithOwner": REPOSITORY},
        "closingIssuesReferences": {
            "nodes": issues,
            "pageInfo": {"hasNextPage": False},
        },
        "files": {
            "nodes": [{"path": UNIT_PATH, "changeType": "ADDED"}],
            "pageInfo": {"hasNextPage": False},
        },
    }


def unit_content(unit_id: str = UNIT_ID) -> str:
    return json.dumps(
        {
            "unit_id": unit_id,
            "source_commit": SOURCE_COMMIT,
            "chapter": "guide",
            "parent_tag": "04V1",
        }
    )


class PrContractTests(unittest.TestCase):
    def _large_fetch(self, *, deleted=False, mutate_metadata=None, mutate_blob=None,
                     raw=None, unavailable=False):
        value = payload()
        value['headRepository']['nameWithOwner'] = 'fork/contributor'
        if deleted:
            value['files']['nodes'][0]['changeType'] = 'DELETED'
        if raw is None:
            raw = (unit_content() + '\n' + json.dumps(
                {'text': '中文' * 180_000}, ensure_ascii=False) + '\n').encode('utf-8')
        sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        metadata = {'type': 'file', 'encoding': 'none', 'content': '', 'size': len(raw),
                    'sha': sha, 'git_url': 'https://unrelated.invalid/never-follow-this'}
        blob = {'encoding': 'base64', 'content': base64.encodebytes(raw).decode('ascii'),
                'size': len(raw), 'sha': sha}
        if mutate_metadata:
            mutate_metadata(metadata)
        if mutate_blob:
            mutate_blob(blob)
        calls = []
        def request(url, token, *, data=None):
            calls.append((url, token, data))
            if data is not None:
                return {'data': {'repository': {'pullRequest': value}}}
            if '/contents/' in url:
                return metadata
            if unavailable:
                raise ContractApiError('blob unavailable')
            return blob
        _, contents = fetch_pr_contract(
            REPOSITORY, 99, 'test-token', api_url='https://api.example.test',
            graphql_url='https://api.example.test/graphql', request_json=request)
        return raw, sha, contents, calls

    def test_fetches_large_utf8_jsonl_from_pinned_head_blob(self):
        raw, sha, contents, calls = self._large_fetch()
        self.assertGreater(len(raw), 1024 * 1024)
        self.assertEqual(contents[UNIT_PATH].encode('utf-8'), raw)
        self.assertIn('/repos/fork/contributor/contents/', calls[1][0])
        self.assertIn('ref=' + 'b' * 40, calls[1][0])
        self.assertEqual(calls[2][:2], (
            'https://api.example.test/repos/fork/contributor/git/blobs/' + sha, 'test-token'))
        self.assertEqual(len(calls), 3)

    def test_fetches_deleted_large_file_from_base_repository_blob(self):
        raw, sha, contents, calls = self._large_fetch(deleted=True)
        self.assertEqual(contents[UNIT_PATH].encode(), raw)
        self.assertIn('/repos/' + REPOSITORY + '/contents/', calls[1][0])
        self.assertIn('ref=' + 'c' * 40, calls[1][0])
        self.assertEqual(calls[2][0], 'https://api.example.test/repos/' + REPOSITORY + '/git/blobs/' + sha)

    def test_rejects_invalid_large_file_metadata(self):
        for field, value in [('type', 'symlink'), ('content', 'unexpected'), ('size', 1_000_000),
                             ('size', 100 * 1024 * 1024 + 1), ('size', True), ('size', '1061688'),
                             ('sha', '../moving-ref'), ('sha', 'g' * 40)]:
            with self.subTest(field=field, value=value), self.assertRaises(ContractApiError):
                self._large_fetch(mutate_metadata=lambda m: m.update({field: value}))

    def test_rejects_blob_identity_size_encoding_and_corrupt_bytes(self):
        for field, value in [('sha', 'd' * 40), ('size', 1), ('encoding', 'utf-8'),
                             ('content', 'not base64!'), ('content', None), ('content', '')]:
            with self.subTest(field=field), self.assertRaises(ContractApiError):
                self._large_fetch(mutate_blob=lambda b: b.update({field: value}))
        with self.assertRaisesRegex(ContractApiError, 'bytes do not match'):
            self._large_fetch(mutate_blob=lambda b: b.update(
                content=base64.b64encode(b'x' * b['size']).decode()))

    def test_rejects_valid_git_blob_with_non_utf8_text(self):
        with self.assertRaisesRegex(ContractApiError, 'cannot decode changed file'):
            self._large_fetch(raw=b'\xff' * 1_080_000)

    def test_propagates_unavailable_large_blob(self):
        with self.assertRaisesRegex(ContractApiError, 'blob unavailable'):
            self._large_fetch(unavailable=True)

    def test_grouped_scope_checks_all_new_coordinates_and_only_linked_old_parents(self):
        from test_group_derivations import fixture, read
        with tempfile.TemporaryDirectory() as tmp:
            root, _, records = fixture(Path(tmp))
            record = records[0]
            derivation_path = 'translation-data/derivations/' + record['derivation_id'] + '.json'
            retired_path = record['files']['input_units']['path']
            active_path = record['files']['output_units']['path']
            old = {'unit_id':record['unit_groups'][2]['input_unit_ids'][-1],
                   'chapter':'test', 'parent_tag':'0999', 'source_commit':record['source_commit']}
            active = record['unit_groups'][2]['output_units'][0]
            objects = {derivation_path:record, retired_path:old, active_path:active}
            paths = list(objects)
            all_ids = {identifier for group in record['unit_groups']
                       for identifier in group['input_unit_ids'] + group['output_unit_ids']}
            value = payload()
            value['files']['nodes'] = [{'path':path, 'changeType':'ADDED'} for path in paths]
            body = ('task_id: guide-04V1-scope\nowner: @contributor\nbranch: tool/scope/guide-04v1/model\n'
                    'allowed_write_files:\n' + ''.join('- ' + path + '\n' for path in paths) +
                    'source_commit: ' + record['source_commit'] + '\nchapter: test\nparent_tag: 0000\n'
                    'historical_parent_tags:\n- 0999\nunit_ids:\n' + ''.join('- ' + i + '\n' for i in sorted(all_ids)))
            value['closingIssuesReferences']['nodes'][0]['body'] = body
            value['body'] = 'Closes #42\nguide-04V1-scope\n' + record['source_commit']
            encode = lambda rows: {path:json.dumps(row) for path,row in rows.items()}
            self.assertEqual(validate_pr_contract(REPOSITORY, value, encode(objects)), [])
            for fault in ['current-parent', 'nested-parent', 'nested-chapter', 'hidden-old-id', 'unlinked-snapshot', 'legacy']:
                broken, pr = copy.deepcopy(objects), copy.deepcopy(value)
                if fault == 'current-parent':
                    broken[active_path]['parent_tag'] = '0999'
                elif fault == 'nested-parent':
                    broken[derivation_path]['unit_groups'][1]['output_units'][0]['parent_tag'] = '0999'
                elif fault == 'nested-chapter':
                    broken[derivation_path]['unit_groups'][1]['output_units'][0]['chapter'] = 'other'
                elif fault == 'hidden-old-id':
                    broken[derivation_path]['unit_groups'][2]['input_unit_ids'][1] = 'tag:UNDECLARED:proof'
                elif fault == 'unlinked-snapshot':
                    unrelated = 'translation-data/retired/derivations/unrelated/units.jsonl'
                    broken[unrelated] = old
                    pr['files']['nodes'].append({'path':unrelated, 'changeType':'ADDED'})
                    pr['closingIssuesReferences']['nodes'][0]['body'] = body.replace('allowed_write_files:\n', 'allowed_write_files:\n- ' + unrelated + '\n')
                else:
                    broken[derivation_path]['tool']['version'] = '3'
                with self.subTest(fault=fault):
                    self.assertTrue(validate_pr_contract(REPOSITORY, pr, encode(broken)))

    def test_pre_adoption_managed_history_requires_declared_scope_and_linked_parent(self):
        from test_pre_adoption_replays import two_runs
        with tempfile.TemporaryDirectory() as tmp:
            root, _, current, manifest = two_runs(Path(tmp))
            manifest_path = 'translation-data/pre-adoption-replays/' + manifest['replay_id'] + '.json'
            derivation_path = 'translation-data/derivations/' + current['derivation_id'] + '.json'
            candidate_path = manifest['files']['candidates']['path']
            old = {'unit_id':manifest['output_unit_ids'][0], 'source_commit':current['source_commit'],
                   'chapter':'test', 'parent_tag':'0999'}
            objects = {manifest_path:manifest, derivation_path:current, candidate_path:old}
            value = payload()
            value['files']['nodes'] = [{'path':p,'changeType':'ADDED'} for p in objects]
            ids = {uid for group in current['unit_groups'] for uid in group['input_unit_ids'] + group['output_unit_ids']}
            body = ('task_id: guide-04V1-scope\nowner: @contributor\nbranch: tool/scope/guide-04v1/model\n'
                    'allowed_write_files:\n' + ''.join('- ' + p + '\n' for p in objects) +
                    'source_commit: ' + current['source_commit'] + '\nchapter: test\nparent_tag: 0000\n'
                    'historical_parent_tags:\n- 0999\nunit_ids:\n' + ''.join('- ' + uid + '\n' for uid in sorted(ids)))
            value['closingIssuesReferences']['nodes'][0]['body'] = body
            value['body'] = 'Closes #42\nguide-04V1-scope\n' + current['source_commit']
            encode = lambda rows: {p:json.dumps(r) for p,r in rows.items()}
            self.assertEqual(validate_pr_contract(REPOSITORY,value,encode(objects)), [])
            for fault in ['unlinked','bad-schema','extra-unit','wrong-source','undeclared-path']:
                broken, pr = copy.deepcopy(objects), copy.deepcopy(value)
                if fault == 'unlinked':
                    broken[manifest_path]['current_derivation_id'] = 'unrelated'
                elif fault == 'bad-schema':
                    broken[manifest_path]['tool_version'] = 'unsupported'
                elif fault == 'extra-unit':
                    broken[candidate_path]['unit_id'] = 'tag:UNDECLARED:p001'
                elif fault == 'wrong-source':
                    broken[candidate_path]['source_commit'] = 'd' * 40
                else:
                    pr['closingIssuesReferences']['nodes'][0]['body'] = body.replace('- ' + manifest_path + '\n','')
                with self.subTest(fault=fault):
                    self.assertTrue(validate_pr_contract(REPOSITORY,pr,encode(broken)))

    def test_accepts_matching_issue_branch_path_and_unit(self) -> None:
        errors = validate_pr_contract(
            REPOSITORY,
            payload(),
            {UNIT_PATH: unit_content()},
        )
        self.assertEqual(errors, [])

    def test_rejects_missing_closing_issue(self) -> None:
        errors = validate_pr_contract(REPOSITORY, payload(issues=[]), {})
        self.assertIn("exactly one task Issue", errors[0])

    def test_rejects_closed_issue(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["state"] = "CLOSED"
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("must be OPEN" in error for error in errors))

    def test_rejects_multiple_closing_issues(self) -> None:
        value = payload()
        issue = dict(value["closingIssuesReferences"]["nodes"][0])
        issue["number"] = 43
        value["closingIssuesReferences"]["nodes"].append(issue)
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertIn("exactly one task Issue", errors[0])

    def test_rejects_unclaimed_issue(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["labels"] = {"nodes": []}
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("claimed label" in error for error in errors))

    def test_rejects_issue_created_after_pr(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["createdAt"] = (
            "2026-08-29T03:00:00Z"
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("created after the PR" in error for error in errors))

    def test_rejects_branch_mismatch(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = issue_body(
            branch="tool/scope/wrong"
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("does not match PR head" in error for error in errors))

    def test_rejects_changed_path_outside_issue_scope(self) -> None:
        value = payload()
        value["files"]["nodes"].append(
            {"path": "config/glossary.yml", "changeType": "MODIFIED"}
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertIn("changed path is outside Issue scope: config/glossary.yml", errors)

    def test_rejects_unit_outside_issue_scope(self) -> None:
        errors = validate_pr_contract(
            REPOSITORY,
            payload(),
            {UNIT_PATH: unit_content("tag:04V1:p001")},
        )
        self.assertIn(
            "changed structured record is outside Issue unit_ids: tag:04V1:p001",
            errors,
        )

    def test_rejects_unavailable_structured_content(self) -> None:
        errors = validate_pr_contract(REPOSITORY, payload(), {})
        self.assertIn(
            f"cannot verify changed structured file content: {UNIT_PATH}",
            errors,
        )

    def test_accepts_multi_tag_batch_issue(self) -> None:
        value = payload()
        value["body"] = (
            f"Closes #42\n\nTask: guide-batch-scope\nSource: {SOURCE_COMMIT}"
        )
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body()
        value["files"]["nodes"].append(
            {"path": SECOND_UNIT_PATH, "changeType": "ADDED"}
        )
        errors = validate_pr_contract(
            REPOSITORY,
            value,
            {
                UNIT_PATH: unit_content(),
                SECOND_UNIT_PATH: json.dumps(
                    {
                        "unit_id": SECOND_UNIT_ID,
                        "source_commit": SOURCE_COMMIT,
                        "chapter": "guide",
                        "parent_tag": "04V2",
                    }
                ),
            },
        )
        self.assertEqual(errors, [])

    def test_accepts_nested_unit_tag_with_batch_parent_tag(self) -> None:
        value = payload()
        value["body"] = (
            f"Closes #42\n\nTask: guide-batch-scope\nSource: {SOURCE_COMMIT}"
        )
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            unit_ids=["tag:04AT:statement"]
        )
        errors = validate_pr_contract(
            REPOSITORY,
            value,
            {
                UNIT_PATH: json.dumps(
                    {
                        "unit_id": "tag:04AT:statement",
                        "source_commit": SOURCE_COMMIT,
                        "chapter": "guide",
                        "parent_tag": "04V1",
                    }
                )
            },
        )
        self.assertEqual(errors, [])

    def test_rejects_both_parent_tag_forms(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            include_parent_tag=True
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("not both" in error for error in errors))

    def test_rejects_batch_with_fewer_than_two_tags(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            parent_tags=["04V1"], unit_ids=[UNIT_ID]
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("2 to 8 Tags" in error for error in errors))

    def test_rejects_batch_with_more_than_eight_tags(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            parent_tags=[f"A00{index}" for index in range(9)], unit_ids=[UNIT_ID]
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("2 to 8 Tags" in error for error in errors))

    def test_rejects_duplicate_batch_tags(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            parent_tags=["04V1", "04V1"], unit_ids=[UNIT_ID]
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("duplicates: 04V1" in error for error in errors))

    def test_rejects_invalid_batch_tag(self) -> None:
        value = payload()
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            parent_tags=["04V1", "not-a-tag"], unit_ids=[UNIT_ID]
        )
        errors = validate_pr_contract(REPOSITORY, value, {UNIT_PATH: unit_content()})
        self.assertTrue(any("invalid permanent Tags: not-a-tag" in error for error in errors))

    def test_rejects_record_outside_batch_parent_tags(self) -> None:
        value = payload()
        outside_unit_id = "tag:04V3:title"
        value["closingIssuesReferences"]["nodes"][0]["body"] = batch_issue_body(
            unit_ids=[UNIT_ID, outside_unit_id]
        )
        errors = validate_pr_contract(
            REPOSITORY,
            value,
            {
                UNIT_PATH: json.dumps(
                    {
                        "unit_id": outside_unit_id,
                        "source_commit": SOURCE_COMMIT,
                        "chapter": "guide",
                        "parent_tag": "04V3",
                    }
                )
            },
        )
        self.assertTrue(any("parent_tag '04V3' is outside" in error for error in errors))
        self.assertFalse(any("unit_id 'tag:04V3:title' has Tag" in error for error in errors))

    def test_fetches_deleted_structured_file_from_base(self) -> None:
        value = payload()
        value["files"]["nodes"][0]["changeType"] = "DELETED"
        calls: list[tuple[str, dict | None]] = []

        def request_json(url: str, token: str, *, data: dict | None = None) -> dict:
            calls.append((url, data))
            if data is not None:
                return {"data": {"repository": {"pullRequest": value}}}
            return {
                "encoding": "base64",
                "content": "eyJ1bml0X2lkIjogInRhZzowNFYxOnRpdGxlIn0=",
            }

        _, contents = fetch_pr_contract(
            REPOSITORY,
            99,
            "token",
            api_url="https://api.example.test",
            graphql_url="https://api.example.test/graphql",
            request_json=request_json,
        )

        self.assertEqual(json.loads(contents[UNIT_PATH])["unit_id"], UNIT_ID)
        self.assertIn(f"/repos/{REPOSITORY}/contents/{UNIT_PATH}", calls[1][0])
        self.assertIn("ref=" + "c" * 40, calls[1][0])


MANIFEST_PATH = 'task-scopes/fixture-bulk.json'
SETS_PATH = 'translation-data/units/sets-0008.jsonl'


def bulk_payload(extra_files=0):
    value = payload()
    paths = [MANIFEST_PATH,UNIT_PATH,SETS_PATH]+[f'docs/fixture-{i}.md' for i in range(extra_files)]
    def scope(identifier,chapter,tag,path):
        return dict(scope_id=identifier,chapter=chapter,parent_tags=[tag],historical_parent_tags=[],
            unit_ids=['tag:'+tag+':title'],input_unit_ids=['tag:'+tag+':title'],
            output_unit_ids=['tag:'+tag+':title'],allowed_write_files=[path],run_scope=[],model_scope=[])
    manifest = dict(schema_version=1,task_id='guide-04V1-scope',owner='contributor',
        branch=value['headRefName'],source_commit=SOURCE_COMMIT,allowed_write_files=paths,
        data_scopes=[scope('guide','guide','04V1',UNIT_PATH),scope('sets','sets','0008',SETS_PATH)])
    value['files']['nodes'] = [dict(path=p,changeType='ADDED') for p in paths]
    value['changedFiles'] = len(paths)
    contents = {UNIT_PATH:unit_content(),SETS_PATH:json.dumps(dict(unit_id='tag:0008:title',
        source_commit=SOURCE_COMMIT,chapter='sets',parent_tag='0008'))}
    bind_bulk(value,contents,manifest)
    return value,contents,manifest


def bind_bulk(value,contents,manifest):
    raw = json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    digest = 'sha256:'+hashlib.sha256(raw.encode()).hexdigest()
    contents[MANIFEST_PATH] = raw
    value['closingIssuesReferences']['nodes'][0]['body'] = (
        f'task_id: guide-04V1-scope\nowner: @contributor\nbranch: {value["headRefName"]}\n'
        f'source_commit: {SOURCE_COMMIT}\nscope_manifest: {MANIFEST_PATH}\nscope_manifest_sha256: {digest}\n')
    value['body'] = f'Closes #42\nTask: guide-04V1-scope\nSource: {SOURCE_COMMIT}\n{MANIFEST_PATH}\n{digest}'


class BulkScopeContractTests(unittest.TestCase):
    def test_batched_git_blob_reads_preserve_utf8_whitespace_and_bound_requests(self):
        contents={f'translation-data/units/chapter-{i}.jsonl':'中文\r\n  \n' for i in range(26)}
        calls=[]
        def request(url,token,*,data=None):
            calls.append(data);variables=data['variables'];objects={}
            self.assertEqual((variables['owner'],variables['name']),('fork','repo'))
            for key,expression in variables.items():
                if not key.startswith('expr'):continue
                commit,path=expression.split(':',1);self.assertEqual(commit,'b'*40)
                raw=contents[path].encode()
                objects['file'+key[4:]]=dict(oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                    byteSize=len(raw),isBinary=False,isTruncated=False,text=raw.decode())
            self.assertLessEqual(len(objects),25)
            return {'data':{'repository':objects}}
        actual=_batch_blob_contents(list(contents),'fork/repo','b'*40,'synthetic-token','api','graphql',request)
        self.assertEqual(actual,contents);self.assertEqual(len(calls),2)

    def test_batched_blob_metadata_and_truncation_fallback_are_verified(self):
        raw='中文\n '.encode();sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        for fault in [None,'size','bool-size','oid','binary','flag','text','missing','errors','fallback-sha','fallback-bytes','invalid-utf8']:
            truncated=fault in {None,'fallback-sha','fallback-bytes','invalid-utf8'}
            test_raw=b'\xff' if fault=='invalid-utf8' else raw
            test_sha=hashlib.sha1(b'blob '+str(len(test_raw)).encode()+b'\0'+test_raw).hexdigest()
            calls=[]
            def request(url,token,*,data=None):
                calls.append((url,data))
                if data:
                    self.assertEqual(data['variables']['expr0'],'c'*40+':deleted.jsonl')
                    obj=dict(oid=test_sha,byteSize=len(test_raw),isBinary=False,isTruncated=truncated,text=raw.decode())
                    if fault=='size':obj['byteSize']+=1
                    if fault=='bool-size':obj['byteSize']=True
                    if fault=='oid':obj['oid']='d'*40
                    if fault=='binary':obj['isBinary']=True
                    if fault=='flag':obj['isTruncated']='false'
                    if fault=='text':obj['text']=raw.decode().strip()
                    return {'errors':['unavailable']} if fault=='errors' else {'data':{'repository':{'file0':None if fault=='missing' else obj}}}
                self.assertEqual(url,'api/repos/base/repo/git/blobs/'+test_sha)
                return dict(encoding='base64',sha='e'*40 if fault=='fallback-sha' else test_sha,size=len(test_raw),
                    content=base64.b64encode(b'changed' if fault=='fallback-bytes' else test_raw).decode())
            with self.subTest(fault=fault):
                if fault is None:
                    self.assertEqual(_batch_blob_contents(['deleted.jsonl'],'base/repo','c'*40,'t','api','graphql',request),{'deleted.jsonl':raw.decode()})
                    self.assertEqual(len(calls),2)
                else:
                    with self.assertRaises(ContractApiError):_batch_blob_contents(['deleted.jsonl'],'base/repo','c'*40,'t','api','graphql',request)

    def test_nullable_large_blob_classification_still_requires_complete_verified_utf8(self):
        raw = '中文\r\n  '.encode()
        for fault in [None, 'not-truncated', 'missing-classification', 'binary', 'hash', 'size', 'utf8']:
            payload = b'\xff' if fault == 'utf8' else raw
            sha = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
            calls = []
            def request(url, token, *, data=None):
                calls.append(url)
                if data:
                    obj = dict(oid=sha, byteSize=len(payload), isBinary=None,
                               isTruncated=fault != 'not-truncated', text=None)
                    if fault == 'missing-classification': del obj['isBinary']
                    if fault == 'binary': obj['isBinary'] = True
                    return {'data': {'repository': {'file0': obj}}}
                self.assertEqual(url, 'api/repos/base/repo/git/blobs/'+sha)
                return dict(encoding='base64', sha=sha, size=len(payload)+(fault == 'size'),
                    content=base64.b64encode(b'changed' if fault == 'hash' else payload).decode())
            with self.subTest(fault=fault):
                if fault is None:
                    self.assertEqual(_batch_blob_contents(['large.jsonl'], 'base/repo', 'c'*40,
                        'synthetic', 'api', 'graphql', request), {'large.jsonl': raw.decode()})
                    self.assertEqual(len(calls), 2)
                else:
                    with self.assertRaises(ContractApiError):
                        _batch_blob_contents(['large.jsonl'], 'base/repo', 'c'*40,
                            'synthetic', 'api', 'graphql', request)

    def test_explicit_hash_scopes_allow_many_exact_files_and_distinct_chapters(self):
        value,contents,_ = bulk_payload(105)
        self.assertGreater(len(value['files']['nodes']),100)
        self.assertEqual(validate_pr_contract(REPOSITORY,value,contents),[])

    def test_explicit_scope_keeps_all_nine_declared_parents_without_inline_limit(self):
        value,contents,m=bulk_payload();scope=m['data_scopes'][0]
        tags=['04V1',*[f'{i:04d}' for i in range(8)]]
        ids=['tag:'+tag+':title' for tag in tags]
        scope.update(parent_tags=tags,unit_ids=ids,input_unit_ids=ids,output_unit_ids=ids)
        contents[UNIT_PATH]=''.join(json.dumps(dict(unit_id=uid,source_commit=SOURCE_COMMIT,
            chapter='guide',parent_tag=tag))+'\n' for uid,tag in zip(ids,tags,strict=True))
        bind_bulk(value,contents,m)
        self.assertEqual(validate_pr_contract(REPOSITORY,value,contents),[])

    def test_all_bytes_hash_identity_and_pr_reference_are_required(self):
        for fault in ['bytes','hash','task','owner','branch','source','pr-hash','pr-path','inline','missing']:
            value,contents,manifest = bulk_payload()
            if fault in {'task','owner','branch','source'}:
                key={'task':'task_id','source':'source_commit'}.get(fault,fault)
                manifest[key]='f'*40 if key=='source_commit' else 'different'
                bind_bulk(value,contents,manifest)
            if fault=='bytes':contents[MANIFEST_PATH]+='\n'
            if fault=='hash':value['closingIssuesReferences']['nodes'][0]['body']=value['closingIssuesReferences']['nodes'][0]['body'].replace('sha256:','sha256:0')
            if fault=='pr-hash':value['body']=value['body'].split('sha256:')[0]
            if fault=='pr-path':value['body']=value['body'].replace(MANIFEST_PATH,'other.json')
            if fault=='inline':value['closingIssuesReferences']['nodes'][0]['body']+='allowed_write_files:\n- '+UNIT_PATH+'\n'
            if fault=='missing':contents.pop(MANIFEST_PATH)
            with self.subTest(fault=fault):self.assertTrue(validate_pr_contract(REPOSITORY,value,contents))

    def test_manifest_schema_paths_scope_uniqueness_and_complete_ids_are_strict(self):
        for fault in ['unknown','glob','directory','escape','absolute','duplicate-path','self','scope-id','scope-path','outside','old-id','newline']:
            value,contents,m = bulk_payload()
            if fault=='unknown':m['approved']=True
            if fault in {'glob','directory','escape','absolute'}:
                m['allowed_write_files'].append({'glob':'docs/*','directory':'docs/','escape':'../other.json','absolute':'/tmp/other.json'}[fault])
            if fault=='duplicate-path':m['allowed_write_files'].append(UNIT_PATH)
            if fault=='self':m['allowed_write_files'].remove(MANIFEST_PATH)
            if fault=='scope-id':m['data_scopes'][1]['scope_id']='guide'
            if fault=='scope-path':m['data_scopes'][1]['allowed_write_files']=[UNIT_PATH]
            if fault=='outside':m['data_scopes'][0]['allowed_write_files']=['translation-data/units/undeclared.jsonl']
            if fault=='old-id':m['data_scopes'][0]['input_unit_ids']=['tag:9999:title']
            if fault=='newline':m['data_scopes'][0]['unit_ids'].append('tag:9999:title\nparent_tag: 9999')
            bind_bulk(value,contents,m)
            with self.subTest(fault=fault):self.assertTrue(validate_pr_contract(REPOSITORY,value,contents))

    def test_empty_required_collections_cannot_bypass_the_full_contract(self):
        for key in ['allowed_write_files','data_scopes','parent_tags','unit_ids','scope-files']:
            value,contents,m=bulk_payload()
            if key in {'allowed_write_files','data_scopes'}:m[key]=[]
            else:m['data_scopes'][0]['allowed_write_files' if key=='scope-files' else key]=[]
            bind_bulk(value,contents,m)
            with self.subTest(key=key):self.assertTrue(validate_pr_contract(REPOSITORY,value,contents))

    def test_version_and_active_output_roles_cannot_be_falsified(self):
        for fault in ['boolean','float','missing','old','empty-unit','missing-candidate']:
            value,contents,m=bulk_payload()
            if fault in {'boolean','float'}:m['schema_version']=True if fault=='boolean' else 1.0
            if fault=='missing':m['data_scopes'][0]['output_unit_ids']=[]
            if fault=='old':
                m['data_scopes'][0]['unit_ids'].append('tag:04V1:old')
                m['data_scopes'][0]['output_unit_ids']=['tag:04V1:old']
            if fault=='empty-unit':contents[UNIT_PATH]=''
            if fault=='missing-candidate':
                path='translation-data/candidates/model/guide.jsonl'
                m['allowed_write_files'].append(path);m['data_scopes'][0]['allowed_write_files'].append(path)
                value['files']['nodes'].append(dict(path=path,changeType='ADDED'));contents[path]=''
                value['changedFiles']+=1
            bind_bulk(value,contents,m)
            with self.subTest(fault=fault):self.assertTrue(validate_pr_contract(REPOSITORY,value,contents))

    def test_records_cannot_borrow_another_scope_ids_chapter_parent_or_model(self):
        for key,bad in [('unit_id','tag:0008:title'),('chapter','sets'),('parent_tag','0008'),
                        ('source_commit','f'*40),('run_id','undeclared-run'),('model_id','undeclared-model'),
                        ('model_record_id','undeclared:model'),('model',{'resolved_id':'undeclared-model'})]:
            value,contents,_ = bulk_payload();row=json.loads(contents[UNIT_PATH]);row[key]=bad;contents[UNIT_PATH]=json.dumps(row)
            with self.subTest(key=key):self.assertTrue(validate_pr_contract(REPOSITORY,value,contents))

    def test_unassigned_managed_file_and_fake_historical_parent_are_not_authorized(self):
        value,contents,m = bulk_payload();m['data_scopes'][1]['allowed_write_files']=['docs/unused.md'];m['allowed_write_files'].append('docs/unused.md');bind_bulk(value,contents,m)
        self.assertTrue(any('unique exact data scope' in e for e in validate_pr_contract(REPOSITORY,value,contents)))
        value,contents,m = bulk_payload();m['data_scopes'][0]['historical_parent_tags']=['0008'];bind_bulk(value,contents,m)
        row=json.loads(contents[UNIT_PATH]);row['parent_tag']='0008';contents[UNIT_PATH]=json.dumps(row)
        errors=validate_pr_contract(REPOSITORY,value,contents)
        self.assertTrue(any('valid v4 derivation' in e for e in errors))
        self.assertTrue(any('outside Issue' in e for e in errors))

    def test_legacy_without_manifest_retains_file_and_parent_limits(self):
        value=payload();value['files']['nodes']=[dict(path=f'docs/file-{i}.md') for i in range(101)]
        value['closingIssuesReferences']['nodes'][0]['body']+='\nallowed_write_files:\n- docs/\n'
        self.assertTrue(any('more than 100' in e for e in validate_pr_contract(REPOSITORY,value,{})))

    def _fetch(self, fault=None):
        value,contents,m = bulk_payload(105)
        if fault=='deleted':
            m['data_scopes'][0]['output_unit_ids']=[];bind_bulk(value,contents,m)
        nodes=copy.deepcopy(value['files']['nodes']);initial=copy.deepcopy(value)
        if fault=='deleted':initial['files']['nodes'][1]['changeType']='DELETED';nodes[1]['changeType']='DELETED'
        initial['files']={'nodes':nodes[:100],'pageInfo':{'hasNextPage':True,'endCursor':'page-one'}}
        graph_calls=0;calls=[]
        def request(url,token,*,data=None):
            nonlocal graph_calls
            calls.append((url,data))
            if data is not None:
                if 'PrContractBlobs' in data['query']:
                    self.assertEqual(data['variables']['owner'],'example')
                    objects={}
                    for key,expression in data['variables'].items():
                        if not key.startswith('expr'):continue
                        commit,path=expression.split(':',1)
                        self.assertEqual(commit,('c' if fault=='deleted' and path==UNIT_PATH else 'b')*40)
                        raw=contents[path].encode()
                        objects['file'+key[4:]]=dict(oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                            byteSize=len(raw),isBinary=False,isTruncated=False,text=raw.decode())
                    return {'data':{'repository':objects}}
                if 'cursor' not in data['variables']:
                    graph_calls+=1;pr=copy.deepcopy(initial)
                    if fault=='final-head' and graph_calls>1:pr['headRefOid']='d'*40
                    if fault=='final-scope' and graph_calls>1:pr['closingIssuesReferences']['nodes'][0]['body']+='\nchanged'
                    if fault=='final-body' and graph_calls>1:pr['body']+='\nchanged'
                    if fault=='count':pr['changedFiles']+=1
                    if fault=='cursor':pr['files']['pageInfo'].pop('endCursor')
                    return {'data':{'repository':{'pullRequest':pr}}}
                self.assertEqual(data['variables']['cursor'],'page-one')
                page=dict(headRefOid='b'*40,baseRefOid='c'*40,files=dict(nodes=copy.deepcopy(nodes[100:]),pageInfo={'hasNextPage':False,'endCursor':'done'}))
                if fault=='head':page['headRefOid']='d'*40
                if fault=='base':page['baseRefOid']='d'*40
                if fault=='duplicate':page['files']['nodes'].append(copy.deepcopy(nodes[0]))
                if fault=='empty':page['files']['nodes']=[]
                if fault=='missing-page-info':page['files'].pop('pageInfo')
                if fault=='cycle':page['files']['pageInfo']={'hasNextPage':True,'endCursor':'page-one'}
                if fault=='renamed':page['files']['nodes'][0]['changeType']='RENAMED'
                return {'data':{'repository':{'pullRequest':page}}}
            from urllib.parse import unquote,urlsplit,parse_qs
            self.assertEqual(parse_qs(urlsplit(url).query)['ref'],['b'*40])
            path=unquote(urlsplit(url).path.split('/contents/',1)[1])
            return {'encoding':'base64','content':base64.b64encode(contents[path].encode()).decode()}
        result=fetch_pr_contract(REPOSITORY,99,'synthetic-token',api_url='https://api.example.test',
            graphql_url='https://api.example.test/graphql',request_json=request)
        return result,nodes,calls

    def test_native_pagination_gets_all_paths_and_pins_every_content_request(self):
        (value,contents),nodes,calls=self._fetch()
        self.assertEqual(value['files']['nodes'],nodes)
        self.assertEqual(validate_pr_contract(REPOSITORY,value,contents),[])
        self.assertEqual(sum(data is not None for _,data in calls),4)

    def test_deleted_bulk_file_uses_its_exact_base_commit(self):
        (value,contents),nodes,calls=self._fetch('deleted')
        self.assertEqual(validate_pr_contract(REPOSITORY,value,contents),[])
        expressions=[v for _,data in calls if data and 'PrContractBlobs' in data['query']
                     for k,v in data['variables'].items() if k.startswith('expr')]
        self.assertIn('c'*40+':'+UNIT_PATH,expressions)

    def test_pagination_refuses_duplicates_empty_pages_cycles_missing_cursors_and_drift(self):
        for fault in ['head','base','duplicate','empty','missing-page-info','cycle','cursor','final-head','final-scope','final-body','count','renamed']:
            with self.subTest(fault=fault),self.assertRaises(ContractApiError):self._fetch(fault)


if __name__ == "__main__":
    unittest.main()
