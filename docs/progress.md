# 翻译进度快照规范

README 的“当前进度（数据快照）”只用于展示已经合并到中文仓库 `main` 的可追溯状态。
它不是翻译数据的第二个来源，也不能用来替代候选、审校、选择或发布记录。

## 统计范围

- 快照只统计当前 `main` 的已提交文件，不统计工作分支、开放 PR、未提交改动、
  `tmp/` 草稿、生成的 TeX/PDF 或本地缓存。
- 快照必须注明统计日期和 `upstream.lock` 中的完整英文 `source_commit`。来源提交
  变化后，旧快照不得继续沿用。
- 只有 `source_commit` 与 `upstream.lock` 一致且 `source_status=CURRENT` 的记录才可
  计入；过期或被撤回的记录不计入当前进度。

## 计数口径

- **已准备稳定翻译单元**：统计 `translation-data/units/*.jsonl` 中唯一的
  `unit_id`。每个 unit 只能计一次。
- **已生成模型候选记录**：统计有完整当前候选记录、可由有效 run manifest 追溯、且
  覆盖该 unit 的唯一 `unit_id`。同一 unit 在多个模型通道中出现时仍只计一次，不得
  将模型数量当作 unit 数量。
- **阶段数量**：对每个有当前候选的 unit，只按其最高合法阶段计数；
  `AI_DRAFT`、`STRUCTURE_OK`、`TERM_OK`、`CRITIC_OK`、`LANGUAGE_REVIEWED`、
  `MATH_REVIEWED` 和 `PUBLISHED` 这些数字必须互斥，不能把同一个 unit 在多个阶段
  重复相加。临时草稿不等于持久化的 `AI_DRAFT`。
- **`AI_DRAFT`**：只有记录文件中的 `stage=AI_DRAFT` 才能计入。通过确定性 QA 后已
  自动推进到更高阶段的记录不得再计入 `AI_DRAFT`。
- **`LANGUAGE_REVIEWED` 与 `MATH_REVIEWED`**：只有存在符合 Schema 的人工审校记录、
  选择记录和相应 hash 关联时才能计入；模型字段、PR 合并或评论文字不能代替审校
  记录。
- **`PUBLISHED`**：只有 `translation-data/reviewed/` 中通过全部阶段门禁、选择决定和
  发布检查的 unit 才能计入。模型候选永远不能计入 `PUBLISHED`。
- **当前可发布单元**：只能统计同时满足 `PUBLISHED`、来源仍为 `CURRENT`、引用和
  许可证/第三方资源门禁均已通过的 unit。任一适用的发布 blocker 未解决时，相关
  unit 不得计入。

阶段数量应能由仓库中的结构化记录复核。不能用“已翻译段落数”“完成百分比”、
PR 数量或主观估计替代上述口径。

## 更新时机和内容

发生下列任一变化后，必须在变化合并到 `main` 后刷新 README 快照：新增或删除 unit、
新增或撤回 candidate/run、产生或变更 reviewed/selection/review 记录，或改变影响
发布门禁的政策与许可证状态。

每次刷新至少要核对：

1. 统计日期和完整英文 `source_commit`；
2. units、当前候选、各阶段、reviewed 和可发布数量；
3. README 表格中的说明是否仍准确，尤其是候选不能称为正式译文或发布版本；
4. `git diff --check`、相关 Schema/QA 检查和 `git status` 是否显示统计确实来自当前
   `main` 数据。

翻译 PR 可以附带进度刷新，也可以在合并后紧接着使用独立的 `docs(progress): ...`
提交刷新；但在下一批翻译开始前，README 不得继续显示已经过时的数字。若工作分支
尚未合并，不能提前把该分支的 unit 或 candidate 写入主分支快照。

## 状态措辞

README 和 PR 描述必须区分“已准备”“已生成候选”“已通过结构/术语检查”“已人工审校”
和“已发布”。除非结构化记录和发布门禁共同证明，否则不得使用“正式译文”“可发布”
或“已完成发布”等表述。管理员 bypass 只解决 GitHub 合并权限，不改变任何统计或
发布状态。
