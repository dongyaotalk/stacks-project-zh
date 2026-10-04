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

Harness 记录 `id`、版本和项目适配器版本。新运行不得手工复制版本，也不得写
`unknown`：使用 `--harness-version auto`（默认）或 `make harness-check
HARNESS_ID=<harness-id>`，由 `config/harnesses.yml` 中登记的命令在运行时执行并
解析版本。命令失败、输出为空或无法解析时，运行必须失败。`unknown` 只保留给
不可回写的历史 manifest。

当前桌面 Codex 会优先使用客户端导出的 `CODEX_MCP_NODE_PATH` 推导嵌入式
`codex` 可执行文件；没有该环境信息时才回退到注册的 `codex --version`。因此
客户端升级后，新运行会自动记录升级后的 Harness 版本。

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

## 6. 历史候选的工具派生合同

坐标、提取包装和已有译文的机械显示修复不创建伪造的模型 run，也不改写原 run。
机器合同位于 `schema/derivation.schema.json` 与 `stacks_zh/derivations.py`；
`schema-check` 检查记录，`provenance-check` 检查快照、Git 原字节和重放结果。

```text
translation-data/derivations/<derivation-id>.json
translation-data/retired/derivations/<derivation-id>/units.jsonl
translation-data/retired/derivations/<derivation-id>/candidates.jsonl
```

每个派生记录必须声明：schema 版本、唯一派生 ID、工具 ID/版本、源 commit、
中文仓库的 `origin_commit`、
生成时间、活跃 unit/candidate 路径、原字节快照路径及四个文件的 sha256、完整
旧→新 unit 映射、逐单元操作与理由。输入快照还须与可达 `origin_commit` 中原活跃
路径的 Git blob 原字节相同；原 run 也须与该 commit 的字节相同。只重算快照 hash
不能篡改原输出。校验环境须具备对应中文 Git 历史。操作必须可以从输入快照重放，输出字节和
记录 hash 必须与活跃数据一致；路径只能位于本仓库声明的目录，不能引用外部文件。
工具校验还须拒绝 ID 冲突、快照覆盖、重复派生和未经声明的模型/审批字段变化。

当前候选使用 `derivation_id` 引用工具派生；原 Harness/model/run/created_at 保留为
原始生成的身份和时间，派生时间独立记录。溯源检查先用原候选快照核对原 run 的
unit_ids/context_hashes，再核对变换后的当前候选。不能把新坐标 hash 回写到原 run
来绕过检查。原单位和模型输出快照保留原字节；历史 manifest 仍位于 `runs/`。

工具操作的范围须明确：永久 Tag 坐标重映射、源包装/占位符重提取、根据已声明
source/target 配对补齐双语显示，以及固定短语的脚注显示变换。自由生成或重译
自然语言必须另建实际身份可验证的新模型 run，不能作为工具操作夹带。未批准
术语仍为 `DECISION_REQUIRED`；模型和工具无权新增人工 approved 条目。

当前版本只支持一层派生，原快照不能是另一份派生候选。同一活跃 batch 只能归属
一份记录；后续多项机械修复须合并为从原始快照重放的操作清单，不能覆盖已提交
派生记录。操作只允许修改提取字段及显示/术语元数据，模型、来源、审批、阶段和
时间字段不能由操作改写。来源恢复后的 TeX 必须逐字相同；剥离机械双语英文插入
与结构控制字符后中文正文须保持相同。阶段由工具重算且最高到候选结构/术语阶段。派生输出的自然语言节点不得残留
未保护的 TeX 控制字符；历史提取缺陷必须在同一派生操作中修复。
脚注只允许固定短语 `See Remark` → `见注` 的显示变换，不开放自由重译接口。

派生不得改动来源锁、公式内容、引用指向或原始模型身份。当前数据重跑 schema、
provenance 和 QA；已有 selection/review/revision 绑定旧 hash 时必须拒绝沿用，
由独立审校/替换任务处理。活跃目录只保存一个当前版本，历史快照不进入当前
进度、渲染和权威 TM。预览必须明示工具派生，不能只显示原模型名称。
