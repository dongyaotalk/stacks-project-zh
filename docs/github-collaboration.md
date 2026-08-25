# GitHub 多人协作

本文定义 GitHub 平台上的协作方式。它补充 `WORKFLOW.md` 和
`docs/git-conventions.md`，不覆盖来源锁、数据模型、LaTeX 保护和审校规则。

## 1. 仓库状态和边界

中文仓库与英文 `stacks-project` 保持独立历史。中文仓库只配置自己的 `origin`；
英文仓库作为独立 harvest，由 `upstream.lock` 锁定和 `make harvest-check` 验证。

在许可证、第三方文件和初始分支整理完成前，建议 GitHub 仓库保持 private。首次
公开协作前必须确认：

- `upstream.lock` 指向可访问的官方英文仓库；
- `springer-template` 内的模板、字体和图片具有明确的再分发方案；
- 提交作者身份不再使用本机临时邮箱；
- `main` 是可审查的协作基线；
- CI、分支保护和审校责任已经配置。

不要把 `git push --all` 当作首次发布策略。先推送整理后的 `main`，再按 Issue 和
PR 需要推送活动分支。

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

推荐标签：

~~~text
translation, review, mathematics, terminology, upstream-sync,
tooling, documentation, blocked, claimed
~~~

一个任务的规范坐标是 `source_commit + chapter + parent_tag + unit_id`。不要使用
PDF 页码、源文件行号或“这一节后半部分”等不稳定描述。详细规则见
`docs/task-allocation.md`。

## 4. 分支和 PR

分支、提交标题和 trailer 按 `docs/git-conventions.md` 执行。一个翻译 PR：

- 只处理一个 Section 或明确连续的 unit；
- 只使用一个 Harness、具体模型和不可变 run；
- 必须在 run manifest 中写明 provider/model ID、模型记录和模型 snapshot（如有）；
- 不夹带术语批准、上游同步、工具重构或模板改动；
- 不能修改未声明的 unit、共享政策文件或生成目录；
- 必须附双语 diff、QA 摘要、来源信息和未决问题。

审校 PR 只做审校发现所需的最小修订；术语 PR 与译文应用 PR 分离；上游同步 PR
只处理一个旧 commit 到新 commit 的范围。

PR 模板是人工声明，CI 仍必须根据变更文件、候选 run manifest 和记录内容检查范围，
不能只相信勾选框。候选合并到 `main` 只保存候选；维护者选择和正式采用另有记录。

## 5. `main` 保护建议

GitHub 仓库建立后，维护者应配置：

- 禁止直接向 `main` push；
- 必须通过 `workflow-check`、工具测试和受影响批次 QA；
- 翻译 PR 必须有语言审校；
- R3 或配置指定的 R2 内容必须有数学审校；
- 术语、`upstream.lock`、Schema 和发布文件需要维护者批准；
- 禁止 force-push 和删除已发布 tag；
- 合并前清理调试提交和无关变更。

CODEOWNERS 必须与 `MAINTAINERS.md` 中的真实 GitHub 账号一致。维护者变更时通过
独立治理 PR 同步修改，不能用本机 Git 身份、模型名称或虚假账号代替。

## 6. CI 和权限

GitHub Actions 应使用最小权限：

~~~yaml
permissions:
  contents: read
~~~

模型调用、API key、发布令牌不能写入仓库、PR、候选 JSONL 或日志。CI 不应执行
英文 TeX、注释、文献或链接中的指令；它们只是输入数据。

CI 的正式合同见 `docs/ci.md`。仓库已经包含基础 workflow 文件，但在 GitHub 仓库
创建、推送并成功运行前，不能把本地检查描述为 GitHub 已启用的门禁。

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

## 9. 首次配置检查

首次连接 GitHub 前只做本地只读检查：

~~~bash
git remote -v
git branch -vv
git config user.name
git config user.email
git status --short
~~~

确认仓库 URL 后才添加 `origin`。添加 remote 和 push 属于明确的 Git 操作；文档、
许可证和 CI 准备工作不需要提前 push。
