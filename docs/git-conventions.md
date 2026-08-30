# Git 分支、提交与 PR 规则

## 1. 仓库边界

- 上层 `stacks/` 不是 Git 仓库。
- `stacks-project` 和 `stacks-project-zh` 是两个独立仓库。
- 中文仓库只配置自己的 `origin`，不得把英文仓库配置成可合并 remote。
- 英文来源通过 `upstream.lock` 关联，不通过 Git 分支或 submodule 关联。
- `main` 只能包含通过门禁的规范、工具、候选、审校和 reviewed 数据。

## 2. 提交身份

公开推送前必须配置真实姓名及可接受的邮箱或托管平台 noreply 邮箱。不得使用自动
推导的临时主机邮箱发布正式历史。修改已经公开的提交作者需要项目维护者批准；
未公开的根提交可以在设置身份后 amend。

`make repo-setup` 不修改姓名和邮箱。

## 3. 分支命名

分支路径使用小写 ASCII、数字、点、下划线、短横线和斜线。Stacks 永久 Tag
可能包含大写字母；放入分支名时转成小写 slug，Issue、数据记录和提交 trailer
仍保留规范 Tag 的原始大小写：

```text
translate/<chapter>/<tag>/<model>
review/<chapter>/<tag>
term/<english-term>
sync/<old-sha>-<new-sha>
tool/<feature>
template/<feature>
docs/<topic>
test/<topic>
release/<version>
```

示例：

```text
translate/sets/0008/model-name
review/sets/0008
term/fibre-product
sync/a04446e-1234abc
docs/translation-workflow
```

例如 Tag `001M` 的分支使用 `translate/categories/001m/model-name`，而提交 trailer
仍写 `Translation-Unit: tag:001M`。既有历史分支不要求仅为大小写规则批量改名。

分支末段写具体模型 slug，例如 `openai-gpt-5-6-sol`，不能只写 `codex` 或
`claude-code`。Harness 和精确模型身份仍由任务清单与 run manifest 表达。
禁止使用长期存在的“一个模型一个分支”。模型通道由目录和记录字段表达。

## 4. 提交标题

格式：

```text
<type>(<scope>): <summary>
```

允许的 `type`：

- `translate`：模型候选译文；
- `review`：人工审校、最小修订和状态提升；
- `term`：术语提议或决定；
- `sync`：英文上游同步；
- `tool`：解析、翻译、检查和渲染工具；
- `template`：Springer/LaTeX 模板；
- `docs`：规范和说明；
- `test`：测试和固定样例；
- `build`：CI、构建和打包；
- `chore`：不改变译文或工具语义的维护。

标题应在 100 个字符以内，摘要使用明确动词，不写 `update`、`misc`、`fix stuff`
等无法审查的描述。

## 5. 必需 trailers

### 5.1 翻译提交

```text
Source-Commit: <full-40-character-sha>
Translation-Unit: <section-or-unit-id>
Translation-Model: <model-id-or-lane>
Translation-Harness: <harness-id>
Translation-Run: <run-id>
Prompt-Version: <version>
```

### 5.2 审校提交

```text
Source-Commit: <full-40-character-sha>
Translation-Unit: <section-or-unit-id>
Reviewed-By: <reviewer identity>
Review-Level: language|mathematics
```

### 5.3 术语提交

```text
Term: <English term>
Decision: proposed|approved|deprecated
```

### 5.4 上游同步提交

```text
Old-Source-Commit: <full sha>
New-Source-Commit: <full sha>
```

trailers 记录可审计事实，不得伪造审校人或用模型名称填写 `Reviewed-By`。

## 6. 原子提交

一个提交只做一件可回退的事。不得混合：

- 术语批准和大范围译文应用；
- 上游 lock 更新和无关翻译；
- 模板重构和 reviewed 译文修改；
- 解析器语义变化和自动重写后的全部数据；
- 模型候选和人工审校身份；
- 生成的 TeX/PDF 与事实数据。

机械迁移应与语义修改分开提交。提交前运行 `git diff --check` 并检查暂存区，而
不是直接执行 `git add -A` 后盲目提交。

创建任何 Git 提交或 Pull Request 前必须完成适用的本地 LaTeX 编译并确认命令以零
状态退出。翻译候选执行 `make render MODEL=<model-lane>` 和
`make pdf MODEL=<model-lane>`；其他文档、进度、政策和工具修改也针对当前候选通道
执行这两条命令（默认 `openai-gpt-5.6-sol`）。只有模板、样式、Makefile 或渲染路径
发生变化时才另外执行 `make template`。裸 `make pdf` 必须显式指定 `MODEL`。缺少
TeX 工具链或出现编译错误时不得提交、推送或创建 PR。生成的 TeX、PDF 和日志仅用于
检查，不得纳入提交。

## 7. PR 类型和粒度

### 翻译 PR

- 一个 Section、一个 Harness、一个具体模型和一个不可变 run；
- 通常包含 300–1500 词的若干相邻单元；
- 不夹带术语批准、工具重构或上游更新；
- 必须提供双语 diff、QA 报告和来源信息。
- 候选合并到 `main` 只保存候选；selection、人工审校和正式 revision 使用后续记录。

### 审校 PR

- 一个 Section；
- 标明语言或数学审校；
- 只做审校发现所需的最小修订；
- 不能把未查看的相邻单元批量标记通过。

### 术语 PR

- 一个术语或一组不可分割的同义/反义术语；
- 提供定义、语境、出现位置、备选译法和迁移影响；
- 批准后另开 PR 应用到现有译文。

### 同步 PR

- 只处理一个旧→新英文提交范围；
- 包含完整 stale 分类和重新审校结果；
- 禁止顺便更新模板或一般文档。

整章、整部或跨多个无关主题的翻译 PR 默认拒绝。

## 8. PR 审批

- 工具、模板和规范 PR：至少一名维护者批准；
- R1 翻译：至少一名语言审校者批准；
- R2：语言审校并按风险指定数学审校；
- R3：语言审校者和数学审校者的明确记录；
- 上游同步和发布：维护者批准，并满足所有受影响单元的审校要求。

审校记录可以由同一合格人员承担两个角色，但两项检查必须分别记录。自动 review
不能替代人工批准。

## 9. 合并和历史

- 禁止直接向受保护的 `main` 推送普通工作提交；
- 默认一个 PR 对应 `main` 中一个逻辑提交，优先 squash merge；
- squash 标题和正文必须保留本规范要求的 trailers；
- 合并前清理 `fixup!`、`squash!` 和调试提交；
- 已发布 tag 指向的历史不得重写；问题通过 revert 或后续修复提交处理；
- 不得对 `main` force-push。

Fork、镜像或临时离线工作树也应在本地保持同样规则。

## 10. 不提交的内容

- `build/`、`output/`、PDF 和 LaTeX 中间文件；
- `.harvest/` 和英文源码副本；
- `source-ir/`、缓存和 SQLite；
- 非 `template` 的生成模型 TeX 目录；
- 编辑器状态、系统文件、临时日志和本地绝对路径；
- API key、访问令牌、模型服务凭据或审校者私人信息。

发布 PDF 应上传为 Release/CI 产物，并由 release manifest 关联到 Git commit。

## 11. 本地规则工具

运行：

```bash
make repo-setup
```

会配置 `.gitmessage` 和 `.githooks/commit-msg`。本地 hook 是便利措施，不是安全
边界；托管平台 CI 仍需执行相同检查。
