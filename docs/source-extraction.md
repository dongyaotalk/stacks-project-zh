# 全库来源抽取器

目标是一次扫描锁定英文库全部117章，集中准备来源及问题清单。现有1480个unit只代表已准备范围，不能成为全库覆盖基准。本工具不生成译文，不替换当前单元或批准术语；它提供可复查、确定性生成的来源暂存包，后续实际修订按来源匹配和问题清单执行。

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

全库库存生成后执行 `make source-alignment`，为当前239个batch/1480个unit准备统一对应及修订队列；更新事实后执行同一命令，`make source-alignment-check`检查是否过期。工具从锁定Git重新验证用到的章容器，再按真实永久Tag/proof链定位，合并terms/source/proof三个独立审计；现有分段不能按新库存序号覆盖。

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
| Arrows | text | applied | categories-lemma-limits-products-equalizers 的箭头集记号 |
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
