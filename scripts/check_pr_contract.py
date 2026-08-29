#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stacks_zh.pr_contract import ContractApiError, fetch_pr_contract, validate_pr_contract


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    number_text = os.environ.get("PR_NUMBER", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    graphql_url = os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql")
    if not repository or not number_text or not token:
        print(
            "ERROR: GITHUB_REPOSITORY, PR_NUMBER and GITHUB_TOKEN are required",
            file=sys.stderr,
        )
        return 2
    try:
        pull_request, file_contents = fetch_pr_contract(
            repository,
            int(number_text),
            token,
            api_url=api_url,
            graphql_url=graphql_url,
        )
    except (ContractApiError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate_pr_contract(repository, pull_request, file_contents)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    issue = pull_request["closingIssuesReferences"]["nodes"][0]
    print(
        f"PR contract: PASS (PR #{pull_request['number']} -> Issue #{issue['number']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
