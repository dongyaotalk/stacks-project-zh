# 章节验收简化开发记录

基线：远端 main 与 origin/main 均确认为 `a20e21539cfeee7bbb364c6bb19596ff777cf240`。
从该提交创建独立工具工作树；工作区根 AGENTS.md 不存在，仓库 AGENTS/WORKFLOW 已读。
用户主库 HEAD 为 `13b17d1`，有三处 tracked 修改、两处 untracked 和九条 stash；保持原状。
基准工作树含旧实验工具修改，只读使用其事实，不移植工具 patch。

合同调整：章节日常检查当前完整章、直接新关系；公共变化走当前全量；历史审计显式执行。
旧严格 qa-all/check-repository、批次与普通整书渲染继续保留严格语义。
隐式历史点：CLI 当前 QA 后 workflow.render_batch → _complete_provenance；
无标签 typed 定位 → source_placement → load_repository_source_adoptions；
决策 → validate_repository_provenance。章节结果必须切断这三处调用。

阶段与实际命令、耗时、限制及最终证据在本任务 build/chapter-validation 下汇总；
以下记录截止本地开发验收阶段，当时没有提交、推送或远端写入。
报告不能表示历史审计或人工审校通过；随后获得的发布授权与远端结果单独记录。

## 实现与回归

复用 CurrentSourceQA、Schema 与真实采用/派生重放函数；新增章节范围、直接关系
和 CI 分类的小模块。章节渲染消费同进程结果，保留事务恢复及最终 TeX 日志门禁。
可信边界取 accepted main tree 的真实路径、模式及 Git blob ID；计算读取字节的
Git 对象哈希，避免对大型旧 blob 反复解包。它不是磁盘 PASS 或独立基线平台。

日常接口：qa-chapter/check-chapter、render --chapter、pdf-chapter。
公共变化：qa-current-all；显式历史入口：audit-history（qa-all 严格兼容）。
CI 保留 policy-and-data 和 pr-contract，纯数据使用可信比较 checkout 的实现。

原 941 个测试名称均有保留的通过证据，来自完整测试执行与受影响路径复测的并集，
不是一次全绿 make tool-test。最初完整执行在 738 项后因沙箱进程查询错误停止：
719 项通过、19 项失败/错误；后续 200 项有 198 项通过，另两项已修复并复测。
沙箱外进程恢复测试、错误 base 夹具修正及新增交错文件/Git 身份/派生 manifest
回归均保留原失败记录。输入删除转换为 RecordError，符号链接先拒绝再消费结果。
章节 17 项回归 160.740 秒；相关修复后又做针对性边界复测。

当前全量诊断先发现文件 envelope 过严、派生候选误套原 run 坐标要求，修复后
又在 1200 秒上限终止一次历史 blob 解包慢路径；所有日志保留，不表示通过。
直接派生阶段保留 daily 边界，104 个 categories 派生节点的有界诊断随后通过，
运行器总耗时 58.562 秒（阶段内部 49.231 秒）。

旧 composite 新审批仍需显式 decision-check 完整核验原格式绑定；已接受且身份
不变的批准保留主线 hash，不新造审批 hash，也不赋予人工审阅状态。

实际命令、源码冻结清单、测试名称映射和失败/成功日志见 ignored
build/chapter-validation；性能与最终交付结果将在同目录报告中记录。
开发阶段 A–D 未各自单独使用计时器，不估算开发用时；验证命令及阶段使用真实计时。

联合当前检查仅记录阶段结果，在末尾复核实际输入并完成当前验收；阶段对象不发行渲染凭证。新增回归核对阶段对象拒绝渲染，以及阶段结束后输入变化仍使最终检查失败。

较早一轮当前全量成功：15 个 scope、768 对文件，运行器 1076.910 秒；此前失败/超时保留。
后续修改限于同会话字节复用和本次辅助准备资料验证，以受影响输入/联合/渲染回归
复核，未重复执行整库。第 41 章首次完整联合检查 189.374 秒后被未消费证据门禁
拒绝，render_count=0，未开始 PDF。补齐所有实际辅助资料后再冻结并实测。
补充准备资料不授予采用资格，报告明确保留 source_errors；原拒绝记录哈希与
实际 native selector 失败重现。新候选仍执行真实完整采用重放。

第二次联合：章节入口检查 199.203 秒（报告内阶段 188.568 秒），渲染 72.448 秒，
check_count=1/render_count=1，历史守卫未触发。XeLaTeX 因沙箱中字体发现失败，
整次退出 2、275.529 秒，无合格 PDF；沙箱外最小字体诊断 1.579 秒零退出。
恢复编译后 Biber 发现绝对 HARVEST_DIR 带空格被 GNU make abspath 拆分；修正为
单个目录参数解析并添加实际 Make 变量回归，不修改英文库或模板。原失败日志保留。
重复复核整改：章节末尾及渲染同一边界合并实际读取与 snapshot；每个安装边界仍
读取原字节并核对发行声明。输入删除、瞬时变化、声明删除、模式/HEAD/来源与
输出失败恢复回归继续通过。CI 受影响章集合顶层报告也明确为 chapter-current。

第三次冻结联合已成功：入口检查 188.297 秒、渲染 17.417 秒、整次 228.293 秒；
检查/渲染各一次，历史守卫未触发；最终 PDF 与日志通过。检查 180 秒目标仍未达，
保留这次性能证据。决策阶段定位到逐文件 glob 对整份冻结路径库存重复比较，
改为一次枚举与名字集合筛选；原所有 lane 的关联候选范围保持，新增回归核对
枚举次数和其他 lane 重复候选仍被拒绝。共享多章 CI 明确运行当前全量；
单章仍局部，工具调度器改动不能伪装纯数据。来源 context 同会话复用只依据
完整实际值、来源和 native 身份，严格独立接口仍实际校验。

有界决策范围实测（同一 52 对）：原逐名字查询 15.570 秒，单次全部名字查询
0.483 秒；关联路径集合逐项相等。真实当前决策校验 2.323 秒，诊断总计
22.033 秒。改动没有读取其他章候选/context 正文，没有省略其他 lane 同 unit 的
决定与重复检查。对应枚举次数、其他 lane 重复以及未知新决定回归 15.316 秒通过。

当前共 951 个测试名称。完整执行和受影响复测的通过证据逐项映射保留；
未称一次 make tool-test 全绿。最终冻结后的章节/当前全量、编译与保护核对结果
将写入 build/chapter-validation/delivery.json，并导出包含新文件的 review.patch。

最终需求审计的 synthetic 诊断发现无 candidate 的当前 unit 只被读取而未做 Schema；
隔离夹具真实得到 current-all/exit 0。停止正在执行的当前全量（296.723 秒，SIGTERM），
保留日志且不计为通过。补齐全部当前 unit Schema 与至少一个实际 candidate 配对门禁。
首轮回归又发现 glob 迭代器重复消费，立即改为一次保留列表；未删除失败测试。
新增 Schema/缺失配对与原联合输入回归实际通过（17.849 秒）。现共 952 项名称；
重新冻结，章节及当前全量终验使用新的独立标签，旧性能/失败证据保持。

## 第 41 章最终冻结实测

`frozen-source-post-unpaired.json` 绑定实际实现、配置、Schema 和测试，共 162 文件。
使用隔离事实工作树，保持样本 HEAD `0dc8d12b2bb9d152cb755334052424d0f577d1ee`。
`etale41-post-unpaired` 实际通过 52 对文件、189 单元；完整入口检查 167.999707 秒、
渲染 17.036248 秒，联合 Make/PDF 207.034284 秒，退出 0。检查/渲染各一次，
四个显式完整历史入口的运行时守卫未触发。两项性能目标均达成。

报告内阶段实测：范围/Schema 5.103685 秒，当前来源/结构/术语 25.611335 秒，
直接 run/raw/冻结/采用/派生/准备关系 127.817810 秒，相关决策 2.804346 秒。
阶段小计与入口墙钟不同：入口另含实际输入、来源与发行身份的末尾复核。
实际检查 30 个新直接节点；准备资料保留未采用和失败状态，不能冒称模型生成成功。
编译为三轮 XeLaTeX 与一次 Biber；每轮零退出，最终日志门禁通过，无截图。

本轮 evidence 为 `etale41-post-unpaired.json`、`etale41-post-unpaired-cli-timing.json`、
`etale41-post-unpaired-compilation-stages.jsonl` 和同名 `.log`。原 170.696/209.885 秒
的冻结实测及此前全部失败/超时/超预算记录保留，不拿旧源码时间替代本轮。
复现包装器副本与实际命令在 `build/chapter-validation/reproduction/commands.md`；
所有运行命令、真实状态、耗时与日志 hash 由 `verification-runs.json` 汇总。

补充静态门禁的 workflow/harvest/index/117 章节模板已通过；60 秒联合诊断在
progress-check 全书统计阶段终止，未执行 plan-check，不计为完整通过。
剩余 progress/plan 正式验收实际通过，117 章，98.455581 秒；未改写统计文件。
最终 `current-all-post-unpaired` 零退出，812.537594 秒：15 个 scope、768 对文件、
2758 次候选单元检查（包含各 lane），末尾实际输入联合复核完成；不表示全书都已
翻译或重跑了完整历史。章节目标使用独立上述 207.034284 秒的测量，不混入公共验证时间。

## 本地交付与边界

`build/chapter-validation/delivery.json` 汇总真实结果；`test-coverage-final.json` 对应
952 个测试名称全部通过证据，`requirements-evidence.json` 提供关键需求与回归映射。
证据为原广范围执行和受影响复测的并集，不宣称一次 make tool-test 全绿。
`review.patch` 包括全部 tracked diff 和新增源码/规范/测试，可直接审查；导出后执行
反向 apply 的 check 模式和 diff --check，不实际应用补丁。
`preservation-final.json` 核对用户主库、stash、旧实验、基准、原 etale 事实与 PDF、
英文库；最终冻结实现身份另核对。所有旧失败/超时/超预算记录仍在证据目录。

本地开发验收阶段只做工作树准备、实现和验证，没有提交、推送、Issue/PR 写入、合并、
远端 CI 运行或保护修改。完整真实整库历史审计未运行；严格兼容和故意损坏旧历史
由真实 synthetic 回归验证。结果为 chapter-current/history_audit=not_run，
未授予 critic、术语、语言/数学人工审阅或出版批准；默认仅编译验收，无截图。
旧 composite 新审批的严格 decision-check 扩大要求仍明确保留，不伪造兼容审批 hash。

后续发布：用户另行授权先 Issue、后 PR，并使用 PR-only administrator bypass。
提交前确认 main 仍为 a20e215，全部未完成项仅 Issue #907 / PR #916 的第 41 章
候选数据；分页读取其 390 个 changed files，与本工具改动没有路径交集。
执行顺序为工具 Issue #917 → 本工具 PR 与真实门禁 → 授权 bypass squash merge；
#916 对新主线的同步与重新验收随后另行处理，不改写其原事实、审批或状态。
本地代码、配置、Schema、测试和测量事实未变，复用上述冻结验收；仅补齐协作规范
与发布状态说明，并在提交前做适用快速核对。远端结果以实际 PR 检查和合并记录为准。
