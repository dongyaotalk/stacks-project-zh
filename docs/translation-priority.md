# 翻译优先级和任务调度

本文定义全书 117 章的长期默认翻译政策，以及用户如何在一次运行中覆盖该政策。
`config/translation-priorities.json` 是 P0–P4、wave、章内推荐顺序和研究轨道的唯一
机器事实源；本文件解释其语义，不复制 117 条配置。

## 1. 分级目标

- `P0`：中文资源稀缺且位于 Stacks Project 核心主线，应首先推进；
- `P1`：直接支撑核心主线，或具有很高的研究与教学价值；
- `P2`：重要但替代教材较多，或属于第二阶段进阶内容；
- `P3`：受众较窄或技术性较强，按明确读者需求推进；
- `P4`：维护、废弃、许可或自动生成内容，不作为正文翻译投入重点。

评级衡量的是“中文翻译的边际读者价值”，不是数学重要性的绝对排序，也不是英文
目录依赖顺序。已有低优先级候选不会被删除或回滚；优先级只决定后续资源首先投向
哪里。章号会随锁定上游目录显示，稳定机器身份始终使用 chapter slug。

当前维护目标在第一 wave 最前，顺序是：

~~~text
115 → 116 → 117 → 112 → 113 → 114
~~~

第 117 章是由上游自动生成的索引；当前没有可翻译 Section 时，计划仍明确显示其 P0
政策和不可执行状态，自动选择器会跳到下一个可执行范围。完成 112–117 的当前维护目标
后，长期入口路线从第 105 章开始，再连接位点、层、下降、代数空间、代数栈和可表性。
第 10 章交换代数仍然重要，但完整翻译成本很高且中文替代教材较多，因此列为 P1，并
优先准备 P0/P1 主线实际引用的 Section。

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
make next-task CHAPTER=115
make next-task CHAPTER=obsolete TAG=0BM0
make next-task CHAPTER=115 TAG=0BM0 JSON=1
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

修改优先级属于独立政策变更，需要说明 method revision 和评级理由；不得在普通候选
翻译中顺手调整。chapter template 是可再生任务骨架，unit/candidate/reviewed 是翻译
事实，均不得承载 P0–P4 字段。current unit、candidate 或 reviewed 数据合并后，应像
进度报告一样用独立计划更新运行 `make plan`，普通翻译 PR 不夹带生成文档。
