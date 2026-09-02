from __future__ import annotations

import json
import unittest

from stacks_zh.pr_contract import fetch_pr_contract, validate_pr_contract


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
        self.assertTrue(any("unit_id 'tag:04V3:title' has Tag" in error for error in errors))

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


if __name__ == "__main__":
    unittest.main()
