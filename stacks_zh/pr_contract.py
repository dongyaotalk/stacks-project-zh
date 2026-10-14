from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import PurePosixPath
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
      changedFiles
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
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

GRAPHQL_FILE_PAGE_QUERY = """
query PrContractFiles($owner: String!, $name: String!, $number: Int!, $cursor: String!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      headRefOid
      baseRefOid
      files(first: 100, after: $cursor) {
        nodes { path changeType }
        pageInfo { hasNextPage endCursor }
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
    "scope_manifest": ("scope_manifest",),
    "scope_manifest_sha256": ("scope_manifest_sha256",),
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
    "translation-data/pre-adoption-replays/",
    "translation-data/retired/pre-adoption-replays/",
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


def _exact_paths(paths):
    if any(not isinstance(p,str) or not p or p.startswith('/') or p.endswith('/')
           or PurePosixPath(p).as_posix() != p or '..' in PurePosixPath(p).parts
           or re.search(r'[\\*?\[\]\x00-\x1f\x7f]',p) for p in paths):
        raise ValueError('scope manifest paths must be exact canonical repository files')
    if len(paths) != len(set(paths)):
        raise ValueError('scope manifest repeats an allowed path')


def _scope_manifest(issue_body, file_contents):
    path = _field_value(issue_body,'scope_manifest')
    expected = _field_value(issue_body,'scope_manifest_sha256')
    if not path and not expected:
        return None
    if not path or not re.fullmatch(r'task-scopes/[A-Za-z0-9][A-Za-z0-9._-]*\.json',path):
        raise ValueError('scope_manifest needs an exact task-scopes JSON path')
    if not expected or not re.fullmatch(r'sha256:[0-9a-f]{64}',expected):
        raise ValueError('scope_manifest_sha256 must bind the complete manifest bytes')
    if _field_value(issue_body,'allowed_write_files'):
        raise ValueError('scope manifest and inline allowed_write_files cannot be mixed')
    raw = file_contents.get(path)
    if not isinstance(raw,str) or len(raw.encode('utf-8')) > 8*1024*1024:
        raise ValueError('cannot verify bounded scope manifest content: '+path)
    if 'sha256:'+hashlib.sha256(raw.encode('utf-8')).hexdigest() != expected:
        raise ValueError('scope manifest differs from the Issue SHA256')
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise ValueError('invalid scope manifest JSON: '+str(exc)) from exc
    from .schema_validation import validate_named_schema
    errors = validate_named_schema(value,'task-scope.schema.json','scope manifest')
    if errors:
        raise ValueError('\n'.join(errors))
    # The repository's deliberately small Schema engine has no minItems.
    # These cardinalities remain mandatory in the complete trusted contract.
    if not value['allowed_write_files'] or not value['data_scopes']:
        raise ValueError('scope manifest needs nonempty exact files and data scopes')
    for key in ['task_id','branch','source_commit']:
        if value[key] != _field_value(issue_body,key):
            raise ValueError('scope manifest '+key+' differs from the linked Issue')
    owner = re.search(r'@?([A-Za-z0-9][A-Za-z0-9-]{0,38})',_field_value(issue_body,'owner') or '')
    if not owner or owner[1].casefold() != value['owner'].casefold():
        raise ValueError('scope manifest owner differs from the linked Issue')
    _exact_paths(value['allowed_write_files'])
    if path not in value['allowed_write_files']:
        raise ValueError('scope manifest must declare its own exact file')
    seen_ids,seen_paths = set(),set()
    for scope in value['data_scopes']:
        if any(not scope[key] for key in ['parent_tags','unit_ids','allowed_write_files']):
            raise ValueError('data scope needs nonempty parents, complete IDs and exact files')
        if scope['scope_id'] in seen_ids:
            raise ValueError('scope manifest repeats a data scope identity')
        seen_ids.add(scope['scope_id']);_exact_paths(scope['allowed_write_files'])
        paths = set(scope['allowed_write_files'])
        if not paths <= set(value['allowed_write_files']) or seen_paths & paths:
            raise ValueError('data scopes overlap or escape the complete allowed files')
        if not set(scope['input_unit_ids']+scope['output_unit_ids']) <= set(scope['unit_ids']):
            raise ValueError('complete old/new unit IDs escape their data scope')
        seen_paths.update(paths)
    value['_path'] = path;value['_sha256'] = expected
    return value


def validate_pr_contract(
    repository: str,
    pull_request: dict[str, Any],
    file_contents: dict[str, str],
    *, _from_manifest: bool = False,
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
    try:
        manifest = _scope_manifest(issue_body,file_contents)
    except ValueError as exc:
        errors.append(str(exc));return errors
    file_nodes = files.get("nodes") or []
    changed_paths = [node.get("path") for node in file_nodes if node.get("path")]
    if len(changed_paths) != len(set(changed_paths)):
        errors.append('native changed files contain duplicate paths')
    if len(changed_paths) > 100 and not manifest and not _from_manifest:
        errors.append('PR changes more than 100 files; an explicit hash-pinned scope manifest is required')
    allowed_paths = manifest['allowed_write_files'] if manifest else _list_values(_field_value(issue_body, "allowed_write_files"))
    if manifest and (manifest['_path'] not in pr_body or manifest['_sha256'] not in pr_body):
        errors.append('PR body must reference the exact scope manifest path and Issue hash')
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

    if manifest:
        assigned = set()
        if manifest['source_commit'] not in pr_body:
            errors.append('PR body source commit does not match the linked Issue')
        for scope in manifest['data_scopes']:
            paths = set(managed_paths) & set(scope['allowed_write_files'])
            assigned.update(paths)
            if not paths:
                continue
            child = copy.deepcopy(pull_request)
            parents = scope['parent_tags']
            body = '\n'.join(f'{k}: {manifest[k]}' for k in ['task_id','owner','branch','source_commit'])+'\n'
            body += 'chapter: '+scope['chapter']+'\n'
            body += ('parent_tag: '+parents[0]+'\n' if len(parents)==1 else
                     'parent_tags:\n'+''.join('- '+p+'\n' for p in parents))
            for key,values in [('allowed_write_files',sorted(paths)),('unit_ids',scope['unit_ids']),
                               ('historical_parent_tags',scope['historical_parent_tags'])]:
                if values:
                    body += key+':\n'+''.join('- '+v+'\n' for v in values)
            child['closingIssuesReferences']['nodes'][0]['body'] = body
            child['files'] = {'nodes':[n for n in file_nodes if n.get('path') in paths],
                              'pageInfo':{'hasNextPage':False}}
            errors.extend(scope['scope_id']+': '+e for e in validate_pr_contract(
                repository,child,file_contents,_from_manifest=True))
            rows = []
            active_ids = {}
            deleted_paths = {node['path'] for node in file_nodes if node.get('changeType') == 'DELETED'}
            for path in paths:
                if path in file_contents:
                    try:
                        path_rows = _load_structured_records(path,file_contents[path])
                        rows.extend(path_rows)
                        for role in ('units','candidates'):
                            if path.startswith('translation-data/'+role+'/'):
                                ids = active_ids.setdefault(role,set())
                                if path not in deleted_paths:
                                    ids.update(_record_values(path_rows,'unit_id'))
                    except ValueError:pass  # The recursive full validator reports the malformed record.
            for role,ids in active_ids.items():
                if ids != set(scope['output_unit_ids']):
                    errors.append(scope['scope_id']+': active '+role+' IDs differ from complete output_unit_ids')
            for key,declared in [('run_id',scope['run_scope']),('model_id',scope['model_scope']),
                                 ('model_record_id',scope['model_scope'])]:
                for actual in sorted(_record_values(rows,key)-set(declared)):
                    errors.append(scope['scope_id']+': structured '+key+' escapes its declared scope: '+actual)
            for row in rows:
                model = row.get('model')
                if isinstance(model,dict):
                    for key in ['record_id','requested_id','resolved_id']:
                        value = model.get(key)
                        if isinstance(value,str) and value not in scope['model_scope']:
                            errors.append(scope['scope_id']+': run model '+key+' escapes its declared scope: '+value)
        for path in sorted(set(managed_paths)-assigned):
            errors.append('managed file lacks its unique exact data scope: '+path)
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
        if not (len(parent_tags) >= 2 and (_from_manifest or len(parent_tags) <= 8)):
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
        for path, rows in records_by_path.items():
            if not path.startswith('translation-data/pre-adoption-replays/'):
                continue
            for record in rows:
                if (record.get('current_derivation_id') in {r['derivation_id'] for r in grouped}
                        and not validate_named_schema(record, 'pre-adoption-replay.schema.json', path)):
                    identifier = re.escape(record['replay_id'])
                    for role, name in [('derivation', 'derivation.json'), ('units', 'units.jsonl'), ('candidates', 'candidates.jsonl')]:
                        target = record['files'][role]['path']
                        if re.fullmatch(rf'translation-data/retired/pre-adoption-replays/{identifier}/{re.escape(name)}', target):
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


def _large_file_bytes(
    metadata: dict[str, Any],
    path: str,
    repository: str,
    token: str,
    api_url: str,
    request_json: Callable[..., dict[str, Any]],
    *, minimum_size: int = 1_000_000,
) -> bytes:
    # Contents already resolved this path against the exact PR head/base commit.
    # Fetch its immutable blob, never a supplied URL or a moving branch.
    size, sha = metadata.get("size"), metadata.get("sha")
    if (
        metadata.get("type") != "file"
        or metadata.get("content") != ""
        or type(size) is not int
        or not minimum_size < size <= 100 * 1024 * 1024
        or not isinstance(sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", sha) is None
    ):
        raise ContractApiError(f"invalid large-file metadata for {path}")
    blob = request_json(f"{api_url}/repos/{repository}/git/blobs/{sha}", token)
    if (
        not isinstance(blob, dict)
        or blob.get("encoding") != "base64"
        or blob.get("sha") != sha
        or blob.get("size") != size
        or not isinstance(blob.get("content"), str)
    ):
        raise ContractApiError(f"invalid Git blob response for {path}")
    try:
        raw = base64.b64decode(
            b"".join(blob["content"].encode("ascii").split()), validate=True
        )
    except (ValueError, UnicodeError) as exc:
        raise ContractApiError(f"cannot decode Git blob for {path}: {exc}") from exc
    blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if len(raw) != size or blob_sha != sha:
        raise ContractApiError(f"Git blob bytes do not match metadata for {path}")
    return raw


def _batch_blob_contents(paths, repository, commit, token, api_url, graphql_url, request_json):
    if (not isinstance(repository,str) or '/' not in repository
            or not isinstance(commit,str) or not re.fullmatch(r'[0-9a-f]{40}',commit)):
        raise ContractApiError('bulk content retrieval requires exact repository and commit')
    owner,name = repository.split('/',1)
    contents = {}
    for start in range(0,len(paths),25):
        batch = paths[start:start+25]
        declarations = ', '.join(f'$expr{i}: String!' for i in range(len(batch)))
        fields = ' '.join(f'file{i}: object(expression: $expr{i}) {{ ... on Blob {{ oid byteSize isTruncated isBinary text }} }}'
                          for i in range(len(batch)))
        query = 'query PrContractBlobs($owner: String!, $name: String!, '+declarations+') { repository(owner: $owner, name: $name) { '+fields+' } }'
        variables = {'owner':owner,'name':name,**{f'expr{i}':commit+':'+p for i,p in enumerate(batch)}}
        response = request_json(graphql_url,token,data={'query':query,'variables':variables})
        objects = response.get('data',{}).get('repository')
        if response.get('errors') or not isinstance(objects,dict):
            raise ContractApiError('GitHub bulk Git blob lookup failed')
        for i,path in enumerate(batch):
            obj = objects.get(f'file{i}')
            if (not isinstance(obj,dict) or not isinstance(obj.get('oid'),str)
                    or not re.fullmatch(r'[0-9a-f]{40}',obj['oid'])
                    or type(obj.get('byteSize')) is not int or not 0 <= obj['byteSize'] <= 100*1024*1024
                    or obj.get('isBinary') is not False or type(obj.get('isTruncated')) is not bool):
                raise ContractApiError('invalid pinned Git blob metadata for '+path)
            if obj['isTruncated']:
                raw = _large_file_bytes(dict(type='file',content='',sha=obj['oid'],size=obj['byteSize']),
                    path,repository,token,api_url,request_json,minimum_size=-1)
            elif isinstance(obj.get('text'),str):
                raw = obj['text'].encode('utf-8')
            else:
                raise ContractApiError('missing complete Git blob text for '+path)
            sha = hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
            if len(raw) != obj['byteSize'] or sha != obj['oid']:
                raise ContractApiError('pinned Git blob bytes differ from metadata for '+path)
            try:contents[path] = raw.decode('utf-8')
            except UnicodeError as exc:
                raise ContractApiError('Git blob is not UTF-8: '+path) from exc
    return contents


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

    def read_content(path, content_repository, content_ref):
        if not content_repository or not content_ref:
            raise ContractApiError(f"cannot resolve repository and commit for {path}")
        encoded_path = urllib.parse.quote(path, safe="/")
        encoded_ref = urllib.parse.urlencode({"ref": content_ref})
        value = request_json(f"{api_url}/repos/{content_repository}/contents/{encoded_path}?{encoded_ref}",token)
        if value.get('encoding') == 'none':
            raw = _large_file_bytes(value,path,content_repository,token,api_url,request_json)
        elif value.get('encoding') == 'base64':
            try:
                raw = base64.b64decode(b''.join(value.get('content','').encode('ascii').split()),validate=True)
            except (ValueError,UnicodeError) as exc:
                raise ContractApiError(f'cannot decode changed file {path}: {exc}') from exc
        else:
            raise ContractApiError(f'GitHub did not return base64 content for {path}')
        try:return raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ContractApiError(f'cannot decode changed file {path}: {exc}') from exc

    issues = pull_request.get('closingIssuesReferences',{}).get('nodes') or []
    manifest_path = _field_value(issues[0].get('body') or '', 'scope_manifest') if len(issues)==1 else None
    if manifest_path:
        if not re.fullmatch(r'task-scopes/[A-Za-z0-9][A-Za-z0-9._-]*\.json',manifest_path):
            raise ContractApiError('invalid Issue scope manifest path')
        file_contents[manifest_path] = read_content(manifest_path,head_repository,head_oid)
        try:
            manifest = _scope_manifest(issues[0].get('body') or '',file_contents)
        except ValueError as exc:
            raise ContractApiError(str(exc)) from exc
    files = pull_request.get('files',{})
    if manifest_path:
        if (not isinstance(files,dict) or not isinstance(files.get('nodes'),list)
                or not isinstance(files.get('pageInfo'),dict)
                or type(files['pageInfo'].get('hasNextPage')) is not bool):
            raise ContractApiError('invalid initial native changed-file page')
    paginated = bool(manifest_path and files.get('pageInfo',{}).get('hasNextPage'))
    if paginated:
        if not all(isinstance(v,str) and re.fullmatch(r'[0-9a-f]{40}',v) for v in [head_oid,base_oid]):
            raise ContractApiError('pagination requires exact native head/base commits')
        nodes = list(files.get('nodes') or []);seen_cursors = set()
        while files.get('pageInfo',{}).get('hasNextPage'):
            cursor = files.get('pageInfo',{}).get('endCursor')
            if not isinstance(cursor,str) or not cursor or cursor in seen_cursors:
                raise ContractApiError('native changed-file pagination is truncated or cyclic')
            seen_cursors.add(cursor)
            page = request_json(graphql_url,token,data={'query':GRAPHQL_FILE_PAGE_QUERY,
                'variables':{'owner':owner,'name':name,'number':number,'cursor':cursor}})
            if page.get('errors'):
                raise ContractApiError('GitHub changed-file pagination failed: '+str(page['errors']))
            current = page.get('data',{}).get('repository',{}).get('pullRequest')
            if (not isinstance(current,dict) or current.get('headRefOid') != head_oid
                    or current.get('baseRefOid') != base_oid):
                raise ContractApiError('native head/base changed during file pagination')
            files = current.get('files',{})
            if (not isinstance(files,dict) or not isinstance(files.get('nodes'),list) or not files['nodes']
                    or not isinstance(files.get('pageInfo'),dict)
                    or type(files['pageInfo'].get('hasNextPage')) is not bool):
                raise ContractApiError('native changed-file pagination returned an empty or invalid page')
            nodes.extend(files['nodes'])
            if len(nodes) > len(manifest['allowed_write_files']):
                raise ContractApiError('native changed-file pagination exceeds exact allowed files')
        pull_request['files'] = {'nodes':nodes,'pageInfo':{'hasNextPage':False}}
    if manifest_path:
        nodes = pull_request['files']['nodes']
        paths = [n.get('path') if isinstance(n,dict) else None for n in nodes]
        if (any(not isinstance(p,str) or not p for p in paths) or len(paths)!=len(set(paths))
                or not set(paths) <= set(manifest['allowed_write_files'])):
            raise ContractApiError('native changed files repeat, omit or escape exact paths')
        if type(pull_request.get('changedFiles')) is not int or len(nodes) != pull_request['changedFiles']:
            raise ContractApiError('complete native changed-file count differs from paginated paths')
    if manifest_path and any(n.get('changeType')=='RENAMED' for n in pull_request.get('files',{}).get('nodes',[])):
        raise ContractApiError('scope manifest cannot authorize a rename without its complete old/new path witness')
    bulk_paths = {}
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
        if manifest_path:
            if node.get('changeType') not in {'ADDED','MODIFIED','DELETED'}:
                raise ContractApiError('unsupported native change type for '+path)
            bulk_paths.setdefault((content_repository,content_ref),[]).append(path)
        else:
            file_contents[path] = read_content(path,content_repository,content_ref)
    if manifest_path:
        for (content_repository,content_ref),paths in bulk_paths.items():
            file_contents.update(_batch_blob_contents(paths,content_repository,content_ref,
                token,api_url,graphql_url,request_json))
        latest = request_json(graphql_url,token,data={'query':GRAPHQL_QUERY,
            'variables':{'owner':owner,'name':name,'number':number}})
        current = latest.get('data',{}).get('repository',{}).get('pullRequest')
        if (latest.get('errors') or not isinstance(current,dict)
                or any(current.get(key) != pull_request.get(key) for key in [
                    'headRefOid','baseRefOid','headRefName','headRepository','baseRepository',
                    'closingIssuesReferences','body','author','changedFiles'])):
            raise ContractApiError('native head/base or linked scope changed during content retrieval')
    return pull_request, file_contents
