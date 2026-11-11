# 章节当前验收

普通新增/修改章节使用 `qa-chapter`；需要 PDF 时直接使用 `pdf-chapter`，不要先重复
QA。必须显式提供 `CHAPTER`、`MODEL`、`BASE_REF`、`PYTHON`（3.12）和 `HARVEST_DIR`。
章可含多个真实 run，每个 run 保留自己的身份、冻结输入、原输出、完整参与者与顺序。

```sh
make qa-chapter CHAPTER=etale MODEL=<lane> BASE_REF=<accepted-main> PYTHON=<python3.12> HARVEST_DIR=<read-only-English>
make pdf-chapter CHAPTER=etale MODEL=<lane> BASE_REF=<accepted-main> PYTHON=<python3.12> HARVEST_DIR=<read-only-English>
make qa-current-all BASE_REF=<accepted-main> PYTHON=<python3.12> HARVEST_DIR=<read-only-English>
make audit-history PYTHON=<python3.12> HARVEST_DIR=<read-only-English>
```

`check-chapter --root ... --chapter ... --model-lane ... --base-ref ... --harvest ...`
是 Python CLI。`render --chapter` 使用同一章节会话；生成到独立
`<lane>-chapter-<chapter>` 目录，PDF 逻辑构建允许必要的引擎/书目/索引多轮。
默认无截图或逐页视觉验收，最终 TeX 日志门禁保持。

检查范围从全部真实 unit 的 chapter、候选目录 lane 和文件配对发现，读取轻量全局
unit ID 库存；不能用一两个文件或文件名前缀缩小章节。核对整个章节来源覆盖、Schema、
锁定英文 Git 完整容器、Tag、公式/保护 token 的顺序次数和尾空白、术语和相关决定。
新增 raw/run/freeze/采用/派生及直接父输入必须核验，不允许只核验当前译文而忽略真实生成。

BASE_REF 必须是本地确认主线历史中的确切提交且为 HEAD 祖先。Git 对象的路径、模式
和原字节构成边界身份；任意磁盘 PASS 没有权限。CI 使用实际事件 base/head 的比较点，
纯数据验证器来自可信比较 checkout。无法确认 base 时明确失败，不启动隐式历史回放。

同一变更中的新节点逐个完整检查；共享参与者缺失、错序或范围不完整明确报错并要求
扩大到全部关联章/qa-current-all。到已接受且身份未变的旧祖先停止递归，不展开无关旧
context 或 retired 内容。修改/删除/rename/模式变化的旧不可变输入拒绝日常路径，另立
专门任务；未知路径、公共政策、来源和工具变化扩大到 qa-current-all 与适用回归。

`qa-current-all` 对全部当前 unit 执行 Schema，并要求每个当前 unit 文件至少有一个
实际候选配对；无候选的 unit 不能因未生成章/lane scope 而被漏检。尚未采用的准备
仍保存于冻结输入和证据目录，不能作为无候选的当前 unit 绕过这一门禁。

输入清单包含实际消费的字节、枚举结果、来源身份和加载实现；读取中短暂变化再恢复
仍失败。章节结果仅供同一进程真实渲染消费，拒绝伪造、复制、内容篡改或 root/head/
pairs/lane/来源错配。输出在内存准备并事务安装，失败恢复旧输出。JSON/Markdown 报告
只是 ignored build 下的证据，不是跨进程凭证。

报告 scope=chapter-current、history_audit=not_run，记录 base/head/tree、worktree 视图、
source commit、chapter/lane、pairs/units、阶段实测时间、错误和退出状态。机器通过不
授予语言/数学审校、术语批准或发布资格。完整历史 `audit-history`、旧 `qa-all`/
`check-repository`、严格 batch/整书接口继续保持原语义，日常不必串行调用它们。

纯章节 CI 与本地使用同一局部合同；公共变化执行当前全量，不固定重放全部祖先。
纯生成 progress/plan 同步使用 [CI 合同](ci.md) 的独立 `generated-reports` 范围，
不运行章节/当前全量或历史；这类报告结果不能称为 chapter-current。
历史验证器或历史语义变化需要对应历史回归；任务明确要求全审计时才执行真实全历史。
首次迁移尚未部署的远端 CI 可能继续使用旧合同，本地结果不能冒称远端状态成功。

旧派生候选的人审绑定：已接受且候选/输入身份未变的 composite decision 保留原主线 hash；新增或改变该旧格式 composite 审批须显式 `decision-check` 核验完整旧格式绑定。本章入口报告此具体扩大要求，不生成替代审批 hash。首次采用 decision 的直接 record/input 绑定由同一实际章节会话核验。

新增模型输入/runtime 副本逐项绑定实际冻结输入、任务范围、全部政策、身份、术语清单与
上一候选快照。有 run 的失败生成继续由原失败重放函数核验。没有 run/采用的准备资料
只作未采用输入库存：核验 Schema、来源 lowering、raw 顺序、哈希及拒绝记录；非完整
selector/context 的已保存准备在 preparations 中列出具体 source_errors 和
rejected-unadopted-preparation，generation_validation=not_claimed。它不能提供任何
当前候选、祖先或生成成功凭证；当前候选错误、新实际 run/采用错误仍使章节失败。
未知辅助资料仍触发未消费输入门禁，不通过泛化“证据文件”豁免。

未采用准备的原 model_scope 若恰好只列 lane（可连同真实 model-record），遗漏同一具体
requested/resolved model ID，库存可列为拒绝负结果，保留原 `scope_errors` 与
`generation_validation=not_claimed`。原 scope 文件/冻结字节、唯一路径/unit所有权、
run/章节/parent、接受 origin 的模型/Harness注册和其余来源/政策/runtime/raw检查
全部保持；只支持无前继的原v1/v4准备。该原身份不得有 run、采用或当前候选。
其他 scope 错误继续阻断；不改原 scope，不将负结果转为成功生成或祖先凭证。
未采用准备保留的分片和局部重试输出沿用既有 `_raw_records`，按原预留路径顺序
绑定每份原字节/hash和实际unit顺序；汇集后必须覆盖全部冻结unit，单份不得重复
或越出原unit集合，五字段Schema仍检查。没有raw的库存不宣称模型生成。
若同类无前继、无run/采用/该身份候选的原v1/v4准备误记 origin，只有三个既有
来源Schema的hash可进入负结果：完整冻结政策集合必须精确匹配一个更晚的真实
接受主线Git快照，来源/模型/Harness/提示/词表等其他政策保持原origin字节。保留
原错误origin与policy_errors，匹配快照只用于验证库存，不能重新绑定生成身份。
其他政策差异或不存在完整接受快照仍失败。
无raw的纯准备可只读核验“zeroth”后保护caron前缀的原术语投影：原Git函数必须
匹配已知指纹，保护的组/重音字节正确，完整元数据仅有恰好一处原`ech cohomology
group`声明与现行词核范围差异。核验原范围并保留原元数据，不改变unit、词表或
现行候选术语要求；未知旧实现、其他元数据变化或已有raw/run/采用继续拒绝。

章节末尾与每个渲染安装边界先合并实际读取和快照声明，再一次读取依赖并核验原始
内容 hash；保留各自 root/HEAD、路径、模式、实现、来源与发行声明检查。渲染内部不
重复调用同一章节凭证的完整输入复核；安装前后仍分别检查，失败恢复旧输出。
