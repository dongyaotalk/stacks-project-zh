SHELL := /bin/sh

ENGINE ?= xelatex
MODEL ?= template
PYTHON ?= python3
BATCH ?=
MODEL_DISPLAY_NAME ?= $(MODEL) 模型候选译文
-include config/local.mk
HARVEST_DIR ?= ../stacks-project
CHAPTER_MANIFEST ?= $(HARVEST_DIR)/chapters.tex
CHAPTER_SOURCE_DIR ?= $(HARVEST_DIR)
CHAPTER_TITLE_MAP ?= config/chapter-titles.json
TAGS_FILE ?= $(HARVEST_DIR)/tags/tags
UPSTREAM_LOCK ?= upstream.lock
BUILD_ROOT ?= build
OUTPUT_DIR ?= output/pdf
CHAPTER_TEMPLATE_DIR ?= translation-data/chapter-templates
HARNESS_ID ?= codex
HARNESS_CONFIG ?= config/harnesses.yml

UPSTREAM_REPOSITORY := $(shell sed -n 's/^repository = "\(.*\)"$$/\1/p' "$(UPSTREAM_LOCK)" 2>/dev/null)
UPSTREAM_COMMIT := $(shell sed -n 's/^commit = "\(.*\)"$$/\1/p' "$(UPSTREAM_LOCK)" 2>/dev/null)
UPSTREAM_COMMIT_DATE := $(shell sed -n 's/^commit_date = "\(.*\)"$$/\1/p' "$(UPSTREAM_LOCK)" 2>/dev/null)

TEMPLATE_DIR := springer-template
MAIN := stacks-project-zh.tex
MODEL_DIR := $(TEMPLATE_DIR)/translations/$(MODEL)
BUILD_DIR := $(BUILD_ROOT)/$(MODEL)
ABS_BUILD_DIR := $(abspath $(BUILD_DIR))
JOBNAME := stacks-project-zh-$(MODEL)
PDF := $(BUILD_DIR)/$(JOBNAME).pdf
OUTPUT_PDF := $(OUTPUT_DIR)/$(JOBNAME).pdf
INDEX_STYLE := $(TEMPLATE_DIR)/styles/svind-zh.ist

WORKFLOW_FILES := \
	README.md \
	WORKFLOW.md \
	CONTRIBUTING.md \
	GOVERNANCE.md \
	MAINTAINERS.md \
	CODE_OF_CONDUCT.md \
	SECURITY.md \
	LICENSE \
	LICENSES/MIT.txt \
	THIRD_PARTY_NOTICES.md \
	UPSTREAM_HISTORY.md \
	docs/data-model.md \
	docs/translation-rules.md \
	docs/review-and-qa.md \
	docs/upstream-sync.md \
	docs/git-conventions.md \
	docs/codex-workflow.md \
	docs/release.md \
	docs/github-collaboration.md \
	docs/task-allocation.md \
	docs/terminology.md \
	docs/licensing.md \
	docs/ci.md \
	docs/model-provenance.md \
	docs/progress.md \
	docs/translation-progress.md \
	docs/candidate-selection.md \
	docs/translation-replacement.md \
	review/language/README.md \
	review/mathematics/README.md \
	config/workflow.yml \
	config/harnesses.yml \
	config/macro-policy.yml \
	config/chapter-titles.json \
	config/glossary.yml \
	config/models.yml \
	config/style-guide.md \
	schema/unit.schema.json \
	schema/chapter-template.schema.json \
	schema/candidate.schema.json \
	schema/review.schema.json \
	schema/run-manifest.schema.json \
	schema/selection.schema.json \
	schema/translation-revision.schema.json \
	schema/upstream-sync-report.schema.json \
	schema/upstream-index-manifest.schema.json \
	schema/translator-output.schema.json \
	.github/pull_request_template.md \
	.github/CODEOWNERS \
	.github/ISSUE_TEMPLATE/config.yml \
	.github/ISSUE_TEMPLATE/translation-task.yml \
	.github/ISSUE_TEMPLATE/terminology.yml \
	.github/ISSUE_TEMPLATE/review-request.yml \
	.github/ISSUE_TEMPLATE/translation-problem.yml \
	.github/ISSUE_TEMPLATE/codeowner-application.yml \
	.github/ISSUE_TEMPLATE/work-item.yml \
	.github/ISSUE_TEMPLATE/unit-preparation.yml \
	.github/workflows/ci.yml \
	.github/workflows/pr-contract.yml \
	prompts/README.md \
	prompts/translator-v1.md \
	prompts/translator-v2.md \
	migration/model-identity-map.json \
	migration/unit-id-map.json \
	scripts/migrate_model_identity.py \
	scripts/migrate_permanent_tags.py \
	scripts/check_pr_contract.py \
	scripts/upstream_diff.py \
	stacks_zh/decisions.py \
	stacks_zh/harness.py \
	stacks_zh/chapter_templates.py \
	stacks_zh/provenance.py \
	stacks_zh/pr_contract.py \
	stacks_zh/progress.py \
	stacks_zh/records.py \
	stacks_zh/schema_validation.py \
	stacks_zh/upstream.py \
	stacks_zh/workflow.py \
	upstream-index/README.md \
	translation-data/chapter-templates/README.md

BASELINE_REPORT := sync-reports/baseline-a04446e5.json
BASELINE_INDEX_MANIFEST := upstream-index/manifests/$(UPSTREAM_COMMIT).json

UNIT_FILE := translation-data/units/$(BATCH).jsonl
CANDIDATE_FILE := translation-data/candidates/$(MODEL)/$(BATCH).jsonl
MODEL_CANDIDATE_FILES = $(sort $(wildcard translation-data/candidates/$(MODEL)/*.jsonl))
MODEL_BATCHES = $(notdir $(basename $(MODEL_CANDIDATE_FILES)))
MODEL_UNIT_FILES = $(addprefix translation-data/units/,$(addsuffix .jsonl,$(MODEL_BATCHES)))

SOURCE_REVISION ?= $(shell printf '%s' '$(UPSTREAM_COMMIT)' | cut -c1-12)
SOURCE_DATE ?= $(UPSTREAM_COMMIT_DATE)

TEX_SEARCH_PATH := $(abspath $(TEMPLATE_DIR)):$(abspath $(TEMPLATE_DIR)/styles):
BIB_SEARCH_PATH := $(abspath $(HARVEST_DIR)):$(abspath $(TEMPLATE_DIR)):
BST_SEARCH_PATH := $(abspath $(TEMPLATE_DIR)):$(abspath $(TEMPLATE_DIR)/styles):

LATEX_COMMAND = cd "$(TEMPLATE_DIR)" && \
	TEXINPUTS="$(TEX_SEARCH_PATH)" BIBINPUTS="$(BIB_SEARCH_PATH)" BSTINPUTS="$(BST_SEARCH_PATH)" \
	$(ENGINE) -interaction=nonstopmode -halt-on-error -file-line-error \
	-output-directory="$(ABS_BUILD_DIR)" -jobname="$(JOBNAME)" \
	"\def\TranslationModel{$(MODEL)}\def\StacksSourceRevision{$(SOURCE_REVISION)}\def\StacksSourceDate{$(SOURCE_DATE)}\input{$(MAIN)}"

.PHONY: all pdf template check repo-setup workflow-check harvest-check upstream-index-check chapter-template-check init-chapters progress progress-check tool-test schema-check provenance-check decision-check harness-version harness-check upstream-diff qa qa-all render validate-batch validate-render validate-model list-models help clean distclean

all: pdf

pdf: check
	@mkdir -p "$(BUILD_DIR)" "$(OUTPUT_DIR)"
	$(LATEX_COMMAND)
	@if grep -q '^\\bibdata' "$(BUILD_DIR)/$(JOBNAME).aux"; then \
		cd "$(BUILD_DIR)" && BIBINPUTS="$(BIB_SEARCH_PATH)" BSTINPUTS="$(BST_SEARCH_PATH)" bibtex "$(JOBNAME)"; \
	fi
	@if test -s "$(BUILD_DIR)/$(JOBNAME).idx"; then \
		makeindex -s "$(CURDIR)/$(INDEX_STYLE)" \
			-o "$(BUILD_DIR)/$(JOBNAME).ind" "$(BUILD_DIR)/$(JOBNAME).idx"; \
	fi
	$(LATEX_COMMAND)
	$(LATEX_COMMAND)
	cp "$(PDF)" "$(OUTPUT_PDF)"
	@printf 'Built %s\n' "$(OUTPUT_PDF)"

# Backward-compatible, deterministic smoke-test target.
template:
	@$(MAKE) --no-print-directory pdf MODEL=template

tool-test:
	$(PYTHON) -m compileall -q stacks_zh.py stacks_zh tests
	$(PYTHON) stacks_zh.py -h >/dev/null
	$(PYTHON) -m stacks_zh -h >/dev/null
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

provenance-check:
	$(PYTHON) stacks_zh.py provenance-check --root .

decision-check:
	$(PYTHON) stacks_zh.py decision-check --root .

schema-check:
	$(PYTHON) stacks_zh.py schema-check --root .

upstream-index-check:
	$(PYTHON) stacks_zh.py upstream-index-check --root . --harvest "$(HARVEST_DIR)"

init-chapters: harvest-check upstream-index-check
	$(PYTHON) stacks_zh.py init-chapters --root . --harvest "$(HARVEST_DIR)" \
		--lock "$(UPSTREAM_LOCK)" --units-dir translation-data/units \
		--output-dir "$(CHAPTER_TEMPLATE_DIR)"

chapter-template-check: harvest-check upstream-index-check
	$(PYTHON) stacks_zh.py init-chapters --root . --harvest "$(HARVEST_DIR)" \
		--lock "$(UPSTREAM_LOCK)" --units-dir translation-data/units \
		--output-dir "$(CHAPTER_TEMPLATE_DIR)" --check

progress:
	$(PYTHON) stacks_zh.py progress --root . --tags "$(TAGS_FILE)"

progress-check:
	$(PYTHON) stacks_zh.py progress --root . --tags "$(TAGS_FILE)" --check

harness-version:
	@test -n "$(strip $(HARNESS_ID))" || { printf 'HARNESS_ID is required\n' >&2; exit 1; }
	$(PYTHON) stacks_zh.py harness-version --harness-id "$(HARNESS_ID)" --config "$(HARNESS_CONFIG)"

harness-check: harness-version

upstream-diff:
	@test -n "$(OLD_UNITS)" || { printf 'OLD_UNITS is required\n' >&2; exit 1; }
	@test -n "$(NEW_UNITS)" || { printf 'NEW_UNITS is required\n' >&2; exit 1; }
	@test -n "$(NEW_COMMIT)" || { printf 'NEW_COMMIT is required\n' >&2; exit 1; }
	@test -n "$(OUTPUT_JSON)" || { printf 'OUTPUT_JSON is required\n' >&2; exit 1; }
	@test -n "$(OUTPUT_MD)" || { printf 'OUTPUT_MD is required\n' >&2; exit 1; }
	$(PYTHON) scripts/upstream_diff.py \
		--old-units "$(OLD_UNITS)" --new-units "$(NEW_UNITS)" \
		$(if $(OLD_COMMIT),--old-commit "$(OLD_COMMIT)",) \
		--new-commit "$(NEW_COMMIT)" \
		$(if $(OLD_TAGS),--old-tags "$(OLD_TAGS)",) \
		$(if $(NEW_TAGS),--new-tags "$(NEW_TAGS)",) \
		$(if $(OLD_CHAPTERS),--old-chapters "$(OLD_CHAPTERS)",) \
		$(if $(NEW_CHAPTERS),--new-chapters "$(NEW_CHAPTERS)",) \
		$(if $(UNIT_ID_MAP),--unit-id-map "$(UNIT_ID_MAP)",) \
		--output-json "$(OUTPUT_JSON)" --output-md "$(OUTPUT_MD)"

validate-batch:
	@test -n "$(BATCH)" || { printf 'BATCH is required\n' >&2; exit 1; }
	@test "$(MODEL)" != template || { printf 'MODEL must identify a candidate lane\n' >&2; exit 1; }
	@test -f "$(UNIT_FILE)" || { printf 'Missing unit file: %s\n' "$(UNIT_FILE)" >&2; exit 1; }
	@test -f "$(CANDIDATE_FILE)" || { printf 'Missing candidate file: %s\n' "$(CANDIDATE_FILE)" >&2; exit 1; }

qa: validate-model validate-batch workflow-check harvest-check upstream-index-check chapter-template-check schema-check provenance-check decision-check
	$(PYTHON) stacks_zh.py validate \
		--units "$(UNIT_FILE)" \
		--candidates "$(CANDIDATE_FILE)" \
		--lock "$(UPSTREAM_LOCK)"

qa-all: workflow-check harvest-check upstream-index-check chapter-template-check schema-check provenance-check decision-check
	@set -eu; count=0; \
		for candidate in translation-data/candidates/*/*.jsonl; do \
			model=$$(basename "$$(dirname "$$candidate")"); \
			batch=$$(basename "$$candidate" .jsonl); \
			unit="translation-data/units/$$batch.jsonl"; \
			test -f "$$unit" || { printf 'Missing unit file: %s\n' "$$unit" >&2; exit 1; }; \
			$(PYTHON) stacks_zh.py validate --units "$$unit" --candidates "$$candidate" --lock "$(UPSTREAM_LOCK)" >/dev/null; \
			count=$$((count + 1)); \
		done; \
		printf 'All candidate batches: PASS (%s batch(es))\n' "$$count"

validate-render:
	@test -n "$(strip $(MODEL_CANDIDATE_FILES))" || { printf 'No candidate batches for MODEL=%s\n' "$(MODEL)" >&2; exit 1; }
	@set -eu; for file in $(MODEL_UNIT_FILES); do \
		test -f "$$file" || { printf 'Missing unit file: %s\n' "$$file" >&2; exit 1; }; \
	done

render: validate-model validate-render workflow-check harvest-check
	$(PYTHON) stacks_zh.py render \
		--units $(foreach file,$(MODEL_UNIT_FILES),"$(file)") \
		--candidates $(foreach file,$(MODEL_CANDIDATE_FILES),"$(file)") \
		--lock "$(UPSTREAM_LOCK)" \
		--model-lane "$(MODEL)" \
		--display-name "$(MODEL_DISPLAY_NAME)" \
		--chapter-manifest "$(CHAPTER_MANIFEST)" \
		--chapter-title-map "$(CHAPTER_TITLE_MAP)" \
		--chapter-source-dir "$(CHAPTER_SOURCE_DIR)" \
		--tags-file "$(TAGS_FILE)" \
		--output-dir "$(MODEL_DIR)"

check: validate-model workflow-check harvest-check
	@command -v "$(ENGINE)" >/dev/null || { printf 'Missing TeX engine: %s\n' "$(ENGINE)" >&2; exit 1; }
	@command -v bibtex >/dev/null || { printf 'Missing command: bibtex\n' >&2; exit 1; }
	@command -v makeindex >/dev/null || { printf 'Missing command: makeindex\n' >&2; exit 1; }
	@test -f "$(MODEL_DIR)/metadata.tex" || { printf 'Missing model metadata: %s/metadata.tex\n' "$(MODEL_DIR)" >&2; exit 1; }
	@test -f "$(MODEL_DIR)/contents.tex" || { printf 'Missing model contents: %s/contents.tex\n' "$(MODEL_DIR)" >&2; exit 1; }

repo-setup:
	@git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { printf 'Not inside a Git worktree\n' >&2; exit 1; }
	@git config core.hooksPath .githooks
	@git config commit.template .gitmessage
	@git config core.fileMode false
	@chmod +x .githooks/commit-msg
	@printf '%s\n' \
		'Configured repository-local Git settings:' \
		'  core.hooksPath=.githooks' \
		'  commit.template=.gitmessage' \
		'  core.fileMode=false'

workflow-check:
	@set -eu; \
		for file in $(WORKFLOW_FILES); do \
			test -s "$$file" || { printf 'Missing or empty workflow file: %s\n' "$$file" >&2; exit 1; }; \
		done; \
		test -s .gitmessage || { printf 'Missing commit template: .gitmessage\n' >&2; exit 1; }; \
		test -s .githooks/commit-msg || { printf 'Missing commit hook: .githooks/commit-msg\n' >&2; exit 1; }; \
		sh -n .githooks/commit-msg; \
		.githooks/commit-msg tests/commit-messages/valid-docs.txt; \
		.githooks/commit-msg tests/commit-messages/valid-translate.txt; \
		if .githooks/commit-msg tests/commit-messages/invalid-translate.txt >/dev/null 2>&1; then \
			printf 'Commit hook accepted invalid fixture\n' >&2; exit 1; \
		fi; \
		test -s "$(BASELINE_REPORT)" || { printf 'Missing baseline sync report: %s\n' "$(BASELINE_REPORT)" >&2; exit 1; }; \
		test -s "$(BASELINE_INDEX_MANIFEST)" || { printf 'Missing upstream index manifest: %s\n' "$(BASELINE_INDEX_MANIFEST)" >&2; exit 1; }; \
		grep -Fq '"commit": "$(UPSTREAM_COMMIT)"' "$(BASELINE_INDEX_MANIFEST)" || { printf 'Upstream index manifest does not match upstream.lock\n' >&2; exit 1; }; \
		printf 'Workflow policy: OK (%s required files)\n' "$(words $(WORKFLOW_FILES))"

harvest-check:
	@set -eu; \
		test -f "$(UPSTREAM_LOCK)" || { printf 'Missing upstream lock: %s\n' "$(UPSTREAM_LOCK)" >&2; exit 1; }; \
		test -n "$(UPSTREAM_REPOSITORY)" || { printf 'Missing repository in %s\n' "$(UPSTREAM_LOCK)" >&2; exit 1; }; \
		test -n "$(UPSTREAM_COMMIT)" || { printf 'Missing commit in %s\n' "$(UPSTREAM_LOCK)" >&2; exit 1; }; \
		test -n "$(UPSTREAM_COMMIT_DATE)" || { printf 'Missing commit_date in %s\n' "$(UPSTREAM_LOCK)" >&2; exit 1; }; \
		test -f "$(HARVEST_DIR)/preamble.tex" || { printf 'Invalid HARVEST_DIR: %s\n' "$(HARVEST_DIR)" >&2; exit 1; }; \
		git -C "$(HARVEST_DIR)" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { printf 'HARVEST_DIR is not a Git worktree: %s\n' "$(HARVEST_DIR)" >&2; exit 1; }; \
		actual_remote=$$(git -C "$(HARVEST_DIR)" remote get-url origin 2>/dev/null || true); \
		actual_commit=$$(git -C "$(HARVEST_DIR)" rev-parse HEAD); \
		actual_commit_date=$$(git -C "$(HARVEST_DIR)" show -s --format=%cs HEAD); \
		dirty=$$(git -C "$(HARVEST_DIR)" status --short --untracked-files=no); \
		test "$$actual_remote" = "$(UPSTREAM_REPOSITORY)" || { printf 'Harvest remote mismatch\n  expected: %s\n  actual:   %s\n' "$(UPSTREAM_REPOSITORY)" "$$actual_remote" >&2; exit 1; }; \
		test "$$actual_commit" = "$(UPSTREAM_COMMIT)" || { printf 'Harvest commit mismatch\n  expected: %s\n  actual:   %s\n' "$(UPSTREAM_COMMIT)" "$$actual_commit" >&2; exit 1; }; \
		test "$$actual_commit_date" = "$(UPSTREAM_COMMIT_DATE)" || { printf 'Harvest commit date mismatch\n  expected: %s\n  actual:   %s\n' "$(UPSTREAM_COMMIT_DATE)" "$$actual_commit_date" >&2; exit 1; }; \
		test -z "$$dirty" || { printf 'Harvest has tracked modifications:\n%s\n' "$$dirty" >&2; exit 1; }; \
		printf '%s\n' \
			"Harvest directory: $(HARVEST_DIR)" \
			"Repository: $(UPSTREAM_REPOSITORY)" \
			"Commit: $(UPSTREAM_COMMIT)" \
			"Commit date: $(UPSTREAM_COMMIT_DATE)" \
			"Working tree: clean" \
			"Status: OK"

validate-model:
	@case '$(MODEL)' in \
		''|*[!A-Za-z0-9._-]*|*..*) \
			printf 'Invalid MODEL: %s (use letters, digits, dot, underscore, or hyphen; no ..)\n' '$(MODEL)' >&2; \
			exit 1 ;; \
	esac

list-models:
	@awk '/^  [A-Za-z0-9._-]+:$$/ {gsub(":", "", $$1); print $$1}' config/models.yml | LC_ALL=C sort

help:
	@printf '%s\n' \
		'make repo-setup                  Configure repository-local Git rules' \
		'make workflow-check              Verify required workflow policy files' \
		'make harvest-check              Verify harvest remote, revision, and cleanliness' \
		'make upstream-index-check       Verify locked Tag/chapter index and sync history' \
		'make progress                   Refresh README and per-chapter translation progress' \
		'make progress-check             Verify committed translation progress is current' \
		'make tool-test                  Run candidate pipeline tests' \
		'make schema-check                Validate all structured records against JSON Schema' \
		'make provenance-check           Verify candidates and model runs' \
		'make decision-check             Verify selections, reviews and revisions' \
		'make harness-check HARNESS_ID=codex  Resolve the current Harness version' \
		'make upstream-diff OLD_UNITS=... NEW_UNITS=... NEW_COMMIT=... OUTPUT_JSON=... OUTPUT_MD=...' \
		'make qa BATCH=<batch> MODEL=<model>       Validate one candidate batch' \
		'make qa-all                     Validate every tracked candidate batch' \
		'make render MODEL=<model>                 Render all batches in a model lane' \
		'make template                   Build the template smoke test' \
		'make pdf MODEL=<model>          Build springer-template/translations/<model>' \
		'make list-models                List configured translation model lanes' \
		'make clean MODEL=<model>        Remove one model build directory' \
		'make distclean                  Remove all generated files' \
		'' \
		'Optional: HARVEST_DIR=/path/to/stacks-project ENGINE=xelatex' \
		'Local override: config/local.mk (ignored by Git)'

clean: validate-model
	rm -rf "$(BUILD_DIR)"
	rm -f "$(OUTPUT_PDF)"

distclean:
	rm -rf "$(BUILD_ROOT)" "$(OUTPUT_DIR)"
