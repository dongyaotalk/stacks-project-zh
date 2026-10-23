# 全库来源抽取器

目标是一次扫描锁定英文库全部117章，集中准备来源及问题清单。工具首次开发时已有的1480个unit只代表当时已准备范围，不能成为全库覆盖基准。本工具不生成译文，不替换当前单元或批准术语；它提供可复查、确定性生成的来源暂存包，后续实际修订按来源匹配和问题清单执行。

## 类别构造记号的独立工具合同

工具任务 [Issue #721](https://github.com/dongyaotalk/stacks-project-zh/issues/721)
增加显式 `category-constructor` 用法。本工具任务不增加实际宏政策条目、不采用
事实；后续政策任务必须独立验证锁定原文定义及完整使用见证，接受后另开 DATA。

只有精确字面量 `Ind-`、`Pro-` 可以声明该用法，命令必须仅为 `text`，usage
必须仅为 `category-constructor`。条目还必须声明 JSON 字符串 `suffix`，值仅允许
一个完整的 `\mathcal{C}` 形原子，其中字母是单个 ASCII 大写字母。运行时比较
该条目声明的完整后继原字节；声明 C 不会放行 D、无花括号的 mathcal C、
QCoh、D 的导出范畴记号、参数空白/嵌套或相似词形。缺失、多余、重复字段、
混用 usage、其他命令及其他带连字符字面量均失败。

前置词法上下文必须是普通数学位置或包含完整构造的数学下标/上标花括号组。
文本、字体和未知命令参数、未闭合组以及借用组外后继的单 token 脚本仍阻断。
已有 `prefixed-symbol` 用法继续拒绝脚本参数，解释历史政策时不会启用新构造。
这里只识别已显式声明的数学记号；`and`、`if` 等自然语言仍遵守独立 typed-text
合同，未知语法和未分类数学文字保留 BLOCKED。

正向记录保留完整 text 命令、notation、command、usage、source_label 和原 UTF-8
位置；`usage_source` 保存完整 suffix 及其前的原空白、注释。完整 MATH 节点
与所有数学字节保持，既不生成译文，也不批准术语或人审。工具的来源回归见证为
锁定 `a04446e57ec1fbc252a871afcec7752fb2807b14` 的 Categories Section 05PT，
完整 remark 05PW/05PX/0G2X 共7处，以及 Duality Section 0G4Z 的完整 remark
0G53 中相同 Pro-mathcal C 用法3处。不同后继的 Pro-D、Pro-QCoh 仍需独立合同。

## 命令与产物

`make extract-all` 默认输出 `source-ir/extraction/`；`make extract-all CHAPTER=categories` 可做选章验收。`make extract-all-check` 对同一锁定Git、宏政策和当前unit索引重新生成并比较所有产物。CLI `extract-all --root . --harvest ../stacks-project --output source-ir/extraction [--chapter ...] [--check] [--require-ready]`。

输出manifest.json、units.jsonl、segments.jsonl、diagnostics.jsonl和report.md。所有章均在manifest有明确状态；无独立TeX的生成index为SOURCE_UNAVAILABLE。每个source block有chapter、parent/owner永久Tag、语义路径、原Git字节位置/行号和片段hash。提议unit保存在record.unit中，使用已有unit字段与保护占位符；inventory_id与事实unit_id分开。只有唯一且source TeX/owner均相符的历史匹配才报告existing_unit_id；不能靠行号或标题猜测采用。

## 扫描与覆盖

不展开/执行宏。递归识别所有数学delimiter、数学environment、注释、转义字符、配对分组、命令参数、结构environment、标题、字体组、链接可译参数、脚注、列表和多段证明。保护结构及数学原字节；脚注自然语言与命名标题显式暴露。保留section与自身陈述Tag及完整proof所有权，labels从锁定tags/tags解析。顶层段落和标题分别输出；陈述、列表和证明保留完整容器，内部脚注、字体及命名标题的自然语言显式暴露。无法安全解析的构造保留完整片段且BLOCKED。

特殊索引记录、数学中的显式文字、未知命令/环境及无明确归属等进入统一diagnostics，保留原文和位置，不能借成功生成包宣称可翻译。editorial metadata和literal按当前macro-policy锁定，保留独立segment。分段输出覆盖所有源字节，非译文结构也分类保存；重新拼接每个unit默认restore后的片段与locked segments，逐字等于原Git blob。roundtrip证明字节没丢，不能单独证明语义解析无误；BLOCKED仍需解决。

## 写入、检查与采用

产物仅写入本仓库ignored source-ir/build。先完整生成到临时目录并核对覆盖/hash；以完整目录替换，失败保留旧包。默认exit0表示完整库存生成与roundtrip通过，打印READY/BLOCKED数量；`--require-ready` 在任何blocker或缺章时非零。`--check`不写文件并拒绝所有过期/缺失/多余内容。

本工具不修改translation-data、任何旧run、原输出、English harvest、source lock、宏政策或来源恢复合同；不会把unapproved结果作为TM。来源恢复采用仍需独立证据、显式历史映射及真实模型修订，不能通过复制包绕过保护。全库提取可一次完成；模型生成按上下文容量分组，来源与问题统一准备，减少重复预处理。

## 验收

Synthetic fixtures覆盖公式转义/注释、嵌套字体和脚注、标题与自身标签、列表嵌套、多份分段proof、数学environment、metadata/literal、unknown macro、缺章、所有权匹配、UTF-8字节跨度、原子输出安全、确定性check及CLI。真实锁定库117章完整报告，116个可读文件全部回放逐字相等；READY/BLOCKED与来源问题量公开，不冒称现有译文通过。工具回归和当前候选整书/模板build按仓库规则执行。

## 首次全库结果

锁定 `a04446e57ec1fbc252a871afcec7752fb2807b14`，117章均有明确结果；116个独立章源全部逐字回放一致，自动生成index没有独立TeX。库存43,270个提议单元：34,985个READY、8,285个BLOCKED。

24,189条诊断分为：数学内显式文字24,068条、归属待映射72条、未知命令46条、未知环境2条、无独立源文件1条。数学文字包含函数/对象名称和自然语言，须先分类，不能把诊断总数当作译文错误数。现有事实单元与新完整容器的分段和包装不同，只有1个满足完全相同来源和owner的唯一引用；旧译文不能按库存序号直接覆盖，后续需显式来源范围/历史映射。

完整包约129MB，生成和全库确定性复核两次扫描在本机合计约115秒（同时进行工具门禁）。来源库存支持统一准备和查错；模型修订仍按上下文容量及完整语义范围分组。

## 当前译文集中修订

全库库存生成后执行 `make source-alignment`，最初为239个batch/1480个unit准备统一对应及修订队列，后续按当前事实重建；更新事实后执行同一命令，`make source-alignment-check`检查是否过期。工具从锁定Git重新验证用到的章容器，再按真实永久Tag/proof链定位，合并terms/source/proof三个独立审计；现有分段不能按新库存序号覆盖。

报告在`build/source-alignment/report.md`，逐批任务在`repair-queue.jsonl`。队列保存当前unit/candidate和审计政策hash，来源byte span、提案和差异；排版/已核实引用别名相同仍只作定位证据，不豁免来源恢复或实际模型修订。完整设计见[source-alignment.md](source-alignment.md)。

## 数学内记号分类（v2）

独立政策/工具任务：[Issue #618](https://github.com/dongyaotalk/stacks-project-zh/issues/618)。
先实现本合同，验收合并后另开具体数据采用任务。数学内自然语言仍需后续独立的
翻译/数学保护合同；本次仅识别明确记号，不修改公式或生成译文。不得将全部
`\text`、`\textit`、`\textbf` 参数统一锁定或翻译。

宏政策的 `locked_math_text_notations` 显式列出精确字面量、允许命令、使用类别和
锁定来源依据。字面量按原字节、大小写和完整参数比较，不 trim、词干匹配或推断
别名。缺字段、重复字段/条目、不支持的命令/类别和非标识符条目均拒绝。未配置
该节的历史政策保持全部数学文字阻断的原语义。

| 字面量 | 命令 | 允许用法 | 锁定原文依据 |
| --- | --- | --- | --- |
| pr | text | subscripted | categories-lemma-representable-diagonal 的投影记号 |
| id | text | symbol | categories-definition-category 的恒等态射记号 |
| Arrows | text | applied、symbol | categories-lemma-limits-products-equalizers 的箭头集记号；Section0013 五元组中的独立符号 |
| Ob | text | symbol | categories-section-definition-categories（0013）五元组的对象集记号 |
| Ab | textit | applied、symbol | categories-remark-big-categories（0015）阿贝尔群范畴及其层范畴记号 |
| Groups | textit | symbol | 同一完整 remark0015 的群范畴记号 |
| Mod | text | subscripted | 同一完整 remark0015 的 R-模范畴记号 |
| Top | textit | symbol | 同一完整 remark0015 的拓扑空间范畴记号 |
| PAb | textit | applied | 同一完整 remark0015 的阿贝尔群预层范畴记号 |
| Aut | text | subscripted | Section0013 中 definition0017 之后完整段落的自同构群记号 |
| PSh | textit | applied | categories-definition-presheaf（02X6／Section001L）明确登记的预层范畴记号 |
| Sets | text、textit | symbol | categories-remark-big-categories 的集合范畴记号 |
| size | text | applied | sets-section-categories-schemes 的 size(S) 定义 |
| Cov | text | applied | sets-section-coverings-site 的覆盖类记号 |
| Supp | text | applied | sets-lemma-coverings-site 的支撑集合记号 |
| cf | text | applied | sets-section-cofinality 的余终性记号 |

`applied` 要求完整参数之后的真实数学 token 是 `(`，可带明确的 left/big 系列
括号大小命令；`subscripted` 要求其后是非空下标；`symbol` 仅用于表中已明确的
独立符号。注释/空白可以跨过但保存原字节；不匹配用法、相似词形、嵌套参数、
未列命令及 `and`、`if`、`affine opens of` 等自然语言仍为原 math-text BLOCKED。
识别既不会改变完整 MATH token，也不会授予词表或人类数学审校批准。

`PSh` 的完整锁定来源见证为英文提交
`a04446e57ec1fbc252a871afcec7752fb2807b14` 中 categories 的 definition 02X6，
真实 Section001L、label `categories-definition-presheaf`、definition/1。完整原片段
SHA-256 为 `889d705564c0b0d46f3a1313e8bbb2276d53c39dba22d3f7d0591683c9a18ac4`，
原文明确写出预层范畴记号 `\textit{PSh}(\mathcal{C})`。只登记精确 `PSh`、
`textit` 和已有 `applied` 形状；无括号、下标、其他字体命令、大小写或参数
空白变体均不由本条放行。历史政策原字节解释不变，普通正文中的 PSh 仍作为
自然语言暴露。独立政策只改善来源准备状态，不修改任何候选/run/raw，具体
DATA 仍须完整来源与旧组冻结和实际模型五字段。数学内自然连接词 `" and "`
不属于 PSh 记号条目，未支持的语法角色仍 BLOCKED。

Definitions 记号的独立政策任务为 [Issue #778](https://github.com/dongyaotalk/stacks-project-zh/issues/778)。
在同一锁定英文提交中，完整来源均属真实 Section0013
（`categories-section-definition-categories`），其 Git 容器见证为：

| 完整语义 selector | 完整原片段 SHA-256 | 记号原字样 |
| --- | --- | --- |
| owner0013、paragraph/2 | `4bc52ac2b785e320fc653001d06bf6f2462cc468fb5b6eb020252c11066c02c4` | `$(\text{Ob}, \text{Arrows}, s, t, \circ)$` |
| owner0015、`categories-remark-big-categories`、remark/1 | `67f8624c8987b067e029d9e39dbd82ed79a8ad52a2cde1960a9e566b5c45b7fe` | `\textit{Ab}`、`\textit{Groups}`、`\text{Mod}_R`、`\textit{Top}`、`\textit{PAb}(X)`、`\textit{Ab}(X)` |
| owner0013、paragraph/3 | `d580537d8c54ae721e787754f200795d7df265e4af11d45c22570ba950850ee1` | `$\text{Aut}_\mathcal{A}(x)$` |

`Ob`、`Aut` 使用真实 Section 标签作为政策见证；`Arrows` 保留已有 applied
来源标签并追加上述独立符号见证。`Ab` 先核对 applied，再核对明确常量 symbol；
`Mod`、`Aut` 必须跟非空下标，`PAb` 必须跟真实括号。大小写、命令、完整参数
原字节严格比较；不允许的词形、参数空白、嵌套文本、普通连接词及未知记号继续
BLOCKED，普通正文的这些字样仍可翻译。政策既不扩展解析算法，也不批准中文术语。
完整数学字节保持，库存重新生成时 typed 数学文字见证的政策 hash 随真实政策
更新，但事实和历史使用其原有冻结政策，不改写原 unit/run/raw。READY 变化仅表示
来源准备；具体 DATA 必须另开任务，冻结全部旧组、新容器和上下文，再实际生成五字段。

每个接受项保存 `math_text_classifications`：完整命令 source、notation、command、
usage、source_label、原 UTF-8 byte/line location 以及 usage_source（原下标或函数
括号前缀）。记录随提议 unit 保存；只有记号且没有自然语言的完整数学片段仍为
locked segment，分类记录随 segment 保存。manifest/report 统计两处的正向记录，
不以删除诊断代替可审查证据。未分类文字继续保留原诊断及位置；全部源字节照常
回放，不改变保护结构、事实 unit 或任一历史记录。

库存版本为 source-extraction-v2，文件集合仍为原五件。允许具有原五文件、完整
原 manifest/hash 且无 symlink 的 v1 ignored 库存安全再生成；其他版本、陌生目录
或额外文件拒绝。check 只读并拒绝旧库存、分类记录/政策/内容篡改；安全失败保留
上一目录。库存临时 ID 可能因纯数学片段回归 locked segment 而改变，不得据此
改写事实 ID。具体模型修订仍走完整旧 batch 快照和锁定 Git 容器的独立 v4 合同。

验收覆盖接受/拒绝用法、精确词形、字体命令、嵌套文本、注释/转义、完整数学
字节和 UTF-8 位置、纯数学 segment、v1 政策/库存迁移、分类记录篡改及实际容器。
再次扫描全部 117 章并逐字回放 116 份 Git blob，公开分类与剩余 BLOCKED 数量；
当前事实及 source/proof/term 审计残项不得减少，数据修复留待后续独立任务。

### 后续自然语言保护合同

[math-text-translation.md](math-text-translation.md) 定义数学文字的后续 unit-v2、
完整 region/typed slot、双重数学保护和 source-extraction-v3 开发合同。
与记号分类分开：只开放经实际语法及锁定 Git 见证核验的纯文字参数，其余
数学字节完整锁定。现行工具、政策及 math-text BLOCKED 仍生效；须先由独立
Schema/工具 PR 验收合并，再由完整 batch 的实际模型修订任务采用。

### Cat 与 Fib 的明确记号来源

[Issue #642](https://github.com/dongyaotalk/stacks-project-zh/issues/642) 先定义此
补充，再修改政策与回归。完整 02XG 与 02XJ 容器的预检发现 `\textit{Cat}`
和 `\textit{Fib}` 是未分类数学标识符。锁定 Git 的真实 Section 003D
（`categories-section-formal-cat-cat`）以 Ob(Cat) 表示范畴的类并讨论形式
2-范畴结构；真实定义 02XP（`categories-definition-fibred-categories-over-C`）
以 Mor 的 Fib/C 下标记号表示纤维范畴间 1-态射的范畴。

沿用既有精确分类合同，仅增加 Cat、Fib 两个字面量，命令仅 textit，用法为
symbol，source_label 分别指向上述真实锚点。完整原数学、命令/位置及正向
分类证据保持；大小写、完整参数和字体命令不能推断别名。正文里的相同词仍
作为自然语言暴露，旧政策仍阻断这两个名字。and、if、affine opens of 等
数学内自然语言和其他未知名字继续阻断，不借常量分类开放一般文本翻译。

真实 Fib 定义标签以大写 C 结束。记号证据标签的词法校验必须保留原 ASCII
大小写，不能伪造不存在的小写别名；本任务先扩展声明范围，再允许 label
部分的 ASCII 大写字母，仍拒绝路径、空白、非 ASCII 或空 label。该词法
支持不替代真实锁定 Tag 与原文上下文的独立核对。

全库重建/check 公开两项分类增量并回放 116 份 Git；独立实际 Git 预检完整
02XG/02XJ 范围，04Z2 的 and 保持阻断。所有事实及术语/来源/证明残项保持，
匹配变化逐项核对并披露；当前书稿编译及文本保持通过后工具 PR。具体 DATA
后续重新冻结新政策输入，所有历史容器仍按原 origin 政策核验，不回写原输出。

### 独立 size、Cov 下标及群作用范畴后缀

[Issue #676](https://github.com/dongyaotalk/stacks-project-zh/issues/676) 先补充此合同，
再实现政策与独立回归。真实 Section 000H 定义 size(S)，引理000J又把独立的
`\text{size}` 明确列作记号；Section 000W定义Cov(C)，引理000X及其证明使用
`\text{Cov}_0`。size保留applied优先并新增symbol，Cov保留applied优先并新增
subscripted，原已接受用法的分类、source_label和原数学字节保持。

Section000T以 `G\textit{-Sets}` 和带下标的形式命名群作用集合范畴，000U沿用。
新增通用prefixed-symbol用法，只增加非identifier字面量 `-Sets`，命令仅textit、
prefix为G。该用法独有prefix字段，必须是一个ASCII大写数学字母；字段集合精确，
用法只能是prefixed-symbol，不能夹带symbol来跳过前缀。其他非identifier、错误
大小写、词形、字体命令或未声明前缀保持阻断；普通规则禁止prefix字段。

前缀须为实际紧邻命令的裸数学token；中间仅允许原空白/comment。拒绝连写标识符、
转义、comment/literal/文字参数中的假前缀、未知命令的参数及嵌套文字。按源语法
解析真实token及分组，不以任意末尾字符匹配来提供依据；不推断其他群名。接受项
仍保存完整命令与原UTF-8位置，usage_source保存前缀及中间原字节，整条数学不变。
扫描器不执行TeX宏；仅显式列出的零参数数学算子、箭头及间距命令可引入裸前缀。
普通数学分组可用，命令参数、脚标参数及literal内容不可用；未知命令后即使空格或
连续参数也不授权，未支持的语法继续阻断。
已明确的单参数数学字体命令在完整参数结束后恢复数学范围；未知宏不按相同
规则猜测参数个数，其后的箭头命令也不能越过未知参数边界。
旧政策没有该条目时仍阻断；不扩展自然文字slot或授予glossary/数学审校批准。

工具范围保持全部事实与历史原字节。完整000U/000X旧批次共22单元，只读准备和
check四个完整来源提议；000X证明沿用已有and typed-slot。000J陈述可lower后，
其旧混合parent仍需另一个来源边界合同，不能宣称全batch已准备或隐藏proof差异。
全库/check与116 Git文件逐字回放、分类/READY/BLOCKED增量、全部匹配变化公开；
来源/术语/proof审计及186修复batch等事实残项保持。全量回归、239 QA、进度/计划
和当前lane render/pdf通过后工具PR；具体DATA另开任务并重新冻结全部来源/上下文。
准备接口要求政策字节等于真实已提交origin：先核验四个源容器及旧组并完成本地
检查/编译，再用本地工具提交冻结政策，执行多批prepare/check后才push及开PR。
不伪造origin或放宽准备门禁。

### 显式分组的强调声明

独立工具 [Issue #688](https://github.com/dongyaotalk/stacks-project-zh/issues/688)
先定义本合同，再修改政策、代码和目录。categories 0032 的完整 proof 使用
`{\em finitely generated}` 命名概念；真实归属为 Section002Z。仅当政策明确登记
em 的 `preserve_scoped_declaration_translate_children`，且它是完整显式花括号组
的首个非空白命令时，扫描器保存开组和声明原字节为 EMPHOPEN、闭组为 EMPHCLOSE，
递归暴露组内自然语言。嵌套数学、字体、脚注、引用、comment 与空白继续无损保护；
不执行宏，也不把强调文字分类为数学记号。分组内声明前的原空白保持。

未分组 em、相似命令、缺少 em 声明的旧政策和未知语法继续 BLOCKED；bf/it 的
既有语义不变。术语投影只识别完整匹配的真实 em 字体包装，支持开组后原空白；
控制序列、公式、伪包装和语义节点不能提供词汇声明。定义/命名语境及逐次术语
要求仍适用，不授予 glossary 或人审批准。

回归覆盖完整嵌套容器/Unicode/空白回放、旧政策与未分组拒绝、相似命令和伪包装、
新概念声明及逐次覆盖。实际全库重新生成/check，公开只由 em 引起的保护/状态/
诊断与匹配变化，116份 Git blob 全回放；全部现有事实、术语候选/来源/proof 残项
保持。三个旧来源词汇锚点先迁到0032完整proof，合同见 source-term-inventory。
当前 lane render/pdf 和整书 layout 保持后创建工具提交，再以真实提交政策只读
prepare/check 完整15旧→2新；不生成事实、run 或中文。工具合并后具体 DATA 重新
冻结输入并实际修订，来源恢复、历史及人审规则保持。

## 精确 Ind-/Pro- 构造的独立政策采用

前置工具 [PR #722](https://github.com/dongyaotalk/stacks-project-zh/pull/722) 接受后，
独立政策只声明两条 `Ind-`/`Pro-`，命令仅text、usage仅category-constructor，
suffix均为完整 `\mathcal{C}`，source_label分别绑定Categories的
remark-ind-category和remark-pro-category。原文在真实Section05PT下定义这两个
范畴；完整remark 05PW/05PX/0G2X使用3/3/1处，同一记号在Duality真实Section
0G4Z下完整remark 0G53使用3处，并显式引用Categories相应讨论。所有源容器
与十处命令、完整后继、owner/Section/selector、原Git字节独立核验。

这里只改变来源准备分类。全部提案source TeX与116个源blob保持原字节相等；
现有译文、全部历史输入/run/raw/恢复证据及词表不变。其余Pro-D、Pro-QCoh等
未声明后继与未知语法/数学自然语言继续BLOCKED，不归一或借宽泛symbol用法
放行，不授予术语或人工数学批准。后续实际DATA必须重新冻结新上下文和完整
旧新分组/候选/历史，由当前模型实际生成完整五字段；不能复制暂存包当译文。

### 集中修复中的精确数学记号见证（Issue #808）

全量预检在当前问题来源中发现以下明确函数/对象记号；新增分类只保留数学
原字节，不生成中文、不批准术语。阶段2的23项完整锁定Git容器原片段/hash、实际命令
和用法曾独立核验，合计113个不同真实出现；该记录是阶段2检查点。来源准备变化
不代表活跃译文修复。旧版本来源按origin政策重放，不改旧证据或run。

| 精确参数 | 命令 | 使用形状 | 锁定 Git 真实 label |
| --- | --- | --- | --- |
| Equalizer | text | applied | categories-lemma-almost-directed-commutes-equalizers |
| Fun | text | applied | categories-section-formal-cat-cat |
| GL | text | subscripted | guide-section-papers |
| Br | text | applied | guide-section-papers |
| Quot | text | applied | guide-section-papers |
| Bun | textit | subscripted | desirables-section-examples-stacks |
| length | text | subscripted | obsolete-lemma-not-domain |
| ord | text | subscripted | obsolete-lemma-not-domain |
| div | text | applied | obsolete-lemma-bound-primes |
| depth | text | subscripted | obsolete-lemma-kill-local |
| cd | text | applied | obsolete-lemma-algebraize-local-cohomology-bis-bis |
| Coh | textit | applied | obsolete-lemma-fully-faithful-simple-one |
| Gr | text | subscripted | obsolete-lemma-get-morphism-general |
| cosk | text | subscripted | obsolete-lemma-cosk-hom-deltak |
| sk | text | subscripted | obsolete-lemma-cosk-hom-deltak |
| Vect | text/subscripted、textit/applied精确配对 | contexts | obsolete-lemma-bondal-van-den-bergh |
| Lift | text/applied、textit/applied、textit/subscripted精确配对 | contexts | obsolete-section-modules |
| Bad | text | applied | obsolete-lemma-blowing-up-intersections |
| Good | text | applied | obsolete-lemma-blowing-up-intersections |
| Gal | text | subscripted | obsolete-theorem-equivalence-sheaves-point |
| Inf | text | subscripted | obsolete-lemma-tangent-and-inf |
| End | text | subscripted | obsolete-lemma-tangent-and-inf |
| Der | text | subscripted | obsolete-lemma-tangent-and-inf |

只匹配完整精确参数和表中语法；错误命令、大小写和角色仍拒绝。普通正文
Equalizer/functor等仍暴露为自然语言。unit/counit、in/and、composes to、lying over、
restriction of、monomorphism和irred. comp. with不作为记号登记；Ext/Tor上标、
Hilb/Hom分段拼字在阶段2时仍BLOCKED；阶段6的明确扩展见下文。其他未支持用法继续在
同一集中Issue/PR中进行，不用宽泛symbol规则掩盖未知文字。

### 集中阶段5/6：真实层级与额外记号用法

source-extraction-v4仅在显式hierarchical_prose模式跟踪实际Section/subsection/
subsubsection层级：正文owner为最近有真实永久Tag的祖先，parent保持实际Section。
同级新标题清理同级及更深旧owner，未标同级不借用前同级Tag。无真实根Section仍
阻断。原v1–v12来源恢复按旧模式独立重放；新v13使用真实层级，不改历史含义。
全部片段仍逐字回放完整源blob。尾部input{chapters}/bibliography/bibliographystyle
只按真实连续基础设施段处理，后续自然文字仍阻断。版权literal是完整锁定元数据，
内部伪label/标题不提供来源锚点，不执行任何源命令。

阶段6再登记Groupoids(textit symbol)、Map(text applied)、Ext(text superscripted)、
Tor(text superscripted/subscripted)，及精确mathcal{H}+text{ilb|om}的sheaf-symbol-suffix。
后者必须在真实根数学位置并后接实际应用或非空脚本，未知宏/脚本参数不可借前缀。
Br支持primed-applied，Coh支持下标及独立对象，Lift/div支持下标，Aut支持应用，
Quot/sk/cosk/ord支持独立符号。-Sets的新用法只允许真实根层箭头目标G的显式后缀，
左操作数必须已闭合，不以一般symbol豁免。原数学全部保持。

新增notation配对已从锁定Git实际命令节点独立核验：43项有效配对全部有来源。
Vect/Lift的可选contexts是精确command/usage字符串集合，成员须唯一、合法并覆盖
所列commands/usages；未列组合拒绝。没有contexts的原政策语义保持。当前registry
50项，新增29项；不是50个已批准术语，也不是实际译文修复数。

FDL前言中的center明确作为可译body，copyright/large声明locked_arguments:[]；
扫描器只锁零参数命令原字节，后续文字继续暴露。未知环境/宏仍拒绝，不执行TeX。
该支持与完整phantom章头/body边界的v13证据一同核验，不能仅因单个命令可保护就
绕过真实owner、完整旧组、原生两边界或历史绑定。

当前集中工具完整重建/check结果：117章、116 Git原字节回放、43223提议，
READY38422/BLOCKED4801、12491诊断；声明notation10822处，自然数学region756、
slot874。v4分段始终完整回放；已分类且无可译正文的整条数学可进入锁定段，
提议unit数相对旧缓存减少不能解释成删除源字节或采用译文。全活跃事实数学
探针未分类0、待真实typed迁移11节点；完整Git来源支持不代表中文已经修复。

## 位点章记号上下文的独立工具合同（Issue #847）

当前锁定英文的 sites section 00VL 使用独立的 `$\text{pr}^*_i$`；section 00VZ、
04D4 在真实 `Mor` 类别下标和 `xymatrix` 对象格中使用 `G\textit{-Sets}`，并明确
使用 `H\textit{-Sets}`。这些位置不能借现有裸 G 前缀或一般 `symbol` 放行。
本工具不登记实际宏政策，后续独立政策必须提供完整锁定 Git 见证。

新增可选 `locked_math_text_contexts`；每个命名项的全部字段均为 JSON 值，必须有
`base_notation`、`commands`、`usages`、`source_label`。基记号只能直接引用原已登记
的 `pr` 或 `-Sets`，不能引用另一个上下文或发明普通文字记号。`pr` 只允许 `text`
与 `starred-subscripted`；`-Sets` 只允许 `textit`，还须有显式 `prefix` G 或 H，
用法限于原 `prefixed-symbol` 或以下两个新上下文。不能用新项重复旧的裸 G 权限，
重复权限、字段、条目/节、错误命令、字体、前缀、来源 label 及不支持的基记号失败。

- `starred-subscripted` 仅接受一个完整 inline 数学原子 `\text{pr}^*_i` 的裸星、
  下划线和单个 ASCII 字母/数字指标；没有应用尾部、分组星号或未知宏参数权限。
- `morphism-category-prefixed-symbol` 要求完整的 `\Mor_{G\textit{-Sets}}(...)` 或
  显式 H 变体；后缀是该单独类别下标的直接文字节点，不能借其他构造、额外前缀、
  未完成的下标或未知命令参数。有限前置算子支持不改变旧前缀扫描权限。
- `diagram-category-prefixed-symbol` 只识别根层 `\xymatrix` 的直接 G 对象格：真实列
  分隔符后为显式前缀及完整后缀，随后是带非空 l/r/u/d 路由的真实 `\ar`；脚本、
  嵌套组、伪图、metadata/literal/注释及未知箭头命令不能提供该位置。

主 registry 的字段、原使用顺序和全部旧权限保持，优先采用已有效的原规则；只在
原规则不匹配时检查显式新上下文。没有新节的历史政策不获得新权限。新项不改变
`math_text_classifications` 记录结构：仍保存原命令、usage、实际相邻原字节和
source_label，完整 MATH 原字节保持；不会生成中文或批准数学术语。

数学内 `in`、`and`、集合描述和相容条件遵守独立
[自然文字上下文合同](math-text-translation.md)，不会登记为记号。工具接受前继续
BLOCKED；具体政策与实际 DATA 分别另行声明、冻结和验收。
