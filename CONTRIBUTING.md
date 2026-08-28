# 参与 Stacks Project 中文翻译

提交任何修改前，请先阅读 `WORKFLOW.md` 和与本次工作对应的 `docs/` 细则。使用
GitHub 协作时还应阅读 `docs/github-collaboration.md` 和
`docs/task-allocation.md`；术语、许可证或 CI 修改分别阅读对应细则。

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
```

`repo-setup` 只设置本仓库的提交模板、hooks 路径和文件模式策略，不设置姓名、
邮箱或远程仓库。

## 选择工作类型

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

1. 从最新 `main` 建立 `translate/<chapter>/<tag>/<model>` 分支，并在 Issue 中声明 Harness、具体模型和 run ID；
2. 验证 harvest 与 `upstream.lock`；
3. 生成冻结的输入包；
4. 只写入指定 Harness、模型、run 和单元的候选数据；
5. 运行结构、术语和语义检查；
6. 生成双语 diff 与 QA 摘要；
7. 执行 `make render MODEL=<model-lane>` 和 `make pdf MODEL=<model-lane>`，确认本次
   候选所在模型通道的 LaTeX 编译无错误；
8. 按 `.gitmessage` 写原子提交；
9. 使用 PR 模板提交，不自行提升人工审校状态。

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

其他修改至少执行：

```bash
make template
```

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
