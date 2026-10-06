from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Callable


GRAPHQL_QUERY = """
query PrContract($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      number
      body
      createdAt
      headRefName
      headRefOid
      baseRefOid
      author { login }
      headRepository { nameWithOwner }
      baseRepository { nameWithOwner }
      closingIssuesReferences(first: 10) {
        nodes {
          number
          state
          createdAt
          body
          repository { nameWithOwner }
          labels(first: 50) { nodes { name } }
        }
        pageInfo { hasNextPage }
      }
      files(first: 100) {
        nodes { path changeType }
        pageInfo { hasNextPage }
      }
    }
  }
}
"""

FIELD_ALIASES = {
    "task_id": ("task_id", "Task ID"),
    "owner": ("owner", "Owner"),
    "branch": ("branch", "Branch"),
    "allowed_write_files": ("allowed_write_files", "Allowed write files"),
    "source_commit": ("source_commit", "English source commit"),
    "chapter": ("chapter", "Chapter", "Upstream chapter"),
    "parent_tag": (
        "parent_tag",
        "Section or parent Tag",
        "Permanent Tag or full label",
    ),
    "parent_tags": (
        "parent_tags",
        "Section or parent Tags",
        "Permanent Tags",
    ),
    "unit_ids": ("unit_ids", "Unit IDs"),
    "historical_parent_tags": ("historical_parent_tags", "Historical parent Tags"),
}

TRANSLATION_DATA_PREFIXES = (
    "translation-data/units/",
    "translation-data/candidates/",
    "translation-data/runs/",
    "translation-data/selections/",
    "translation-data/reviewed/",
    "translation-data/derivations/",
    "translation-data/derivation-archives/",
    "translation-data/model-corrections/",
    "translation-data/source-reextractions/",
    "translation-data/source-container-restorations/",
    "translation-data/retired/derivations/",
    "translation-data/retired/model-corrections/",
    "review/language/",
    "review/mathematics/",
)
PERMANENT_TAG_RE = re.compile(r"^[0-9A-Z]+$")


class ContractApiError(RuntimeError):
    pass


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _field_value(body: str, name: str) -> str | None:
    aliases = FIELD_ALIASES[name]
    lines = body.splitlines()

    for index, line in enumerate(lines):
        for alias in aliases:
            match = re.match(
                rf"^\s*{re.escape(alias)}\s*:\s*(.*?)\s*$",
                line,
                flags=re.IGNORECASE,
            )
            if not match:
                continue
            inline = match.group(1).strip()
            if inline:
                return inline.strip("`")
            values: list[str] = []
            for following in lines[index + 1 :]:
                if re.match(r"^\s*#{2,6}\s+", following):
                    break
                if not following.strip():
                    if values:
                        break
                    continue
                if re.match(r"^\s*[A-Za-z][A-Za-z0-9 _/-]*\s*:", following):
                    break
                values.append(following.strip())
            return "\n".join(values).strip() or None

    for index, line in enumerate(lines):
        for alias in aliases:
            if not re.match(
                rf"^\s*###\s+{re.escape(alias)}\s*$",
                line,
                flags=re.IGNORECASE,
            ):
                continue
            values: list[str] = []
            for following in lines[index + 1 :]:
                if re.match(r"^\s*#{2,6}\s+", following):
                    break
                if not following.strip():
                    if values:
                        break
                    continue
                values.append(following.strip())
            return "\n".join(values).strip() or None
    return None


def _list_values(value: str | None) -> list[str]:
    if not value:
        return []
    values: list[str] = []
    for line in value.splitlines():
        item = re.sub(r"^\s*[-*]\s*", "", line).strip().strip("`")
        if item:
            values.append(item)
    return values


def _path_is_allowed(path: str, declarations: list[str]) -> bool:
    for declaration in declarations:
        normalized = declaration.removeprefix("./")
        if normalized.endswith("/") and path.startswith(normalized):
            return True
        if path == normalized:
            return True
    return False


def _load_structured_records(path: str, content: str) -> list[dict[str, Any]]:
    try:
        if path.endswith(".jsonl"):
            records = [
                json.loads(line)
                for line in content.splitlines()
                if line.strip()
            ]
        elif path.endswith(".json"):
            value = json.loads(content)
            records = value if isinstance(value, list) else [value]
        else:
            return []
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse changed structured file {path}: {exc}") from exc
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"changed structured file {path} must contain JSON objects")
    return records


def _record_values(records: list[dict[str, Any]], key: str) -> set[str]:
    values: set[str] = set()
    for record in records:
        value = record.get(key)
        if isinstance(value, str):
            values.add(value)
        elif isinstance(value, list):
            values.update(item for item in value if isinstance(item, str))
        # These are newly adopted facts/group coordinates. Neighbor context and
        # approved TM are read inputs and do not enlarge the writer's scope.
        for nested in ('unit_groups', 'output_units', 'new_units'):
            children = record.get(nested)
            if isinstance(children, list):
                values.update(_record_values([v for v in children if isinstance(v, dict)], key))
        if isinstance(record.get('selector'), dict):
            values.update(_record_values([record['selector']], key))
        if key == 'unit_ids':
            for grouped_ids in ('input_unit_ids', 'output_unit_ids'):
                values.update(v for v in record.get(grouped_ids, []) if isinstance(v, str))
    return values


def validate_pr_contract(
    repository: str,
    pull_request: dict[str, Any],
    file_contents: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    closing = pull_request.get("closingIssuesReferences", {})
    if closing.get("pageInfo", {}).get("hasNextPage"):
        errors.append("PR links more than 10 closing Issues; one task Issue is required")
    issues = closing.get("nodes") or []
    if len(issues) != 1:
        errors.append(
            f"PR must link exactly one task Issue with Closes/Fixes/Resolves; found {len(issues)}"
        )
        return errors

    issue = issues[0]
    issue_number = issue.get("number")
    issue_body = issue.get("body") or ""
    pr_body = pull_request.get("body") or ""

    issue_repository = issue.get("repository", {}).get("nameWithOwner")
    if issue_repository != repository:
        errors.append(
            f"closing Issue #{issue_number} belongs to {issue_repository}, not {repository}"
        )
    if issue.get("state") != "OPEN":
        errors.append(f"closing Issue #{issue_number} must be OPEN before the PR is merged")
    if issue.get("createdAt") and pull_request.get("createdAt"):
        if _parse_datetime(issue["createdAt"]) > _parse_datetime(pull_request["createdAt"]):
            errors.append(f"task Issue #{issue_number} was created after the PR")

    labels = {
        node.get("name")
        for node in issue.get("labels", {}).get("nodes", [])
        if node.get("name")
    }
    if "claimed" not in labels:
        errors.append(f"task Issue #{issue_number} must have the claimed label")

    task_id = _field_value(issue_body, "task_id")
    if not task_id:
        errors.append(f"task Issue #{issue_number} is missing task_id")
    elif task_id not in pr_body:
        errors.append(f"PR body does not reference task_id {task_id!r}")

    branch = _field_value(issue_body, "branch")
    head_ref = pull_request.get("headRefName")
    if not branch:
        errors.append(f"task Issue #{issue_number} is missing branch")
    elif branch != head_ref:
        errors.append(
            f"task Issue branch {branch!r} does not match PR head {head_ref!r}"
        )

    owner = _field_value(issue_body, "owner")
    author = pull_request.get("author", {}).get("login")
    if not owner:
        errors.append(f"task Issue #{issue_number} is missing owner")
    else:
        owner_match = re.search(r"@?([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))", owner)
        if not owner_match:
            errors.append(f"task Issue #{issue_number} has an invalid owner field")
        elif author and owner_match.group(1).casefold() != author.casefold():
            errors.append(
                f"task Issue owner {owner_match.group(1)!r} does not match PR author {author!r}"
            )

    files = pull_request.get("files", {})
    if files.get("pageInfo", {}).get("hasNextPage"):
        errors.append("PR changes more than 100 files; split it into auditable tasks")
    file_nodes = files.get("nodes") or []
    changed_paths = [node.get("path") for node in file_nodes if node.get("path")]
    allowed_paths = _list_values(_field_value(issue_body, "allowed_write_files"))
    if not allowed_paths:
        errors.append(f"task Issue #{issue_number} is missing allowed_write_files")
    else:
        for path in changed_paths:
            if not _path_is_allowed(path, allowed_paths):
                errors.append(f"changed path is outside Issue scope: {path}")

    managed_paths = [
        path
        for path in changed_paths
        if path.startswith(TRANSLATION_DATA_PREFIXES)
        and path.endswith((".json", ".jsonl"))
    ]
    if not managed_paths:
        return errors

    source_commit = _field_value(issue_body, "source_commit")
    if not source_commit or not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
        errors.append(
            f"translation task Issue #{issue_number} needs a full 40-character source_commit"
        )
    elif source_commit not in pr_body:
        errors.append("PR body source commit does not match the linked Issue")

    chapter = _field_value(issue_body, "chapter")
    parent_tag = _field_value(issue_body, "parent_tag")
    parent_tags_value = _field_value(issue_body, "parent_tags")
    parent_tags: list[str] = []
    if parent_tag and parent_tags_value:
        errors.append(
            f"translation task Issue #{issue_number} must declare parent_tag or "
            "parent_tags, not both"
        )
    elif parent_tag:
        parent_tags = [parent_tag]
    elif parent_tags_value:
        parent_tags = _list_values(parent_tags_value)
        if not 2 <= len(parent_tags) <= 8:
            errors.append(
                f"translation batch Issue #{issue_number} parent_tags must contain "
                "2 to 8 Tags"
            )
        duplicates = sorted(
            tag for tag in set(parent_tags) if parent_tags.count(tag) > 1
        )
        if duplicates:
            errors.append(
                f"translation batch Issue #{issue_number} parent_tags contains "
                f"duplicates: {', '.join(duplicates)}"
            )
        invalid_tags = sorted(
            tag for tag in set(parent_tags) if not PERMANENT_TAG_RE.fullmatch(tag)
        )
        if invalid_tags:
            errors.append(
                f"translation batch Issue #{issue_number} parent_tags contains "
                f"invalid permanent Tags: {', '.join(invalid_tags)}"
            )
    declared_unit_ids = set(_list_values(_field_value(issue_body, "unit_ids")))
    if not chapter:
        errors.append(f"translation task Issue #{issue_number} is missing chapter")
    if not parent_tag and not parent_tags_value:
        errors.append(
            f"translation task Issue #{issue_number} is missing parent_tag or parent_tags"
        )
    if not declared_unit_ids:
        errors.append(f"translation task Issue #{issue_number} is missing unit_ids")

    records: list[dict[str, Any]] = []
    records_by_path = {}
    for path in managed_paths:
        content = file_contents.get(path)
        if content is None:
            errors.append(f"cannot verify changed structured file content: {path}")
            continue
        try:
            rows = _load_structured_records(path, content)
            records_by_path[path] = rows
            records.extend(rows)
        except ValueError as exc:
            errors.append(str(exc))

    actual_unit_ids = _record_values(records, "unit_id") | _record_values(
        records, "unit_ids"
    )
    for unit_id in sorted(actual_unit_ids - declared_unit_ids):
        errors.append(f"changed structured record is outside Issue unit_ids: {unit_id}")

    actual_commits = _record_values(records, "source_commit")
    if source_commit:
        for commit in sorted(actual_commits - {source_commit}):
            errors.append(
                f"changed structured record source_commit {commit} differs from Issue"
            )

    actual_chapters = _record_values(records, "chapter")
    if chapter:
        for actual in sorted(actual_chapters - {chapter}):
            errors.append(f"changed structured record chapter {actual!r} differs from Issue")

    declared_parent_tags = set(parent_tags)
    historical = _list_values(_field_value(issue_body, 'historical_parent_tags'))
    historical_paths = set()
    if historical:
        from .schema_validation import validate_named_schema
        grouped = [r for path, rows in records_by_path.items()
                   if path.startswith('translation-data/derivations/') for r in rows
                   if isinstance(r.get('tool'), dict) and r['tool'].get('version') == '4'
                   and not validate_named_schema(r, 'derivation.schema.json', path)]
        if not grouped:
            errors.append('historical_parent_tags requires a changed valid v4 derivation')
        if len(set(historical)) != len(historical) or any(not PERMANENT_TAG_RE.fullmatch(t) for t in historical):
            errors.append('historical_parent_tags must contain unique permanent Tags')
        for record in grouped:
            identifier = re.escape(record['derivation_id'])
            for role in ('input_units', 'input_candidates'):
                path = record['files'][role]['path']
                if re.fullmatch(rf'translation-data/retired/derivations/{identifier}/(?:units|candidates)\.jsonl', path):
                    historical_paths.add(path)
        for path, rows in records_by_path.items():
            if not path.startswith('translation-data/derivation-archives/'):
                continue
            for record in rows:
                if (record.get('successor_derivation_id') in {r['derivation_id'] for r in grouped}
                        and not validate_named_schema(record, 'derivation-archive.schema.json', path)):
                    prior = re.escape(record['prior_derivation_id'])
                    for role in ('output_units', 'output_candidates'):
                        target = record['files'][role]['path']
                        if re.fullmatch(rf'translation-data/retired/derivations/{prior}/output-(?:units|candidates)\.jsonl', target):
                            historical_paths.add(target)
    if declared_parent_tags:
        for path, rows in records_by_path.items():
            permitted = declared_parent_tags | (set(historical) if path in historical_paths else set())
            for actual in sorted(_record_values(rows, 'parent_tag') - permitted):
                errors.append(
                    f"changed structured record parent_tag {actual!r} is outside Issue "
                    f"parent Tag scope ({path})"
                )
    return errors


def _request_json(
    url: str,
    token: str,
    *,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    encoded = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "stacks-project-zh-pr-contract",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ContractApiError(f"GitHub API request failed for {url}: {exc}") from exc


def fetch_pr_contract(
    repository: str,
    number: int,
    token: str,
    *,
    api_url: str = "https://api.github.com",
    graphql_url: str = "https://api.github.com/graphql",
    request_json: Callable[..., dict[str, Any]] = _request_json,
) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        owner, name = repository.split("/", 1)
    except ValueError as exc:
        raise ContractApiError(f"invalid repository name: {repository!r}") from exc

    response = request_json(
        graphql_url,
        token,
        data={
            "query": GRAPHQL_QUERY,
            "variables": {"owner": owner, "name": name, "number": number},
        },
    )
    if response.get("errors"):
        raise ContractApiError(f"GitHub GraphQL errors: {response['errors']}")
    pull_request = response.get("data", {}).get("repository", {}).get("pullRequest")
    if not pull_request:
        raise ContractApiError(f"pull request #{number} was not found in {repository}")

    head_repository = pull_request.get("headRepository", {}).get("nameWithOwner")
    base_repository = pull_request.get("baseRepository", {}).get("nameWithOwner")
    head_oid = pull_request.get("headRefOid")
    base_oid = pull_request.get("baseRefOid")
    file_contents: dict[str, str] = {}
    for node in pull_request.get("files", {}).get("nodes", []):
        path = node.get("path")
        if (
            not path
            or not path.endswith((".json", ".jsonl"))
            or not path.startswith(TRANSLATION_DATA_PREFIXES)
        ):
            continue
        if node.get("changeType") == "DELETED":
            content_repository, content_ref = base_repository, base_oid
        else:
            content_repository, content_ref = head_repository, head_oid
        if not content_repository or not content_ref:
            raise ContractApiError(f"cannot resolve repository and commit for {path}")

        encoded_path = urllib.parse.quote(path, safe="/")
        encoded_ref = urllib.parse.urlencode({"ref": content_ref})
        content_response = request_json(
            f"{api_url}/repos/{content_repository}/contents/{encoded_path}?{encoded_ref}",
            token,
        )
        if content_response.get("encoding") != "base64":
            raise ContractApiError(f"GitHub did not return base64 content for {path}")
        try:
            file_contents[path] = base64.b64decode(
                content_response.get("content", "")
            ).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ContractApiError(f"cannot decode changed file {path}: {exc}") from exc
    return pull_request, file_contents
