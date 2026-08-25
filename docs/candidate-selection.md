# 候选选择和进入正式译文

模型候选、维护者选择和正式译文是三个不同阶段：

```text
生成候选 → 保存候选 → 维护者选择 → 人工审校 → 正式译文
```

候选可以合并到 `main` 保存实验结果，但不能仅凭进入 `main` 就获得
`LANGUAGE_REVIEWED`、`MATH_REVIEWED` 或 `PUBLISHED` 状态。

## 候选 PR

候选 PR 只能新增或修改指定 run 和 unit 的候选记录，并且必须写明：

- 英文 source commit；
- Harness 及其版本；
- 具体 provider/model ID；
- model record 和 run ID；
- prompt、policy、glossary 和 context hash；
- 结构、术语和构建结果，以及人工提供的 critic 状态。当前仓库尚未实现 critic
  记录 Schema 和自动提升命令，不得把 `TERM_OK` 候选描述成已通过 `CRITIC_OK`。

候选可以被维护者：

- 保存为可比较的历史候选；
- 要求修改后重新运行；
- 直接拒绝；
- 选择进入正式译文流程。

## Selection 记录

选择和拒绝必须写入符合 `schema/selection.schema.json` 的记录，至少包含：

```json
{
  "schema_version": 1,
  "selection_id": "selection-001M-statement-003",
  "unit_id": "tag:001M:statement",
  "source_commit": "a04446e57ec1fbc252a871afcec7752fb2807b14",
  "run_id": "run-20260825-categories-001m-gpt56sol-01",
  "translation_hash": "sha256:...",
  "decision": "accept-candidate",
  "decided_by": "github:maintainer",
  "decided_at": "2026-08-25T00:00:00Z",
  "reason": "结构、术语和语义检查通过，等待规定的人工审校。"
}
```

`decided_by` 必须是真实维护者身份。模型、自动 QA 和候选作者不能代替维护者
决定，也不能伪造人工审校。

## 正式采用

维护者选择候选后，仍要根据风险等级完成语言和数学审校。正式记录应符合
`schema/translation-revision.schema.json`，并指向候选的 `run_id` 和
`translation_hash`。revision 必须同时保存经过校验的 `translation`、
`source_text_hash`、`selection_id`、风险等级、人工审校 ID 和
`supersedes_revision_id`；只存 hash 不能生成正式译文。正式译文只从 `reviewed/`
生成，候选目录不参与权威 Translation Memory。`make decision-check` 会验证这些
引用和审校链。
