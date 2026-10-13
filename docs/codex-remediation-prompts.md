# 可复制的 Codex 提示词

使用方式：第一段可续接当前 goal；如你自行选择新建 goal，也可完整粘贴。
旧 goal 的未完成工作须如实记录；不为了交接替你创建新聊天/goal或虚报完成。
第二段用于单个修复批次。实际 branch/main、审计数字和模型身份都要重查。

## 1. 新 goal：继续全部八项修复

```text
本 goal 的目标是完成 stacks-project-zh 项目的全部八项审查修复 F1–F8，
包括 S4 数据修订、S5 默认强制门禁和 S7 全库集成验收。完成后写详细开发文档
和可复制的 Codex 提示词，记录架构、复现命令、验收证据和后续维护方法。

用中文回复。最新DATA为Issue784/PR785，已合并接受main
8cd73b2b1edc31ec4fe3af6711cc5d221d2f515e；其后独立progress/plan及所有已合并
成果也要保留。英文锁定a04446e57ec1fbc252a871afcec7752fb2807b14。
检查点239批/1248活跃unit，剩122问题batch、560术语候选/1813诊断；坐标、来源
错误、proof不匹配零，187组/218proof全部match。完整来源库存43242条、READY
37198/BLOCKED6044、16888诊断、116Git文件roundtrip/117章。数字须从fresh main
重测，READY/BLOCKED不自动采用事实。05SH/05PU已修复，不重复认领；784真实
Section0013六完整batch0014–0019，32旧→8新、六v4/八restoration、125来源要求/141
双语声明及全部旧历史已保存。实际run为run-20261013-categories-definitions-complete-gpt6astra，
真实gpt-6-astra/xhigh，snapshot未暴露；新任务必须重读实际元数据、动态解析Harness，
不得沿用旧模型、turn或版本。首稿一unit token错序被拒且未采用，模型完整重出五字段
后才组装。PR779严格记号、PR781历史parent双锚点v10、PR783完整来源词证据均已合并。
770真实Section001L六完整batch16旧→10新、两个真实gpt-6.1-sol run/raw及001P完整历史仍保留。
前置PR772登记完整英语functor-of-points来源概念，PR774实现首次Git入库前完整
pre-adoption-replay-v1；不重做工具或删原输出。691/698/699已在PR759书末独立
“勘误与原文疑点”表注明英文版本并关闭为留档，非数学裁定或英文修复。
0AHK/d58a764及其后所有数据/工具/独立文档仍是接受历史。开发指南记录完整证据。
下一DATA前先核实784之后独立progress/plan任务是否已合并；Issue786为本检查点
的独立任务，不能依本文猜其当前状态。剩余Categories24、Sets17、Conventions5、
Coding2、Desirables18、FDL2、Guide21、Introduction2、Obsolete31问题batch。
001B–001I只读预检未认领；27旧拟恢复为12完整新/575来源词，001I:p002/p003共同对应
原生paragraph/7，现行单段和split-preceding合同拒绝该边界。完整未来库存另有12项
旧来源词证据需独立迁移至锁定完整容器。须继续核验完整来源及所需前置，不裁去两段
或把可通过11个提议当完整范围，不改变词形/术语批准。继续同章真实完整语义范围的S4，全部S4
后才独立S5默认强门禁和S7；当前goal持续，不因单批或交接文档而结束。

本地使用pyenv已安装的Python3.12，每条Make显式传同一PYTHON；本检查点实际
3.12.6。频繁排版可用make pdf-chapter CHAPTER=categories MODEL=openai-gpt-5.6-sol，
但不能替代提交前规定的全库检查和整书render/pdf。未知语法/数学文字仍BLOCKED。

这是已开展项目的续接，不是重新从零开发。先只读核实当前工作区、Git 分支及
HEAD、GitHub 最新 main、打开 PR/claimed Issue 和实际审计；保留已合并成果及
用户未提交改动，不根据交接快照直接覆盖文件或重复做已完成任务。

先读 AGENTS.md、WORKFLOW.md、docs/engineering-remediation.md、
docs/remediation-development-guide.md、docs/source-extraction.md、
docs/source-alignment.md、docs/source-container-restoration.md、
docs/model-provenance.md、docs/source-term-inventory.md、
docs/task-allocation.md、docs/translation-priority.md、docs/github-collaboration.md、
docs/git-conventions.md 以及任务相关 docs/config。存在未合并数据任务时先核实
并收尾，不新认领相同 unit/candidate 文件。

继续原 F1–F8 的全部范围，不把当前单批或通用抽取器完成当作总目标完成。
全库抽取器已实现，可一次生成锁定 Git 来源库存及统一修复队列；READY/BLOCKED
仅是来源准备状态，不能自动改事实。从最新事实重建 extract-all/check 和
source-alignment/check，按 repair-queue 的真实完整语义范围继续修复。
优先收尾尚存坐标/未保护 TeX/来源诊断，然后集中完成来源术语覆盖，全部数据
修复后才启用 S5 强门禁和完成 S7。不能仅凭 qa-all 通过就声称来源术语已经完整。

先写开发/验收计划，按先 claimed Issue 后分支/实现/本地验收/PR 的顺序执行。
提前声明 owner、branch、锁定 source commit、chapter、真实及历史 parent Tag、
完整旧新 unit ID、精确 allowed_write_files 和 run/model 范围。数据、工具、
政策、术语批准、模板和进度分别开任务/PR，范围变更先更新 Issue。

英文 harvest 和 upstream.lock 保持；不用行号或页码作为范围，不送原 TeX
整文件给模型。完整来源容器从锁定 Git 重新核验真实 owner/Section/selector/
边界及原字节；未知语法/数学文字继续 BLOCKED，不调整规则来掩盖残项。

每次实际生成前冻结完整新 unit、每个完整有序旧组及全部候选、完整 ancestry、
政策/风格/词表/prompt/来源词目录及 context hashes。Harness 运行时动态解析，
模型/effort/turn 根据真实元数据记录；不要复制旧值或猜 snapshot。
当前模型必须实际生成每个新单元完整五字段，程序只保护、序列化、验证和装配，
不能生成中文、机械补术语或把旧输出冒称新模型输出。每个五字段与不可变 raw
逐项相等，保护 token 原序/次数/尾空白严格保持。所有数学术语逐次中文（English），
未知词待决，不授予术语/critic/语言/数学审校或发布批准。
完整旧输入、原输出/run、派生及所有恢复/归档历史原字节保留；有证据地重放
v4 完整分组，不遗弃、重复或归档当前问题以减少残项。

源码 typo、缺失证明或数学疑点只记录 source-only remark；忠实保留原数学，
不补证明、改公式或在正文添加译者说明。remark 不单独阻塞忠实候选。

本地核验 target Git 原片段、全部五字段/context/历史绑定、术语覆盖、全库唯一
ID 和范围外字节；239 全量候选 QA、实际新 run QA、全部所需 Schema/溯源/
决策/来源/117 模板、全库抽取和对齐 check、隔离进度/计划及适用测试通过。
不要无理由反复运行已通过的未变测试。任何 commit/PR 前实际执行当前 lane
make render MODEL=openai-gpt-5.6-sol 和 make pdf MODEL=openai-gpt-5.6-sol，
最终 TeX 无错误；适用模板变化才 make template。比较整书文字，实际查看所有
变化页及邻页 PNG，不能修改生成物绕过失败。generated/build/PDF/本机路径不提交。

本地完成后审查完整 staged diff，只提交允许文件；推送当前分支，创建 PR 并
附加到聊天。核对精确 head/base 的全部远端文件原字节、完整 patch、GitHub-native
单一 closing Issue 合同，以及最新精确 HEAD 的 pr-contract 和 policy-and-data
run/job 均成功、fresh main 等于接受基线。达到上述条件时，已授权使用 admin
bypass squash 合并，无须再问确认，merge body 保留所需 trailers；不直接推 main、
不 force、改 remote/保护规则或伪造人审。合并后核实 main/feature tree、PR MERGED、
Issue CLOSED、原字节和干净工作区。每次 DATA 合并后，下一 DATA 前先完成独立
progress/plan Issue/PR；即使报告没有变化也真实 check 并记录，不手改数字。

除非我明确要求或适用 AGENTS/skill 明确要求，不创建子代理或新聊天，不安装无关
依赖。每约 60 秒用简洁中文汇报真实进展，报告修复前后 counts、下一动作和实际
阻断；不要给未经测量的百分比或工期。只在 F1–F8 最终证据齐备后把 goal 标完成。
如因真实外部条件阻断，遵守 goal 的连续阻断判定，不用困难/耗时代替阻断。
最后交付可审查的详细开发文档与完整可复制提示词，包含最新 main、已合并 PR、
剩余/最终审计、运行命令、门禁及维护边界；未完成部分必须如实列出。
```

## 2. 单个数据批次

将尖括号内容替换为从当前队列读到的真实范围，不能发明 ID、Tag 或路径。

```text
继续修复 stacks-project-zh 的 <chapter>/<batch>，总目标仍是全部 F1–F8。
先核对最新 main/当前工作区和 claimed ownership，读取完整当前 unit/candidate
及其全部 ancestry，用锁定 Git 确认真实 <parent Tag>/<owner Tag> 和完整语义边界。
列出旧新 ID、所有允许路径、来源词数/范围例外和验收标准，创建认领 Issue，
先写开发计划，再按已合并 source-container/v4 合同重新 prepare/check。

冻结完整新来源、全部旧组/candidates/历史、政策/风格/词表/prompt/来源词目录，
动态 Harness 及真实模型/effort/turn；实际完整生成每个新 unit 的五字段。
保留不可变输入/raw/run，逐项验证保护结构与来源术语、context/group/全部历史。
程序只能装配/校验，不能生成中文或改旧输出。

执行适用全量 QA/真实新 run QA/共享门禁/117 模板、全库抽取/对齐 checks，
要求该 target 来源逐字正确且队列清空、范围外 finding/事实保持；当前 lane
render/pdf 和所有变化页及邻页实际看图通过后才提交 PR。远端完整字节/patch/
native 单 Issue 合同、最新精确 HEAD 双 CI 及 fresh base 通过后按授权 bypass
squash。DATA 合并后先独立进度任务，再处理下一批。所有术语和人审仍待决。
批次完成后报告实际 Issue/PR/main、旧新数量及全库残项，继续总 goal。
```

## 3. 最终文档验收

```text
在全部 F1–F8 实际验收完成后，整理详细开发文档和可复制 Codex 提示词。
从最终当前事实重建来源/术语/proof 审计、默认 QA/CI、进度/计划，不靠历史数字。
逐项列 F1–F8 的实现位置、来源依据、拒绝回归、真实命令结果、最终 main/PR/CI，
说明候选修复与人工审校/正式发布的边界。提供 Python/TeX 等环境要求、可复制
运行步骤、完整容器与模型修订/历史流程、常见失败和恢复方法、后续维护提示词。
文档独立 claimed Issue→本地验收→PR，不夹带事实/政策/批准；实际 render/pdf、
完整远端 diff/native 合同及最新 HEAD CI 通过后按已授权 bypass 合并。
只有所有必需工作和文档交付均完成，才把总 goal 标 complete。
```
