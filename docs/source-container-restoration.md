# 完整来源容器恢复与分组修订开发设计

规范任务：[Issue #603](https://github.com/dongyaotalk/stacks-project-zh/issues/603)。
本设计定义独立 Schema/工具合同，实现见 §9；对应工具 PR 验收合并后才允许另开
事实采用任务。现行 v1/v2/v3 及 `model-provenance.md` §9 不变。工具实现、具体数据修复和全库集成分别验收，
不以文档或来源库存生成成功代替原八项审查修复完成。

## 1. 问题与目标

全库抽取器已保存完整来源容器，统一队列覆盖239个batch/1480个当前单元。
现有恢复 helper 只支持单单元、无标题、仅含普通文字/内联数学的proof；现有
派生映射要求旧新ID一对一。它无法恢复拆分证明漏掉的整幅公式，也无法采用完整
定义来修正列表闭合位置或把旧长脚注摘要恢复为完整来源。

锁定英文为 `a04446e57ec1fbc252a871afcec7752fb2807b14`。当前187组/291个proof单元
中166组match、21组mismatch、0组unsupported；差异包含严格字节/引用前缀差异与
真实遗漏，须逐项看证据。002V/04AZ定义末段及002X结论的旧render把
`\end{enumerate}`放在末段之后，而锁定英文在末段之前闭合列表。新合同使这些
完整容器可恢复，不只为另一份简单证明增加例外。

目标是从统一库存选择完整语义范围，程序验证并生成新保护输入，保留所有旧输入、
生成身份和历史，再由实际模型完整重译。允许有依据的分段合并/拆分，不要求为了
保住旧错误的分段而复制、删减或重排英文。源文自身限制仍忠实保留为remark。

## 2. 完整容器与锁定Git证据

新增独立 `translation-data/source-container-restorations/<id>.json`，
不回写§9已有记录。每份不可变证据绑定下列内容：

| 内容 | 必须核验的事实 |
| --- | --- |
| 身份 | schema/tool版本、证据ID、派生ID、时间、完整source commit |
| 英文选择 | 章文件、真实owner Tag/label、Section parent、容器类型及明确proof index等语义selector |
| 原片段 | 锁定Git blob hash、UTF-8 byte span、原始片段及hash；容器原边界与保护结构 |
| 上一输入 | 完整上一batch unit/candidate原字节路径/hash、原Git提交、全部祖先来源及组内有序旧ID |
| 新来源 | 确定性提取/lowering版本、macro-policy hash、完整新unit、语义分段与组内有序新ID |
| 对应与诊断 | 旧新结构/节点差异、分段理由、永久坐标变化及所有未解决诊断 |

重新读取锁定Git章文件及tags，从真实章结构验证selector和容器边界，并重新提取
实际采用的容器。不能信任库存自报的ID、byte span、owner、READY、hash或旧
existing_unit_id；库存用于选择和准备，当前旧输入由本次完整快照独立绑定。
缓存篡改、失效或事实/政策在生成期间变化必须失败。

标题、正文、完整陈述及其列表、证明、脚注和字体组按自然语义边界处理；嵌套脚注、
命名标题及多段proof不能在中间截断。证明同时验证所属陈述和第几份proof，不能
跨owner借用同一句话或依赖当前错误ID。不存在、重复、不明确的selector以及正文、
数学、literal或参数中的伪标签不能授权来源采用。无真实Tag的范围须显式稳定映射，
不能用临时库存序号冒充事实ID。

每个新来源组的unit依次恢复为完整选定Git片段：每个源字节恰有一次覆盖，数学、
标签、引用、metadata、literal、空白及环境均有原字节依据；不做引用别名、数学
空白或公式归一化来取得相等。非译文间隔也须保存，不能在拼接时猜造空白。
独立审计保持其原比较口径和非零残项，不以定位成功豁免mismatch。

## 3. 保护提取、事实格式与阻断

采用通用Scanner的无损解析，并增加明确的IR→事实unit lowering。库存的完整
包装占位符不能绕过当前own-label、statement/proof链或renderer校验；事实格式
须显式保存正确的render开闭、命名标题和稳定语义ID，原TeX仍逐字回放一致。
书稿的章节/引用显示适配只发生在生成层，不把生成TeX当成英文来源。

只暴露自然语言，保护所有公式、控制序列、环境、标签、引用键、URL及literal。
脚注和命名参数的自然语言完整暴露，不能把旧摘要当成来源全文。原文中无独立Tag
的标题按已有稳定坐标规则处理，多proof按完整原序编号。

未知宏/环境、语法/归属歧义及未分类数学内文字仍阻断采用。数学内显式文字诊断
既包含自然语言，也包含操作符/标识符；需要独立可审查的分类/保护规则和回归，
不能把所有`\text{...}`一律锁定、翻译或忽略。改变宏政策时另开明确政策/工具任务；
本合同本身不批准新宏或词条。任何额外支持必须公开实际覆盖及残项。

Issue [#618](https://github.com/dongyaotalk/stacks-project-zh/issues/618) 在独立政策/工具
范围内实施 [source-extraction.md](source-extraction.md) 的数学记号精确分类合同。
只有显式字面量、命令和数学用法匹配的记号保持完整数学原字节；自然语言及未知
名称继续阻断。来源容器使用实际 Git 和该次政策重新分类，不能信任缓存的正向
分类、READY 或临时库存 ID。工具不直接采用事实；后续采用仍冻结完整旧 batch、
保存新的政策 hash 并要求实际模型完整五字段。已有证据按各自 origin 的政策重放，
v1/v2/v3/v4、source-container-v1 格式和历史记录保持不变。

## 4. v4旧新分组与完整历史

数学内自然语言的独立后续合同见
[math-text-translation.md](math-text-translation.md)。它定义 unit-v2 与新的
source-container-v3：完整原数学 region、所有锁定片段及精确分类文字 slot
分别验证，原 source 回放与译文 skeleton 同时通过。专门 Schema/工具验收
合并前，现有未分类文字阻断不变；旧 source-container-v1/v2、全部历史与
v4 分组规则不放宽。具体采用继续另开完整 batch/实际模型修订任务。

v4使用独立Schema分支及`unit_groups`，保留旧v1/v2/v3的映射/重放合同。
每组声明完整有序`input_unit_ids`、`output_unit_ids`、来源证据或未改变来源的
确定性依据、分段/坐标理由与历史身份锚点。旧组与新组内部可以多对多；不能用
重复的`unit_id_map`值假装满足旧bijection。

完整输入是最新整份batch，不是挑选的几行。每个旧ID与每个新ID各属唯一组，
所有输入/输出恰好覆盖；组次序和源次序一致。每个声明的完整来源容器没有重叠或
缺口，组间不能跨owner借文；不要求借此采用同章其他、未声明的英文容器。
来源恢复组同时覆盖完整旧wrapper链和完整新Git容器；未恢复组要求旧新source TeX
相等。单元数变化由完整原文及语义边界证明，不能把缺失内容或未完成单元移入
retired、空组或其他文件后从当前报告消失。全库ID冲突必须拒绝。

初次v4保留原始unit/candidate原字节与原run。上一版本已派生时，先按完整batch
保存且验证前一输出和归档清单，连接其精确唯一当前后继；已有v1/v2/v3/v4的记录、
快照和恢复证据均不得回写。祖先逐层重放，拒绝循环、孤立/重复输出、冲突后继、
假origin commit及重算hash后的历史篡改。每个旧候选的原生成和实际修订历史都
必须验证，不能只保留某个代表单元而丢掉其他来源。

旧新永久坐标/parent改变单独披露，新的own Tag和Section parent来自锁定章结构。
数据Issue提前声明完整旧/新列表、分组、源commit、目标batch、快照/归档/恢复/
run路径及chapter-template影响。具体写入仍遵守同章明确范围和单一writer；不借
通用合同开放未声明章、共同候选文件或任意共享政策。
新node kind及风险等级按真实来源种类和workflow基线生成；不能通过拆分或改名
降低结构/语言/数学审校要求。chapter-template和PR范围检查也必须识别新的分组
证据与完整旧/新坐标，不能只校验活跃候选而遗漏隐藏在组中的其他范围。

### 4.1 游离显示公式与完整证明链

002T 的旧 batch 把证明内部的显示公式保存到了 statement 与 proof 之间。完整来源
恢复必须把这条旧单元与完整旧 proof 链一起绑定，不能让它作为独立输出再次出现。
本补充由独立工具 Issue [#610](https://github.com/dongyaotalk/stacks-project-zh/issues/610)
实现，工具合并验收后另开具体数据任务；不改变来源提取/lowering 格式或 v1/v2/v3。

仅在选择真实完整 proof 时允许额外覆盖紧邻旧 proof 前/后的纯显示数学单元。
全部旧 ID 在整份 frozen batch 中连续、有序，完整旧 wrapper 链恰有一次覆盖；所属
statement、own Tag 和 proof index 仍由原包装及锁定 Git 验证。额外单元同章、同
历史 parent，仅有一个显示数学占位符，source text 除占位符外及 render 只能含空白。
该数学节点必须逐字等于完整目标 proof 的一个真实保护节点，在章内的数学节点库存
中唯一，完整章 Git 字节中也仅出现一次，且尚未出现在旧 proof 中；不得归一化数学
空白、靠旧 ID 自报 owner、从
comment/literal/其他陈述借公式或重复消费。含正文、包装、inline math、错序、
非相邻、跨范围、部分 proof、不同字节或不唯一节点均拒绝。

完整 proof 的恢复组必须包含这些相邻游离节点。把它们留在另一份未改变来源的
输出组、仅恢复旧 wrapper 链也会失败，避免独立数学单元与新 proof 重复显示公式。

恢复证据的完整 `input_unit_ids` 和 batch 快照显式保留这条游离单元及其原候选。
新输出仍为锁定 Git 完整 proof，全部数学只按原文在 proof 内出现；后续数据任务须
冻结完整新输入、由真实模型完整修订并重跑 QA/审计/编译。001Y 等既有不可变记录
逐字保留，不将这一分组修复用作审批或消除其他来源差异的依据。

## 5. 实际模型修订与审批绑定

每个新输出单元都要求一次实际新模型修订的全部五字段：translation、
allowed_english、term_occurrences、unknown_terms、notes。冻结完整新保护输入、
完整旧分组及其候选作为revision对象、提示词/风格/政策/词表、动态Harness与实际
模型身份；新run及完整原输出不可覆盖。程序只能提取、保护和装配，不能生成中文
或把旧文本经机械补字段后称为新模型输出。

新原输出使用明确的分组revision-input类型，保存全部旧unit/candidate，不能把
一个旧候选当作整个分组，也不能把它称为approved TM。每个新五字段与冻结输出
完全相等，占位符按新来源完整原序保留，所有数学术语逐次双语且未知术语待决。
缺少真实新run、少一条输出、只修中文遗漏公式或自行声明批准均失败。

活跃候选显式绑定分组和新修订。若保留历史模型字段作为兼容身份锚点，锚点必须
指向声明组的确切旧候选，并明确其仅是历史身份；完整来源图仍包含组内每个旧
run/model/candidate及其祖先。预览披露所有原生成和实际修订，不能只显示锚点模型
来表示当前文字作者。最终字段及Schema由独立工具任务落实并同步本文。

`candidate_provenance_hash`、selection/review/revision及正式来源绑定覆盖完整新
source、分组、恢复、全部旧/新run和祖先归档，不能只取代表单元或正文hash。
合并/拆分、来源或正文变化不继承旧批准；没有重新绑定的selection/人审不能用于
正式输出。模型、工具和bypass合并不授予critic、语言/数学审校、术语或出版批准。

## 6. 生成、采用与进度

工具默认只读事实/历史，输出ignored待审包，提供确定性check和完整诊断；不创建
Issue、run、事实恢复记录、审批或正式译文。输出拒绝越界、symlink、陌生目录及
无关文件，先完整临时生成再原子替换，失败保留上一包；check只读。

具体数据在工具验收合并后单独声明：冻结上一完整batch，复核全库重复和来源组，
生成真实模型修订、不可变证据及v4，重放后执行全部适用QA、独立源/证明/术语
审计、整书render/pdf和版面核对，再提交/PR。生成文件不提交，英文和lock不变。
数据合并后先另开进度任务，重新生成并检查chapter-template、progress和plan。
旧分段只作为历史证据保存，当前统计必须反映完整新事实及未处理范围。

## 7. 必须通过的独立回归与真实验收

| 类别 | 成功及拒绝案例 |
| --- | --- |
| 完整来源 | 普通/命名陈述、嵌套列表、display/xymatrix、注释、字体、长脚注及完整多段proof逐字回放；丢一字节、公式/环境/引用重排或增加均拒绝 |
| 分组 | 一对一、多旧→一新、一旧→多新及连续多组；遗漏/重复旧新ID、空组、错序、部分proof/列表、跨owner及全库冲突均拒绝 |
| 真正归属 | 多proof index、secondary own Tag与独立命名标题；重复短句、错误章/Tag/label、伪标签和不明确selector均拒绝 |
| 历史 | 原始输入、v1/v2/v3及后续v4祖先和单一当前后继；旧输入替换、改旧run/归档/证据、循环、孤立或冲突叶均拒绝 |
| 模型 | 完整真实新输出和全部旧组context；少字段/少单元、错source/context/run/model/harness、锚点替代完整来源或伪批准均拒绝 |
| 类型与范围 | 真实node kind/风险、全部旧新坐标和声明路径；把证明伪装为低风险段落、降低审校要求或把组外范围藏入证据均拒绝 |
| 审校绑定 | 完整分组来源hash正常；内容相同但来源不同、沿用旧selection/人审、待决术语自报CLEAR均拒绝 |
| 安全输出 | UTF-8 byte span、缓存/源/事实/政策变化、原子写入及失败回滚；越界/symlink/无关文件、部分替换和伪READY均拒绝 |
| 真实范围 | 保留239 batch/1480输入基线和全部21组proof残项；核对001Y/0024/002T等遗漏、002V/002X/04AZ列表边界、003O/02XJ长脚注，逐项记录采用前后而非一概豁免 |

独立synthetic fixture的期望Git片段、边界和拒绝原因不能由同一待测helper生成。
纯roundtrip只证明字节覆盖，必须另外核对语义解析、标题/脚注暴露和owner。实际
数据任务只有通过完整来源和新模型修订证据后才能报告该组修复完成；未处理诊断、
BLOCKED、来源差异和人审状态仍公开。

## 8. 实施顺序与完成边界

1. 本规范Issue/PR：写清完整设计并保持现有数据/权限不变。
2. 独立Schema/工具Issue/PR：实现完整容器证据、IR lowering、v4分组重放、历史/
模型/审批来源绑定、预览披露和安全准备/check；通过上述回归及真实只读验收。
3. 具体数据Issue/PR：从统一队列集中选择完整相邻范围，实际重译、恢复来源、
   保留历史，先本地全部门禁/编译，再推送/PR并核对精确HEAD的GitHub checks。
4. S4全部数据完成后执行S5强制来源/术语/证明集成、S6最终构建和S7进度/八项总验收。

数学内文字分类或未知宏支持也以专门政策/工具任务实施，不能藏在普通数据PR。
本规范PR仅完成第1步；八项审查目标、861个术语问题候选、76个坐标迁移、96条
source诊断及21组proof差异继续处理，计数按后续真实快照更新。

## 9. 工具实现与准备接口

工具任务：[Issue #605](https://github.com/dongyaotalk/stacks-project-zh/issues/605)，
分支 `tool/source-container-restoration`。本任务只实现工具，事实采用必须在其验收
合并后另开数据任务。v1/v2/v3 原 Schema、简单证明及历史门禁仍适用。

- 新来源证据使用 `source-container-restoration.schema.json`。selector 显式声明
  `file`、真实 `owner_tag`/完整 `owner_label`、`parent_tag`、`kind`、`ordinal`；proof
  的 ordinal 是真实第几份相邻证明。Tag/label 在锁定 tags 中必须唯一。
- 完整陈述和证明通常生成一个事实单元；命名陈述可在完整标题/正文边界生成两个。
  `OWNARGEND` 标记新恢复的外层命名标题边界，旧 `ENVARGEND` 仍保留原严格约束，
  嵌套参数不得借外层标题 token 冒充 own label。
- chapter title 保存实际 `title` 至下一语义节点之间的完整 header，必须有真实
  phantom label，注释/参数/literal 中的伪标签不提供归属。书稿投影才把 `title`
  换为 `chapter` 并去除章内 document frontmatter；实际 label/ref/eqref/pageref
  使用统一章前缀或未译永久 Tag 链接，包含数学与脚注中的引用。URL、cite key、
  注释、literal 和 metadata 不参与投影，来源和原始模型证据保持不变。
- 长正文使用 `prose_block` 的完整语义区间，按真实前后 Section、陈述或 proof 边界
  声明 `boundary_witness`，包含全部段落、列表、长脚注和原始非译文间隔。不能按字节
  裁一段脚注；旧分组也必须覆盖这两个真实边界间的所有当前单元。错误边界、部分旧
  单元或区间内未分类标签均阻断；标题/陈述/proof 不可借正文区间移走。
- v4 是独立 `oneOf` 分支，使用完整有序 `unit_groups`，不复用旧 bijection。
  每组保存 `group_id`、旧/新 ID、完整新 unit、历史身份锚点、来源恢复 ID、模型修订
  ID 和理由。每个新输出的原 context 使用 `candidate-group-to-revise`，冻结全部旧
  unit/candidate 与完整新 source，不能只保存锚点。
- 旧恢复证据的 macro policy 从其可达 `origin_commit` 的真实 Git 字节重放；后续
  政策任务不应改写旧证据或用今天的配置重新解释旧提取。当前准备同时冻结全部相关
  事实/历史/政策的 hash，生成期间的变化应失败。
- `make source-containers SOURCE_CONTAINER_PLAN=<plan>` 及对应 `-check` 接口只生成
  ignored 待审包。plan 声明完整旧 batch、派生 ID/时间和所有有序分组；包保存完整旧
  原字节、新提议单元、分组、恢复证据提议及 BLOCKED 诊断。它不创建实际模型 run、
  事实派生或审批；PREPARED 也不是翻译修复完成。
- 新坐标的 Issue `parent_tag`/`parent_tags` 仍声明真实来源 Section。旧错误 parent
  单列 `historical_parent_tags`，只允许出现在本次有效 v4 关联的完整 input 快照及
  直接前继输出归档，不能用于活跃事实、嵌套新 unit、selector 或陌生快照。
  PR 检查遍历全部旧/新 group ID、完整新 unit 和 selector，所有历史 ID 也须声明。

plan 的精确字段为 `derivation_id`、`created_at`、`units_file`、`candidates_file`、
`groups`；每组精确声明 `group_id`、有序 `input_unit_ids`、`identity_anchor`、
`selector`（或来源未变时 null）、`layout`（whole 或命名陈述 split-title）、`reason`。
所有旧单元按完整原序恰有一次覆盖。默认输出 `build/source-containers/` 中的
manifest、groups、restorations、diagnostics、units、input-units、input-candidates
和 report 八份文件；陌生目录、额外文件、旧包篡改和 symlink 均失败。CLI 支持
`--require-prepared`，存在 BLOCKED 时返回非零；生成包不代表授权采用。

独立 Git 试验已覆盖命名标题拆分、完整 display/list/comment、长脚注、分组合并及
旧模型来源披露。当前真实21组 proof 残项中，10组可准备完整来源，11组仍因未分类
数学内文字或未知命令阻断；它们仍全部计为原审计 mismatch。完整拒绝回归、真实
待审包、全门禁和整书/模板编译分别验收；不以工具成功代替 S4 数据修复。

### 9.1 完整引言段落的外围空白

Issue [#629](https://github.com/dongyaotalk/stacks-project-zh/issues/629) 为历史 render
添加外围换行的完整引言提供 `source-container-v2` 核验。旧 `source-container-v1`
记录继续使用原严格检查；v2 不扩大 proof、陈述、prose_block 或其他版本的权限。
只允许完整 `paragraph`，不能裁剪脚注或把数学证明当作普通段落。

完整旧 source TeX 与完整锁定 Git 段落只能在外围 ASCII 空格、tab、CR、LF 上
不同；移除这些外围空白后的 UTF-8 内容必须逐字相同。正文、数学、引用、命令、
内部空白及非 ASCII 字符全部保持。实际新 source TeX 仍须逐字等于未归一化的
完整 Git 原片段，原旧字节保存在完整 batch 快照中，trim 只用于历史证据比较。

真实 selector、Tag/label、Section parent、ordinal、完整 Git 边界和可准备状态
按原合同验证；同 owner/Section 的原字节核心必须唯一。真实英文中的最近语义
锚点须为该 Section 标题，冻结旧 batch 中最近原生锚点也须为具有真实标签的
同一 Section 标题，旧段落 parent 与 owner 同时相等。unit ID、自报 kind 或
陌生前导标签不能替代原生 Section 包装。缺失/错误标题、重复正文、跨范围、
未知语法、公式/引用/内部空白变化均拒绝；v1 仍拒绝外围空白不同的段落。

准备包生成 v2；加载不可变证据按其 tool version 核验，直接旧 helper 调用默认
维持严格规则。该工具只准备来源，不生成中文、run 或事实。DATA #628 须在工具
验收合并后改用完整段落 selector，重新准备/check、冻结上下文及实际模型修订。
