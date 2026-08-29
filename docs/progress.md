# 翻译进度报告规范

README 的“全书翻译进度”和 `docs/translation-progress.md` 用于回答三个问题：整本书
有多少章已经开始翻译，每一章有多少个 Section 已完成或尚未开始，以及每一章处于
未开始、翻译中、候选译文完成、人工审校或发布中的哪一个阶段。报告只展示已经合并
到中文仓库 `main` 的可追溯状态，不是翻译数据的第二个来源。

## 全书与逐章口径

- 全书概览以 117 章为目录，其中 116 章有可翻译正文；每章只归入一个当前阶段，公开
  展示各阶段的章数和具体章号。
- 逐章 Section 来自锁定英文 harvest 的 `\section{}` 目录结构。Section 是读者可以
  在英文目录中直接定位的固定范围，作为全书和逐章公开统计的统一分母；当前锁定来源
  共 3,299 个可翻译 Section。
- Section 内的永久 Tag 只用于确认范围是否完整，不直接展示 Tag 数，也不把不同长度的
  Section 加权为全书完成百分比。章节表中的“候选完成”“翻译中”“未开始”均为
  Section 数，不能理解为页数、字数或工作量百分比。
- 报告同时显示“候选完成 Section / Section 总数”和相应结构覆盖百分比。该百分比便于
  比较章节目录覆盖情况，但不同 Section 长度不同，因此不是字数或工作量完成率。
- 没有永久 Tag 的 Section（例如上游范围未标记）会保留在章节目录中，但在范围补齐前
  不会被标记为候选完成。
- 自动生成索引章没有独立可翻译 Section，逐章表显示为“不适用”。

## 覆盖定义

- **Section 候选完成**：Section 内所有需要翻译的永久 Tag 都有与 `upstream.lock` 一致
  且 `source_status=CURRENT` 的稳定 unit，并且每个当前 unit 都有至少一个当前模型
  candidate。多个模型覆盖同一 unit 时只计一次。
- **Section 翻译中**：该 Section 至少有一个当前模型 candidate，但尚未满足候选完成
  条件。没有 candidate 的 Section 为“未开始”；仅准备 unit 不改变这一状态。
- **Section 人工审校完成**：该 Section 的每个当前 unit 都有 `status=current` 的正式
  translation revision。PR 合并、模型字段和评论文字不能代替人工审校记录。
- **Section 正式发布**：该 Section 的每个当前 unit 都有 `stage=PUBLISHED` 且
  `publication_status=RELEASED` 的 current revision。
- unit 准备必须覆盖其认领 Tag 的完整翻译范围。若发现 unit 提取不完整，应修复范围
  数据，不能靠修改进度算法把不完整范围标记为候选完成。

逐章状态按 Section 阶段的以下优先级确定：

1. 没有可翻译正文 Section：`不适用`；
2. 全部 Section 已正式发布：`已发布`；
3. 部分 Section 已正式发布：`发布中`；
4. 全部 Section 已有人工审校 revision：`人工审校完成，待发布`；
5. 部分 Section 已有人工审校 revision：`人工审校中`；
6. 全部 Section 已有模型候选：`候选译文完成，待审校`；
7. 部分 Section 已有候选：`翻译中`；
8. 没有候选译文：`未开始`，即使已经准备 unit 也不改变此状态。

“候选译文完成”只表示模型候选已覆盖本章全部 Section 固定范围，不等于人工审校完成
或可以发布。README 和 PR 描述必须持续区分模型候选、人工审校和正式发布。

## 确定性生成

进度不是手工维护的数字。统一运行：

```bash
make progress
```

该命令读取：

- `upstream.lock` 和锁定 harvest 的 `tags/tags`；
- `translation-data/chapter-templates/` 和 `config/chapter-titles.json`；
- `translation-data/units/`、`translation-data/candidates/`；
- `translation-data/reviewed/` 中的 current revision。

命令只更新 README 标记区间和 `docs/translation-progress.md`。逐章表属于生成内容，
不得手工修改。下列命令验证提交中的报告与结构化数据完全一致：

```bash
make progress-check
```

进度报告、生成器或本规范发生变化的 PR，CI 必须运行 `make progress-check`。新增、
删除或更改 current unit、candidate、reviewed revision、章节模板、来源 lock 或 Tag
索引合并到 `main` 后，必须用独立进度 PR 先运行 `make progress`，再执行
`make progress-check`。报告只能包含已经进入 `main` 的数据；开放 PR、其他工作分支、
`tmp/` 草稿、生成 TeX/PDF 和本地缓存一律不计入。

## 提交边界

翻译候选 PR 不直接手改进度表。候选合并到 `main` 后，应在下一批翻译开始前运行
`make progress`，并用独立 `docs(progress): ...` PR 提交生成结果。若同一 PR 修改进度
生成器、统计口径或工作流政策，则按工具/政策变更运行全量 QA，并在 Git 提交前通过
适用的本地 LaTeX 编译门禁。

管理员 bypass 只解决 GitHub 合并权限，不改变进度、审校或发布状态。

## 本地编译门禁

任何提交或 Pull Request 前都必须完成适用的本地 LaTeX 编译并确认命令以零状态退出。
进度生成器、进度规范和 README 的改动至少运行 `make template`，并运行
`make progress-check`。这里的验证只扫描 LaTeX 日志中的硬错误（例如 `LaTeX Error`、
`Emergency stop`、`Fatal error` 和 `Undefined control sequence`）；不要求截图、逐页
渲染或图像检查。构建产生的 TeX、PDF 和日志是临时产物，不得提交。
