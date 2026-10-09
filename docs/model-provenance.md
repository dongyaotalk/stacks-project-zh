# Harness、模型和运行溯源

完整来源容器的独立历史边界扩展见
[source-container-restoration.md](source-container-restoration.md) 的 2026-10-10
开发合同。`source-container-v4` 与派生 v4 是不同版本；只有在完整旧 batch
和锁定 Git 独立重算的 `legacy_boundary_witness` 支持下，才可核验带自身 Tag
的列表子项或由紧邻陈述定位的完整段落。旧容器 v1/v2/v3 与派生 v1/v2/v3
语义保持；普通容器仍生成原 v2/v3。新输出仍是逐字 Git 来源、现行保护提取及
每个新 unit 的实际模型完整五字段。该工具须先验收合并，具体事实另开 DATA
任务；扩展不改变来源锁、历史输入、数学保护、术语/critic/人审及出版门禁。

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

当前 v1/v2 只支持一层派生，原快照不能是另一份派生候选。同一活跃 batch 只能归属
一份记录；后续多项机械修复须合并为从原始快照重放的操作清单，不能覆盖已提交
派生记录。操作只允许修改提取字段及显示/术语元数据，模型、来源、审批、阶段和
时间字段不能由操作改写。当前重提取后的 TeX 必须与原 unit 逐字相同；§9 另行
锁定上游恢复合同，仅有完整验证的 v2/v3 来源恢复证据才适用例外。剥离机械双语英文插入
与结构控制字符后中文正文须保持相同。阶段由工具重算且最高到候选结构/术语阶段。派生输出的自然语言节点不得残留
未保护的 TeX 控制字符；历史提取缺陷必须在同一派生操作中修复。
脚注只允许固定短语 `See Remark` → `见注` 的显示变换，不开放自由重译接口。

派生不得改动来源锁或原始模型身份；除 §9 已验证的英文提取恢复外，公式内容与
引用指向保持不变，来源恢复本身也不得改写英文 Git 节点。当前数据重跑 schema、
provenance 和 QA；已有 selection/review/revision 绑定旧 hash 时必须拒绝沿用，
由独立审校/替换任务处理。活跃目录只保存一个当前版本，历史快照不进入当前
进度、渲染和权威 TM。预览必须明示工具派生，不能只显示原模型名称。

## 7. 独立模型修订与复合来源合同

修订证据由 `schema/model-correction.schema.json` 和 `stacks_zh/model_corrections.py`
校验，并通过现有 schema/provenance/decision/render 接口执行。纯工具 v1 仍不允许
自由重译；v2 及 §8 的 v3 中明确引用完整修订证据的 `model-revision` 操作允许改变自然语言。

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

## 8. 后续修订的归档合同

再次发现漏译时，不能回写上一模型修订的原输出，或删除其证据来满足单层限制。
本节规定由归档 Schema、v3 重放和 provenance 实现的独立扩展；具体归档与数据
必须由独立翻译任务声明。现有 v1/v2 的限制及校验继续执行，仍拒绝派生输入。

### 8.1 不可变历史与文件角色

```text
translation-data/derivation-archives/<prior-derivation-id>.json
translation-data/retired/derivations/<prior-derivation-id>/output-units.jsonl
translation-data/retired/derivations/<prior-derivation-id>/output-candidates.jsonl
```

原派生记录仍位于 `derivations/<prior-id>.json`，原输入快照、原 run/输出及此前
model-correction/run/输出均保留原路径和原字节。归档清单单独保存 schema 版本、
此前派生 ID、唯一后继派生 ID、source commit、生成时间、可达 `origin_commit`、
原记录路径/hash、两个历史输出路径/hash。原记录及历史输出必须逐字等于该
commit 中原记录及原活跃 unit/candidate 的 Git blob，且与原记录的输出 hash 和
确定性重放相等。新增归档清单和输出一旦加入 Git，其首次加入字节不可覆盖。

旧记录的输出路径保留当时活跃位置。历史校验通过已验证的归档清单将其解析到
上述冻结输出，不改写旧记录来指向新当前文件，也不把历史的 CURRENT、阶段或
审批字段改成别的状态。它们描述生成时的事实；当前性由验证后的后继关系确定。

### 8.2 后继与完整替换

v3 记录声明 `previous_derivation_id`，指向经归档、重放和 Git 字节核验的
确切直接前一派生。其 `origin_commit` 与对应归档清单一致，新输入快照等于该
commit 的上一活跃输出及归档输出；仅声称一个 ID 或重算 hash 不足以使用派生
输入。旧和新逻辑活跃文件路径保持一致，旧 unit 全部一对一映射到新 unit，不能
通过归档丢掉某个有问题的单元、切断证明链或产生第二份当前候选。

新实际 revision run 冻结完整新 source unit 及确切上一 unit/candidate；每个上一
单元都须声明新的 `model-revision` 操作、修订证据 ID 与全部五个输出字段，输出
完全等于新模型原输出。v3 不开放链式纯工具变换，v1/v2 不因新合同获得链式权限。
除 §9 已验证的英文提取恢复外，新派生逐 unit 保留源 TeX 字节和数学、标签、引用；原模型身份由
最终原始快照和原 run 验证，新文字的实际修订模型必须单独披露。

每个此前版本只有一个直接后继，每个逻辑 batch 只有一个当前末端；拒绝自引用、
环、分叉、重复活跃文件、缺失前驱/后继、悬空归档、快照篡改或重复使用某份模型
修订输出。历史派生及模型修订仍须完整溯源，不能把“不进入当前 QA”解释为
跳过历史验证。之前冻结输出可以仅由合法历史重放消费，新当前输出另由其后继
重放消费，不能因为前者不再活跃就删掉原模型证据。

### 8.3 当前检查与批准

schema/provenance 验证全部原始、历史和当前证据；当前 source/term QA、进度、
渲染和 TM 只消费当前活跃文件。候选合并及归档均不批准 glossary，不完成语言、
数学审校或出版。selection/review/revision 的来源 hash 必须绑定当前候选、原始
run 和全部祖先派生/归档/模型修订证据；即使正文未变，也不能沿用缺少新完整
来源绑定的批准。预览显示原生成、此前及本次实际模型修订的复合来源。

本扩展只处理同一锁定 source commit 的候选再次修订，不授权上游同步、变更
英文来源或继承人工批准。命名环境标题的源文重提取和具体数据修订另开任务；
本工具扩展不创建历史输出、archive manifest、新 run 或 v3 数据。

### 8.4 验证入口

`make schema-check` 覆盖归档清单及两种历史输出；`make provenance-check` 验证
全部归档、历史重放、实际修订运行及唯一当前末端。派生记录和输入快照加入 Git
后也按首次加入字节核验。v3 输入不只与前一解析行相等，还必须逐字等于对应
Git commit 的原活跃文件。溯源返回当前候选的最终原始模型快照，避免把前一
派生的已变更 context 错当成原生成 run 的输入。

selection/review/revision 的来源绑定包含完整祖先记录、归档、全部修订清单和
运行；清单中的文件 hash 绑定其冻结源/输出。原单层候选的既有绑定格式保留，
后续版本增加完整历史，因此不能复用原绑定。渲染先验证复合来源，再披露原模型
和所有历次实际修订模型及运行数量；历史输出本身不成为渲染输入。

## 9. 锁定上游的提取恢复合同

001P 的旧证明 source unit 漏掉英文 `$s$`，并改变相关词与公式的关系。锁定
commit `a04446e57ec1fbc252a871afcec7752fb2807b14` 的 `categories.tex`，
`lemma-yoneda` 紧邻 proof 有七处内联公式，当前 unit 只有六处；英文原文无须修改。
这是旧提取输入的缺陷，不是源文 remark，也不能由中文译文猜测修复。

未声明来源恢复的派生仍要求新旧 unit 恢复的 TeX 相同。`source-reextraction.schema.json`
及 `source_reextractions.py` 对受限的完整简单证明实现独立验证；仅明确引用已验证
证据的 v2/v3 模型修订适用例外。具体数据另开 Issue，先验证来源，再用实际新模型
run 完整重译。工具 PR 不创建真实恢复证据或修订原输出。

### 9.1 不可变证据与英文选择

证据位于 `translation-data/source-reextractions/<id>.json`，逐项绑定：

- schema 版本、证据 ID、派生 ID、时间及同一锁定 source commit；
- 完整旧 unit、新受保护 unit、旧/新 source TeX 字节 hash；
- 受限英文章文件路径、永久陈述 Tag/英文 label、明确 proof selector；
- 从该英文 Git object 选取的完整原始片段字节及 hash。

旧 unit 必须等于派生原输入或经验证的直接上一输出；新 unit 必须等于新模型
修订冻结的 source。证据不得替换旧 run、快照或归档，首次加入 Git 后不可改写。
既有原始字段描述原模型当时拿到的输入缺陷，不冒称修订后 source 仍是旧运行输入。

英文文件与 `tags/tags` 均从锁定 Git commit 读取，不能用工作目录、候选内容、
任意文本片段或自报 hash 代替。selector 必须唯一确定对应陈述/紧邻证明及原始
边界，拒绝不存在、重复、跨章、跨 Tag、越界和不明确的选择。先明确初始工具能
验证的语法及单元覆盖；复杂、注释或嵌套结构不能猜测，未支持的情况另作任务。
源文件只作为数据读取，绝不执行 TeX、宏或注释。

### 9.2 确定性恢复与实际模型修订

恢复后的完整 source TeX 必须与所选英文片段有可重放的逐字依据，公式、引用、
环境和顺序全部来自该片段。支持范围内明确提取边界并保护所有非自然语言节点；
不能以两个内部 hash 自洽代替英文比对，不能新增上游没有的节点或只恢复部分
公式。完整旧→新 unit 映射和 proof 链覆盖仍须验证，不丢掉、拆断或重复单元。

逐单元操作引用 `source_reextraction_id`；唯有证据全部核验、新 source
与锁定片段相等、旧/新 unit 与该操作精确一致，且该单元明确引用实际新模型
修订时，才允许恢复旧提取已经丢失的上游节点。所有未声明、未验证的操作仍
执行新旧 source TeX 相等，纯工具 v1 不获得这项权限；v2/v3 的其他约束不变。

实际 revision run 冻结确切旧 unit/candidate 及完整新英文 unit。全部五个候选
内容/术语字段必须声明并等于新模型原输出，占位符使用新 source 的完整节点，
不能只在中文补一个公式、伪造旧原输出或继承术语/人工批准。来源锁不变，这项
操作修复提取输入而非英文内容；审批必须重新绑定完整当前来源。

### 9.3 来源绑定、覆盖审计和启用顺序

provenance、selection/review/revision 来源 hash 包含恢复证据、英文
Git 选择和全部模型/派生历史；即使正文不变，也不沿用缺少新绑定的旧批准。预览
披露来源恢复及实际修订，历史证据仍完整校验但不计入当前 QA、进度、渲染或 TM。

后续先复核所有当前 proof 单元及完整证明链相对于锁定英文的节点、公式和引用
顺序，记录同类缺陷及未能核验的范围；不把只修 001P 当作 F4 全量验收。明确的
源文 typo/缺失证明仍按 remark 处理，不能混同当前提取丢失。来源/术语独立审计
通过之后，才按 S5 启用全量门禁并完成 S7 总验收。

Schema/工具回归必须包含合法完整恢复及 Git 片段篡改、错误 selector/source、
公式遗漏/重排/增加、错误旧输入、重算 hash、路径/symlink、缺少实际模型修订和
沿用旧批准等拒绝案例。规范、实现和具体数据使用分别声明的独立 Issue/PR；
本节不创建源恢复事实；一般章节提取与复杂语法仍不在当前机器能力范围内。

### 9.4 已实现范围与独立覆盖报告

`LockedEnglish` 只从锁定 commit 的章文件和 `tags/tags` 读取数据，不读取英文
工作目录正文。章文件需具有独占行的 document opening；支持固定 `preamble`/
`chapters` include 边界，不展开任何宏。own label 必须紧随陈述 opening 和简单
命名标题，proof 必须紧邻该陈述或其上一 proof；明确 selector 保存本地英文 label、
陈述永久 Tag 和从 1 起算的 proof index。注释与数学中的标签不参与 ownership；
重复标签、宏定义、literal 环境、文本参数内的陈述/证明等明确报未支持。

`extract_plain_proof` 只支持一个完整、无可选标题的单单元 proof，其 body 由
自然语言与 `$...$` 内联数学组成。保持所有空白和公式原字节，按顺序生成
`MATH_####`，完整 source TeX 等于原始 Git 片段。文本命令、分组、注释、display、
嵌套环境、复杂标题或拆分证明需专门工具任务；不得截断或复制整份 raw TeX 给模型。
重放用完整冻结 batch 的 `permanent_tag_mapping` 校验 old→new 映射与 proof owner，
证据旧 unit、确定性新 unit、新修订冻结 source 及全部五字段必须精确对应。

`make proof-source-audit` 或 `audit-proof-source --root . --harvest <checkout>
--output build/proof-source-audit.json` 独立检查所有当前 proof wrapper group。报告逐组
保留 selector、英文/当前节点序列和 source hash，区分 match、mismatch、unsupported，
任何差异或未覆盖返回非零。比较仅折叠自然语言空白、忽略 TeX 注释；公式/控制/引用
字节和顺序不归一化，因此引用的章前缀、公式换行等差异也须逐项复核，不能一概称为
数学错误。此审计暂不进入默认 QA，S4 修复和范围验收后才在 S5 启用硬门禁。

provenance/decision 的可选 `--harvest` 由 Make 的 `HARVEST_DIR` 传入；render 使用
配置的 chapter source directory。无恢复证据时不新增英文 Git 依赖，既有单层来源
hash 格式不变；存在恢复证据时全部祖先记录加入绑定，预览披露锁定英文恢复及所有
实际修订。历史证据校验不增加当前候选计数。

## 10. 完整来源容器与历史分段修订的开发合同

本节定义独立 v4 Schema/工具合同，实现及命令见来源容器设计 §9。
v1/v2/v3、§8 的一对一后续修订和 §9 的简单证明恢复保持原规则。
完整设计、证据字段、边界与回归矩阵见
[source-container-restoration.md](source-container-restoration.md)。工具合并并完成
验收前，不得创建或采用真实 v4 派生、分组恢复证据或对应模型修订数据。

新合同解决完整定义/列表闭合位置、分段证明漏公式和较长脚注全文的来源采用，
允许在确有来源证据时改变历史分段。按锁定 Git 重新扫描完整语义容器，验证真实
owner、Section parent、陈述/证明 selector、字节范围与片段 hash；缓存及唯一定位
均不是采用依据。新保护输入须完整恢复为 Git 原片段，不归一化公式、引用或环境。
未知宏/环境、未分类数学内自然语言或不明确归属仍失败，不能靠 BLOCKED 库存生成
成功、排版别名或相同内部 hash 授权采用。

完整上一 batch 的 unit/candidate 原字节和全部已有历史须冻结并验证。v4 使用显式
`unit_groups` 记录每组完整有序旧/新 ID，而不改写旧版本的 bijective `unit_id_map`。
每个旧输入与新输出各属唯一组；来源恢复组覆盖完整容器，组外源 TeX 仍相等。
拆分或合并必须保留语义边界、来源次序和全部原文，不能把丢失、重复、跨 owner
借文或归档未完成单元称为分段变化。所有新 ID/parent 及允许路径须在数据 Issue
提前声明，并通过全库重复/冲突及 chapter-template 核对。

每个新输出都要求新实际模型修订的全部五个内容/术语字段，冻结完整新保护 source
和完整旧分组作为修订输入；不得只改 hash、照搬旧候选冒充新生成或由程序补中文。
活跃候选必须明确绑定分组证据和新 run，历史身份锚点不代表全部祖先或当前文字。
provenance、正式来源 hash 与预览披露覆盖组内所有原 run/candidate、祖先派生/
归档/恢复和实际新修订，不能只取一个旧单元隐藏其他来源。审批全部重新绑定，
未知术语不获批准，历史输出不计入当前 QA、进度、渲染或 TM。

规范、实现和具体数据各自使用 claimed Issue → 本地验收 → PR；一般来源恢复
不会修改英文、source lock、词表或 reviewed 数据。工具默认只生成 ignored 待审包，
不创建真实模型运行或自动审批。来源/证明/术语审计仍保留全部差异；完整数据修复
及 S5/S7 验收后才能宣告 F4/F6 与全库目标完成。

旧 proof 外的游离显示公式只有在完整旧包装链及紧邻纯数学单元一起冻结、数学节点
与锁定目标 proof 的真实保护节点逐字一致且章内唯一时，才可由完整来源分组迁回
proof。非相邻、夹带正文/包装、重复、跨范围、不唯一或缺少真实归属的输入均拒绝。
合同与工具验收见 `source-container-restoration.md` §4.1；实际数据仍需后续独立任务、
完整真实模型修订与原输出，不改变已存在的不可变证据或授予审批。

完整引言的旧 render 外围 ASCII 空白差异使用来源容器设计 §9.1 的独立
`source-container-v2` 合同。仅完整 paragraph 在真实旧/新原生 Section 归属及
唯一原字节核心核验下可恢复原 Git 外围；内部正文、数学和引用不归一化，新
source TeX 仍逐字等于原 Git。旧 source-container-v1 逐条保持原严格规则，
与派生 Schema 的 v1/v2/v3/v4 版本无关。先完成独立工具验收，再由具体数据
任务保存全 batch 原字节、重新冻结并实际修订，不继承批准或改写旧证据。

## 11. 数学内自然语言的后续来源保护合同

完整设计见 [math-text-translation.md](math-text-translation.md)。独立工具实施并
验收合并前，现有数学保护与未分类文字阻断不变，不能在普通翻译任务中采用
unit-v2 或 source-container-v3。新格式只允许已验证命令参数的自然文字叶变化，
保留完整原数学 region、全部非文字字节、锁定片段/slot 及政策/真实 Git 见证。
原 source 回放与译文 skeleton 同时通过；公式、标签、引用或边界变化仍失败。

新容器 v3 与派生 v3 是不同版本；旧 unit-v1、source-container-v1/v2 和
§8–§10 的全部历史合同按原政策/版本逐条重放。具体 DATA 仍冻结完整旧 batch
及全部祖先，采用完整 v4 分组并要求每个新输出实际模型完整五字段及不可变
原输出/context。完整来源 hash、正式审批绑定与预览披露包含全部 region/slot
和新修订，不继承任何旧批准。政策/工具只准备来源，不生成中文或批准术语。
