# Stacks Project 中文翻译工作流

本文件是中文翻译项目的规范入口。文中的“必须”“不得”是强制规则；“应”表示
除非在 PR 中说明并获得批准，否则必须遵守；“可以”表示可选做法。

## 1. 项目目标

项目以只读英文 harvest 为输入，维护可追踪、可审校、可随上游更新的中文译文，
并通过完整的 Springer LaTeX 模板生成模型预览版和人工审校版 PDF。

本项目不把模型对话、生成后的 TeX 或 PDF 当作翻译事实来源。翻译事实必须保存
为可审查的结构化数据，并记录英文提交、翻译单元、模型、提示词和审校信息。

## 2. 规范优先级

发生冲突时不得自行选择一种解释，应停止工作并提交规范修订。相关文件职责如下：

1. `upstream.lock`：英文来源仓库和精确提交；
2. `config/workflow.yml`：状态、风险等级和硬性流程配置；
3. `config/macro-policy.yml`：LaTeX 节点处理策略；
4. `config/glossary.yml`：已批准和待决术语；
5. 本文件及 `docs/`：完整的人类可读规范；
6. `AGENTS.md`：Codex 和其他自动化代理的执行边界；
7. `README.md`：项目介绍，不覆盖上述规范。

模型身份还必须遵守 `config/harnesses.yml`、`config/models.yml` 和
`docs/model-provenance.md`。Harness 是执行工具，模型是文本生成者，二者不得混用。

## 3. 数据和仓库边界

- `../stacks-project` 是只读英文 harvest，禁止修改或写入生成文件。
- `stacks-project-zh` 是独立 Git 仓库，禁止合并英文仓库历史。
- 英文版本由 `upstream.lock` 中的完整 commit 决定；本地路径不决定版本。
- `translation-data/` 是译文事实来源。
- `springer-template/translations/<model>/` 是渲染输出，不是翻译数据库。
- `build/`、`output/`、`source-ir/`、`.harvest/` 和 SQLite 索引均为可再生数据。
- 未经专门的上游同步 PR，不得修改 `upstream.lock`。

## 4. 端到端流程

```text
锁定英文提交
  → 无损解析 LaTeX
  → 生成稳定翻译单元
  → 构造受控上下文包
  → 生成模型候选译文
  → 结构与术语硬检查
  → 独立语义批评
  → 人工语言审校
  → 必要的人工数学审校
  → 提升到 reviewed
  → 生成 TeX、PDF 和发布清单
```

### 4.1 锁定来源

每个批次开始前必须执行 `make harvest-check`。检查不通过时不得解析、翻译或
构建正式输出。翻译过程中禁止自动拉取或切换英文提交。

### 4.2 解析和分段

解析器必须保留完整 LaTeX 结构，只把自然语言文本节点送给模型。翻译单元优先
使用 Stacks Project 永久 Tag；没有 Tag 的节点使用父级 Tag、AST 路径和内容
指纹建立稳定 ID。详见 `docs/data-model.md`。

### 4.3 构造上下文

每个单元只接收完成当前翻译所需的最小上下文：风格规范、相关术语、邻近文本、
直接引用的数学陈述、章节记忆和已批准翻译样例。不得把整本项目或未经审校的模型
输出作为翻译记忆注入。

### 4.4 翻译

模型必须输出结构化候选记录，不得直接重写原始 TeX。所有公式、标签、引用、
引用键、环境和占位符都由程序保管。每一次数学术语出现都必须采用
`中文（English）`，并逐项写入 `term_occurrences`。未知术语必须报告为待决项，
模型无权批准。

每次模型生成都必须创建不可覆盖的 run manifest，记录 Harness、具体模型、来源、
提示词、词表和上下文。候选合并到 `main` 只表示保存这次运行，不表示正式采用。
维护者选择、人工审校和正式 revision 必须分别记录。

### 4.5 自动检查

结构检查属于硬门禁。任一受保护节点缺失、增加、重排或改变时，候选译文直接
失败，不得由模型猜测修复。术语检查和语义批评随后执行。

### 4.6 人工审校

所有公开译文至少需要人工语言审校。定义、引理、命题、定理、推论、证明及其他
高风险数学内容还必须由具备相应背景的人员完成数学审校。模型不能把自己的输出
标记为人工审校通过。

### 4.7 渲染和发布

只有结构化翻译数据通过对应门禁后，渲染器才生成模型目录和 TeX。正式发布仅从
`reviewed` 通道构建；原始模型候选只能生成带有明确声明的预览版。

任何修改在创建 Git 提交或 Pull Request 前都必须完成一次适用的本地 LaTeX 编译，
且命令必须以零状态退出。翻译候选必须先执行 `make render MODEL=<model-lane>`，再执行
`make pdf MODEL=<model-lane>`，以编译包含本次候选的模型通道；其他修改至少执行
`make template`。缺少 TeX 工具链或出现编译错误时不得提交、推送或创建 PR，也不得
通过修改生成的 TeX、PDF 或日志绕过失败。生成产物仍不得提交。

## 5. 状态模型

主阶段 `stage`：

```text
UNTRANSLATED
  → AI_DRAFT
  → STRUCTURE_OK
  → TERM_OK
  → CRITIC_OK
  → LANGUAGE_REVIEWED
  → MATH_REVIEWED（高风险单元必需）
  → PUBLISHED
```

与主阶段正交的状态：

- `source_status`：`CURRENT`、`STALE_TEXT`、`STALE_MATH`、
  `PARTIAL_STALE`、`RETIRED`；
- `qa_status`：`NOT_RUN`、`PASS`、`FAIL`；
- `term_status`：`CLEAR`、`DECISION_REQUIRED`；
- `publication_status`：`INTERNAL`、`CANDIDATE`、`RELEASED`。

只要 `source_status` 不是 `CURRENT`，单元就不得发布。只有 `PUBLISHED` 译文可以
进入权威 Translation Memory。

## 6. 一个翻译单元的完成定义

一个单元只有同时满足以下条件才算完成：

- 来源 commit、单元 ID、文本/结构/数学 hash 已记录；
- 所有受保护 LaTeX 节点与来源一致；
- 没有未说明的英文自然语言残留；
- 每个数学术语在每次出现时都同时保留中文和英文，且记录、顺序与重复次数一致；
- 术语符合已批准词表，待决术语已经解决；
- 独立批评中没有未关闭的 blocker 或 critical 问题；
- 已完成要求的人工语言和数学审校；
- 生成的 TeX 可以在目标书稿中编译；
- PR 中包含双语 diff、QA 摘要和来源信息；
- Git 提交和 PR 满足 `docs/git-conventions.md`。

## 7. 并行工作原则

- 并行单位是互不重叠的 Section 或明确分离的检查任务。
- 任意时刻一个翻译单元只能有一个写入者。
- 翻译者和语义批评者必须使用独立上下文。
- 多模型比较必须使用字节一致的输入包和同一提示词版本。
- 不同任务不得同时修改 `config/glossary.yml`、`upstream.lock` 或同一 reviewed 文件。
- 不同 Harness 可以运行同一具体模型，同一 Harness 也可以运行不同模型；模型比较
  必须使用不同 run ID。新模型替换旧译文时保留旧候选和 revision。

## 8. 当前命令与计划命令

当前已经实现并可执行：

```bash
make repo-setup
make workflow-check
make harvest-check
make upstream-index-check
make init-chapters
make chapter-template-check
make template
make pdf MODEL=template
make tool-test
make schema-check
make qa BATCH=<batch> MODEL=<model>
make qa-all
make provenance-check
make decision-check
make render MODEL=<model>
make upstream-diff OLD_UNITS=<dir> NEW_UNITS=<dir> NEW_COMMIT=<sha> \
  OUTPUT_JSON=<path> OUTPUT_MD=<path>
```

`make init-chapters` 为锁定上游的全部章节生成 Section 级任务骨架，
`make chapter-template-check` 验证骨架未过期。骨架只提供稳定坐标、建议 batch 和
准备状态；它不代替下列尚未实现的完整章节提取接口。`make render MODEL=<model>`
会同时为没有候选译文的章节生成使用 `config/chapter-titles.json` 中双语标题的空白、
可编译骨架，使预览 PDF 保留上游的完整章节顺序和章节标签；骨架不显示“待译”正文，
这些生成文件也不是译文编辑入口。

以下是流水线必须实现的稳定接口，目前仅是命令契约，不得声称已经可用：

```bash
make extract CHAPTER=<chapter>
make queue SECTION=<tag>
make translate BATCH=<batch> MODEL=<model>
make critic BATCH=<batch> MODEL=<model>
make promote BATCH=<batch>
make upstream-status
```

## 9. 细则索引

- `docs/data-model.md`：文件布局、稳定 ID、记录字段和翻译记忆；
- `docs/translation-rules.md`：语言、语义和 LaTeX 硬约束；
- `docs/review-and-qa.md`：风险等级、审校职责、QA 和失败处理；
- `docs/upstream-sync.md`：英文更新、失效分类和最小修订；
- `docs/git-conventions.md`：分支、提交、PR 和合并规则；
- `docs/codex-workflow.md`：Codex 任务拆分、输入输出和并发规则；
- `docs/github-collaboration.md`：GitHub Issue、PR、角色和分支保护；
- `docs/task-allocation.md`：任务坐标、认领生命周期和写入所有权；
- `docs/terminology.md`：术语决策和 AI 限制；
- `docs/licensing.md`：公开仓库和 Release 的许可证检查；
- `docs/ci.md`：GitHub Actions 的可执行门禁合同；
- `docs/release.md`：发布门禁、版本号、许可证和产物。

任何影响含义、状态或提交要求的修改，都必须使用独立的 `docs/*` 或 `tool/*` PR，
不得夹带在普通翻译 PR 中。
