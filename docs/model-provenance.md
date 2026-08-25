# Harness、模型和运行溯源

本项目同时支持不同的执行工具（Harness）和不同的模型。二者必须分开记录：

```text
Harness = 谁负责执行任务
Model   = 实际生成文本的模型
Run     = 某一次冻结输入后的运行
```

例如：

```text
harness_id: codex
model_record_id: openai:gpt-5.6-sol:owner-confirmed
run_id: run-20260825-categories-001m-gpt56sol-01
```

`codex` 不等于 GPT-5.6-sol，`claude-code` 也不自动等于 Opus。任务清单和 run
manifest 必须同时写明 Harness 和具体模型。

## 1. 三个身份

### Harness

可用 Harness 在 `config/harnesses.yml` 登记，例如：

- `codex`
- `claude-code`
- `custom-api`

Harness 记录 `id`、版本和项目适配器版本。工具版本不可得时写 `unknown`，不得
猜测。

### Model

模型记录在 `config/models.yml` 的 `model_records` 中。至少保存：

- provider；
- 请求的模型 ID；
- 运行时解析出的模型 ID；
- snapshot 或 revision（如果服务提供）；
- 身份置信度；
- 是否能够重新运行；
- active、deprecated、retired 或 unavailable 状态。

模型别名可能在服务端改变含义。没有 snapshot 时必须写 `snapshot: null`，并将
`replayable` 设为 `false`，不能把营销名称当作不可变版本。

### Run

每次生成候选都创建不可覆盖的 `run_id`。同一个模型再次执行也必须使用新的
`run_id`，因为输入包、提示词、上下文、服务端后端或参数可能已经变化。

运行清单必须符合 `schema/run-manifest.schema.json`，并保存：

- 英文 `source_commit`；
- 完整 `unit_ids`；
- Harness 身份；
- 模型身份；
- prompt、policy、glossary 版本；
- 上下文 hash；
- 生成时间和运行可重放性。

## 2. 目录和权威性

```text
translation-data/
├── runs/<run-id>.json                 # 一次运行的不可变事实
├── candidates/<model-lane>/          # 候选译文，按模型便于浏览
├── selections/                       # 维护者选择或拒绝候选的决定
├── reviewed/                         # 正式译文事实
└── retired/                          # 被替换或上游退休的记录
```

目录名只是索引，不能单独证明模型身份。真正的身份以候选记录和 run manifest
为准。

模型候选进入 `main` 只表示这次实验被保存，不表示它已经成为正式译文。正式译文
必须有 selection、所需人工审校和 translation revision 记录。

## 3. 模型下架

模型下架不会使历史候选或已发布译文失效。应当：

1. 将模型注册表状态改为 `retired` 或 `unavailable`；
2. 保留旧候选、run manifest 和审校记录；
3. 使用新模型创建新的 run；
4. 生成新候选并重新进行必要审校；
5. 通过 translation revision 记录新版本 `supersedes` 旧版本。

不得把旧候选的模型名称批量改成新模型，也不得因为新模型更好就覆盖旧记录。

## 4. 历史记录的身份置信度

历史记录可以使用以下值：

```text
runtime-resolved   服务运行时返回了精确模型版本
owner-confirmed    项目维护者确认了具体模型，但后端 snapshot 未暴露
declared           任务声明了模型，尚未由运行时确认
unknown            无法确认
```

当前早期 Codex 候选根据项目所有者确认登记为
`openai:gpt-5.6-sol:owner-confirmed`；由于原运行没有暴露 snapshot，仍标记为
不可保证重放。

## 5. 不保存隐藏推理

为了溯源，应保存可见的输入、输出、提示词版本、上下文 hash 和配置；不要求保存
模型的隐藏推理或内部思维链。模型身份和翻译结果必须可审查，隐藏推理不是项目事实来源。
