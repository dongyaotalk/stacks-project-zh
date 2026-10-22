# 完整来源首次采用与临时生成历史

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

## 来源权限

从锁定 English Git 重新选择完整容器，验证真实 owner、Section、kind、ordinal、
源 blob、边界、全部保护结构和现行 lowering 的完整有序 unit，不能凭任意跨度、
ID 或自报 hash 证明来源。origin 中目标文件及 unit ID 必须不存在；另从实际
完整来源对应核对 origin 与其他 active 来源，拒绝语义重叠或重复首次采用。
同一生成包内的所有容器也逐对核对实际 Git 边界；不同 batch 或不同 ID 不能
同时采用完整正文块和其中的段落，或以其他重叠容器重复消费来源。
完整陈述、证明、列表、脚注及 typed 数学文字不截断，未知语法仍阻断。

新候选的 `source_adoption_id` 指向 `source-adoption-v1`。溯源逐项重放冻结输入、
完整来源、实际 raw、run、五字段、context 和输出原字节，而非只检查 Schema。
渲染先完成同一完整重放，再按锁定来源投影标签和引用；无标签 typed 正文还须
通过完整来源位置、相关来源不重叠及批次不交错检查。原 v1/v2/v3/v4 历史合同
保持，首次采用不制造旧分组、工具派生或人审身份。

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
当前来源/术语/证明独立审计、真实每个 run QA、全库提取与对应、两个要求的 lane
完整构建、最终 TeX 日志和精确远端门禁。排版验收默认只检查编译；仅用户明确
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
