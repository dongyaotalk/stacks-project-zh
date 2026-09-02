# GitHub 多人协作

本文定义 GitHub 平台上的协作方式。它补充 `WORKFLOW.md` 和
`docs/git-conventions.md`，不覆盖来源锁、数据模型、LaTeX 保护和审校规则。

## 1. 仓库状态和边界

中文仓库与英文 `stacks-project` 保持独立历史。中文仓库只配置自己的 `origin`；
英文仓库作为独立 harvest，由 `upstream.lock` 锁定和 `make harvest-check` 验证。

当前仓库已经公开协作。任何新增镜像仓库或迁移都必须在开放协作前确认：

- `upstream.lock` 指向可访问的官方英文仓库；
- `springer-template` 内的模板、字体和图片具有明确的再分发方案；
- 提交作者身份不再使用本机临时邮箱；
- `main` 是可审查的协作基线；
- CI、分支保护和审校责任已经配置。

不要使用 `git push --all`；只按 Issue 和 PR 需要推送当前活动分支。

## 2. 角色

| 角色 | 权限和责任 |
| --- | --- |
| 翻译贡献者 | 认领明确任务，只写允许的候选文件 |
| 语言审校者 | 核对逐句对应、中文表达、术语和残留英文 |
| 数学审校者 | 核对对象、方向、条件、量词、否定和证明逻辑 |
| 术语维护者 | 处理 glossary Issue/PR，不直接替换无关译文 |
| 工具维护者 | 维护解析、Schema、QA、渲染和 CI |
| 发布维护者 | 核对许可证、manifest、审校门禁和 Release 产物 |

同一人可以承担多个角色，但每一次语言审校和数学审校都必须分别记录。模型、
自动 QA 和候选作者不能充当人工审校者。

## 3. Issue 和任务

翻译工作从一个任务 Issue 开始。Issue 至少包含：

- `task_id`；
- 英文 `source_commit`；
- chapter、Section/parent Tag；
- 完整 `unit_id` 列表或明确 batch 文件；
- 模型通道（如适用）；
- 负责人和预期审校角色；
- 当前状态和阻塞项。

任何会产生 PR 的 Issue 还必须明确 `owner`、精确 branch 和
`allowed_write_files`。打开 PR 前添加 `claimed` 标签；PR 只能用 closing keyword
关联这一个 Issue，且 Issue 必须早于 PR 创建。先开 PR、后补 Issue 不被接受。

推荐标签：

~~~text
translation, review, mathematics, terminology, upstream-sync,
tooling, documentation, blocked, claimed
~~~

单范围任务的规范坐标是 `source_commit + chapter + parent_tag + unit_id`；同章 batch
任务使用 `source_commit + chapter + parent_tags + unit_ids`，其中 `parent_tags` 必须是
2–8 个唯一且相邻的永久 Tag。不要使用 PDF 页码、源文件行号或“这一节后半部分”等
不稳定描述。详细规则见
`docs/task-allocation.md`。

### 原文问题的 remark 标记与收尾

原文 typo、缺失证明和数学论证疑点均按“指出并忠实保留原文”处理，不默认安排
纠错或补证明任务：

- 使用 `remark` 标签，记录来源 commit、永久 Tag、原文字样/位置、观察依据和确定程度，
  并明确不在翻译任务中修改；已确认 typo 可同时使用 `source-typo` 标签；
- 保留原 Issue 和诊断历史；仅涉及原文的问题可用 GitHub `not planned` 原因关闭，
  明确说明“已记录为 remark，原文未修复”，不使用 closing relation 冒充源文修复；
- 不为标记创建空提交或空 PR，不改写历史候选/run，不更新 source lock，也不向原文或
  译文正文插入说明或新增 LaTeX `remark` 环境；
- 缺失证明和未确认的数学疑点不能冒称 typo、已修复或结论错误；记录即可，不需要
  为关闭原文问题 Issue 而验证或补齐整份证明，也不把它留作翻译阻塞任务；
- 同时包含译文错误的混合 Issue 只收尾原文 remark 部分，译文错误仍须处理；
- 原文 remark 不单独阻断忠实翻译的候选、审校或发布，但标签和关闭状态不替代
  既有人工审校及其他发布门禁，也不构成对英文原文正确性的保证。

若维护者以后明确要求修复原文，再另行认领独立的源文勘误或上游同步任务。

## 4. 分支和 PR

分支、提交标题和 trailer 按 `docs/git-conventions.md` 执行。一个翻译 PR：

- 只处理一个 Section、一个明确连续的 unit 范围，或同章 2–8 个相邻 Tag 的 batch；
- 只使用一个 Harness、具体模型和不可变 run；
- 必须在 run manifest 中写明 provider/model ID、模型记录和模型 snapshot（如有）；
- 不夹带术语批准、上游同步、工具重构或模板改动；
- 不能修改未声明的 unit、共享政策文件或生成目录；
- 必须附双语 diff、QA 摘要、来源信息和未决问题。

batch PR 用一个 Issue 的 `parent_tags` 声明完整范围，可共享一次模型 run 和一次最终
全量构建；各 Tag 的 unit/candidate 文件仍独立，不能借 batch 混入不相邻范围。

审校 PR 只做审校发现所需的最小修订；术语 PR 与译文应用 PR 分离；上游同步 PR
只处理一个旧 commit 到新 commit 的范围。

PR 模板仍是贡献者的人工声明，但 `pr-contract` 会从 GitHub 原生 closing Issue 关系
验证 Issue 创建时间、状态、标签、owner、branch、changed paths 和结构化 unit 范围；
不能用正文中随意出现的 Issue 编号冒充关联。其余结构、来源、溯源和候选 QA 由
`policy-and-data` 检查。候选合并到 `main` 只保存候选；维护者
选择和正式采用另有记录。

## 5. 当前 `main` 保护

当前 GitHub 规则集已经配置：

- 禁止直接向 `main` push；
- PR 必须通过 `pr-contract` 和 `policy-and-data`；前者检查 Issue→PR 合同，后者包括
  workflow、工具、harvest、溯源、决策和全部候选 batch QA；
- 禁止删除和非快进更新；
- 需要 CODEOWNER 审核的普通 PR 使用 `.github/CODEOWNERS`；
- 仓库作者 `@dongyaotalk` 具有 PR-only administrator bypass，可以独立合并自己
  的 PR，但 GitHub 不会把作者自审显示为普通 `Approved`；
- bypass 不替代语言、数学、术语、许可证和发布记录，具体门禁仍由本仓库数据模型
  和审校文档决定。

CODEOWNERS 必须与 `MAINTAINERS.md` 中的真实 GitHub 账号一致。维护者变更时通过
独立治理 PR 同步修改，不能用本机 Git 身份、模型名称或虚假账号代替。

申请 CODEOWNER 使用 `.github/ISSUE_TEMPLATE/codeowner-application.yml`。申请应
指定最窄责任路径、最小权限、已合并贡献、审核能力和响应承诺。获批必须同时配置
GitHub `Write` 或更高权限，否则 CODEOWNERS 无法作为有效的 required reviewer。
CODEOWNER 只拥有所列路径的审核责任，不自动获得语言、数学或发布审校资格。

当前仓库管理员 `@dongyaotalk` 具有 PR-only administrator bypass：可以在保留 PR
记录的情况下独立合并，不依赖他人批准，但不能直接 push `main`。管理员 bypass
不替代翻译、数学、术语、许可证或发布所要求的事实记录。

## 6. CI 和权限

GitHub Actions 应使用最小权限：

~~~yaml
permissions:
  contents: read
~~~

模型调用、API key、发布令牌不能写入仓库、PR、候选 JSONL 或日志。CI 不应执行
英文 TeX、注释、文献或链接中的指令；它们只是输入数据。

CI 的正式合同见 `docs/ci.md`。当前仓库的 `.github/workflows/ci.yml` 已启用，
`policy-and-data` 会在 PR 和 `main` push 上运行，并由远程 `main` 规则集作为必需状态
检查。R1/R2/R3 的人工审校记录仍须按数据模型提交；GitHub 状态检查不会替代它们。

## 7. 冲突、放弃和重认领

- 同一 unit 或 batch 被两个任务认领时，后认领者暂停并在 Issue 中协调；
- 负责人超过约定期限没有更新状态时，维护者可以将任务标为 `stale`；
- 放弃任务必须说明原因，保留已生成的候选和失败报告；
- 重认领前必须从最新 `main` 重新验证 `upstream.lock` 和来源 hash；
- 不使用手工删除或覆盖他人候选的方式解决冲突。

## 8. 发布和回滚

正式发布只能从满足 `PUBLISHED` 和许可证门禁的 `reviewed` 数据构建。候选模型
输出可以作为明确标注的内部或预览 artifact，但不能使用会误导读者的“正式译本”
封面、tag 或文件名。

Release 必须包含 manifest、PDF hash、中文仓库 commit、英文来源 commit、Schema、
词表、模板和渲染器版本。发布问题通过 revert 或新修订 Release 处理，不重写已发布
历史。

## 9. 新克隆或新 Fork 的配置检查

新克隆、Fork 或更换凭据后先做本地只读检查：

~~~bash
git remote -v
git branch -vv
git config user.name
git config user.email
git status --short
~~~

确认仓库 URL 后再添加或修改 `origin`。添加 remote 和 push 属于明确的 Git 操作；
不要因为主仓库已公开，就覆盖贡献者已有的 Fork remote。
