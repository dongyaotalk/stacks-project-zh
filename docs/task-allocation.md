# 翻译任务分配和范围锁定

本文定义“指定翻译某一部分”的机器可识别边界。内容规范仍以
`WORKFLOW.md`、`docs/data-model.md` 和 `config/workflow.yml` 为准。

## 1. 任务坐标

一个任务至少由以下字段确定：

~~~yaml
task_id: categories-001M
source_commit: a04446e57ec1fbc252a871afcec7752fb2807b14
chapter: categories
parent_tag: 001M
unit_ids:
  - tag:001M:title
  - tag:001M:statement
  - tag:001M:p001
harness_id: codex
model_id: gpt-5.6-sol
model_record_id: openai:gpt-5.6-sol:owner-confirmed
run_id: run-20260825-categories-001m-gpt56sol-01
model_lane: openai-gpt-5.6-sol
~~~

含义：

- `source_commit`：英文内容的完整 40 位 SHA；
- `chapter`：上游 chapter 文件名；
- `parent_tag`：Section 或父级永久 Tag；
- `unit_ids`：实际允许修改的稳定单元；
- `harness_id`：执行任务的工具，例如 `codex` 或 `claude-code`；
- `model_id`：实际生成候选的具体模型；
- `model_record_id`：模型注册表中的身份记录；
- `run_id`：一次冻结输入运行的不可变清单；
- `model_lane`：候选目录和渲染通道的安全 slug，不能单独作为模型溯源；
- `task_id`：供 Issue、分支和 PR 互相引用的短名称。

`unit_id` 优先使用 `tag:<TAG>:<sub-id>`。没有永久 Tag 的单元仍必须使用已保存的
合成 ID；不能因为上游移动或换页重新编号。

### 1.1 从任意章节开始

`translation-data/chapter-templates/<chapter>.json` 预先初始化锁定上游的全部章节，
并按原书顺序列出 Section 标题、永久 Tag、建议 batch 和 unit 路径。贡献者可以先在
目标章节模板中选择一个 Section：

- `READY`：使用 `unit_files` 中的现有稳定单元创建翻译任务；
- `UNPREPARED`：坐标和建议文件已冻结，但必须先完成独立的 scope preparation；
- `BLOCKED_NO_TAG`：不得手工发明 ID，应先解决永久 Tag 或合成 ID 映射；
- 章节为 `SOURCE_UNAVAILABLE`：该项由上游生成或不提供独立章源文件，不能直接认领。

模板是任务骨架，不是译文容器。候选内容仍只写入对应模型 lane 的 candidate JSONL，
正式译文仍只来自 reviewed revision。运行 `make init-chapters` 更新全部模板，运行
`make chapter-template-check` 检查它们是否与锁定来源和现有 unit 一致。

## 2. 允许和禁止的范围

允许的任务范围：

- 一个 Section；
- 一个 parent Tag 下的相邻 unit；
- 一个明确的候选 batch 文件；
- 一个独立的术语、审校、QA 或上游同步任务。

禁止的范围：

- 以 PDF 页码或源文件行号定义范围；
- 同一 PR 跨多个不相干章节；
- 在定义、列表或证明逻辑中间任意切断单元；
- 修改任务清单之外的 unit；
- 以“顺手修复”为理由修改术语表、`upstream.lock`、reviewed 数据或模板。

默认候选单元总量以 `config/workflow.yml` 中的 300–1500 英文词为宜。标题、短注记、
不可拆的定义或证明可以低于下限；超过上限应拆成语义完整的子任务。

## 3. 写入所有权

- 一个 unit 同一时间只能有一个写入者；
- 一个候选 batch 文件同一时间只能由一个 PR 修改；
- 翻译者和 critic 不得共享同一上下文；
- 并行任务必须写入不同文件，不能依赖行级合并；
- 共享政策文件、词表、`upstream.lock`、reviewed 汇总和公共 manifest 串行修改；
- 生成的 TeX、PDF 和报告不属于任务写入范围。

如果一个 batch 文件经常需要多人同时修改，应先进行工具/数据 PR，把它拆成稳定
的 unit-level 文件，再开放并行翻译。

## 4. 认领生命周期

推荐状态：

~~~text
AVAILABLE → CLAIMED → IN_PROGRESS → PR_OPEN → REVIEW
                                      ├→ BLOCKED
                                      └→ MERGED
AVAILABLE ← ABANDONED
~~~

认领步骤：

1. 创建或更新翻译任务 Issue；
2. 填写 `source_commit`、Tag 和完整 unit 列表；
3. 由负责人认领 Issue，并写入分支名；
4. 从最新 `main` 创建任务分支；
5. 只写任务声明的文件；
6. 打开 PR，引用任务 Issue；
7. CI 和人工审校通过后合并；
8. Issue 记录合并 commit 和剩余问题。

任务被阻塞时保留 `BLOCKED`，不要把未完成单元伪装成 `MERGED`。放弃任务时说明
原因和已有输出，其他人从最新 `main` 重新认领。

这里的“引用”必须使用 `Closes #<issue>`、`Fixes #<issue>` 或
`Resolves #<issue>` 形成 GitHub 原生 closing relation。Issue 必须早于 PR 创建、处于
`OPEN`、带有 `claimed` 标签，并包含与 PR 一致的 owner、branch 和
`allowed_write_files`。不得先开 PR 再补 Issue，也不得只在正文中提到一个编号。

## 5. 分支命名和大小写

分支格式见 `docs/git-conventions.md`。Tag 本身可以含大写字母，但分支 slug 建议
使用小写；PR、Issue 和 `Translation-Unit` trailer 保留来源中的规范 Tag。例如：

~~~text
translate/categories/001m/codex
Translation-Unit: tag:001M
~~~

历史分支不因本规则批量改名；新任务按统一规则创建。

## 6. PR 范围检查

翻译 PR 的变更必须能映射回任务坐标：

~~~text
Source-Commit: <same as upstream.lock>
Translation-Unit: <declared section or unit>
Translation-Model: <declared lane>
Translation-Harness: <declared harness>
Translation-Run: <immutable run ID>
Prompt-Version: <declared version>
~~~

维护者或 CI 应检查：

- 变更的 unit 是否都在 Issue/PR 声明范围内；
- unit 的来源 hash 是否与 `upstream.lock` 一致；
- candidate 文件和 unit 文件是否成对存在；
- 是否出现重复 `unit_id`；
- 是否修改了生成目录或不允许的共享文件；
- 是否把一个模型候选提升成了人工审校状态。

当前本地 `make qa` 验证单个 batch；GitHub 的 `policy-and-data` job 对仓库内全部已跟踪
候选 batch 执行 `make qa-all`。独立的 `pr-contract` job 验证 Issue 生命周期、branch、
changed paths 和结构化 unit 是否落在任务坐标内；语义范围和非结构化内容仍由维护者
人工核对，不能把 PR 模板勾选框当作完整审查。

## 7. 任务记录最小模板

~~~yaml
task_id: categories-001M
state: CLAIMED
source_commit: a04446e57ec1fbc252a871afcec7752fb2807b14
chapter: categories
parent_tag: 001M
unit_ids:
  - tag:001M:title
  - tag:001M:statement
owner: github-user
branch: translate/categories/001m/openai-gpt-5-6-sol
harness_id: codex
model_id: gpt-5.6-sol
model_record_id: openai:gpt-5.6-sol:owner-confirmed
run_id: run-20260825-categories-001m-gpt56sol-01
model_lane: openai-gpt-5.6-sol
review_roles:
  language: required
  mathematics: required
claimed_at: 2026-08-25T00:00:00+08:00
issue: "#123"
pr: null
blocked_reason: null
~~~

GitHub Issue 是协作认领记录，`translation-data/` 是译文事实来源。不要把同一条
译文复制到任务记录中形成第二套事实来源。
