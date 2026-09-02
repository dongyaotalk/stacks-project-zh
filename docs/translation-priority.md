# 翻译优先级和任务调度

本文定义全书 117 章的长期默认翻译政策，以及用户如何在一次运行中覆盖该政策。
`config/translation-priorities.json` 是 P0–P4、wave、章内推荐顺序和研究轨道的唯一
机器事实源；本文件解释其语义，不复制 117 条配置。

## 1. 分级目标与证据口径

优先级同时衡量两个主维度：

1. **重要性**：是否位于概形到栈、étale 上同调、形变和可表性等核心路线，是否被
   后续章节反复依赖，以及是否具有高频研究、查阅或教学价值；
2. **中文资料稀缺度**：是否已有正式出版的中文教材、中文译本，或公开且成体系的
   中文课程讲义。只有百科条目、课程大纲、单次报告、零散笔记或片段，不视为系统
   中文替代资料。

资源稀缺度来自可复查的公开资料抽样，不声称穷尽整个中文互联网；遇到新的成体系
资料时可以在独立政策 PR 中调整。按这两个维度，分级为：

- `P0`：重要性高，且系统中文资料稀缺或缺失；第 4 章另有显式用户覆盖；
- `P1`：重要性高但已有较多中文替代，或重要且稀缺但不是第一主线；
- `P2`：有明确价值但已有成熟中文替代，或属于第二阶段进阶内容；
- `P3`：中文资料可能稀缺，但受众较窄、依赖较深或边际读者价值较低；
- `P4`：维护、废弃、许可或自动生成内容；候选完成后不占正文翻译队列。

评级衡量的是“中文翻译的边际读者价值”，不是数学重要性的绝对排序，也不是英文
目录依赖顺序。已有低优先级候选不会被删除或回滚；优先级只决定后续资源首先投向
哪里。章号会随锁定上游目录显示，稳定机器身份始终使用 chapter slug。

第 4 章“范畴”已有较多中文替代，本来不会因稀缺度进入 P0；但用户明确要求先把该章
翻译到候选完成，因此它是唯一的 P0 第一 wave：

~~~text
第 4 章（categories）候选完成
→ P0 第二 wave：代数栈导论、位点与栈、下降、étale、代数空间、代数栈、形变与可表性
~~~

第一 wave 是持久化的用户范围覆盖，不改变“范畴论中文材料相对丰富”的资源判断。
第 112–116 章的候选已经完成，第 117 章又是自动生成索引，因此六章现在均为 P4；它们
仍保留完整进度和审校状态，但不再挤占正文翻译顺序。概形、交换代数等基础仍然非常
重要，不过已有中文教材或中文授课材料，所以列入 P1/P2，并优先准备稀缺主线实际依赖
的 Section。

## 2. 选择优先级

任务选择严格分两步：

~~~text
effective_scope = explicit_user_scope if provided
                  else highest_ranked_unfinished_scope

next_action = resolve_workflow_state(effective_scope)
~~~

展开后的排序为：

1. 用户显式指定的 Chapter/Tag；
2. 否则按 chapter priority 的 P0 → P4；
3. 同一优先级按 wave 和 chapter order；
4. 同一章按 Section ordinal；
5. 该 Section 的事实状态决定具体动作。

状态决定“做什么”，不会轻易推翻章节价值排序。例如 P0 章节需要先准备 unit，而 P3
章节已经 `READY` 时，自动模式仍返回 P0 的 `PREPARE_SCOPE`。

## 3. 显式范围覆盖

~~~bash
make next-task
make next-task CHAPTER=4
make next-task CHAPTER=categories TAG=001L
make next-task CHAPTER=4 TAG=001L JSON=1
~~~

无参数时系统决定 Chapter 和 Section。指定 Chapter 后，系统只在该章选择下一节；同时
指定 Tag 后，系统只判断该 Section 的下一动作。用户选择是运行时约束，不会把章节永久
改成 P0，也不会改写配置。

显式范围没有剩余工作时，命令明确返回这一事实，不会悄悄跳到其他章。如果调用者确实
希望继续自动选择，可以明确设置 `FALLBACK=1`。

## 4. 动作状态机

| 事实状态 | 返回动作 |
| --- | --- |
| `BLOCKED_NO_TAG` | `RESOLVE_TAG` |
| `UNPREPARED` | `PREPARE_SCOPE` |
| `READY` 且没有 candidate | `TRANSLATE` |
| candidate 只覆盖部分 unit | `CONTINUE_TRANSLATION` |
| candidate 完整且没有人工 revision | `REVIEW` |
| 人工 revision 只覆盖部分 unit | `CONTINUE_REVIEW` |
| 实际要求数学审校（含 R3 固有要求或 selection 指定的 R2）且只有语言审校 | `MATHEMATICS_REVIEW` |
| 所有必需审校完成但尚未发布 | `PUBLISH_PREPARATION` |
| 全部 current revision 已发布 | `DONE` |

候选合并仍不等于审校或发布。选择器读取 chapter template、unit、candidate、selection
和 current reviewed revision，从 selection 的 `review_required` 与风险基线合成实际审校
要求；它不授予人工审校状态，也不修改任何翻译事实。

## 5. 确定性计划

`make plan` 更新 README 的推荐任务区间和 `docs/translation-plan.md`；后者列出 117 章
的政策、当前下一范围和动作。`make plan-check` 验证生成结果与配置和结构化数据完全
一致，并由 CI 执行。

README 的区间名为“推荐翻译顺序”，因此只展示仍需补 Tag、准备范围、生成候选或继续
候选翻译的章节；同一章较早的 Section 已进入 `REVIEW` 时，表格继续显示该章第一个仍
处于翻译阶段的 Section。整章候选译文已经完整后，它才不再占用这张翻译推荐表，但仍
完整保留在 `docs/translation-plan.md` 的当前任务和 117 章总表中；自动选择器和显式
Chapter/Tag 选择也继续使用完整动作状态机。

修改优先级属于独立政策变更，需要说明 method revision 和评级理由；不得在普通候选
翻译中顺手调整。chapter template 是可再生任务骨架，unit/candidate/reviewed 是翻译
事实，均不得承载 P0–P4 字段。current unit、candidate 或 reviewed 数据合并后，应像
进度报告一样用独立计划更新运行 `make plan`，普通翻译 PR 不夹带生成文档。
