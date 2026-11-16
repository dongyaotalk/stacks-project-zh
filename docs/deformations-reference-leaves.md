# 数学文字内部引用两侧的纯文字叶

独立工具任务 [#1018](https://github.com/dongyaotalk/stacks-project-zh/issues/1018)
针对锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 中 defos 的六个完整
remark 容器：08LB、08LC、08LD、08MI、08MJ、08MK。完整 selector、永久 Tag、
Git blob/container hash、来源 UTF-8 范围及原式都保存在独立 fixture 中。
十个参数包含二十个纯自然语言叶；来源不会按任意局部 span 采用。

完整参数只允许 ` as in (\ref{equation-extension}) with ` 或
` as in (\ref{equation-extension-ringed-topoi}) with `。两侧 ` as in ` 和
` with ` 分别交给模型，中间括号、完整引用命令/键以及其余数学帧原字节保持。
有限帧角色必须由独立生产政策显式启用；本工具不登记生产 literal。
模型仍只接收提取后的受保护节点，不能读取完整原 TeX 作整文件翻译。

每叶独立绑定原父参数、叶序号、父/叶/分隔符/引用 UTF-8 范围和分类见证。
同一父参数严格按 [1,2] 各一次出现；源文本重放与译文 skeleton 检查保留
完整 token 顺序、次数、结构和参数外空白。改键、操作数、字体、括号、帧空白、
叶边界、序号、重排、重复、缺失、嵌套或截断均不能借用该权限。

## 来源、Schema 与首次生成

独立 unit-v5 使用 `schema/math-text-internal-references.schema.json`。
`source-adoption-input-v7` / `source-adoption-v7` 仅处理完整首次生成包，至少含
一个 v5 输出，其他输出只能是 v1/v2；不混入 v3 组件或 v4 前缀引用格式。
完整来源、邻近/引用上下文、任务 scope 原字节/hash、唯一 writer、实际模型
五字段及 model/Harness/turn/effort 和所有原始尝试仍必须冻结和验证。

政策集合为全部 REFERENCE_POLICIES 加新的独立 internal-reference Schema。
所有原字节必须来自实际 accepted origin，且其 unit/首次采用 Schema 明确允许
unit-v5 与 input-v7/v7、独立 Schema ID 正确。已有 unit-v4 英文引用上下文在
v7 内按其独立 references Schema 同时校验原冻结和当前输入，原对象不转换；
这不允许 v4 成为 v7 输出，也不改变旧 v1–v6 的 Schema 映射或来源权限。

v7 不接收 prior_attempts、prior_adoptions 或 shared_run_histories。实际原输出
的失败与重试继续全部保留，并按完整原冻结和有序 raw_attempts 验证。旧 run、
raw、freeze 和已接受事实不回写；未审校候选不能成为权威翻译记忆。

普通 assemble 的两个入口、旧 source-container 准备及历史回放、group-derivation
v4 和旧 v1–v6 首次采用入口明确拒绝 unit-v5。当前 provenance、来源定位、
章节关系、preflight、QA 与 renderer 只消费完整验证的首次 v7 来源凭证；不能
由新通用 unit Schema 或自报 adoption pointer 放宽旧历史/修订/恢复权限。
完整合同见 [首次来源采用](source-adoption.md)。

## 验证与采用边界

回归测试覆盖六个真实完整锁定容器、二十叶的来源重放与保护结构；独立 synthetic
Git 测试覆盖完整首次 v7 装配、溯源、渲染、preflight、原/current Schema、
accepted-origin 能力、写入回滚及旧入口拒绝。Synthetic raw/run 均明确不是实际
模型输出，不构成章节候选或审校证据。

具体生产政策和数据须在工具验收并合并后，由各自独立任务声明精确来源、
文件范围、冻结输入和实际完整模型运行。公共工具/Schema 变更需要适用回归、
实际 current-all、绑定的编译/最终完整日志及实际必需 CI；章节数据另做适用
最终 pdf-chapter。没有语言/数学审校、术语批准、选择或发布状态由工具通过、
候选合并或管理员 bypass 自动获得。
