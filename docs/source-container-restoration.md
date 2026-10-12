# 完整来源容器恢复与分组修订开发设计

规范任务：[Issue #603](https://github.com/dongyaotalk/stacks-project-zh/issues/603)。
本设计定义独立 Schema/工具合同，实现见 §9；对应工具 PR 验收合并后才允许另开
事实采用任务。现行 v1/v2/v3 及 `model-provenance.md` §9 不变。工具实现、具体数据修复和全库集成分别验收，
不以文档或来源库存生成成功代替原八项审查修复完成。

## 独立历史边界核验合同（2026-10-10）

剩余 sets-000J 完整陈述含独立永久 Tag 的列表子项；0AHL/04VA 的完整引言
使用历史错误 parent/owner，且英文普通换行已折叠。不得为准备这些范围关闭
同章、完整链或来源归属检查。本工具先实现以下独立 `source-container-v4`
证据；事实采用在工具验收合并后另开 DATA Issue/PR，全部旧输入及历史保持。

普通来源准备仍输出原 v2/v3。只有实际使用本合同核验的组输出 v4，并必须含
`legacy_boundary_witness`。验证器从证据 origin 的宏政策、锁定 English Git
及完整旧 batch 独立重算 witness，逐项相等；不得信任缓存、历史 ID/parent
或调用者提供的白名单。旧 source-container-v1/v2/v3 继续原检查。

- 完整陈述中的跨历史 parent 仅允许 `list_item` 自有标签等于其 parent，且
  prefix 是真实 item 与紧邻标签。完整旧主包装连续、有序、闭合，同章同来源；
  原生完整陈述的主标签和全部列表子标签与旧链逐项同 Tag、同顺序。标签必须
  位于真实列表结构中；数学、注释、literal、嵌套参数中的伪标签无效。核验相邻
  proof 时也验证整份 frozen batch 中这一完整所属陈述。witness 保存完整旧
  陈述 ID、历史 parent、原生 selector/fragment hash 和子标签序列。
- 完整 paragraph 可以由紧邻的完整 labelled statement 建立归属：旧段落和
  旧陈述链同章、同历史 parent、同锁定来源；Git 完整段落之后也紧邻同一真实
  陈述，间隔只能是 ASCII 排版空白。段落自然文字的普通 ASCII 空格、tab、CR、LF
  可折叠作历史对应证据；其数学、命令、引用、保护片段和非 ASCII 字符精确不变。
  内部空段、typed 数学文字及解析诊断不在此扩展中，继续阻断。整个章内该
  对应必须唯一，不能截取段落、删除脚注或借另一陈述的引言。witness 保存完整
  旧段落及相邻旧陈述 ID、历史 parent、真实陈述 selector/hash 和段落签名。

v4 可消费现行 unit-v1/v2 lowering；数学内文字仍仅按原 v3 的明确 typed slot
合同处理，边界扩展本身不暴露新数学文字或批准宏。每个新输出的 source TeX
仍逐字等于未经归一化的完整 Git 片段。完整旧 batch 快照、不可变 ancestry、
完整分组、全部新实际模型五字段、审校及出版门禁保持。

验收覆盖两类真实边界、旧版本拒绝、新 witness 篡改、未知/重复/伪标签、错误
owner/Section、跨章/来源/任意 parent、部分/乱序链、重复/切片/更改段落以及
分组重放。只读生成三个真实完整 batch 包及确定性 check；库存、审计和事实
保持当前残项，完整回归/239 QA/117 模板/Schema/溯源/决策/进度计划与当前
lane render/pdf 本地成功后才提交。八项总修复和 S4/S5/S7 不因工具完成而结束。

同一独立工具 Issue #695 在修改目录前声明唯一 transfinite-induction 来源证据
迁移到真实000J完整 proof；细节见 [source-term-inventory.md](source-term-inventory.md)。
这仅消除后续 DATA 的证据依赖，所有词形/范围/诊断和翻译事实保持，不批准术语。

## 1. 问题与目标

### 不同历史 parent 的完整段落双锚点（source-container-v10）

独立工具 [Issue #780](https://github.com/dongyaotalk/stacks-project-zh/issues/780)
处理真实完整 `categories-0015`：段落 `tag:0014:p002` 沿用前定义0014的历史
parent，同批完整后继 remark0015 的十九个旧单元沿用0015。现行 v4 同历史
parent 检查和 v5 同批前陈述检查继续拒绝这个范围。新增 v10 来源证据分支，
派生仍 v4；旧 v1–v9 的 Schema、默认权限、政策和历史重放保持。

完整 frozen batch 必须保留全部旧 unit/candidate 原字节。只接受一个完整
unit-v1 paragraph，ID 为 `tag:<历史parent>:pNNN`，原 prefix 为纯 ASCII 空白
和 `\noindent`、suffix 仅 ASCII 空白；不接受切片、多个旧段落、额外包装或
typed 数学文字。它必须紧邻同批完整、有序、连续、真实闭合的后继陈述链；
后继全部成员的历史 parent 恰等于该陈述 own Tag，并与段落的历史 parent 不同。
后继完整文本、列表及保护节点须逐项匹配完整锁定原文，不能仅比较首尾包装。

锁定 Git 中，完整前陈述 own Tag 恰等于段落历史 parent，完整后陈述 own Tag
恰等于后继历史 parent。前陈述、完整段落、后陈述都在同一真实 Section；段落
owner 等于 Section，库存位置立即相邻，两个原字节间隔仅 ASCII 排版空白。
前锚点直接重扫锁定 Git，不借另一 batch 的输入。错误历史 parent、错误真实
Section、注释/数学/其他内容间隔、未知或不唯一锚点继续 BLOCKED。

完整段落签名沿用 `paragraph_signature`，并须在整章唯一；完整后陈述沿用
`_complete_statement_signature`，另核验所有真实列表标签顺序。只比较普通
prose 的 ASCII 排版空白及已锁定永久 Tag label 映射；数学、引用、命令、结构、
非 ASCII 字节、内部空段和 typed 数学文字不获新的归一化权限。新来源逐字等于
未经归一化的完整原 Git 片段。

`paragraph_anchor` 保存旧段落 ID、两个历史 parents、完整有序后继旧 ID、真实
前后 selectors 和完整片段 hashes、完整后陈述 signature hash、完整段落
signature hash。Schema 使用独立 v10 分支；加载器仅对 v10 开启该见证，并从
实际 origin Git 宏政策、锁定英文、完整旧快照逐项重算，不信任缓存或自报 hash。
篡改、降级为旧版本或同 parent 冒充本见证均拒绝。

真实只读验收为完整0015二十旧→二完整新 prepare/check；事实、不可变 run/raw、
完整历史和修复队列保持。另开26项英文词目录来源见证任务后，才独立认领真实
Section0013六批完整 DATA，冻结全部旧组、候选、ancestry、政策/context 并实际
生成每个新单元完整五字段。工具接受不减少当前128问题批，也不完成S4/S5/S7。

### 一个完整来源段落的多个旧分段见证（source-container-v8）

独立工具 Issue [#762](https://github.com/dongyaotalk/stacks-project-zh/issues/762)
处理真实001M的两个旧paragraph：它们共同组成Section001L、
`categories-section-opposite`的完整paragraph/1。既有单段落合同拒绝该组，
不能只采用其中一段或修改旧证据。新增v8来源证据分支，派生仍v4；旧v1–v7的
Schema分支、默认权限及历史重放保持，普通单段落继续使用原版本。

必须冻结完整旧batch。至少两个不同旧paragraph组成连续、有序、完整的最大
paragraph组，紧邻完整plain labelled statement之后；不跨旧章、来源或历史
parent。第一段prefix只能是ASCII空白及真实`\noindent`，其余prefix及全部
suffix仅ASCII空白；内部空段、额外包装、切片、重复、缺段及乱序均拒绝。
直接拼接每个完整旧source TeX原字节，不插入分隔符、trim或临时合成unit。

锁定Git的完整前陈述和完整paragraph也须立即相邻，间隔仅ASCII空白；它们
必须在同一真实Section，paragraph owner等于Section。完整旧前陈述与原生
陈述签名逐项相等：普通ASCII prose排版空白可折叠，label只按已锁定的永久
Tag映射比较，其数学、命令、引用、结构及非ASCII原字节均保持。前陈述缺项、
内容变化、伪标签、非plain closing或另一陈述不得提供归属。

全部旧段落拼接后的`paragraph_signature`必须逐项等于完整Git paragraph，
并在锁定整章唯一。该签名只折叠普通ASCII prose排版空白，数学及其他保护
节点原字节保持；未知语法、内部空段和typed数学文字继续BLOCKED。新unit的
source TeX逐字等于未经归一化的完整Git片段，本合同不暴露新数学文字或登记
记号，不替代原数学保护门禁。

`paragraph_anchor`保存完整有序`paragraph_input_unit_ids`、历史parent、完整
前陈述旧ID、真实selector、原片段hash、完整前陈述signature hash及完整段落
signature hash。Schema使用仓库现有子集，数组唯一性由Schema检查，至少
两个和最大完整组由独立重算检查；不加入未实现的Schema关键字。只有v8加载
器开启多旧段落权限，并从origin真实Git宏政策、锁定英文及完整旧batch重算
全部字段；v5/v7降级、单值旧段落字段、调用者自报hash和篡改均拒绝。

真实只读验收为完整001M三旧→二新prepare/check。当前及历史候选/run/raw、
英文锁、词表批准和审计队列保持；工具不生成中文、实际模型run或事实。具体
DATA在工具验收合并后独立认领真实001L剩六个完整当前batch，273词的完整
小节剩余范围明确说明偏好范围例外，不为凑词数新增当前没有的paragraph。
完整旧新组/context/ancestry冻结、每个新unit实际模型完整五字段、immutable
raw、人审及出版门禁保持；不以工具准备完成宣告S4/S5/S7或F1–F8完成。

### Section 标题后的完整首段见证（source-container-v7）

独立工具 Issue [#749](https://github.com/dongyaotalk/stacks-project-zh/issues/749)
处理 DATA748 的真实 002D 引言边界。旧完整 batch 只有标题和首段；不能借另一
batch 的陈述充当后锚点，也不能放宽完整 prose_block 的双锚点规则。新增 v7
来源证据分支，派生仍 v4；旧 v1–v6 Schema 分支、边界权限及不可变历史保持。

仅一个完整旧 paragraph 可以使用本见证。它在完整旧 batch 中必须紧邻一个
完整 section_title，两者同章、同来源、同历史 parent；标题 own Tag 必须等于
真实 Section。旧标题只能有普通 section opening 和单一 own label closing，
包装间隔仅 ASCII 空白。从锁定 Git 独立选择同 Section 的 section_title/1 与
paragraph/1，原生库存也须立即相邻，间隔仅 ASCII 空白。

完整标题正文和保护字节逐字相等，外围 ASCII 空白不参与比较。own label 的
唯一例外是锁定 tags/tags 已登记的章前缀映射：旧名字必须精确等于 selector
的 owner_label，原生名字只能是同名或精确去除当前 chapter 前缀的局部名字，
两者实际映射同一永久 Tag。真实002D旧 categories-section-limits 与原生
section-limits 已核验；不猜其他别名，不归一化标题文字、公式或其他命令。

完整段落沿用 paragraph_signature：仅折叠普通 ASCII prose 排版空白，其数学、
命令、引用、字体、评论和非 ASCII 原字节保持；整章签名唯一。内部空段、未知
语法、typed 数学文字、切片、重复、跨来源或非相邻范围继续 BLOCKED。
paragraph_anchor 保存旧段落 ID、历史 parent、完整旧标题 ID、真实标题 selector
及 fragment hash、完整段落 signature hash。加载器只对 v7 开启首段权限，并从
origin 宏政策、锁定 Git 和完整旧快照独立重算全部见证，不能信任缓存或自报 hash。

真实只读验收采用完整 categories-002D 两旧→两新，不生成中文或新 run，不采用
事实，不减少修复队列。工具验收合并后更新 DATA748 基线和 paragraph/1 合同，
保留十二批48旧→22新完整范围，再重新 prepare/check、冻结并实际生成五字段。
全部历史、实际模型/raw/context、人审及出版门禁不变；S4/S5/S7 仍分别完成。

### 列表陈述后的完整段落见证（source-container-v6）

独立工具 Issue [#741](https://github.com/dongyaotalk/stacks-project-zh/issues/741)
处理 DATA740 准备时实际发现的 002C 边界：旧完整定义跨三个 unit，最后 suffix
同时闭合 enumerate 与 definition，旧 v5 的 plain closing 合同仍拒绝它。
v6 是独立来源证据分支，派生仍 v4；旧 v1–v5 Schema、默认权限、边界函数及历史
不改。只有真实需要列表末端闭合的见证使用 v6，普通陈述后的段落仍使用 v5。

必须冻结完整旧 batch；前陈述链完整、有序、连续、同章同来源及同历史 parent。
首 prefix 只能是真实 statement opening 与 own label；最后 suffix 只能由一个或
多个 enumerate/itemize closing 和同一 statement closing 组成，间隔仅 ASCII
排版空白。Scanner 独立核验完整旧及原生陈述的平衡结构，锁定 Git 的末端列表
closing 链必须逐项同序。完整陈述签名只折叠普通 ASCII prose 空白，并仅将实际
永久 Tag 映射一致的 label 记为该 Tag；其余数学、结构、命令、引用、注释及非
ASCII 字节保持。旧链少一个列表项、正文或保护节点即拒绝，不只比较首尾包装。

v6 paragraph_anchor 必含 `preceding_statement_list_closings` 与
`preceding_statement_signature_hash`。闭合列表非空由实际完整 closing 正则与
独立重算强制，Schema 使用仓库现有子集；不能信任调用者提供的数组或 hash。
同一原生陈述后必须立即是完整段落、真实 Section 相同、间隔仅 ASCII 空白；
完整段落签名及章内唯一性沿用严格合同。伪/未知 label、错误闭合、切片、重复、
非相邻、内部空段、未知语法或 typed 数学段落继续 BLOCKED。加载器只有 v6
允许新分支，并从 origin 宏政策、锁定 Git 与完整旧快照重算全部见证。

真实只读验收使用完整 categories-002C 的四旧 input：三项完整定义链及其后段落，
新来源为完整定义与真实 002B paragraph/0001。工具不采用事实、不生成中文或
新 run，不减少 repair-queue 残项。工具合并后 DATA740 更新基线与合同、恢复
claimed，再对原八批完整范围重新 prepare/check、冻结并实际生成全部五字段。

### 陈述后完整段落的独立见证（source-container-v5）

`source-container-v5` 是来源恢复证据版本，派生仍使用 v4 完整分组合同。
它只增加紧邻完整 labelled statement **之后**的完整 paragraph 归属见证；
旧 v4 的陈述前段落核验及历史重放不变。普通准备仍产生 v2/v3，已有边界
仍产生 v4；只有实际使用下述前陈述见证的段落产生 v5。

- 冻结完整旧 batch。旧段落之前必须紧邻完整、有序、连续的陈述链，全部同章、
  同锁定来源及同历史 parent。陈述 opening 是普通环境及自有 label，closing
  是完整真实 closing，不能借数学、注释、literal、嵌套参数或附加正文伪造。
- 从锁定 Git 独立定位同一真实陈述及完整段落。两者必须属于同一真实 Section，
  段落 owner 等于 Section；原生库存中也必须紧邻，间隔仅 ASCII 排版空白。
  不能跨证明、另一段落、标题、注释或任意未分类节点。
- 完整段落对应采用既有 `paragraph_signature`：只折叠普通 ASCII 排版空白，
  所有数学、命令、引用、保护字节及非 ASCII 字符不变；整章签名必须唯一。
  切片、重复、内部空段、未知语法及 typed 数学文字继续阻断。v5 只产生一个
  unit-v1 的完整 paragraph，不扩展数学内文字权限。
- `legacy_boundary_witness.paragraph_anchor` 保存旧段落 ID、历史 parent、完整
  `preceding_statement_input_unit_ids`、真实 `preceding_statement_selector`、
  `preceding_statement_fragment_hash` 和 `paragraph_signature_hash`。
  验证器从实际 origin Git 宏政策、锁定英文与完整旧快照逐项重算；Schema 拒绝
  v4/v5 witness 混用，旧版本无法借今天的新开关获得重放权限。

真实开发见证是 Categories 完整 001T 定义及其后段落：真实 Section001R、
`paragraph/0002`。本工具任务仅只读准备及检查，事实采用必须另开 DATA；
完整 ancestry、所有旧原字节、新模型五字段与不可变 raw/context 绑定、人审
和发布门禁不变。工具准备成功不代表术语修复或 S4 完成。

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

首次 Git 入库前发生第二次实际完整模型修订时，按
[model-provenance.md §8.5](model-provenance.md#85-首次-git-采用前的完整临时-v4-重放)
保存完整上一临时 batch 原字节，并严格重放 `pre-adoption-replay-v1` sidecar。
该历史只允许相同完整 v4 分组/source/unit/原输入、全部组实际 correction 指针与
候选 hash 的变化；不是已入库派生的普通 Git archive，不能丢弃原 run/raw，不能
跳过当前 replay 或重复消费来源恢复。DATA770 的 001O/001Q 需要此验收能力；
独立工具接受后才能采用具体历史文件和数据。

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

### 9.2 多批次共用一次来源准备校验

集中准备多个完整 batch 时，单批接口重复重放全仓库历史，四批准备/check 共
执行八次全仓库溯源校验。新增 `prepare-source-containers-many` CLI，重复
`--plan <file>` 声明至少两个同章、互不重叠的完整 batch，输出一个 ignored
aggregate 包。原单批接口、八文件包格式、source-container-v1/v2/v3、v4 证据
及全部历史语义保持；工具不生成中文、run、事实或批准。

一次调用先冻结中文 HEAD、锁、政策、全部事实/历史/审校及所有已跟踪输入原字节，
执行真实完整 provenance 校验；仅本次内部会话复用该已验证快照和锁定 Git 扫描器。
不存在 caller 提供“已验证”、跳过验证的参数或跨调用磁盘缓存。每份 plan 仍独立
验证完整旧 Git batch、全部旧新有序组、每份真实 selector 与无损 lowering，且每包
的八文件字节与相同输入的原单批接口相等。重复单位/候选写入目标、派生 ID、新输出
ID、跨章、跨批容器重叠均拒绝；输入顺序不授权重复消费原文。

aggregate manifest 使用独立 generator/version，记录每个 plan 原字节 hash、原序
子包 ID、完整子包文件 hash、总旧新/组/BLOCKED 数；子目录为安全 derivation ID。
BLOCKED 包和完整输入照常保存，不以其余包 PREPARED 隐藏问题。
`--require-prepared` 在任意组阻断时非零；`--check` 重做实际完整验证并只读比较
全部目录/文件/字节，不修改 mtime。未知、额外、篡改、越界或 symlink 文件拒绝。

每个 plan 前后及落盘前重查全快照、HEAD、锁、policy、源 blob、plan、输出目录和
旧包原字节；任一变化失败。全部子包先在同一临时 aggregate 目录生成，最后一次
原子替换，失败回滚整包；不分别安装部分成功的子包。全输入快照、输出完整性、
子包逐字等价和跨包所有权拒绝均由独立 fixture 回归验证。

工具任务只改工具/回归及本文和工程计划。真实四份完整现有批次分别运行原接口
与新接口，逐字比较所有子包并报告实际耗时；全部事实/历史/英文原字节、全书库存/
对齐及残项保持。全量工具/QA、来源库存/check→对齐/check、进度/计划及当前 lane
render/pdf 验收后提交；具体修订仍另开 DATA 任务，S4/S5/S7 与八项总验收继续。

工具任务：[Issue #670](https://github.com/dongyaotalk/stacks-project-zh/issues/670)。
同章集中准备示例（每份 plan 仍必须声明完整 batch 和全部有序分组）：

```bash
python3 stacks_zh.py prepare-source-containers-many \
  --harvest ../stacks-project \
  --plan build/plan-a.json --plan build/plan-b.json \
  --output build/source-container-packages --require-prepared
```

在同一命令末尾加 `--check` 可独立完整复核，包及目录时间戳保持。
四个实际完整当前规模界 batch 的只读验收中，原已合并实现准备耗时311.096秒，
新接口99.201秒（3.136倍），独立check98.412秒；32个子包文件与原接口逐字相等，
全部输入/事实/历史保持。该计时是同一冻结输入上的一次实测，不承诺固定耗时；
check重做完整溯源而不是信任上次PREPARED。具体DATA仍在工具合并后另开任务。

### 9.3 完整陈述后段落的历史数学排版见证

独立工具任务：[Issue #764](https://github.com/dongyaotalk/stacks-project-zh/issues/764)。
001N 的完整旧 paragraph 把一条原行内数学包成展示数学，并把另一条数学内 LF
折成空格；旧规则正确拒绝。这是旧提取缺陷，不能只改中文或将其称为原文 remark。
新增独立 `source-container-v9`，派生仍 v4，v1–v8 与全局数学/slot 政策保持。

只支持一个完整 unit-v1 paragraph，原 `\noindent` prefix、仅 ASCII 空白 suffix，
完整旧有序 batch 中紧邻完整 plain labelled statement。旧/新前陈述完整签名须匹配，
label 只按真实永久 Tag 映射；真实 Git 前陈述与段落同属一个 Section、立即相邻且
间隔仅 ASCII 空白。完整旧段落、完整前陈述、完整新段落均不得取切片；匹配必须在
锁定章内唯一。普通 prose 空白沿用既有签名合同，其余节点逐项比较。

独立保守数学词法仅接受单个 ASCII 字母/数字、圆括号、冒号/等号、零参数记号
`\Ob`、`\to`、`\phi`、`\psi`、`\circ` 及完整 `\mathcal{A}` 型单大写字母
原子。段落中所有数学节点（包括未变节点）均须满足该有限语言；它只限定历史见证，
不新增宏政策。其他命令、一般花括号/脚标、数学文字、注释、literal、非 ASCII
或未知语法保持 BLOCKED。旧/新节点都须由 Scanner 确认为单一 dollar math。

只允许可确定性重放的两种原生→历史变换：原单美元变旧双美元并可增加外围 ASCII
空格；原 LF/CRLF 变旧单 ASCII 空格。后者只允许完整原子之间、圆括号深度为零且
两侧没有空白的位置；命令/参数内、连续空白、裸 CR 均拒绝。原内联 body 不能有
外围空白；未替换的换行及所有其他字节原样保留。不得一般去空白或数学等价化，
不得反向转换、改公式 token、普通空格或节点数。至少存在一项真实受支持差异。

见证记录旧/新完整段落签名 hash、完整前陈述 ID/selector/片段与签名 hash，逐个
不同数学节点的序号、原旧/原 Git 节点、字节 hash、操作种类、添加的外围空格与
每个换行的原节点内字节位置及 LF/CRLF。加载器只在 v9 启用，从 origin 政策、
完整旧输入及锁定 Git 重算全部字段；篡改、删项或降级均拒绝。新 source 始终来自
完整未归一化 Git 片段，五字段/raw/context、全部旧组/ancestry、人审门禁保持。

验收先运行独立 synthetic Git 正反例、Schema/准备/check/加载及完整五字段分组
重放，再核验真实完整 001N 两旧→两新和 Section001L 六批十组完整范围；保留
当前审计残项、事实/历史与范围外原字节，执行全库库存/对齐及 checks、239QA、
共享门禁/117模板、隔离进度/计划、当前 lane render/pdf 和整书文字/PNG 核验。
工具验收合并后才另开完整小节 DATA，不将来源准备成功当成术语修复。
