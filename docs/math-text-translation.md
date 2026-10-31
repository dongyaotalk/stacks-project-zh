# 数学内自然语言的保护与翻译开发合同

完整来源没有旧候选时的独立首次采用及临时生成历史合同见
[source-adoption.md](source-adoption.md)（Issue #819）。经完整锁定Git、实际run/raw、
冻结上下文和来源不重叠重放的 `source-adoption-v1` 可采用 unit-v2/v3；普通
`assemble`/`assemble-many` 无包拒绝规则及下述既有v4历史合同保持。具体DATA须在
工具接受后另行冻结生成，首次采用不伪造旧候选或给予审校批准。

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

## 9. 集中修复的根层短语、条件前缀和箭头文字

Issue #808 / 草稿 PR #809 统一完成剩余修复；不再逐个数据批开 Issue/PR。
本扩展沿用 unit-v2 的完整原数学、pieces/slots、双重 hash、真实 Git 见证和
实际模型完整五字段合同，新增三种精确语法角色。旧三角色的权限保持。

| 角色 | 独立语法条件 | 精确登记的原参数 |
| --- | --- | --- |
| root-phrase | 完整数学的根层 text 参数，两侧有真实非 delimiter 节点；不在嵌套命令/脚本或 matrix 内 | `" in "`、`" and "`、`" composes to "`、`" gives "`、`"unit"`、`"counit"`、`"in "`、`" lying over "`、`" monomorphism"` |
| matrix-prefix-condition | 真实 matrix 内，text 参数紧随列分隔符，后接本列条件 | `"if "` |
| arrow-label-prefix | 真实 xrightarrow 必选参数内，纯 text 参数是首节点，其后仍有原数学节点 | `"restriction of "` |

双引号标出精确 ASCII 空格，不属于参数。不能 trim、推广其他空白/大小写或
忽略控制字。政策只有英文来源、命令、角色及真实 witness，不保存中文或批准。
实际 Git 核验锁定 a04446e57ec1fbc252a871afcec7752fb2807b14：002U、002Z、003D、
0036、0CXS、0CXY、03IF 等真实完整 Section/陈述分别提供见证。003E未采用定义中
的 gives 用于核验003D的完整后锚点，不新增003E事实。未知的嵌套文字/语法仍
BLOCKED；尤其带 TeX 空格的 `irred.\ comp. with` 尚不在本扩展内。

独立 math-text-regions 与 unit-v2 内嵌 Schema 同步登记新 role，unit-v1 和旧
region 数据不变。v13 prose 对应重组完整原英文 math 后才比较，原 slot/公式
字节不得消失或被 ASCII prose 空白归一。完整旧源、raw、run 和所有祖先保留。

独立 synthetic Git 测试覆盖全部新字面量、原空格、三语法角色、真实 witness、
完整region原字节回放、错误命令/角色/嵌套/注释/literal/变体拒绝、数学/slot
篡改及注入拒绝；另验证旧v1→新v2的v13完整package/check和origin loader历史
重放。synthetic 输出不冒称模型生成，真正DATA仍须冻结后实际生成五字段。

## 10. 完整参数内受保护 TeX 空格（unit-v3 开发合同）

Issue808的剩余完整02T5 proof中，两处bigcup下标参数为
`\text{ irred.\ comp. with }`。它是自然语言，不能登记数学记号，也不能放宽v2
的完整纯参数或plain_text。原unit-v1/v2、独立v2 regions Schema和历史语义保持。

新unit-v3使用独立math-text-components Schema；只登记上述精确完整参数和真实
indexed-component-description角色。父参数属于bigcup/nolimits的根下标组，前有
真实对象，后有dim条件；标签/proof/ordinal及全部源Git命令独立见证。将父参数
分成两个完整纯文字叶` irred.`、`comp. with `，中间原控制空格`\ `单独锁为
MATHSEG。每叶保存同一父参数原字节/UTF8范围、component序号和separator；完整
pieces按原序覆盖整个数学，无新增事实unit/候选、丢叶或重复消费。

Schema/QA分别重算：两叶恰好完整覆盖父参数、唯一separator和原边界，完整原
数学hash、typed skeleton、所有保护token顺序/次数及恢复后全部非文字字节。
译文只能改变两个纯叶值，原控制空格仍在原参数内。不能插入命令、改数学、
移动空格、把叶合并到参数外，或借嵌套/注释/literal/未知语法提供角色。

v3仍以完整新unit冻结全部上下文并由实际当前模型生成完整五字段，模型须真实
翻译全部叶并逐次双语报告待决术语，程序不补中文或猜术语批准。来源采用使用
独立source-container-v14，并按完整v4分组与全部原历史重放。ordinary assemble
继续拒绝typed输入，render仍要求活跃真实v4及来源证据。v14不能解释旧v13记录。
当前只是合同与工具开发，没有新DATA/raw/run或审校/术语/发布批准。

## 完整矩阵说明、数值限定同构及命名箭头

[Issue #820](https://github.com/dongyaotalk/stacks-project-zh/issues/820) 在已有
unit-v2完整纯文字参数合同中增加三个明确usage，不新增unit或历史格式：

- `matrix-row-text`：深度0、唯一matrix环境中的真实行首，前为matrix opening或
  行分隔，完整参数之后立即是行分隔或matrix closing。
- `matrix-row-prefix`：相同行首，完整文字参数后恰为完整 `\mathcal{C}` 形式的
  单个ASCII大写对象，随后即真实行尾。字体、分组、对象及行界原字节继续锁定。
- `numeric-isomorphism-suffix`：仅精确完整参数 `-isomorphism`，根层无环境，
  前面必须是真实 `\Big/2`，2紧邻text命令，后继必须为根层等号。

矩阵本身必须从完整数学起点或明确的关系/类型位置开始；不能借未知命令的
未分组参数提供matrix结构。嵌套、脚本、列内文字、未知环境/参数、注释和literal
中的伪边界仍拒绝。数字仅在新matrix说明role的纯英文参数中开放，以支持真实
`the 2-category of categories`；旧role的literal词法不变。前导连字符只为上述
精确数值同构后缀开放，译文完整叶也须保留该连字符。

已完整验证的数值slot在来源术语投影中暴露完整 `2-isomorphism`，由真实源声明
要求逐次双语覆盖；仅配对内部isomorphism不能覆盖完整限定术语。原2仍在锁定
MATHSEG中，unit.source_text、英文回放、全部数学字节及hash语义不变。程序不
拼接中文；生成模型负责完整参数和全部五字段。英文自身回放不要求中文双语。

同一工具另增加独立锁定notation usage `named-arrow`，只允许单独的text/can
登记。必须是完整单美元inline数学，开头直接为 `\text{can}`，完整形式为
`\text{can} : \mathcal{S} \to \mathcal{S}'`
形式：两个完整mathcal大写对象、可选目标prime、完整类型后立即数学结束。
普通can、其他字体/箭头、缺类型、脚本、未知参数或尾随运算仍阻断，不能与
symbol等usage混用。Mor继续使用原applied，不扩大其权限。

现有unit-v1及旧v2/v3记录解释不变；新纯叶也可与已有v3组件共存，组件边界及
separator合同保持。工具不登记生产字面量、修改config或采用译文。实际来源政策
须独立验收后才可用于DATA；首次来源仍使用已接受的source-adoption完整冻结/
模型原输出合同，不伪造旧v4祖先，不授予术语、critic、人审或发布批准。

开发先做synthetic边界回归及锁定Git完整来源探针，稳定后统一最终验收。
排版按当前用户规则仅检查实际lane编译和最终日志，不做截图或逐页视觉检查。

## 根层和矩阵行条件及带连字符短语（独立开发合同）

[Issue #840](https://github.com/dongyaotalk/stacks-project-zh/issues/840) 为完整纯文字
叶增加三个显式 usage，不改变旧 usage、unit-v1/v2/v3、组件或历史回放语义。
本工具不登记生产字面量；具体英文参数、精确空白及真实 Git witness 须在独立
政策任务接受后才可暴露，DATA 仍须重新冻结并由实际模型生成全部五字段。

- `root-condition`：完整数学的根层，真实数学对象末端之后的 text 参数，后面是
  真实逻辑关系及单字母/数字对象，或恰好完整数学的结束 delimiter。
- `matrix-row-condition`：深度0、唯一 matrix 环境的非空无列行中，数学对象之后
  的 text 参数，后面是逻辑关系及对象，或本行的分隔/closing。matrix 本身必须
  是原有明确根层说明位置，或完整 `left brace / left parenthesis / matrix /
  right parenthesis / middle bar / matrix / right brace` 集合条件结构的第二个
  matrix。该完整集合可直接位于根层，或紧随单个 ASCII 大写对象及根层等号；
  不能借其他表达式前缀、未知命令、其他包裹或嵌套环境构造条件矩阵。
- `root-hyphen-phrase`：根层两个相邻的单个 ASCII 大写对象之间，完整 text
  参数以单个 ASCII 连字符开始。对象必须紧邻命令两侧，参数只有已登记英文
  纯文字；源参数之外的每个字节仍锁定。译文的同一完整叶必须保留开头连字符。

新角色仅在完整 inline/display 数学 delimiter 内使用。对象末端限单字母/数字、
真实闭合分组/括号及 prime，逻辑关系限 Leftarrow、Rightarrow、Leftrightarrow。
为避免把未分组命令参数当根层文字，根层命令只接收明确的结构/关系、Spec/QCoh
操作记号、以及带显式花括号的 mathcal/mathbf/mathbb/mathrm/mathsf 对象。
其他命令、脚本 text、嵌套 text、伪环境、列中参数及不完整边界继续拒绝；现有
Scanner 的未知宏/环境门禁不能被这些 usage 绕过。

完整数学/typed skeleton 的双重核验、真实前后 witness、UTF-8 范围和数学非文字
原字节均保持。三个 usage 同步进入独立 regions、components 中的普通叶及 unit
内嵌 Schema；v3 组件分隔控制空格的权限没有变化。syntax 能力不等于政策授权，
不把自然文字登记成 notation，也不授予词条、critic、人审或发布批准。

## 第105章完整来源的英文登记

[Issue #842](https://github.com/dongyaotalk/stacks-project-zh/issues/842) 在已接受的
Issue840工具上，独立登记以下完整英文参数。双引号标示精确ASCII空格，不属于
参数；不trim、改大小写或推广其他字面量。来源均为锁定英文
`a04446e57ec1fbc252a871afcec7752fb2807b14`，完整Git见证、命令范围和hash保存在
[`stacks-introduction-math-policy-20261022.json`](evidence/stacks-introduction-math-policy-20261022.json)。

| 完整原参数 | 已接受usage | 真实见证 |
| --- | --- | --- |
| `" as above"` | root-phrase | 072M完整lemma |
| `" unit"`、`" arbitrary"` | matrix-row-condition | 072T完整proof |
| `" is smooth"` | root-condition | 072V完整Section |
| `" is quasi-compact"`、`" is irreducible"` | matrix-row-condition | 072V完整Section |
| `"-equivariant quasi-coherent modules on "` | root-hyphen-phrase | 072V完整Section |
| `" factors "` | root-phrase | 072V完整Section |

既有`Gal`记号只增加实际`applied`用法，保留`subscripted`及原有obsolete见证；
新增使用另有第105章真实Git数学节点见证。自然文字不登记成记号，所有slot外
数学字节、完整参数和旧usage权限保持。当前1090单元/9130完整数学节点的实际
影响扫描未发现新增自然文字分类或Gal-applied命中；旧unit/candidate/run/raw和
冻结政策不回写，历史仍按各自真实origin完整重放。

这只是英文来源政策，不生成或批准中文。完整来源库存和对齐在政策稳定后集中
重建并检查；工具和政策接受后，DATA另行冻结完整输入并由实际模型生成五字段。

## 位点章的独立上下文工具合同（Issue #847）

本工具扩展来自锁定英文的实际新位置，不修改现有 `root-phrase` 等角色的权限。
`sites` 的 section 00VC、00XF、proof 04IL 和 proof 00YV 中，下列完整参数不能借用
既有根层、独立文字列或特殊行首规则。每个参数以原大小写、全部空白和完整命令匹配；
其他数学节点和字节继续锁定。

| 新 usage | 有限语法范围 | 实际来源 |
| --- | --- | --- |
| `matrix-membership` | matrix 的态射类别归属：集合行中声明态射后接一个完整 `mathcal` 类别并紧接 `mid`；或单列集合描述中以 `forall` 开始的态射行，后接 `{}_V` 左指标的完整类别并结束该行 | section 00VC 的 equation/1；section 00XF 的 paragraph/2 |
| `aligned-set-connector` | `align*` 中真实集合条件的连接词，前有集合描述的 `mid`、两侧均有等式，不跨列或换行 | proof 04IL |
| `matrix-row-description` | 实际左右花括号包围的单列 matrix 行首完整文字，后有属于关系的数学对象描述 | section 00XF 的 paragraph/2 |
| `matrix-row-statement` | 同一单列集合 matrix 行首完整文字，后有数学等式陈述 | section 00XF 的 paragraph/2 |
| `matrix-operator-compatibility` | 同一单列集合 matrix 内，完整 `varphi` 后的文字与原算子列 `+,0,i` | proof 00YV |

这些角色只接受有限数学命令和真实完整边界。错误环境、额外列、脚本/命令参数中的
假位置、嵌套文字、未知宏、metadata、literal 和注释不能提供结构；同一公式的其他
未知文字仍阻断。它们不是一般的 matrix/align 文本解锁，也不修正原文。

原 `translatable_math_text` 继续拒绝重复字面量，原组件规则保持。新的可选
`translatable_math_text_contexts` 仅表达原根层 `" in "`、`" and "` 的独立新位置。
每个命名项精确包含 JSON 值 `base_rule`、`usage`、`source_label`、`witness_kind` 和
`witness_ordinal`；继承直接普通根规则的完整 `literal` 与 `command`，不能改写它们。
目前只允许 `" in "` → `matrix-membership`、`" and "` → `aligned-set-connector`。
基规则不能是组件、其他上下文或不存在的条目；重复权限、缺失/多余字段、错误见证、
循环及同一实际参数匹配多个角色均失败。新角色与原根层规则互不借用位置。

归一后的新项仍是原 unit-v2 的完整普通参数叶，有独立 `policy_entry`、真实 Git
见证和当前政策 hash；不新增 unit、组件、来源采用或历史版本。普通叶的枚举同步到
unit、独立 regions 和 components 内的普通叶；组件拆分语义、全部旧政策和历史回放
保持。只有独立工具验收合并后，后续政策任务才登记真实规则；DATA 再冻结完整来源、
邻近/引用英文和实际模型五字段。工具、只读英文探针及 READY 不授予译文或批准。
术语、critic、人工审校及发布仍各有门禁。

## 位点章完整自然参数政策（Issue #849）

以下登记使用 PR #848 已接受的有限角色，以锁定英文
`a04446e57ec1fbc252a871afcec7752fb2807b14` 的完整真实容器见证。引号中的空白
均属于参数；不能修剪、拆词或以近似文字匹配。所有见证 ordinal 均为 1。

| 精确完整参数 | usage | 真实 Tag / witness kind |
| --- | --- | --- |
| `"  and  "` | `root-phrase` | 00VB / section |
| `"collections "` | `matrix-row-description` | 00XF / section |
| `" we have "` | `matrix-row-statement` | 00XF / section |
| `" is compatible with "` | `matrix-operator-compatibility` | 00YV / proof |
| `"infinite set"` | `root-phrase` | 00X9 / section |
| `"for presheaves and"` | `quad-connector` | 00Y1 / proof |
| `"where"` | `quad-connector` | 0D5R / lemma |
| `" is a right inverse to "` | `root-phrase` | 04H0 / lemma |
| `"class of "` | `root-phrase` | 00Y6 / proof |
| `"or"` | `quad-connector` | 04I9 / section |
| `" and correspondingly "` | `root-phrase` | 00YP / proof |
| `" is sheaf theoretically empty"` | `root-phrase` | 04B8 / proof |
| `"versus"` | `quad-connector` | 0CMZ / section |

另有两个显式 `translatable_math_text_contexts`：原 `root-in` 的 `" in "`
在 section 00VC 以 `matrix-membership` 见证；原 `root-and` 的 `" and "`
在 proof 04IL 以 `aligned-set-connector` 见证。继承原 literal/command，保留
独立实际 anchor，不重写根层规则，不复制 literal 到原普通 registry，也不允许
上下文链或组件借用。00XF 的同角色归属仍须通过完整实际 matrix 语法核验。

每项在来源库存生成时从真实锁定 Git 验证 Tag、种类、ordinal、完整命令及结构，
其他数学节点/字节保持。政策改变后使用新政策 hash 的真实来源库存和对齐；
此前只读提案不冒充采用。当前 unit/candidate/raw/run/freeze 和历史不迁移。
具体候选在独立 DATA Issue 中冻结完整英文、邻近与引用上下文，再由实际模型
生成完整五字段。当前政策没有中文译名、术语批准、critic 或人工审校记录。

## 第8章04WV的有限矩阵描述工具合同

本地独立工具任务仅增加两个显式 usage，不登记生产政策或采用事实：

| usage | 可验证的位置 |
| --- | --- |
| `matrix-numeric-category-prefix` | 下述完整矩阵结构中，真实行首数字2后紧邻的完整 text 参数，参数保留单个前导 ASCII 连字符 |
| `matrix-category-description` | 同一完整结构中的六个自然说明参数：切片范畴说明前缀、有序对之后的行尾说明、对象行的三个文字参数及态射行的底范畴说明 |

验证器消费整个原数学节点，仅接受完整美元、圆括号或方括号数学 delimiter。
节点内恰为两个 `left brace / matrix / right brace`，中间为 `leftrightarrow`；
左矩阵恰有两行，右矩阵恰有三行，无列分隔。其有限语法为：

```text
左1：2 + 文字
左2：文字 + mathcal对象 / 单个大写对象
右1：2 + 文字 + (mathcal对象, 单个小写态射) + 文字
右2：文字 + mathcal对象 + 文字 + mathcal对象 + 文字
右3：单个小写态射 : mathcal对象 to mathcal对象 / 单个大写对象 + 文字 + mathcal对象
```

每个 mathcal 对象原字节须恰为 `\mathcal{C}` 形式的单个 ASCII 大写字母，
不归一花括号内空白；所有文字均为完整、非空、纯 text 参数。未知命令、其他
环境、额外前后表达式、脚本/命令参数包裹、嵌套参数、额外行列或不完整边界
不能提供位置。既有所有 usage 的权限保持，不开放一般矩阵文字。

实际锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 的
`stacks-lemma-localize-stacks`（04WV，parent04WT，lemma/1）提供八个参数：
`"-category of"`、`"stacks over "`、`"-category of pairs "`、`" consisting"`、
`"of a stack "`、`" over "`、`" and a morphism"`、`" of stacks over "`。
引号标示精确空格，不属于参数；这里只列工具见证，不构成政策授权。

`translatable_math_text_contexts` 另允许精确 `" over "` 从直接普通
`root-phrase` 基规则继承到 `matrix-category-description`。根层见证来自
0CKJ 的完整 lemma，矩阵见证须独立核验04WV完整 lemma。不能重复登记普通
literal、改写继承的 command/literal、引用上下文链或组件、重复权限或制造
同一实际参数的角色歧义。原 `" in "`、`" and "` 上下文权限保持。

新叶沿用 unit-v2；与既有组件共存时沿用 unit-v3。独立 regions、components
和两处内嵌 unit Schema 同步登记 usage，完整参数、UTF-8范围、原数学 hash、
typed skeleton、真实 witness、保护 token 顺序及原字节回放继续分别核验。
数字2保持锁定，术语投影暴露完整 `2-category`，两次出现分别计数；译文的数字
前缀叶仍须保留连字符。工具不生成中文，不批准术语或人审。

首次采用、旧batch恢复、冻结origin及全部历史重放仍走原合同，普通 assemble
不能直接采用 typed 输入。真实来源探针可以在内存中使用明确标记的未批准
实验政策证明两处完整容器的能力，但不能安装到 config 或称为事实采用。
工具接受后，另开集中政策任务登记这些完整参数和 Stacks/Eq/pr 的缺失用法，
再以新政策核验库存和预检；DATA冻结、实际模型及独立审校另行执行。

## 第8章完整英文参数与投影函数应用政策

本次只登记锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 的英文用法，
不改变有限矩阵语法、Schema、来源采用和历史合同，不包含中文译文或词条批准。

| 登记 | 精确命令/usage | 完整来源依据 |
| --- | --- | --- |
| `Stacks` | `textit/symbol` | 02ZG definition/1定义栈的2范畴；04W9 lemma/1、04WK lemma/1、04WS lemma/1与proof/1合计7处使用 |
| `Eq` | `text/applied` | 04WG proof/1明确指equalizer，3处实际函数应用 |
| `pr`新增用途 | `text/applied` | 04WI proof/1定义投影函子，12处实际应用，包含xymatrix内位置 |

`pr`原 `text/subscripted`、`text/superscripted` 及原定义标签
`categories-lemma-representable-diagonal` 保持；新增应用的独立见证为
`stacks-lemma-adjointness-pullback-pushforward` 的完整proof/1。
定义锚点与新增使用见证分别保留，不声称旧锚点提供本章所有新用法。
`sites-projection-pullback` 的 `starred-subscripted` context及其独立见证保持。

普通registry精确新增以下8个完整参数。引号只显示空格，不属于参数。

| 完整参数 | usage | witness |
| --- | --- | --- |
| `" over "` | root-phrase | 0CKJ lemma/1，parent042Y |
| `"-category of"` | matrix-numeric-category-prefix | 04WV lemma/1，parent04WT |
| `"stacks over "` | matrix-category-description | 同上 |
| `"-category of pairs "` | matrix-numeric-category-prefix | 同上 |
| `" consisting"` | matrix-category-description | 同上 |
| `"of a stack "` | matrix-category-description | 同上 |
| `" and a morphism"` | matrix-category-description | 同上 |
| `" of stacks over "` | matrix-category-description | 同上 |

唯一新增自然文字context `stacks-matrix-over` 直接继承 `stacks-root-over`，
以04WV完整lemma独立见证 `matrix-category-description`；不复制普通literal、
修改继承命令或引用context链。完整矩阵8个叶仍只在既有有限框架内暴露，两个
数字2及单前导连字符保持，两个完整 `2-category` 术语逐次可见。

### 尚未登记的裸pr：明确工具边界

04WI proof/1中 `\text{pr}` 的独立符号定义仍保持BLOCKED，不能借can的named-arrow
权限，也不能登记成可译自然语言。现有解析器先匹配主记号，再尝试独立context；
主规则添加通用 `symbol` 会抢先接受 `pr^*_i` 并改变其旧见证，还会使原拒绝的
`pr^*`、`pr^*_i(x)` 通过。登记该政策时pr context仅支持 `starred-subscripted`，不能在
政策内独立表达新增 `symbol/applied` context。因此本次只安全追加 `applied`，
保留裸pr阻断；独立工具任务处理前，不放宽解析器或以READY掩盖此缺口。

政策影响须沿全部现有unit的完整原数学及锁定Git库存重新扫描，包括章外命中。
旧unit/candidate/run/raw/freeze/history不回写，历史始终按各自origin政策重放。
新库存、来源对应与整章预检绑定实际新政策和新指纹，旧准备包保留；来源READY、
当前候选QA、contract support及人工审校分开报告，不把准备结果当作采用或批准。

## 完整投影函子声明的独立上下文工具（Issue #865）

本工具只扩展显式可选的 `locked_math_text_contexts`，生产宏政策保持原字节。
在工具验收合入及后续独立政策登记之前，04WI proof/1的裸pr仍为生产BLOCKED；
实验完整来源可lowering不表示已采用、已有中文或获得审校/术语/发布批准。

独立 usage `projection-declaration` 仅允许直接引用已有 `pr`，命令仅 `text`。
沿用上下文原四字段 `base_notation`、`commands`、`usages`、`source_label`，
均为JSON值；新usage必须单独列出，不能与其他usage混用，也不能与primary
pr的通用 `symbol` 并用。重复权限、额外/缺失/错误字段、借用其他基记号仍失败。
新usage不能写进primary registry；没有新项的所有旧政策保持原解释。

匹配消费完整单美元inline数学，唯一支持的有限类型声明为：

```tex
$\text{pr} : u^p\mathcal{T} \to \mathcal{T}$
```

必须从第一个美元后立即开始精确 `\text{pr}`，末尾mathcal对象后立即结束数学。
token序列、分组深度和环境全部核验；冒号、源对象 `u^p\mathcal{T}`、箭头
`\to` 及目标对象 `\mathcal{T}` 均完整匹配。只在pr与冒号、冒号与u、源对象与
箭头、箭头与目标对象四处允许零个或多个ASCII空格/tab/CR/LF，保留原字节。
对象/脚本、mathcal命令及参数内部不允许额外空白，字母u/p/T不泛化。

错误字体/大小写/参数空白、裸pr、脚本或应用形式、其他对象/箭头、缺类型、
尾随运算、未知前缀/参数、包裹/嵌套、注释、Unicode空白、literal及其他数学
delimiter/environment均不能提供这个角色。已被原规则接受的应用等形状继续
使用其原usage和见证，不获得声明权限；同一完整容器的未知邻居仍使其阻断。

primary匹配顺序及所有旧context保持，新项仅在原规则未匹配时检查。原
Categories定义标签、pr应用及Sites starred-subscripted见证不替换、不迁移。
接受项仍是完整锁定MATH节点，沿用分类记录结构；`usage_source` 保存pr完整
命令结束后至最后美元之前的完整声明后缀，`source_label` 来自新独立上下文。
无可译pr slot、不新增unit/region/来源/历史Schema版本，不改变旧origin重放。

真实见证从锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 的Stacks
04WI、parent04WA、`stacks-lemma-adjointness-pullback-pushforward` 完整proof/1
重选。该证明4348个UTF-8字节，SHA256为
`c85ef6d777e3e832c7e0a59395a962e16376708ad6d06fa7a34a683a7b7236ff`；
原文明确称其为投影函子，并在同一证明中另有12处已登记的pr应用。声明及
已有应用分别核验，不能以一个标签代替完整Git边界、语义和实际数学位置。

回归覆盖显式启用/缺省拒绝、完整有限边界、旧分类/负例、UTF-8完整来源及
Schema/lowering回放、与v2/v3 typed叶共存和重算hash后的数学篡改拒绝。
全库生产影响、实验新增命中及章外影响分别报告；生产预检、实验能力和DATA
采用严格分开。工具接受后另开真实政策登记，再准备新指纹及实际模型任务。

## 完整投影函子声明的生产政策（Issue #867）

工具 PR #866 接受合入后，本独立政策仅在既有
`locked_math_text_contexts` 节登记一项：

```yaml
  stacks-projection-declaration:
    base_notation: "pr"
    commands: ["text"]
    usages: ["projection-declaration"]
    source_label: "stacks-lemma-adjointness-pullback-pushforward"
```

它使用上一节的完整04WI proof/1见证及有限语法，整个声明仍为锁定MATH，
没有可译pr slot。primary pr的Categories标签、既有应用权限和Sites上下文
保持；未知邻居、其他对象/脚本/箭头或未登记形状继续阻断。不新增解析器或
Schema，不把新增政策绑定回写到既有unit/candidate/run/origin历史。

`tests/fixtures/macro-policy-before-projection-declaration.yml` 保存本次登记前的
完整政策原字节，用于证明无此登记仍阻断及历史primary行为；真实生产配置
另有精确正例。后续政策变更应单独审查兼容性，不改写这份历史fixture来消除失败。
新政策下的库存、来源对应及整章预检必须绑定实际输入；分支验收不代替合入后
新main的预检/check。来源READY仍不表示已采用、已生成中文、术语批准或人工审校。
