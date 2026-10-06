# 翻译数据模型

## 1. 数据所有权

仓库中的数据分为三类：

| 类别 | 示例 | 是否提交 Git | 是否可手工修改 |
|---|---|---:|---:|
| 规范事实 | `upstream.lock`、`config/`、reviewed 数据 | 是 | 按对应 PR 规则 |
| 候选与审校记录 | 模型候选、问题和审校决定 | 是 | 仅在授权阶段修改 |
| 可再生产物 | IR 缓存、SQLite、TeX、PDF、报告页面 | 否 | 否 |

推荐布局：

```text
translation-data/
├── chapter-templates/           # 全章节 Section 任务骨架，不保存译文
├── units/                       # 稳定单元索引，不复制整份 TeX
├── runs/<run-id>.json           # Harness、具体模型和冻结输入的 manifest
├── candidates/<model-lane>/     # 各模型候选 JSONL
├── derivations/                 # 当前工具派生的原字节、映射和重放证据
├── model-corrections/           # 独立实际模型修订与完整冻结输出证据
├── selections/                  # 维护者对候选的选择/拒绝决定
├── reviewed/                    # 正式结构化译文
└── retired/                     # 上游删除后的历史记录

review/
├── language/                    # 人工语言审校记录
└── mathematics/                 # 人工数学审校记录
```

`review/issues/` 是自动/模型 critic 记录的规划接口；当前尚无对应 Schema、目录和
命令，不能把它当作已经实现的数据事实。

`source-ir/` 是按 `upstream.lock` 和解析器版本可重建的缓存，不提交 Git。权威
Translation Memory 由 `translation-data/reviewed/` 生成，SQLite 只作为查询索引。

`chapter-templates/` 是从锁定 `chapters.tex`、章源文件、`tags/tags` 和现有 unit
确定性生成的协作索引。每章一个文件，每个 Section 记录永久 Tag、建议 batch/unit
路径及 `READY`、`UNPREPARED` 或 `BLOCKED_NO_TAG` 状态。它既不包含译文，也不把
尚未提取的范围伪装成可翻译 unit；更新后必须通过 `make chapter-template-check`。

翻译规划是独立于上述事实数据的一层：`config/translation-priorities.json` 保存 117 章
长期 P0–P4 政策，`docs/translation-plan.md` 是该政策与当前 template、unit、candidate、
reviewed 状态的生成结果。priority 不写入 chapter template、unit、candidate 或
reviewed revision；用户显式 Chapter/Tag 也只是运行时约束。详见
`docs/translation-priority.md`。

## 2. 稳定翻译单元

### 2.1 有永久 Tag 的节点

定义、引理、节等拥有 Stacks Project 永久 Tag 时，主 ID 使用：

```text
tag:<TAG>
```

同一 Tag 下需要拆分时追加语义稳定的子 ID：

```text
tag:0001:title
tag:0001:p001
tag:0001:proof-p003
```

不得把当前页码、行号或模型名称放入 `unit_id`。

所有自身拥有永久 Tag 的数学陈述必须使用自身标签对应的 Tag，不能借用外围
Section Tag。完整陈述的证明和无独立 Tag 的结构子节点继承陈述归属；自身带永久
Tag 的列表项仍使用其独立 Tag。历史 `label:` 子坐标只在锁定索引证明标签有永久
Tag 时显式迁移，保持语义 suffix 和旧→新映射。
`audit-source` 已提供独立审计；历史修复完成后再将这一检查接入整库强制门禁。

原文若含没有独立标签的显式证明标题，例如 `\begin{proof}[Proof (sketch)]`，
可以将标题文字保存为所属数学陈述的 `tag:<TAG>:proof-title`，节点类型为
`environment_title`，而不是发明新 Tag 或丢掉提纲等限定。该标题的包装只打开
proof 环境及其可选参数并闭合参数；其后 `tag:<TAG>:proof-p001` 正文不得重复打开
proof 环境。单份显式标题使用上述既有坐标，必须在同一 batch 中紧接完整带标签的
lemma/proposition/theorem/corollary 陈述，并紧邻第一段 proof 正文，同时校验三者
自身 Tag、chapter、parent Tag 及陈述标签的永久 Tag 对应。

同一陈述有多份显式带标题的证明时，使用编号证明组，例如：

```text
tag:02TF:statement
tag:02TF:proof-001-title
tag:02TF:proof-001-p001
tag:02TF:proof-001-p002
tag:02TF:proof-002-title
tag:02TF:proof-002-p001
```

这是所属永久 Tag 内持久化的子坐标，不是新的永久 Tag，也不迁移既有单份证明 ID。
同一 batch 必须包含一个完整带标签陈述及其至少两份完整证明，保持原文顺序且中间
不得夹入无关单元。证明组和组内段落都从 `001` 连续编号，采用三位数字；每组标题
仍为 `environment_title`，正文为 `proof`，所有单元共享自身 Tag、chapter 和 parent Tag。
标题包装恰为 `\begin{proof}[` 与 `]`（右括号后可有空白），标题文字和引用占位符
不得遗漏或隐藏于包装中。第一段正文前只能有空白；后续段落前可有空白或原文的
`\medskip\noindent`。非末段后只能有空白；末段后必须且只能有一个 `\end{proof}`
及空白，正文和占位符不得暗藏额外 proof 开闭命令。后续标题只能沿同批完整证明链
继承首个陈述的真实标签；不能伪造标题标签、重复陈述或跨文件寻找所属引理。
每个标题的继承标签仍须解析为该陈述自身的永久 Tag。

其他无标签标题仍需单独
解决稳定坐标，不能借用别的章节、batch 或不相邻陈述的标签。

### 2.2 没有永久 Tag 的节点

初次导入时使用以下信息建立合成 ID：

- 最近的父级永久 Tag；
- 节点类型；
- 规范化 AST 路径；
- 当前内容指纹；
- 前后邻居指纹。

首次建立后，`unit_id` 必须持久保存。上游移动或格式化不能重新分配 ID；匹配
不确定时进入人工映射队列，禁止自动创建两个重复单元。

如果历史导入时暂时使用了 `label:<label>:<suffix>`，而锁定的 `tags/tags` 后来证明
该节点本身拥有永久 Tag，则必须执行一次显式坐标迁移，改为
`tag:<TAG>:<suffix>`。迁移只改变坐标及包含坐标的上下文 hash，不改英文快照、数学
片段或译文。旧、新 ID 保存在 `migration/unit-id-map.json` 和独立派生记录；活跃
unit/candidate 更新，但原始 run manifest 不回写。原文件须按原字节保存至
`retired/derivations/`，派生记录引用快照和输入/输出 hash，并能确定性重放。
外部任务引用旧 ID 时先查该映射，不能静默创建第二个单元。来源提取或双语显示
修复属于另外声明的变换，不得混称为纯坐标迁移。详见 `docs/model-provenance.md`。

再次修订已派生版本时，前一版本不成为第二份当前候选。归档清单位于
`derivation-archives/`，历史完整输出位于原 `retired/derivations/<id>/` 的
`output-units.jsonl`、`output-candidates.jsonl`；旧派生记录、原输入及所有模型
run/输出保持原字节。新旧版本必须按完整 batch 一对一替换并验证全部历史，
历史输出不进入当前 QA、进度、渲染或 TM。Schema 与 provenance 校验覆盖归档和
历史输出；v3 要求完整 batch 的实际模型修订，具体数据由独立任务声明。合同和
校验规则见 `docs/model-provenance.md` §8。

命名陈述环境的自然语言标题与正文保存在同一 unit 中，不增加当前单元或重编号。
简单标题可以通过 `expose_environment_title` 从完整 `render.prefix` 重提取：
prefix 以 opening bracket 结束，source_text 从英文标题开始，其后的
`ENVARGEND_####` 保存 closing bracket、原空白及紧邻 own label。源 TeX 原字节
保持不变，Tag 校验严格识别这一边界，证明继承同一陈述 owner。复杂标题须显式
提取任务，不能用任意正文/公式占位符中的标签替代 own label。历史快照保持原样；
当前源重新提取后由独立模型修订冻结新的完整 unit，不回写旧 run 或输出。
既有独立 `environment_title` 单元仍可把 closing bracket/own label 保存在 suffix；
这些标题已经暴露，不需要 ENVARGEND，也不应为采用新 helper 而拆分、合并或重编号。

旧 source unit 已经丢掉上游节点时，内部 hash 及无损派生不能证明英文输入完整。
来源恢复证据位于 `source-reextractions/`，同时绑定完整旧/新 unit、派生、
锁定英文 Git 片段和受限 selector。`source-reextraction.schema.json`/loader 只支持
完整单单元的简单证明；通过证据及完整实际模型修订的 v2/v3 才获得受限例外，其他
操作仍要求新旧 source TeX 相等。合同见 `docs/model-provenance.md` §9。旧缺陷输入
保持原字节，新的受保护英文输入由实际新模型修订完整冻结，不冒用旧 run 身份。

完整语义容器的来源恢复及旧分段合并/拆分使用独立 v4 合同，见
`docs/model-provenance.md` §10 与 `source-container-restoration.md`。v1/v2/v3 的一对一
映射和现有 Schema 不变；新合同的 Schema/工具合并验收前不能写入 v4 事实。
v4 用显式旧新分组覆盖完整上一 batch，每个旧单元与新单元各属于唯一分组，
完整 Git 容器逐字验证且每个新单元有实际模型修订；所有旧 run、原输出及祖先归档
保留。单元数变化须对应可验证的语义边界和完整原文覆盖，进度只统计新的活跃事实，
不得通过归档未修单元、静默换 ID 或重复候选来降低待办。

`source-container-restorations/<id>.json` 保存独立完整容器证据；`unit_groups`
保存有序旧/新 ID、完整新 unit、历史身份锚点、模型修订及来源恢复 ID。活跃候选
的 `unit_group_id` 必须绑定经过完整重放的 v4。原 context 的
`candidate-group-to-revise` 包含全部旧 unit/candidate，不属于批准的 TM。
完整标题 lowering 使用受来源证据约束的 `OWNARGEND`，旧 `ENVARGEND` 不放宽。
章标题原 `title`/phantom header 和章内 label/ref 在事实中保持 Git 原字节，书稿
生成层才转换为 chapter 与统一 namespace。全部旧/新来源进入审校 binding。

## 3. 来源 hash

占位符的原 payload 和默认 `restore_placeholders` 恢复结果保持原字节。实际渲染
使用 `delimit_commands=True` 时，控制词与后续正文分隔；对历史 `SPACE_####`
角色中恰为单个反斜线的 payload，其后若没有已有空白，补一个空白构成 TeX
控制空格。这保证紧接的中文或字体组不会被吞入命令。已有空白不重复补充，
原 source_text 必须在 token 后提供 TeX ASCII 空白（space/tab/CR/LF）作为证据，
否则渲染报错；译文后已有空白也仅按这一集合判断，全角空白不能冒充词法分隔。
完整控制空格、细空格、双反斜线及其他角色不套用该规则；它不改变源文、数学、
记录或 hash，也不许可任意未知控制序列。渲染产物不能回写为事实数据。

每个单元至少记录三类 hash：

- `source_text_hash`：规范化自然语言文本；
- `source_structure_hash`：环境、命令、参数位置和占位符序列；
- `source_math_hash`：所有数学节点的规范化 AST。

三者分别用于判断文本修改、结构修改和数学修改。只存一个整段字符串 hash 无法
区分普通编辑与数学语义变化，因此不符合本项目要求。

## 4. 单元记录

记录至少包含：

```json
{
  "schema_version": 1,
  "unit_id": "tag:0001:p001",
  "parent_tag": "0001",
  "chapter": "introduction",
  "node_kind": "paragraph",
  "risk_level": "R1",
  "source_commit": "a04446e57ec1fbc252a871afcec7752fb2807b14",
  "source_text": "...",
  "source_text_hash": "sha256:...",
  "source_structure_hash": "sha256:...",
  "source_math_hash": "sha256:...",
  "source_status": "CURRENT"
}
```

`source_text` 可以保存可审查的自然语言快照，但不得复制并维护另一套完整英文
TeX。LaTeX 原始位置由 `chapter`、Tag 和 AST 定位信息表达。

## 5. 候选译文记录

每个模型输出独立记录，不覆盖其他模型：

下面是包含关键字段的缩略示例；`...` 只是哈希等长值的文档占位符，实际文件必须
完整符合 `schema/candidate.schema.json`，不能直接把本例当作可提交 JSON。

```json
{
  "schema_version": 2,
  "unit_id": "tag:0001:p001",
  "source_commit": "a04446e57ec1fbc252a871afcec7752fb2807b14",
  "source_text_hash": "sha256:...",
  "harness_id": "codex",
  "harness_version": "<observed-at-run-time>",
  "model_id": "gpt-5.6-sol",
  "model_lane": "openai-gpt-5.6-sol",
  "model_record_id": "openai:gpt-5.6-sol:owner-confirmed",
  "model_snapshot": null,
  "model_identity_confidence": "owner-confirmed",
  "run_id": "run-20260825-categories-001m-gpt56sol-01",
  "reasoning_effort": "configured-value",
  "prompt_version": "translator-v2",
  "glossary_revision": "git:<commit>",
  "context": {"prompt_version": "translator-v2"},
  "context_hash": "sha256:...",
  "translation": "...",
  "term_occurrences": [
    {"source_term": "algebraic stacks", "target_term": "代数栈"}
  ],
  "unknown_terms": [],
  "notes": [],
  "stage": "AI_DRAFT",
  "source_status": "CURRENT",
  "qa_status": "NOT_RUN",
  "term_status": "CLEAR",
  "publication_status": "CANDIDATE",
  "translation_hash": "sha256:...",
  "created_at": "RFC3339 timestamp"
}
```

必须记录 Harness、实际模型、模型记录和不可变 `run_id`。新候选装配默认动态执行
`config/harnesses.yml` 中的 Harness 版本命令（等价于 `--harness-version auto`）；
如果命令失败或无法解析版本，装配必须失败。如果供应商没有暴露模型
快照，`model_snapshot` 写 `null`，并明确可重放性；不能只写 `codex`、`claude-code`
或营销名称。不同模型使用相同输入时，`context_hash` 和 `prompt_version` 必须一致。

候选进入 `main` 只表示候选运行被保存。维护者选择写入 `selections/`，正式采用的
版本另有 translation revision；模型下架或新模型替换都不能覆盖旧候选。

工具派生候选另有 `derivation_id`，合同位于 `schema/derivation.schema.json`。
它绑定原字节快照及可达的中文 `origin_commit`，同时记录当前输出 hash、完整坐标
映射和逐单元操作。`make provenance-check` 用原候选核对不可变 run，再重放验证
当前数据；原 Harness/model/created_at 仅表示原始生成，派生时间另存。
预览显示派生声明；这些记录仍不代表人工审校或正式采用。
自由自然语言修订须另有实际模型 run 和冻结完整输出，并在派生记录明确引用。
原生成模型与新增修订模型的身份同时保留；`docs/model-provenance.md` §7 的扩展
合同须由独立工具实现后才可应用，纯工具派生目前仍禁止自由重译。

`term_occurrences` 按译文中的出现顺序逐项记录；同一术语出现两次就记录两次。
渲染文本中的对应字面形式必须是 `target_term（source_term）`。该字段记录显示
约束，不代表术语已经批准；批准状态仍由词表和 `unknown_terms` 决定。

## 6. 上下文包

上下文包按固定顺序组成：

1. 翻译硬约束和输出 Schema；
2. `config/style-guide.md`；
3. 与当前文本匹配的已批准术语子集；
4. 当前章节记忆；
5. 当前单元；
6. 直接引用的定义、定理或引理；
7. 前后邻近单元；
8. 3–10 个已发布 Translation Memory 样例。

通常只注入被引用陈述，不注入其完整证明。整个上下文包必须可序列化、可 hash，
且不能包含其他候选模型的未审校输出。

## 7. 审校记录

审校决定必须与译文分开记录，并至少包含：

```text
unit_id
candidate_hash
run_id
source_commit
review_type
reviewer
reviewed_at
decision
issues_closed
resulting_translation_hash
```

`review_type` 只能是 Schema 允许的类型：`language` 或 `mathematics`。术语决定不使用
review schema，而是通过术语 Issue/PR、`config/glossary.yml` 和独立的术语提交记录。
审校记录引用候选 hash，防止候选改变后旧批准仍被错误沿用。

正式 revision 不是只保存一个 hash 的目录索引，而是包含被采用的 `translation` 和
`source_text_hash` 的可渲染事实；它还必须引用 `selection_id`、`origin_run_id` 和
全部人工审校 ID。`make decision-check` 会阻止缺少选择、审校、hash 或替换链的
revision 进入正式数据。

## 8. 术语和翻译记忆

- 术语状态为 `proposed` 或 `approved`；只有人工决定能进入 `approved`。
- 同一英文词可以按数学语境拥有多个词条，但必须给出适用条件。
- 只有 `PUBLISHED` 单元进入权威 Translation Memory。
- 候选译文可以保留用于比较，但不得作为自动检索样例。
- 术语或 TM 更新必须记录所依据的 Git commit。

## 9. Schema 演进

所有结构化记录必须带 `schema_version`。不兼容修改必须提供迁移程序、迁移测试和
受影响文件清单；不得通过一次大规模格式化提交掩盖含义变化。

`schema/unit.schema.json` 和 `schema/review.schema.json` 当前是版本 1；
`schema/candidate.schema.json` 当前合同是版本 2。运行时验证器仍保留 candidate
版本 1 的兼容分支，仅用于历史 fixture 和迁移检查；新候选必须使用版本 2。翻译器自身的
最小输出合同位于
`schema/translator-output.schema.json`。`python stacks_zh.py stamp-units` 只负责
计算确定性来源 hash；`python stacks_zh.py assemble` 将最小模型输出与来源、上下文、
模型和状态事实装配成候选记录。`make qa BATCH=<batch> MODEL=<model>` 还会检查来源
锁、覆盖率、占位符顺序、状态授权、上下文 hash、英文残留说明和待决术语门禁。
`make schema-check` 对仓库内全部 unit、candidate、run、selection、review、revision 和
sync report 执行机器合同；`make provenance-check` 和 `make decision-check` 再检查
跨文件引用链。Schema 中的必填字段、类型、枚举、格式和 `additionalProperties`
均是可执行约束。

## 10. 复合来源的模型修订

修订快照位于 `retired/model-corrections/<id>/`，只进入 schema/provenance 验证；
不作为另一份当前候选加入进度、渲染或 TM。当前候选以 `model_correction_id`
引用完整新模型输出，依旧以原 model/run 标识原始生成；预览披露两种身份。
selection、review、正式 revision 对这种候选必须绑定完整 `provenance_hash`。
证据和重放合同见 `docs/model-provenance.md` §7，旧正文 hash 不代表新的来源链。
