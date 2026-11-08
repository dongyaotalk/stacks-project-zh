# CI 门禁合同

`policy-and-data` 使用完整变更集合与记录语义分类；`pr-contract` 保留 Issue/PR 精确
范围、来源身份、closing relation 和 fresh-main 等实际职责。名称、权限及远端保护不变。

## 1. 调度矩阵

| 变化 | policy-and-data |
| --- | --- |
| 纯章节 unit/candidate、run/raw/freeze/直接关系/相关决定 | 单章 chapter-current；多章/共享参与者明确扩大为 qa-current-all，纯数据不附加全工具测试 |
| 纯生成 progress/plan 报告，完整 diff 和全部实际输入与可信主线绑定 | workflow-check、harvest-check、progress-check、plan-check、git diff --check；不附加工具测试、当前数据 QA、历史、render/pdf |
| 明确列举的非规范说明文档 | workflow/harvest 与 diff 检查，报告数据验收未运行原因 |
| 工具、Schema、公共政策/来源、共享或未知路径 | tool-test、qa-current-all、来源/index/模板及适用专项回归 |
| 历史语义/验证器变化 | 对应历史回归；任务明确要求真实全审计时运行 audit-history |

纯章节路径不无条件运行全工具测试或历史审计。分类失败、删除、类型变化或无法识别
的公共路径不能静默跳过。全局 ID 库存仍读取全部 unit；不得从文件名前缀猜章节。

PR checkout 明确使用 event head；比较点为 event base 与 head 的 merge-base，并确认
比较点属于事件主线。分类器和纯数据验证器来自比较点的可信 checkout；工具 PR
执行 head 的工具回归和当前全量。首次迁移时 base 无调度器，明确扩大为工具/当前全量。
main push 使用 before/head 范围；首次或缺失比较点明确走当前全量，不依赖历史 artifact。
不使用 pull_request_target 执行不可信 head，不改变现有 pr-contract 的可信执行方式。

本地 Python3.12 命令：

```sh
make qa-chapter CHAPTER=<slug> MODEL=<lane> BASE_REF=<accepted-main> PYTHON=<python3.12>
# 要 PDF 时直接联合执行，不先重复 QA：
make pdf-chapter CHAPTER=<slug> MODEL=<lane> BASE_REF=<accepted-main> PYTHON=<python3.12>
make qa-current-all BASE_REF=<accepted-main> PYTHON=<python3.12>
make audit-history PYTHON=<python3.12>
```

来源路径总是显式传 HARVEST_DIR。章节渲染/QA 的范围、输入变化、恢复与报告见
[章节当前验收](chapter-current-validation.md)。旧 qa-all/check-repository、qa-batch、
render-batch 和普通整书 render 继续保持严格语义；不要把它们放入普通章节固定流水线。

章节构建隔离到章节 lane、build/chapter-preview 和 output/pdf/chapter-preview，
集中渲染一次；必要 XeLaTeX/Biber/索引多轮属于一次逻辑构建。最终日志必须完整、非空，
无缺字、未定义引用/引用键和重复标签；失败不复制新 PDF，保留原输出。默认不截图。
公共模板/样式/渲染/Make 变更做必要集成构建；不再对每个候选 PR 追加无关整书构建。
Python3.12 的针对性与适用完整工具测试证据可在实现未变时注明绑定复用。

### 纯生成报告

允许路径只有 `README.md`、`docs/translation-progress.md` 和 `docs/translation-plan.md`。
README 只能变更现有 progress/plan 生成标记内的内容；两对标记必须唯一、完整、有序，
不得嵌套或重叠。标记外原字节必须等于可信 base。三个文件均须是 base 已有的普通
100644 文件，删除、rename、symlink、类型或执行位变化不进入此路径。

`stacks_zh/ci_scope.py` 只确认形状，报告有效性仍由可信 base 的两个实际生成器
`--check` 证明。完整 Git diff、可见新路径和事实库存一并检查，不能用路径子集隐藏
候选/政策/Makefile/Schema/工具/来源或未知变化。实际消费的非报告输入、加载工具
及目录库存与接受主线绑定；检查过程中 HEAD、比较主线、英文身份、输入字节或路径
变化均失败。错误、手改、过期或非确定性报告不得在 CI 自动覆盖后宣称通过。
不接受磁盘 PASS 或用户自填结果。PR 与 main push 使用同一现有事件调度；本次工具
迁移本身仍由旧可信 base 按工具/当前全量合同检查。

本地复现同一入口（完整 root 的 diff 决定分类，不能手选快速路径）：

```sh
python3.12 <trusted-base-checkout>/scripts/ci-current.py \
  --root <report-worktree> --harvest <locked-harvest> --base-ref <accepted-main>
```

workflow/harvest、两个报告 check、diff 和独立 pr-contract 均保留。报告 check 各一次，
源码覆盖/容器统计沿用现有生成器。结果仅为 `generated-reports`，明确
`data_qa=not_run`、`history_audit=not_run`、`tool_tests=not_run`，不是 chapter-current、
全库验收或人工批准。输出 JSON 是本次证据，不具有跳过下次检查的权限；失败重跑
删除旧报告结果。未知/混合/公共变化扩大，非法输入或无法确认 base 失败。

### 本地编译证据复用

提交/PR 仍须有适用的零退出和最终完整 TeX 日志证据。纯报告或其他不改变渲染输入
与行为的任务可以复用：列明原命令、chapter/lane、来源锁、事实/模板/样式/渲染器/
构建配置及工具链身份，核验相关输入 hash 未变、PDF/log hash 和原退出状态，说明
本次修改为何不影响渲染。不能把报告 PASS 当作编译 PASS，也不能借复用免除本次
报告检查或工具迁移的适用回归。输入改变或无法证明绑定时，运行实际受影响的
章节/集成构建；默认不截图，生成物不提交。

## 2. 来源 checkout

Runner 必须：

1. checkout 中文 PR；
2. 从 `upstream.lock` 读取规范 URL 和完整 commit；
3. 单独 checkout 英文 harvest 到 `HARVEST_DIR`；
4. 验证 remote、HEAD、commit date 和 tracked working tree；
5. 禁止自动更新或切换来源版本。

CI 不应把英文仓库作为中文仓库的 Git remote，也不应把英文源码复制进中文仓库
提交。

## 3. PR 范围和覆盖率

每个 PR 必须由 `pr-contract` 验证：

- 恰好用 `Closes`、`Fixes` 或 `Resolves` 关联一个本仓库 Issue；
- Issue 早于 PR 创建，处于 `OPEN`，并带有 `claimed` 标签；
- Issue 的 `task_id` 出现在 PR 正文中；
- Issue 的 owner 是 PR 作者，branch 与 PR head 完全一致；
- 所有 changed paths 均在 Issue 的 `allowed_write_files` 中；
- 翻译结构化数据中的实际 `unit_id`、`source_commit`、chapter 和 parent Tag 均在
  Issue 的任务坐标内。

单范围 Issue 使用 `parent_tag`；batch Issue 改用 `parent_tags` 声明 2–8 个唯一永久
Tag，两者不得同时出现。校验器会同时检查结构化记录的 `parent_tag` 和
`tag:<TAG>:...` unit ID 前缀，拒绝超出 batch 集合的内容；旧的单 Tag Issue 保持兼容。

`pr-contract` 只检出默认分支，不检出或执行 PR head 中的代码；PR 中对校验器的修改
必须先合并，后续 PR 才会使用。它只有 contents、Issues 和 Pull Requests 的只读权限。

完整的 PR 范围合同要求核对：

- 声明的 `Translation-Unit` 与实际 unit 一致；
- candidate 和 unit 文件成对存在；
- 修改进度报告、生成器或统计规范的 PR 中，README 与逐章进度报告必须和当前
  unit/candidate/reviewed/永久 Tag 数据一致；
- 优先级配置、计划生成器、README 推荐队列和 `docs/translation-plan.md` 必须通过
  `make plan-check` 保持一致；
- unit_id 在任务范围内且不重复；
- source commit 和 hash 与 `upstream.lock` 一致；
- Harness、具体模型、model record、run ID 与不可变 run manifest 一致；
- protected placeholder、公式、标签、引用和环境没有变化；
- 未解释的英文残留、待决术语和非法状态被阻断；
- 没有修改 build、output、生成模型 TeX 或本地路径；
- 翻译 PR 没有夹带 glossary、upstream lock 或 reviewed 汇总变更。

当前自动化已经检查所有已跟踪候选的 Schema 相关字段、来源、run 溯源、
selection/review/revision 链、候选覆盖率、占位符、英文残留、术语和状态。它按完整 diff 的可信分类检查全部受影响章节；公共变化执行当前全量。历史回放由显式审计保留。

自动化已经阻断缺少 Issue、Issue/branch/path 不匹配和结构化 unit 超范围。语义边界
是否合理、自然语言说明是否准确，以及非结构化文件的内容是否属于任务范围，仍由
维护者人工核对。只运行一个手工指定的 `make qa` 不足以覆盖多文件 PR；合并到 `main` 后按真实 push 提交范围执行同一分类规则。

## 4. Artifact 和权限

候选渲染、日志、双语 diff、QA 摘要和 PDF 只能作为 CI artifact 保存，不能写回
仓库事实数据。正式 PDF 和 manifest 作为 GitHub Release 产物上传。

Actions 默认使用最小权限：

~~~yaml
permissions:
  contents: read
  issues: read
  pull-requests: read
~~~

第三方 Actions 必须固定到完整 commit SHA，并在行尾注释对应主版本；不能只使用
可移动的分支名。升级 Action 使用独立构建/CI PR，并重新运行门禁。

不在 workflow、Issue、PR 评论、日志或候选 JSONL 中输出模型凭据、API key、SSH
私钥、访问令牌或个人隐私。

## 5. 分支保护

当前远程 `main-protection` 规则集实际配置为：

- 所有普通变更通过 Pull Request；
- 至少一项批准和 CODEOWNER 审核，并解决 review threads；
- strict required status checks `policy-and-data` 和 `pr-contract`；
- 禁止删除 `main` 和非快进更新；
- `@dongyaotalk` 仅可在 PR 上使用管理员 bypass，不能绕过 PR 直接 push。

R1 以上语言审校、R3 和指定 R2 数学审校由结构化审校记录和
`make decision-check` 负责；已发布 tag 不可移动是仓库治理政策。它们不是 GitHub
ruleset 中独立的 reviewer/status/tag 规则，不能把平台设置描述成已经自动完成这些
语义判断。

CODEOWNERS 必须与 `MAINTAINERS.md` 一致。CODEOWNERS 审批不能替代语言或数学
审校；对应 reviewer 仍须按风险等级留下结构化记录。

## 6. 失败处理

- 来源 checkout 失败：阻断，不降级到其他 commit；
- Schema、结构或占位符失败：拒绝候选；
- 待决术语：保持 `DECISION_REQUIRED`；
- critic 出现 blocker/critical：不能提升阶段；当前自动 critic 门禁尚未实现，
  `CRITIC_OK` 不得由贡献者手工宣称；
- TeX 失败：区分数据、渲染器、模板和环境责任；
- 许可证不确定：阻断公开 Release，但不应由自动检查猜测授权。

## 7. 本地与远端结果

本地源码部署前，既有远端 workflow 可能仍执行旧严格合同。本地 chapter-current 通过
不能冒称已获得远端必需状态；远端写入、提交、合并与保护设置均须用户实际授权。
