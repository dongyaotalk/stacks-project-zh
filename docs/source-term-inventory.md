# 来源侧术语出现清单

`python3 -m stacks_zh audit-terms --output build/source-term-audit.json` 从当前英文
unit 生成逐次出现要求，再检查每个候选。检查失败返回非零；报告仅写入 ignored
build 或仓库外，不覆盖事实数据。这一阶段是独立只读审计，尚未接入默认 QA/CI；
现有数据修复完成后另开工具任务启用强制门禁。

## 来源与识别范围

`config/source-terms.json` 声明英语数学词汇的识别范围。它只有来源词形、章节范围
和英文节点证据，不含中文译法或批准状态，也不是 `config/glossary.yml` 的替代品。
证据绑定锁定来源 commit 和完整 source TeX hash；坐标迁移或无损占位符重提取
不会使证据丢失。旧式证据必须仍存在于当前英文节点，不能从候选的术语数组反推。

扫描格式包装内的自然语言，但不读取受保护公式、引用或其他完整受保护节点。
命名陈述环境标题同样属于自然语言，必须重提取到 source_text 才进入逐次来源
要求；标题结束的 `ENVARGEND` 是语义边界，不能把标题词组与正文拼成新词组。
标题与正文重复的同一术语需要分别显示和记录。只读 `audit-source` 报告仍隐藏在
render.prefix 的标题，以及无效的命名参数边界；简单词组可用 source helper
无损提取，复杂 TeX 标题须显式任务。本规则不扩大 glossary 批准或审校权限。
定义节点，或含 called/call/say/defined 的声明语境，还从斜体/emph 包装提取新
概念。这条规则能发现未登记的新定义词；数学限定表达式保持在受保护节点中，
清单记录外部的英语词汇核心。冠词、末尾连接词不作为词汇核心；明确的非数学
声明排除项必须在目录中写明理由。

斜体中以 let/assume/suppose 开始且含数学参数的完整措辞句属于使用示例，不能
按公式切成新的词汇声明；例如 “let … be the … category associated to …” 不会
生成 let 或 be the 术语。句内目录词仍逐次强制核对，其他真正的新命名和短关系
声明继续生效。只有 payload 确认为纯字体包装的 OPEN/CLOSE 才产生声明；完整
受保护公式或引用不能借字体 token 名称变成英语声明。此规则是可审查的语法
分类，未登记概念的语义歧义仍需逐句审查。

词形匹配遵守单词边界；同处有重叠时采用最长短语。报告保留每次出现的原词形、
投影位置、识别规则、source text/structure hash 和目录 hash。来源 hash 过期、
目录重复词形/概念、证据消失、candidate batch 缺失或覆盖范围不一致均失败。

## 候选合同

每个要求的来源出现必须有对应的 `term_occurrences`，正文必须按记录顺序出现
`中文（English）`。该英语词形必须在源句中精确存在，不能改变大小写、单复数或
重复使用同一次来源出现；源句中出现两次需要两份记录和两次显示。允许保留该处
实际存在的 a/an/the 冠词；把一整句或任意更长表达式申报为一个词条，不能代替
句内各术语的逐项显示。中文句法导致的术语顺序变化不要求英文来源同序。

所有申报词对仍须有真实 glossary 批准或 `unknown_terms` 上下文及
`DECISION_REQUIRED`。模型自报 `CLEAR` 不能批准词条。来源覆盖检查不评定所提
中文词是否正确，也不能完成语言、数学审校或把候选提升为正式译文。

术语显示检查忽略 TEXTIT/TEXTBF/TEXTSF/TEXTTT/TEXTSC/TEXTRM/EMPH/TEXT 的
OPEN/CLOSE 字体包装，允许一个词组横跨纯排版边界。`target_term` 可以只记录
中文词形，无须包含单元专用格式 token；历史记录含格式 token 时按相同显示投影
兼容核对。公式、引用、结构、脚注等语义节点保持不透明，不能用它们连接两个
不连续词片段。占位符的原始次数与顺序仍由结构检查独立强制验证。

## 能力边界与后续维护

确定性词汇匹配不是完整的数学概念识别：未登记且没有声明包装的术语、代词所指、
跨公式表达式和语义歧义仍须逐句审查。目录可能需要按章节区分普通用词与数学
用词；缩减范围、排除声明或新增复合词必须在独立工具任务中说明英文依据，不能
在翻译数据 PR 中为通过检查而关闭要求。目录没有人工术语批准的含义。

已校准的普通用法也只由英语来源确定：紧接受保护数学参数的 Set 祈使句及明确的
we/can/let us 等赋值语境不作为集合名词；a/the set 等名词仍强制核对。模糊语境
不能由候选自行豁免。目录的 `nonmathematical_occurrences` 保存逐次分类的章、
完整 source TeX hash、原词形、从 0 开始的出现序数和理由。目前仅明确排除 coding
中拆分长证明的 splitting，以及 08VZ 列表中的 set 赋值句；后者未落入简单祈使
语法规则。数学 splitting 的证据来自 02XJ 的真正概念说明，其他同词出现仍检查。

`nonmathematical_chapters` 当前只声明 GNU Free Documentation License 章属于法律
与文档格式语境，绑定完整英文章标题、source TeX hash 和具体理由；其 image、large、
equivalent、limit 等普通用词不产生数学要求。全库审计验证章标题必须是当前章的
chapter_title，逐次分类的原词形/序数必须仍存在，证据缺失或变更就失败。证据按
TeX 字节而非易迁移的坐标核验；unit_id 是可追溯定位提示。重复范围、负序数或
缺少理由均被拒绝。所有候选自报术语仍须满足源词形、显示次数和待决合同；编码
章中的真正数学引用继续检查。这些有限语法/语境分类不能替代人工数学审校。
同词的普通用法与数学用法共存时，源词形分配优先满足真实数学出现；随后仍允许
普通用法的可选双语记录，但不得复用任一次来源出现。

默认全库门禁尚未启用，不能把当前 `qa-all` 通过当作来源覆盖已经修复。数据任务
必须保存原始输出，通过派生/实际模型修订补齐文字及记录，再运行本审计；最终
集成阶段才将其接入 `make qa-all` 和 CI。本任务不修改现有 run 或术语批准。

## 完整容器恢复后的稳定来源证据

开发任务：[Issue #624](https://github.com/dongyaotalk/stacks-project-zh/issues/624)。
0024 的 cartesian / equivalence 目录证据目前绑定两个旧 proof 碎片。完整 proof
恢复后这些碎片不再是当前单元，原完整 TeX hash 不会等于新 proof；不能忽略
证据消失、改写历史，或在普通 DATA #623 中修改目录来绕过检查。

来源证据使用互斥的两种格式。旧 `chapter/unit_id/source_term/source_tex_hash`
格式仍按当前英文节点验证，unit_id 只是定位提示，原有失败条件保持。新增
`kind: locked-source-container` 明确保存 `chapter`、`source_term`、
`source_commit`、`selector` 和完整原片段的 `fragment_hash`。selector 保存章文件、
真实 owner Tag/label、Section parent、容器 kind 和从 1 开始的 ordinal；不得
包含旧式字段或任意额外键。所有来源词形、forms、chapters 保持原要求。

新证据重新使用完整容器选择器读取锁定 commit 的英文 Git blob 和 tags，核验
唯一真实语义归属、完整边界、可准备状态及原 UTF-8 字节 hash。来源 commit
同时等于目录与 upstream.lock；不能使用工作目录、库存自报 READY、候选文本、
旧分段或自报 hash 代替。未知宏/数学内文字等仍阻断，不扩大抽取政策。只有完整
保护来源的 source_projection 中实际存在的精确词形可提供词汇证据；数学、
引用、命令参数、comment/literal 内文字保持不透明，不因英文 raw TeX 搜索命中
而获得证据。hash、selector、章或词形不匹配全部失败，错误仍写入独立审计报告。

`audit-terms --harvest <checkout>` 支持显式 harvest，未指定时沿用既有默认位置。
统一修复队列必须传入其实际 harvest，不能用默认路径替代调用者配置。报告保存
锁定证据的 selector、commit、Git blob 和片段 hash 及核验结果；证据有效不表示
当前译文通过术语覆盖，更不批准中文词条、人审或出版。旧证据及非数学分类仍按
各自原合同验证，不借新格式扩大排除范围。

本工具仅将 cartesian / equivalence 的来源锚定到真实 0024 完整 proof，不改变
其形式、章节范围、其他目录条目、当前译文或历史证据。真实 Git 回归覆盖当前
分段替换仍能取证、dirty 工作目录、篡改/错误 selector/hash/commit、受保护词
不能冒充正文、旧式证据仍要求当前节点、Schema 互斥与显式 harvest 传递。验收
比较全部当前候选/来源/证明残项及整书文本保持，随后 DATA #623 重新准备并冻结
上下文；S4/S5/S7 和全库严格门禁仍分别完成。

003O 三项来源锚点迁移由独立工具任务
[Issue #633](https://github.com/dongyaotalk/stacks-project-zh/issues/633) 声明。
整节恢复会合并旧 p001/p002，并从锁定 Git 读取完整标题；旧式 evidence 的
完整 TeX hash 因此不能继续定位当前片段。1-morphism 与 2-commutative 改用
真实 Section 003O 的完整 prose_block（ordinal 1），2-fibre-product 改用
该 Section 的完整 section_title。均使用既有 locked-source-container 格式，
核验完整 Git 原字节、真实标签、Section、完整边界和保护后的精确词形。
迁移只改三项 evidence；forms、chapters、其他证据、非数学分类和所有译法
批准状态保持。开发文档先于配置修改；验收要求全部审计残项和译文事实保持，
目录 hash 与证据来源元数据按新锚点更新，整书 layout 文本保持。声明层虽
可产生 and 候选词，既有非数学声明目录已明确排除连接词，完整来源库存没有
该词的要求，无须修改抽取规则。具体 30 单元候选恢复另开任务，最终输入在
本前置合并后冻结。

[Issue #642](https://github.com/dongyaotalk/stacks-project-zh/issues/642) 集中准备
后续 02XG、02XJ、04Z2 的稳定证据：automorphism、base-change、covering、
discrete、fiber-product、natural-isomorphism、pullback、splitting 和
strongly-cartesian 九项旧式 evidence 改用既有 locked-source-container 格式。
数学陈述及 proof 依据真实自身标签与 proof 归属选择完整容器；正文依据旧片段
唯一 Git 对应位置定位完整 prose_block，核对真实前后边界。不能靠候选词对、
裸字节截断或未准备片段提供证据；必须在完整保护后的 source_projection 中
核对准确来源词形，词形须属于既有 forms。

仅上述九项 evidence 可改变，所有 forms、chapters、其他目录条目和非数学
分类保持。此任务同时按独立明确记号合同分类 Cat/Fib，以准备完整英文输入；
不批准中文词汇、不修改事实或自然语言 math-text 规则。验收核对全部现有
候选/来源/proof 残项保持，并逐块重放来源 Git 字节；具体候选另行认领并在
工具合并后冻结新上下文。

02C3 的两项稳定证据由独立工具 [Issue #683](https://github.com/dongyaotalk/stacks-project-zh/issues/683)
声明：axiom-of-choice 改为真实02C3完整 proof 的锁定 Git 证据，
essentially-surjective 改为真实02C3完整 lemma 的锁定 Git 证据。两者都属于
Section0013，ordinal1，按原完整片段 hash 与保护后 source_projection 的准确
词形核验。只改两项 evidence，forms、chapters、其他目录及非数学分类保持；
不批准中文、不改候选或历史。DATA #682 的首轮完整修订发现旧分段证据消失，
失败输出已完整保留且未采用；本前置合并后须重新准备/check、冻结并实际完整
生成，不能把本工具取证当作数据修复完成。全库候选/来源/证明残项和完整译文
事实树保持，仅目录 hash 与两项取证元数据更新；当前 lane render/pdf 零退出
及整书 layout 保持后提交 PR。

0032 的三项稳定来源证据由独立工具
[Issue #688](https://github.com/dongyaotalk/stacks-project-zh/issues/688) 声明。
cofinal、finitely-generated、ordinal 分别保持准确词形 cofinal、finitely generated、
ordinals，均绑定真实0032完整 proof：categories.tex、真实标签
categories-lemma-directed-category-system、Section002Z、ordinal1及锁定 Git 片段 hash。
完整来源的可准备状态先由独立 em 强调声明政策/工具支持；不能跳过未知语法阻断。
保护后 source_projection 必须暴露每个准确词形，finitely generated 不能锁在格式中。
只改这三条 evidence，全部 forms、chapters、其他目录及非数学分类保持；不批准中文。
全库候选/来源/证明残项及事实历史树保持，目录 hash 与三项取证元数据更新。
完整工具回归、库存/check、整书 render/pdf/layout 和真实只读准备通过后工具PR；
具体 DATA 在合并后另开任务、冻结全部新源/旧组并实际完整生成，不能提前采用。

完整 sets 000J/0AHL/04VA 边界工具
[Issue #695](https://github.com/dongyaotalk/stacks-project-zh/issues/695) 在写入目录前
扩展合同：唯一 transfinite-induction evidence 仍依赖将被合并的旧
tag:000J:proof-p001，迁移为既有 locked-source-container 格式，绑定真实
sets-lemma-construct-category 的完整 proof、Section000H、ordinal1 和原 Git
完整片段 hash。完整保护 source_projection 必须有准确词形 transfinite induction。
仅这一条 evidence 改变，forms、chapters、其他目录条目、非数学分类和全部批准
状态保持。先独立工具验收合并，实际 DATA 不临时豁免旧证据消失。目录 hash 与
该词的原生取证元数据可变，全部当前术语/来源/证明 finding、来源库存和事实历史
保持；重新执行完整回归/QA、真实只读包/check、全库库存/对齐及 render/pdf。
