# 翻译进度报告规范

README 的“全书翻译进度”和 `docs/translation-progress.md` 用于回答两个问题：整本书
有多少章已经开始翻译，以及每一章处于未开始、翻译中、候选译文完成、人工审校或
发布中的哪一个阶段。报告只展示已经合并到中文仓库 `main` 的可追溯状态，不是翻译
数据的第二个来源。

## 全书与逐章口径

- 全书概览以 117 章为目录，其中 116 章有可翻译正文。每章只归入一个当前阶段，公开
  展示各阶段的章数和具体章号，不累计 Tag 得出全书完成百分比。
- 逐章“候选译文范围”和“人工审校范围”以锁定英文 harvest 的 `tags/tags` 中本章永久
  Tag 为固定结构分母。Tag 按完整 label 的章名前缀归入
  `translation-data/chapter-templates/` 中的 117 章。
- `book-part-*` 只用于书籍分部导航，不属于任何章，不进入分母。
- 自动生成索引章没有独立可翻译正文 Tag，逐章表显示为“不适用”。
- 逐章 `x / y` 只表示本章有多少永久 Tag 已覆盖，不按页数、字数、公式数量或数学难度
  加权，因此不是阅读工作量百分比。
- 已准备 unit 数不能作为全书分母。只用“候选 unit / 已准备 unit”会隐藏尚未提取的
  大部分英文内容，禁止把这种比例称为全书或本章完成率；单纯准备 unit 也不改变章节
  的公开翻译阶段。

## 覆盖定义

- **已准备 Tag**：该 Tag 至少有一个与 `upstream.lock` 一致且
  `source_status=CURRENT` 的稳定 unit。
- **模型候选 Tag**：该 Tag 已准备的每一个当前 unit 都有至少一个与锁定来源一致的
  当前模型 candidate。多个模型覆盖同一 unit 或 Tag 时只计一次。
- **人工审校 Tag**：该 Tag 已准备的每一个当前 unit 都有 `status=current` 的正式
  translation revision。PR 合并、模型字段和评论文字不能代替人工审校记录。
- **正式发布 Tag**：该 Tag 的每一个当前 unit 都有 `stage=PUBLISHED` 且
  `publication_status=RELEASED` 的 current revision。
- unit 准备必须覆盖其认领 Tag 的完整翻译范围。若发现 unit 提取不完整，应修复范围
  数据，不能靠修改进度算法把不完整范围标记为已覆盖。

逐章状态按以下优先级确定：

1. 没有可翻译正文 Tag：`不适用`；
2. 全部 Tag 已正式发布：`已发布`；
3. 部分 Tag 已正式发布：`发布中`；
4. 全部 Tag 已有人工审校 revision：`人工审校完成，待发布`；
5. 部分 Tag 已有人工审校 revision：`人工审校中`；
6. 全部 Tag 已有模型候选：`候选译文完成，待审校`；
7. 部分 Tag 已有候选：`翻译中`；
8. 没有候选译文：`未开始`，即使已经准备 unit 也不改变此状态。

“候选译文完成”只表示模型候选已覆盖本章全部固定范围，不等于人工审校完成或可以
发布。README 和 PR 描述必须持续区分模型候选、人工审校和正式发布。

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
