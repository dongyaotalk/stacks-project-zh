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

## 7. 独立模型修订与复合来源合同

修订证据由 `schema/model-correction.schema.json` 和 `stacks_zh/model_corrections.py`
校验，并通过现有 schema/provenance/decision/render 接口执行。纯工具 v1 仍不允许
自由重译；只有 v2 中明确引用完整修订证据的 `model-revision` 操作允许改变自然语言。

较长脚注、漏译或需要改变中文表达的术语补齐不是纯机械操作。它们使用新的
`run_kind: revision`：实际模型身份、动态 Harness 版本、当前 source commit、
完整受影响 unit_ids、冻结 unit/context、提示词/政策/词表版本和运行时间均单独
保存。完整模型输出保存为不可变 candidate v2 快照，新 run 不覆盖原 run。
输入可以明确包含同 unit 的旧候选作为修订对象，不能把它作为 approved TM。

配套修订证据须保存冻结 unit/candidate 路径与原字节 hash。当前工具派生仍保留
旧模型原输出的字节及来源，另用明确的模型修订引用连接新 run 和完整新输出。
纯坐标/保护/显示操作继续使用 §6 的受限变换；自由自然语言变化仅在其全部内容
和术语元数据与新模型原输出吻合、当前来源 hash 和上下文吻合时允许。缺少证据、
不匹配的输出、模型/run 身份篡改、重复修订、过期来源或孤立修订记录均须失败。

原模型字段表示原生成的身份，不能被用来宣称全部当前文字仍由旧模型生成。
派生记录列明原 run、新修订 run、精确作用范围和修订时间，预览同时列出原生成
与修订模型及运行数量。目录名仅是检索通道；正式选择/审校必须绑定当前完整
内容 hash 和完整来源链，不能只检查旧 origin_run_id 后就忽略新增修订。

原 run/原输出、修订 run/修订原输出以及派生记录都不回写。当前来源只保留一个
活跃版本；修订快照不单独计为第二份当前候选，不进入 approved TM。模型修订仍
是未经人工审校的候选，未知术语不因换模型而获批准，语义变化不继承旧审校。

当前新增模型登记为 `openai:gpt-6.1-sol:declared`。依据是实际 Codex turn 元数据，
模型字段明确为 `gpt-6.1-sol`；供应商 snapshot 未暴露，登记 `snapshot: null` 和
`replayable: false`，不虚构 owner-confirmed、后端 snapshot 或可保证重放。

### 7.1 可核验文件与输入

```text
translation-data/model-corrections/<correction-id>.json
translation-data/retired/model-corrections/<correction-id>/units.jsonl
translation-data/retired/model-corrections/<correction-id>/candidates.jsonl
```

证据记录保存 source commit、修订 run、生成时间、完整有序 unit 列表、每个 unit
对应的派生 ID，以及两个原字节快照的路径/hash。一份修订 run 对应一份完整证据，
可以在同章关联多个派生批次。冻结 unit 必须与当前派生的完整 source/render/hash
相等；新原输出的 `context.source_unit` 保存该 unit，`context.revision_input` 使用
`kind: candidate-to-revise`、完整原 unit（`source_unit`）和完整原 `candidate`。重放
核对两个原输入完全相等，不能把旧候选混称 approved TM，或替换为相同正文但
不同来源的输入。原 unit 只用于解释旧候选的占位符，译文使用当前冻结 source。

当前 translation、allowed_english、term_occurrences、unknown_terms、notes 全部与
新原输出相等；model/run/time 保留原生成身份，另有 `model_correction_id`。两个
来源分别按模型登记和 run 核验；未知身份、unknown Harness、过期源、不同上下文、
重复/孤立输出、伪术语批准或未披露修订均失败。证据、快照和修订 run 一旦进入
Git，其字节必须等于可达历史中的第一次加入，不能通过重算 hash 覆盖。

### 7.2 正式选择与审校的来源绑定

含 `model_correction_id` 的候选，其 selection、语言/数学 review 及正式 revision
必须提供 `provenance_hash`。该 hash 覆盖完整当前候选、派生、修订证据、原 run 和
修订 run；通过 `candidate_provenance_hash(root, candidate)` 在溯源全部通过后计算。
正文 hash 相同也不能沿用不含完整来源绑定的旧批准。普通历史候选不要求新增字段。
这个绑定不授予批准：术语和人工审校门禁继续独立执行。
