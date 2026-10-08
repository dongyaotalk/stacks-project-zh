# 数学内自然语言的保护与翻译开发合同

规范任务：[Issue #652](https://github.com/dongyaotalk/stacks-project-zh/issues/652)。
本合同定义后续独立 Schema/工具任务的接口；该实现验收合并前，现行数学
占位符、unit-v1、来源恢复版本及 BLOCKED 规则继续生效。规范合并不授权事实
采用，也不表示公式内文字已经修复。

## 1. 问题与分类

全库抽取器已一次保存完整来源与诊断，但整条 MATH token 中的自然语言仍
不可送入翻译输入。把连接词或描述当成数学记号会保留英文并隐藏问题；直接
解锁整条公式则允许改变数学。需要显式的文字叶节点与完整数学保护证据。

锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 中的独立见证为：

| 完整参数字面量 | 命令 | 真实归属 | 语法角色与原文依据 |
| --- | --- | --- | --- |
| `"and"` | text | categories，Section 04Z2 | equation-inertia-structure-map、equation-neutral-section、equation-functorial 中，两侧均为 quad 的连接词 |
| `"if"` | text | sheaves，陈述 009B，lemma-skyscraper-stalks | matrix 的独立条件文字列，两侧是实际列分隔符，后列为条件 |
| `"affine opens of "` | text | sets，陈述 000Q 的完整第一份 proof，lemma-bound-size | 集合描述中的自然语言，后接原数学对象；参数末尾 ASCII 空格属于原文 |

双引号表示精确字符串，不属于 TeX 参数。Tag、完整 label、proof ordinal 及
数学位置必须从实际锁定 Git 再验证，不能用库存序号或行号授权采用。这些
例子不授权所有同词、字体命令或使用场合。普通正文继续按现行规则暴露；
id、size、Cat、Fib 等明确记号沿用独立的精确记号分类合同。

首次工具实现以这三个字面量及其明确语法角色为验收目标。自然语言规则仅
登记英文来源、命令、角色、支持的语法形状及真实来源见证，不保存中文，
不批准 glossary。命令首次仅支持 text，后续支持须另开政策/工具任务。
大小写、参数全部字节及用法精确比较，不 trim、按词干猜测或推广空白变体。
一个参数不能同时是记号和可译文字；重复、冲突或不完整配置失败。

未列文字、角色不符、未知命令/环境、解析歧义、嵌套 TeX/数学、注释或非纯
文本参数继续阻断。comment、literal、命令参数中的伪见证不能提供分类依据。
connector 验证实际相邻数学 token；condition 验证真实 matrix 列边界；
description 验证真实集合描述位置。不能仅搜索片段中的相同词。

## 2. 完整数学 region 与文字 slot

后续工具新增 unit Schema 的独立版本 2，仅用于具有已分类数学文字 slot 的
单元。普通单元继续写版本 1，所有历史 v1 原字节及语义保留。不得给旧 MATH
改角色后绕过校验。一个 region 是原来的一个完整 inline/display/environment
数学节点，保存完整 delimiter、内容及结束边界。

slot 只覆盖一个 text 命令的完整纯文字参数；命令名、参数括号、外部空白及
所有其他数学字节均锁定。slot 属于完整 unit，没有独立事实 unit/candidate，
不重复消费来源。v2 在原 unit 字段外要求 `math_text_regions` 和
`source_math_skeleton_hash`；每个有序 region 至少绑定：

| 字段 | 要求 |
| --- | --- |
| region_id、delimiter_kind | unit 内稳定有序 ID 与真实数学边界类型 |
| source、source_hash、source_byte_span | 完整数学原字节/hash；跨度相对完整恢复的 source TeX，采用证据另保存章 Git byte span |
| pieces | 原序覆盖整个 region；非空锁定片段引用 MATHSEG_####，文字片段引用唯一 slot_id |
| slot_id、source、command、policy_entry | 完整参数原字节、真实命令与精确自然语言规则，不能自报合法 |
| slot_byte_span、boundary_placeholders | 参数 UTF-8 byte span，及其紧邻前后两个锁定 token |
| classification_witness | 语法角色、实际原命令/位置、见证 Tag/label/容器、政策 hash 与锁定来源依据 |

pieces 不允许零长度锁定片段、重复片段/slot、重叠、缺口或错序。完整 source
是可验证证据，不是额外可编辑的英文来源；载入时从 pieces 重建，再读取
锁定 Git 核验。所有 slot 必须是唯一命令参数，不能将操作数、标签、引用、
控制序列、环境或数学子式声明成文字。

source_text 仅暴露 slot 的英文纯文字，两侧均为唯一 MATHSEG token。相邻
slot 之间保留原关闭/开启包装，不能拼接后猜补括号。未分割的其他数学仍用
完整 MATH token。默认 restore 后，整个 unit 连同 render 包装逐字等于真实
Git 容器，不做数学空白、引用或环境归一化。

region/slot ID 用于稳定语义定位，不替代 unit_id、永久 Tag 或 owner；库存
inventory_id 与事实 ID 继续分离。采用仍声明完整旧新分组。具有 slot 的
输出风险至少 R3，不能拆成低风险段落以降低数学审校要求。

## 3. 双重数学保护与实际翻译

v1 的 hash 算法和保护校验保持。v2 的 source_math_hash 绑定按来源次序
排列的完整原数学节点，包含每个 slot 的原英文；不能只 hash 锁定碎片、
从数学清单删除分割 region 或按译文回写来源 hash。

额外 source_math_skeleton_hash 绑定完整有序数学表示：非文字节点保留全部
原字节，只有已验证自然参数替换为带 slot 身份、命令、角色及边界的 typed
leaf。结构 hash 同时绑定 token 序列、pieces、slot 与命令/位置。所有 hash
由实际源与政策重新计算，不信任记录自报的 hash 或分类。

候选先通过原保护 token 的数量、类型及原序校验，再从每对原边界 token
之间取出唯一 slot 译文。区间必须为非空纯文字，不含其他 token、TeX 命令、
数学 delimiter、控制字符或 `% $ \\ { } # _ & ^ ~ < >` 等 TeX/占位符语法。
Unicode 相似字符不能当作结构 delimiter；换行或注释不能隐藏保护节点。
slot 外仍执行全部现有自然语言/TeX 注入检查，v2 不能绕过原 QA。

恢复后译文数学的 region 原序、全部锁定字节、边界与 slot 身份必须相同，
typed skeleton 与来源完全一致。仅已验证自然文字叶值可变；公式其余节点、
环境、标签、引用及原字节不能改变。少操作数、换箭头、增删公式或改变 slot
边界均失败。完整原 source 回放与译文 skeleton 必须分别通过。

候选继续保存实际模型的完整五字段，不维护重复的译文 slot 表。连接词按
语义翻译，数学术语逐次采用 `中文（English）`；source-term projection 必须
看见所有 slot 的自然语言，不能在 MATHSEG 附近重新过滤术语。例如 affine
opens 的两次真实出现均须覆盖，词条仍待决。纯文本限制兼容已有双语标点，
不得手工清空 occurrences/allowed_english 掩盖遗漏。政策分类、自动 QA 和
bypass 均不授予词条、critic 或人工审校批准。

## 4. 来源恢复、历史与审批

新增 source-container-v3，只为上述 unit-v2 保存并重放完整 Git 容器及数学
文字证据；它不是派生 Schema 的版本 3。旧 source-container-v1/v2、派生
v1/v2/v3/v4 与简单 proof 合同保持原限制、原历史重放。

v3 按记录 origin 的真实政策字节重新定位、分类及 lowering，逐项比较新
unit、完整 region、pieces、slot 和 witness。不得用今天的政策解释旧证据、
改写旧记录/hash 或沿用过期 READY。paragraph 的外围 ASCII 空白比较仅沿用
v2 的完整归属及唯一核心条件；其他容器不新增豁免。新 source TeX 始终等于
未 trim 的完整 Git 片段，完整旧输入保留；旧 v1/v2 检查不变。

具体采用仍走 v4 完整 batch 恢复，冻结所有旧 unit/candidate 原字节、祖先、
分组及全部新保护输入。每个新输出要求新的实际模型完整五字段，与不可变
原输出精确相等；不能用程序替换旧英文 slot 或只补一条译文后称为整批完成。
动态 Harness、实际模型、全部 context 和原运行身份继续分别核验。

首次活跃 unit-v2 必须绑定通过验证的 v4 与 source-container-v3，不能从普通
装配或旧派生分支直接写入。新库存/准备绑定本次政策；活跃及历史来源证据
按各自 origin 的政策重放。政策变化使准备包/check 过期，不自动改写事实，
也不因新政策原文件 hash 改变而否认仍可验证的旧来源历史。

来源/修订/分组与审批 binding 覆盖全部 region/slot、完整 source、政策和
见证，不能只看正文 hash 或一个身份锚点。来源变化不继承 selection、critic、
语言/数学审校或正式 revision；历史 run、原输出与归档原字节保留。

renderer 只按已校验结构恢复 slot；完整数学内部不运行一般控制词分隔补丁，
不改公式以消除排版警告。原引用 namespace 等书稿投影在恢复后按原合同
执行，不碰文字 slot，不回写投影后的 TeX。双语排版、公式位置及长证明
在具体 DATA 中编译并作视觉验收。

## 5. 库存与独立验收

抽取器新增 source-extraction-v3，保留原五件产物；manifest 另统计自然
slot/region 与接受分类，record/segment 保存实际证据。纯数学中有自然 slot
时形成可译来源提议，明确记号仍 locked。READY 只表示可准备完整保护输入，
不代表已有译文已修复。旧 ignored 库存仅在文件集合、原版本 manifest/hash
及无 symlink 通过时安全再生成；check 只读并拒绝旧版本。

新格式须贯穿 IR、lowering、Schema/hash、records/QA、术语投影、来源/证明/
对齐审计、v4 分组/溯源/审批、模型输入及 renderer。审计从完整英文 region
恢复来源，原比较口径与全部 mismatch 保留；typed slot 不豁免来源差异。
未支持格式在所有入口失败，不能只在 renderer 接受。

| 独立回归 | 必须验证的结果 |
| --- | --- |
| 成功与语法 | 真实 connector、matrix condition、集合 description；多个 slot、inline/display、UTF-8 位置与全部原字节覆盖 |
| 拒绝分类 | 未列词/命令、空白/大小写变体、记号/自然冲突、嵌套参数、错误角色、comment/literal/伪 label、错误 Tag/owner/见证 |
| 数学保护 | 改/删/增数学字节，片段错序/重复/遗漏，假 slot/跨度、slot 跨边界；重算 hash 后篡改仍拒绝 |
| 译文与术语 | 空 slot、TeX/控制字符/token 注入、未经声明英文与术语漏次；双语术语成功且待决，不把数学名称改成译文 |
| 历史与审批 | 旧 unit/容器/政策原版本回放；新五字段与全部旧 batch/祖先；伪 run、缺 context、旧批准或单锚点替代来源均失败 |
| 输出安全 | 五文件集合、源/政策/事实变化、旧库存篡改、symlink/越界、临时生成与原子失败回滚；check 不写入 |
| 全库与采用 | 117 章有状态，116 Git blob 原字节回放，增量/残项公开；04Z2/000Q 完整预检不隐藏其他 blocker；事实/审计基线保持 |

synthetic 期望原文、边界和拒绝理由须独立编写，不能由待测 helper 同源生成。
结构检查能拒绝 slot 身份/边界交换；同一结构内两段合法纯文字是否译对
对应条件，仍需独立 critic 和人工数学审校，不能靠 skeleton hash 证明。

## 6. 实施顺序与完成边界

1. 本规范 PR：统一入口及开发设计，保留现行工具、政策、Schema 和事实。
2. 独立 Schema/政策/工具 Issue：先精确路径与计划，再实现全部入口；回归、
   全部候选、全库/check、完整容器预检、当前 lane render/pdf 本地通过后 PR；
   根审查远端完整内容与精确 HEAD 的两项 CI。
3. 工具合并后独立 DATA：声明完整旧/新 batch、owner/Tag、证据/模型路径，
   重新冻结并实际修订全部新输出，来源/术语/证明及 PDF 本地验收后 PR。
4. 每次 DATA 合并后先单独同步进度；S4 全部修复后执行 S5 和 S7 八项总验收。

本规范基线 main `677d63e258e04adbfffc5e2f7b209f2d8cfe8b00`：1,427 unique
unit、239 batch、193 个非空修复 batch，756 个术语问题候选/2,397 条诊断，
21 个坐标迁移、3 个错误陈述 Tag、26 条来源诊断、3 对未保护节点、12 组
proof mismatch。全库库存 43,257 提议单元（36,298 READY/6,959 BLOCKED），
不是同一范围的译文错误数。规范/工具成功不减少事实残项，不表示 critic、
人审、词表批准或出版；未知宏等后续事项仍各自处理。

## 7. 工具实施计划

实施任务：[Issue #654](https://github.com/dongyaotalk/stacks-project-zh/issues/654)，
分支 tool/protected-math-text；规范基线 main 000dbb7。先落实独立 math_text
模块与严格 registry，原 Git 见证核验后才开放 Scanner 的纯文字 slot；用
unit-v2/region Schema 与完整原数学/typed skeleton 校验贯穿所有入口。
完整容器 lowering 绑定重命名后的片段/slot 与实际 UTF-8 位置；只有含 slot
的来源证据使用 v3，其他新证据仍为 v2，历史 v1/v2 关闭新分类并按原语义重放。

库存 v3 保存原五件及正向分类/region/slot 计数，旧包升级验证全部文件 hash
与集合；提取/check 后顺序重建对齐/check。实际预检 04Z2/000Q 的完整容器，
所有当前事实、历史及来源/术语/proof 审计残项保持。实际候选首次 unit-v2
必须经过 v4 与 v3 来源证据；raw 修订仍冻结完整新 source/context，所有五字段
与不可变模型输出相等。旧派生分支、普通装配与审批不能跳过这些要求。

独立 synthetic Git 回归覆盖三个语法角色、多个 slot、原字节/数学保护、
术语、注入、假 witness/重算 hash、历史版本与安全输出。synthetic 记录不
表示真实模型生成。全量回归/239 QA/117 章与来源预检通过，当前 lane
render/pdf、模板及 synthetic 数学文字渲染验收后 PR；精确 HEAD 远端完整
内容/native 合同/两项 CI 后按已授权 bypass。具体 DATA 仍另开任务。

## 8. 工具本地验收记录

Issue #654 的实现新增独立 unit-v2、source-container-v3 和
source-extraction-v3。普通装配拒绝 unit-v2，首次活跃采用要求完整 v4、v3
来源及实际修订 context；raw 修订和无候选 unit 不能进入渲染。v1 Schema
分支与原 Schema 相同，原 hash 算法和历史容器政策回放保留。工具不生成中文。

锁定 Git 的三处政策见证合计七次；按精确参数及对应语法规则扫描全库后，
识别 710 个 slot（and 554、if 154、affine opens of 2），619 个完整 region，
分布在 533 个提议 unit。见证不是这 533 个 unit 的采用坐标；各自真实归属
和完整容器仍分别验证。已知 slot 不豁免同一 unit 的其他诊断：312 个提议
READY、221 个仍 BLOCKED。全库 117 章、116 个 Git 文件逐字回放；43,257
个提议 unit 为 36,610 READY / 6,647 BLOCKED，保留 18,781 条诊断。

本地最终验收：419 项测试（原 379 项加 40 项数学文字回归）、239 batch QA、
117 章模板与 progress/plan check、workflow/harvest/upstream-index/Schema/
provenance/decision 均通过。extract-all/check、source-alignment/check 顺序通过；
全部 533 个新格式提议另行检查 Schema/region，04Z2 的完整 prose_block 和
000Q 的陈述/完整 proof 通过旧分组及原字节预检。源/政策/事实在安装前变化、
坏库存、symlink 和原子安装失败均拒绝并保留原包。

当前 lane render/pdf 与 template 零退出，461 页最终日志通过，整书全文
layout 文本与基线相同；独立 synthetic v4/v3 渲染的三种数学文字经 XeLaTeX
编译及 PNG 目视检查，无裁切、重叠或缺字。synthetic 内容不是实际模型输出。
1,056 个事实/配置文件及来源、术语、proof 三份审计报告原字节保持；756 个
术语问题候选、12 组 proof mismatch 等事实残项未减少。远端内容、native
合同和精确 HEAD 两项 CI 仍须在 PR 中分别验证，DATA 采用仍另开任务。
