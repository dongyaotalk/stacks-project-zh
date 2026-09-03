# 参与 Stacks Project 中文翻译

提交任何修改前，请先阅读 `WORKFLOW.md` 和与本次工作对应的 `docs/` 细则。使用
GitHub 协作时还应阅读 `docs/github-collaboration.md` 和
`docs/task-allocation.md`；选择翻译范围时阅读 `docs/translation-priority.md`；术语、
许可证或 CI 修改分别阅读对应细则。

README 的“人类贡献者指南”提供从 Fork、查找 Tag、认领喜欢的范围、生成候选、
提交 PR 到申请 CODEOWNER 的完整操作路径。本文件只保留必须遵守的简明合同。

## 首次设置

默认目录是：

```text
stacks/
├── stacks-project/
└── stacks-project-zh/
```

进入中文仓库后执行：

```bash
make repo-setup
make workflow-check
make harvest-check
make upstream-index-check
make schema-check
make template
make harness-check HARNESS_ID=codex
```

`repo-setup` 只设置本仓库的提交模板、hooks 路径和文件模式策略，不设置姓名、
邮箱或远程仓库。

## 选择工作类型

不确定从哪里开始时，先运行 `make next-task`；也可以用
`make next-task CHAPTER=<slug-or-number> TAG=<parent-tag>` 显式锁定本次范围。显式选择
优先于项目 P0–P4 默认政策，但不会永久改变章节评级。

- 翻译候选：一个 Harness、一个具体模型、一个 Section、一个不重叠批次；
- 人工审校：只修改指定单元的审校结果和必要的最小译文修订；
- 术语决策：使用独立 `term/*` 分支和 PR；
- 上游同步：使用独立 `sync/*` 分支，禁止夹带普通翻译；
- 工具或模板：不得顺便改变 reviewed 译文；
- 规范修改：必须说明迁移影响和需要重新检查的既有数据。

GitHub 任务必须先在 Issue 中锁定英文 `source_commit`、chapter、Tag 和完整
`unit_id` 列表。不要用页码或源文件行号认领任务；一个 unit 或 batch 文件同一时间
只能有一个写入 PR。

如果喜欢的英文范围还没有出现在 `translation-data/units/`，先使用
`.github/ISSUE_TEMPLATE/unit-preparation.yml` 请求结构化提取；不得直接翻译原始
TeX 或手工发明 unit ID。

## 提交翻译

无论翻译流水线状态如何，都不接受把模型直接生成的整份 TeX 当作正式翻译数据。
当前仓库已支持结构化候选装配，标准步骤是：

1. 从最新 `main` 建立 `translate/<chapter>/<tag>/<model>` 分支，并在 Issue 中声明 Harness、具体模型和 run ID；Harness 版本必须由 `make harness-check HARNESS_ID=<harness-id>` 动态获取；
2. 验证 harvest 与 `upstream.lock`；
3. 选择同一章节内 2–8 个相邻、语义完整且总量约 300–1500 个英文词的 batch；
4. 用 `make batch-pack BATCHES="<batch-a> <batch-b>"` 生成一个冻结的模型输入包，
   让一次模型请求返回所有 unit 的 JSONL 草稿；
5. 用 `make assemble-batch BATCHES="<batch-a> <batch-b>" DRAFTS=<drafts.jsonl>
   MODEL=<model-lane> ...` 按 `unit_id` 拆回独立候选文件；
6. 运行结构、术语和语义检查；
7. 生成双语 diff 与 QA 摘要；
8. 开发阶段如一次处理多个不重叠 Section，可执行
   `make qa-batch BATCHES="<batch-a> <batch-b>" MODEL=<model-lane>` 和
   `make render-batch BATCHES="<batch-a> <batch-b>" MODEL=<model-lane>`；文件仍按
   batch 独立保存；
9. 执行完整 `make render MODEL=<model-lane>` 和 `make pdf MODEL=<model-lane>`，确认本次
   候选所在模型通道的 LaTeX 编译无错误；
10. 按 `.gitmessage` 写原子提交；
11. 使用 PR 模板提交，不自行提升人工审校状态。

`batch-pack` 会拒绝跨章节、重复 unit、少于 2 或多于 8 个输入文件，并在超出
300–1500 词偏好范围时要求显式确认不可拆分的语义边界。`assemble-batch` 会先验证
所有 unit 与草稿的完整覆盖、重复和来源，再一次性写出各自 candidate；Harness 版本
只解析一次。batch 只用于开发调度，不合并翻译事实、不改变 schema、不覆盖旧 run，
也不提升人工审校状态。提交前的 `qa-all`、完整渲染、PDF 和 CI 门禁仍不可省略。

## 提交术语

术语 PR 必须提供英文词形、建议中文、定义或语境、出现位置、备选方案和理由。
术语获批前状态保持 `proposed`，不得自动批量修改现有译文。术语批准与译文应用
应使用两个独立提交或 PR。

无论词条状态如何，正文中每一次数学术语出现都必须采用 `中文（English）`
形式；批准词条只决定中文译法，不取消保留英文的要求。

## 提交审校

审校者不得只给出“看起来正确”。必须记录审校层级、审校人、时间、来源 commit、
问题分类和结论。数学审校者需要核对量词、否定、方向、条件、对象以及引用陈述。

## 提交前检查

所有修改至少执行：

```bash
make workflow-check
make harvest-check
make upstream-index-check
make tool-test
make schema-check
git diff --check
```

在创建 Git 提交或 PR 前必须完成一次适用的本地 LaTeX 编译。翻译候选必须执行：

```bash
make render MODEL=<model-lane>
make pdf MODEL=<model-lane>
```

其他文档、进度、政策和工具修改执行当前候选通道的编译：

```bash
make render MODEL=openai-gpt-5.6-sol
make pdf MODEL=openai-gpt-5.6-sol
```

只有修改模板、样式、Makefile 或渲染路径时才另外执行 `make template`。裸
`make pdf` 必须显式指定 `MODEL`，不会再隐式编译 `template`。

上述命令必须以零状态退出。缺少 XeLaTeX、BibTeX 或 makeindex，或者出现编译错误时，
不得提交、推送或创建 PR。不得编辑生成文件来掩盖失败。

不要提交 `build/`、`output/`、`.harvest/`、`source-ir/`、生成的模型 TeX、PDF
或 SQLite 缓存。正式 PDF 作为 Release 产物发布。

## Git 要求

分支名、提交类型、必需 trailers、PR 粒度和合并规则见
`docs/git-conventions.md`。本地 hook 只能提前发现问题，CI 和人工审查仍是最终门禁。

## 申请 Maintainer 或 CODEOWNER

任何人都可以贡献，不需要 CODEOWNER 身份。愿意长期维护明确路径时，使用
`.github/ISSUE_TEMPLATE/codeowner-application.yml` 提交申请，提供责任路径、已合并
贡献、审核能力、响应承诺和最小权限需求。获批后使用独立治理 PR 同步修改
`MAINTAINERS.md`、`.github/CODEOWNERS` 和 GitHub 权限；CODEOWNERS 文件本身不授予
平台权限，也不自动证明语言或数学审校资格。
