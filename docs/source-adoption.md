# 完整来源首次采用与临时生成历史


日常章节验收按 [当前章节合同](chapter-current-validation.md)：检查本次全部新节点、
直接父输入、完整 run 参与者，遇到可信主线身份未变的旧祖先停止递归。下文的完整递归
回放是显式 `audit-history` 及旧严格接口的审计合同；生成/装配仍保留原门禁。旧事实、
原始输出及人审记录不改写；日常机器通过不表示审计或人工审校通过。

本合同对应 [Issue #819](https://github.com/dongyaotalk/stacks-project-zh/issues/819)。
它为没有已采用旧候选的完整锁定 Git 来源提供独立首次采用入口，不伪造 v4
修订祖先。具体数据必须在工具接受后另行声明精确任务范围及真实模型运行。

## 记录和入口

```text
translation-data/source-adoption-inputs/<adoption-id>.json
translation-data/source-adoptions/<adoption-id>.json
translation-data/retired/source-adoptions/<prior-id>/units.jsonl
translation-data/retired/source-adoptions/<prior-id>/candidates.jsonl
```

`source-adoption-input-v1` 在实际生成前冻结：可达 origin、英文锁、完整政策原字节
hash、真实 model/Harness/turn/effort、所有有序完整 unit、实际 selector 和完整 Git
容器、邻近与引用上下文及其 hash、精确输出路径。每个 batch 只属于一个实际
Section，文件按相邻 Section 顺序排列；通常2–8文件、300–1500来源词。一个
不可分割的完整剩余 batch 可单独采用，须明确异常原因；来源词超偏好也须记录
原因。不能增加无关文本凑包。

输入还保存实际 claimed Issue、owner、branch，以及集中任务清单的完整原字节和
SHA256。装配前核对当前分支、清单原字节、唯一数据 scope、完整输出ID、run/model
及每个实际写入/原输出路径。历史回放使用当时不可变输入中冻结的原清单，后续
同一任务扩范围不能回写旧生成冻结或使旧run冒用新范围。

模型实际输出保存在不可变 JSONL，逐项包含 unit_id 和完整五字段。失败尝试保留，
后一次完整记录替代同一 unit 的采用选择，程序不生成中文或修改译者字段。
使用独立 CLI，而原 `assemble` 和 `assemble-many` 的无包 typed guard 保持：

```sh
python3 stacks_zh.py assemble-source-adoption \
  --root . \
  --input translation-data/source-adoption-inputs/<adoption-id>.json \
  --raw docs/evidence/<actual-raw>.jsonl \
  --harvest <locked-English-checkout>
```

多次实际原输出按先后次序传入 `--raw`。装配动态解析注册 Harness，并再次核对
冻结的具体版本；model record、模型通道和身份置信度须匹配当前注册表。工具写出
独立 `translation` run，名称为 `run-<adoption-id>`，不将首次生成称为 revision。
所有 batch 完整验证后才安装全部候选、run 和最后的采用记录；安装故障恢复
已替换的临时候选并移除新文件。

### 已接受来源政策变化后的首次装配

[Issue #942](https://github.com/dongyaotalk/stacks-project-zh/issues/942) 允许尚未首次
Git 采用的完整冻结生成，在 `config/macro-policy.yml` 或 `config/source-terms.json`
以及 `schema/unit.schema.json`、`schema/math-text-regions.schema.json`、
`schema/math-text-components.schema.json` 后来通过主线接受时继续首次装配。
所有原冻结 unit 和来源上下文对象必须同时通过原和当前来源 Schema，不转换对象。
旧政策仍逐字等于冻结 origin；当前完整政策集合
必须逐字等于可确认的 main 祖先，且 origin 到该祖先再到当前 HEAD 的关系成立。
未接受或未提交的政策变化、其他政策/候选、运行、输入、采用 Schema/模型/Harness/提示/词表变化仍拒绝。

先按原政策完整重选来源和上下文，再以当前政策独立重选全部目标完整容器。
除完整 macro hash 引起的分类见证 policy hash 及相应结构 hash 比较差异外，
来源、公式、typed slot/分类语义、包装、位置、边界和分段必须完全相同。
比较副本只用于只读核验，采用的 unit 和候选仍保留原冻结见证和模型五字段，
不重绑定已有候选，不扩大 v5 修订权限，不更改历史 Schema 或生成身份。
来源重复/覆盖、完整 scope、真实模型输出及当前术语/保护/来源 QA 门禁继续执行。
实际术语投影有新增要求而原模型输出不满足时仍拒绝，必须另行完整实际生成。

[Issue #946](https://github.com/dongyaotalk/stacks-project-zh/issues/946) 处理这一边界
内独立完整 proof 的只读英文归属见证。装配已完整验证原冻结及现行接受政策后，
目标 proof 仍以原政策选择和 lowering，逐项等于原冻结 unit。若其真实陈述或此前
完整 proof 在原政策下的唯一阻断是明确的未分类 `math-text`，可用现行已接受
main 分类重新选择该英文见证。需独立核对 main ancestry 和整份宏政策原字节，
现行选择必须 READY，完整英文片段、位置/hash、锁定 blob、owner/Section/ordinal
须等于原库存，且两份来源与政策在检查结束时未变。英文见证只参加临时证明归属
及次序验证，不加入事实、模型输出、run、进度或任何批准；普通 `Containers.select`
和目标 proof 的未分类数学文字门禁不变。未知宏/语法、未接受或仍未分类的文字、
来源/坐标变化及错误 proof 次序继续拒绝。历史冻结、raw 和回放合同均保持。

### 未安装候选的失败生成历史

旧 `source-adoption-input-v1` 的完整只读证明 neighbor 可能来自“段落后清空
proof owner”的已接受提取实现。该兼容只接受原 origin 属于接受主线，且原 Git
`chapter_inventory` 函数精确匹配已知旧指纹的输入。既有 flat/opaque 模式从同一
锁定 Git 和原宏政策完整重提取 Schema 1 证明；原字段、无 owner 的旧 ID、parent
和位置全部必须相等。现行唯一完整证明也必须无损回放相同英文 span，包括当前
typed IR 的完整源还原。仅本次已核验邻近覆盖集合采用现行证明 ID；冻结上下文、
事实、模型输入输出和历史 ID 不写回，不新增历史格式或人工批准。其他版本、未知
旧实现、截断、错位或字段篡改均拒绝；缓存同时绑定 origin 和工具版本。
若同一完整 proof 是 prose_block 的前/后边界，原边界 owner/ordinal 也可能受影响。
只有原冻结 neighbor 完整回放，且其物理端点恰好等于该完整 prose_block 的端点，
才可在内存比较中使用原边界坐标。整个原/现行选择的每个其他字段和完整 lowering
必须相等；不能改变来源范围、分段、公式、unit ID 或候选，原见证仍保留原字节。

只读英文邻近/引用上下文可能保留自然数学文字启用前的完整 Schema 1 IR。
现行同位置完整节点已是 typed IR 时，验证器从相同锁定 Git、原宏政策与既有
`natural_text_enabled=False` 表示重新提取；原冻结节点的每个字段、位置、owner、
parent 和语义序号都必须精确匹配。现行完整节点也须无损还原同一英文片段。
这一兼容仅核验只读上下文，不转换模型输入或事实，不允许目标 unit 使用旧式
数学保护绕过现行采用门禁；修改、截断、错位或伪造的上下文仍拒绝。

实际生成的 raw 在记录 Schema、完整覆盖或受保护候选装配阶段被拒绝时，可保留
现有 run Schema 中 `inputs.settings.frozen_generation_input` 指向的完整原冻结输入。
该失败 run 的 `context_hashes` 和 `accepted_records` 必须为空；实际生成的完整
context hash 顺序另存于 `generation_context_hashes`。`raw_attempts` 保存全部原始
尝试的精确路径、原字节 hash 及逐文件 unit 顺序，`observed_assembly_exit_code`
保存真实非零退出，`observed_assembly_error` 保存 `ERROR: ` 加实际装配错误全文。
身份、来源、政策、模型、Harness、turn、effort、时间及完整 unit 顺序须等于
`frozen_generation_input`；不得同时声明成功采用指针或存在同 ID 的采用记录。

来源采用加载器以原 origin 政策完整重选来源、上下文和全部祖先，逐字核验冻结
输入、run、所有 raw 和历史快照；全部 raw 在首个拒绝之前均绑定。随后只读执行
同一 raw 解析与候选装配，必须重现记录中的拒绝全文；能够完整装配的输出不能
伪称失败。此入口仅支持上述 raw/装配阶段的负结果，不把其他失败原因解释成
已验证历史。已首次加入 Git 的任何证据仍不可通过重算 hash 改写。

经完整验证的失败冻结输入所引用的前继快照是同次来源采用凭证的历史依赖，
不因没有成功采用记录而被误判为孤立文件。未验证或无关快照继续拒绝；失败 run
不新增当前 adoption、候选、进度或渲染正文，不消费当前前继，不获得任何审校、
术语或发布状态。失败证据变化或新增/移除 run 文件会使同次凭证失效。

## 来源权限

从锁定 English Git 重新选择完整容器，验证真实 owner、Section、kind、ordinal、
源 blob、边界、全部保护结构和现行 lowering 的完整有序 unit，不能凭任意跨度、
ID 或自报 hash 证明来源。origin 中目标文件及 unit ID 必须不存在；另从实际
完整来源对应核对 origin 与其他 active 来源，拒绝语义重叠或重复首次采用。
同一生成包内的所有容器也逐对核对实际 Git 边界；不同 batch 或不同 ID 不能
同时采用完整正文块和其中的段落，或以其他重叠容器重复消费来源。
完整陈述、证明、列表、脚注及 typed 数学文字不截断，未知语法仍阻断。

完整 canonical proof 可以独立归入一个事实文件。文件外的归属见证只能从锁定
English Git 重新选出：唯一真实 owner Tag/label、同章同 Section、真实 proof ordinal、
完整陈述及此前各份完整证明。当前 proof 的全部 unit 对象必须等于该 selector 的
完整现行 lowering；来源文字、数学、包装、hash 或 ID 任一变化均拒绝。
这些英文陈述/证明只进入同次只读坐标及 proof 次序验证，不加入输出 facts、模型
候选或进度，不重译、移动或覆盖另一文件已有的合格陈述。没有实际锁定来源时，
旧文件级迁移及不完整 wrapper 检查保持原错误；任意调用者 ID、Tag 库存、跨度或
相似证明不能代替完整 Git 选择。第二份证明必须核验此前的真实证明而非改称第一份。
同一事实文件中连续出现不同 owner 的完整 canonical proof 时，也逐份核对真实
owner；不得让后一份继承前一份的临时陈述而改变其永久坐标或造成重复 ID。
补入见证仍不得重复、移动文件内实际已有的单元；伪造坐标或非完整 proof 仍拒绝。
当前 QA、对齐、首次采用/重放与显式来源/证明审计使用同一见证。采用格式、原
raw/run/freeze 和历史 Schema 均保持；未知宏、数学文字、完整生成、溯源和人工
门禁不因此改变。对应工具任务为 [Issue #939](https://github.com/dongyaotalk/stacks-project-zh/issues/939)。

新候选的 `source_adoption_id` 指向 `source-adoption-v1`。溯源逐项重放冻结输入、
完整来源、实际 raw、run、五字段、context 和输出原字节，而非只检查 Schema。
渲染先完成同一完整重放，再按锁定来源投影标签和引用；无标签 typed 正文还须
通过完整来源位置、相关来源不重叠及批次不交错检查。原 v1/v2/v3/v4 历史合同
保持，首次采用不制造旧分组、工具派生或人审身份。

同进程严格验收可把本次完整重放产生的私有结果交给决策、渲染和 typed 正文定位。
结果绑定实际发行对象、仓库/harvest 位置、当前 unit/candidate、原采用/input、
全部历史候选、动态读取文件 hash 和实际解析政策，并保留自身快照检查；任一相关
内容或路径变化即失效。普通调用无此真实结果时仍完整重放，不接受调用者字典、
复制对象或跨进程成功记录。v1/v2/v3/v4 与 shared histories 的必要递归保持。

进度报告可按 [来源覆盖规则](progress.md#完整来源容器内的永久-tag) 查询当前完整
首次采用陈述中的原生列表项 Tag。查询核对不可变采用记录和输入、完整当前 unit
文件及顺序/hash、accepted origin 的政策和锁定 Git 容器的规范 lowering；后继
已消费的采用不重复计数。来源准备不依赖候选是否存在，因此这里不回放 raw/run
或全库模型历史；候选缺失仍不能计为候选完成。此查询不代替上段完整溯源，也不
授予任何人工审校、术语批准或发布状态。

## 首次加入 Git 前的真实生成历史

`prior_attempts` 可保存同一完整批在首次 Git 采用前的全部临时生成。每次保存
完整有序旧 unit/candidate 原字节、所有原 run、生成输入和原 raw 尝试的路径/hash。
旧新来源必须逐字相等；原候选五字段逐项等于其原输出，原 context、真实身份、
原始政策和时间须保持。前次运行严格早于本次生成；不能把临时旧候选称为
可达 Git 前继，也不能将历史输出变成第二个 active 末端。

溯源把每个旧实际候选插回原 batch 位置，独立验证其原 manifest 和完整 context
顺序；未被本次重译的同 run 其他批次仍参加原验证。原 run、raw 和输入不回写。
缺失、错序、截断、重复、孤立或重算 hash 后的篡改均失败。

采用记录、生成输入、原输出和历史快照一旦首次加入 Git，就按首次加入原字节
核验。v1 不授权采用之后直接覆盖 active 候选或移除首次采用证据。后续需要改变
这类已接受事实时，必须先扩展并接受相应的完整归档/修订合同，不能删掉指针、
借普通 assemble 或伪造现有 v4 祖先规避。

## 决定与验收

selection、review 和正式 revision 对首次采用候选要求完整 `provenance_hash`，
绑定当前候选、采用记录、输入及全部递归文件 hash。绑定 hash 只在完整实际
溯源通过后计算；它本身不是来源验证器。内容、来源、模型身份或历史改变后，
旧决定不能继续匹配。工具没有授予术语、critic、语言/数学审校或发布批准。

独立 synthetic Git 测试覆盖实际公开入口、typed 首采、完整临时历史、保护结构、
漂移、缺失、源范围及写入回滚；测试数据明确不是实际模型输出。具体 DATA 仍须
当前来源/术语/完整覆盖、每个真实 run 直接关系、适用章节构建、最终 TeX 日志和精确远端门禁；公共变化按 CI 矩阵扩大检查。排版验收默认只检查编译；仅用户明确
要求页面检查时才做额外检查，默认不生成截图/PNG或逐页目视验证。

## 首次 Git 采用前的完整再次生成（v2）

[Issue #826](https://github.com/dongyaotalk/stacks-project-zh/issues/826) 增加独立
`source-adoption-input-v2` / `source-adoption-v2` 分支。v1 的 ordinary 临时历史
权限保持；v2 的 `prior_adoptions` 必须绑定每个前次 adoption 的不可变 record
和全部有序完整 output unit/candidate 原字节快照。快照路径为
`translation-data/retired/source-adoptions/<new-id>-<prior-id>-<batch>/units.jsonl`
及同目录 `candidates.jsonl`。新生成必须完整重译所有前次 adoption 的全部 batch，
旧新来源及分段逐字相等，不允许只重译一个缺陷字段或部分 batch。

回放按前次原 input、原政策、原 raw、run、context 和所有递归普通历史重新产生
每个原输出，严格验证时间顺序、快照 hash、完整五字段及原 run 参与者。原 record、
输入、raw、run 不回写；旧 adoption 由唯一当前后继消费，不成为第二个 active
末端。新候选声明全部前次 adoption；决定 hash 因此绑定完整递归历史。

生成时前次 record 和 output 均须未曾加入 Git。首次共同提交后只允许按该同一
首次提交回放历史，已分别采用的前次事实不能以 v2 覆盖。加入 Git 后的 active
修订仍需另外接受相应合同。本分支不授权来源修订、术语或人工审校批准。

完整来源首次采用验证过的 OWNARGEND 标题与 v4 标题具有相同来源权限；旧派生
检查必须消费实际首次采用回放凭证，不能凭 pointer 或任意调用者列表通过。

## 同一普通 run 的范围外参与者（v3）

[Issue #828](https://github.com/dongyaotalk/stacks-project-zh/issues/828) 增加独立
`source-adoption-input-v3` / `source-adoption-v3` 分支。当同一个普通临时 run 的
其他完整 batch 已进入首次采用历史时，v3 用 `shared_run_histories` 显式绑定这些
范围外 adoption 的 record 和全部有序 output 原字节快照。固定快照路径为
`translation-data/retired/source-adoptions/<new-id>-shared-<old-id>-<batch>/units.jsonl`
及同目录 `candidates.jsonl`，record 和快照路径均须包含在当前精确任务 scope 内。

每个新 batch 必须具有完整普通 `prior_attempts`。v3 不能同时声明
`prior_adoptions`；v1/v2 不能声明共享历史。范围外 witness 必须严格早于本次生成、
与新输出及其他 witness 不重叠，并至少包含一个本次普通原 run 的参与者。
工具递归重放整个 witness 的来源、政策、全部五字段、raw、run、context 及普通
历史，再把相关普通参与者插回原 run 的完整路径和顺序。回放 witness 时，同步
使用新 batch 已验证的普通祖先快照；共同采用后，这些快照也用于其他 active
adoption 的原 run 回放。原始 manifest 的完整 accepted-record 和 context 顺序
检查仍必须通过，不能用任意快照或重算 hash 绕过。

共享 witness 只贡献原 run 验证，不消费范围外 adoption，不扩大新输出 ID，不
覆盖范围外候选，不授予审校或来源修改权限。缺失、重复、截断、时间错误、范围
越界、快照或原 raw 篡改，以及递归循环均拒绝。v2 完整前次采用历史的限制保持；
新输出仍须由实际模型完整生成并通过全部现行来源、术语、结构和溯源门禁。

## 唯一完整章首标题（v4 独立开发合同）

[Issue #840](https://github.com/dongyaotalk/stacks-project-zh/issues/840) 增加独立
`source-adoption-input-v4` / `source-adoption-v4`。这里的版本不等于派生 v4 或
source-container 的版本；v1/v2/v3 的真实 Section、相邻范围和历史权限不变。
工具验收并合并后，具体 DATA 才能冻结和采用新分支。

新分支只接受一个 batch、一个 `title_title/0001` 完整容器和一个 canonical
`chapter_title` 单元。它必须是锁定 Git 中唯一、位于首个自然语言节点的真实章首
标题，其 owner/parent 及唯一 phantom label 都从同一完整 header 重选；不能将
chapter Tag 改成 Section Tag，不能混入 Section、普通段落或第二个标题。
完整 title 参数及其后 maketitle、phantomsection、真实 label、tableofcontents
包装仍按已有完整容器选择器逐字核验，不允许自报边界或截短 header。

冻结 origin 的两份首次采用 Schema 必须真实登记 v4；不能用早于该权限的政策
origin 声称新分支。完整政策、真实 Issue/scope、模型/Harness、输入、邻近/引用
上下文、保护结构、来源不重叠和全部五字段/raw/run 继续按原公共入口核验。
单独标题仍须说明不可分割及词数偏好的例外。新分支不接收 `prior_attempts`、
`prior_adoptions` 或 `shared_run_histories`；实际原始尝试按原 raw_attempts 保存。
若以后需要章首采用后的修订或其他历史能力，必须另立完整合同，不能借此覆盖。

记录和输入各自保存独立 v4 身份并完整回放。历史 v1/v2/v3 仍不能使用非 Section
parent；新 Schema enum 不将旧记录重新解释为章首权限。新分支不生成中文，不
登记词表、critic、人审或发布批准；普通 assemble 的完整来源限制和 typed guard
也保持。正反 synthetic Git 回归及完整旧历史、实际本地编译与远端门禁通过后，
才可由独立的候选任务采用。

## 首次 Git 采用前的不变数学文字见证重绑定（v5）

[Issue #892](https://github.com/dongyaotalk/stacks-project-zh/issues/892) 定义独立
`source-adoption-input-v5` / `source-adoption-v5` 分支。完整宏政策修订即使未改变
某个已分类数学文字的来源及保护结构，也会改变其分类见证中的整份政策 hash。
v2 仍要求全部旧新 unit 对象相等；不得在 v2 中忽略这个差异。

v5 保留 v2 的完整 `prior_adoptions`、全部旧输出原字节快照、独立旧政策回放、
实际新模型五字段及所有递归历史合同。新 origin 的两份首次采用 Schema 必须
真实允许 v5；全部新输入必须等于该 origin 政策对锁定 Git 完整容器的规范
lowering。前次采用及其 output 均须未曾独立加入 Git，首次共同提交之后完整
历史仍逐字回放，唯一当前后继及时间约束保持。

唯一允许的旧新 unit 差异为已有 `math_text_regions` 中每个 slot 的
`classification_witness.policy_hash` 从实际旧完整宏政策 hash 变为实际新完整
宏政策 hash，以及由该变化确定性产生的 `source_structure_hash`。旧见证的
政策 hash 必须等于已经独立完整回放的旧政策；新 unit 必须等于新政策的实际
完整 lowering。所有其他字段、来源 TeX、正文、公式、保护节点、区域/slot
次序、文字、锚点、分类条目、坐标及分段逐字相等。组件及其他见证结构不获得
差异权限。要求至少发生一次真实重绑定；相同政策或完全不变输入使用 v2。

验证器只在内存预测这种精确 hash 变化并与完整新输入比较，不修改任何历史
文件，也不生成中文。新 run 必须冻结全部前次采用的全部 batch，实际模型完整
生成每个新单元五字段；不能只替换术语字段或继承旧 raw。当前结构、术语、完整
溯源、来源与保护门禁照常执行，候选及预览绑定旧/新政策、实际运行和全部历史。

该合同不允许来源修复、分段变化、章首 v4 后继或已独立 Git 采用事实的覆盖，
不改变 v1/v2/v3/v4 及派生合同权限，不批准术语、critic、人工审校或发布。具体
数据只能在本独立工具验收合并后于其声明的数据任务采用。

## 受保护数学文字引用的首次生成（v6；独立工具 #924）

`source-adoption-input-v6` / `source-adoption-v6` 仅用于至少包含一个 unit-v4
受保护引用参数的完整首次生成包。包中其他普通 v1/v2 单元仍完整冻结并实际
生成；不凭一个引用叶创建零模型或局部字段采用。精确任务范围、完整 locked-Git
容器、所有相邻/引用上下文、唯一 writer、模型/Harness/runtime、六字段 raw
（unit_id 加五个译者字段）、一次完整装配和不可变证据合同保持。

v6 的政策集合是原 POLICIES 加 `schema/math-text-references.schema.json`。
所有文件必须逐字等于真实 accepted origin；该 origin 的 unit Schema 必须
明确包含 v4、独立引用 Schema 必须存在，两份首次采用 Schema 必须明确允许
input-v6/v6。缺失任何能力或当前政策漂移即拒绝，不从工具分支或自报版本推断
主线权限。旧 v1–v5 继续冻结原政策集合，不能采用 unit-v4 或重新解释旧来源。

v6 不允许 prior_attempts、prior_adoptions 或 shared_run_histories。既有候选
修订、首次 Git 采用前见证重绑定、旧分段恢复和组件共存都需要各自另行版本化
合同；不得把 v6 当作扩大旧历史权限的入口。原 v1–v5 历史记录和 raw 不回写。
当前 QA、完整溯源及 renderer 检查独立 v6 候选，普通装配、历史 source-container
和 group-derivation v4 路径拒绝 unit-v4。模型不能批准术语、语言/数学审校或发布。

该工具验收并进入 main 后，再接受独立 #925 的生产政策；DATA #923 重新冻结
当次完整 source/context/runtime 并实际生成。测试中的 synthetic 冻结/raw/run
仅为明确标注的独立回归样例，不能作为具体章节的模型输出或审校证据。
