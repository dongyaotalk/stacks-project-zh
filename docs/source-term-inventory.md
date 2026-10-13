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

### 完整 functor of points 的普通标题与正文

独立目录任务 [Issue #771](https://github.com/dongyaotalk/stacks-project-zh/issues/771)
新增英语concept `functor-of-points`，canonical form为`functor of points`，章节
范围为空数组，沿用既有全库扫描。完整来源见证为锁定英文
`a04446e57ec1fbc252a871afcec7752fb2807b14`中的categories、001O、
`categories-example-hom-functor`、真实Section001L、example/1；完整Git片段
SHA-256为`d4ad7cd4198fc4efca8a37de87ca4f537f9e45615f8a3772cd39b28a605ef9ce`。
保护后的自然语言投影包含标题`Functor of points`和命名`functor of points`，
source位置保留该次实际大小写，不按行号、页码或候选内容提供证据。

通用`functor`目录无法证明完整复合词显示，普通标题和正文没有声明包装时，
此前可能只要求`Functor`或`functor`。新增完整词形后，最长短语优先生成完整
要求，嵌套generic word不重复计数；该处不能只写`中文（Functor）`或
`中文（functor）`，完整短语需分别显示原大小写。独立出现的functor仍检查，
重复、缺次、大小写改变、整句代替词条、缺失待决上下文均失败。公式等保护
节点仍不透明，本目录不开放数学内自然语言。

这只登记英文来源要求，未批准任何中文译法。DATA770已保存原十单元模型run/
raw及完整暂存内容；目录独立验收接受后，两个实际模型修订单元各须完整五字段
和新freeze/context/run，不能由程序补长英语或重写旧输出。新增要求的诊断变化
按实际全库审计记录，不能把目录完成当作DATA、S4或S5/S7完成。

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

五项稳定来源证据由独立工具 [Issue #716](https://github.com/dongyaotalk/stacks-project-zh/issues/716) 声明。
DATA715首轮恢复使large旧证据失效，原输出完整保存、未采用；模拟还核实main
原诊断已有四条旧式目录证据失效，额外写入前先更新Issue及本合同。

| 概念 | 精确词形 | 真实owner/Section | 完整容器 |
| --- | --- | --- | --- |
| large | large | 05PY/05PT | proof，lemma-characterize-essentially-constant-ind |
| commutative-diagram | commutative diagrams | 001Y/001U | proof，lemma-composition-representable |
| finite | Finite | 002O/04AS | lemma，lemma-finite-limits-exist |
| nonempty | nonempty | 002T/04AQ | proof，lemma-connected-limit-over-X |
| representable | representable | 001Y/001U | lemma，lemma-composition-representable |

全部selector含categories.tex、完整categories-标签、kind、ordinal1及锁定Git
完整片段hash；保护后source_projection须精确暴露词形。nonempty的旧002O
片段不是当前完整proof见证，改从真实002T完整proof的非空性论证取证，不冒称
002O原文含该词。仅五条evidence改变，forms、chapters、其余目录/非数学分类
与全部规则保持，不批准中文。当前事实/历史tree/范围外字节保持，消除四条
既有目录错误，其他候选/来源/proof finding逐项保持，实际重新测量报告。
相关既有回归/239QA、全库库存/对齐checks、当前lane实际render/pdf及整书比较
通过后独立合并。DATA715前置后重新prepare/check、冻结新目录/context并实际
重新生成17完整五字段，不复用首轮输出冒称新生成。

后续完整容器修订在首次实际输出前核对：拟议来源替换旧组后，旧式目录evidence
的完整source TeX hash仍有当前英文节点见证。若失效，先独立迁移到可准备的
完整锁定Git来源、验收合并，再冻结生成；不得在DATA里改目录或忽略错误。

001R 积（product）相关三项稳定来源证据由独立工具 [Issue #731](https://github.com/dongyaotalk/stacks-project-zh/issues/731) 声明。
完整七批修订前，final-object改为真实001R完整paragraph ordinal2，
product改为真实001R完整section_title ordinal1，universal-property改为
真实001S完整definition ordinal1、Section001R；准确词形分别为final object、
Products、universal property。三项使用既有locked-source-container格式，
从锁定Git完整容器核验真实label/owner/Section、完整原字节hash及保护后
source_projection词形。仅三条evidence改变，forms、chapters、其他目录字段与
非数学分类保持；不批准中文、不改候选或历史。实际DATA必须在此前置合并后
重新prepare/check、冻结全部新源/完整旧组/ancestry及新目录context并实际完整
生成五字段；工具取证不表示术语覆盖、S4或全库门禁完成。

- 独立完整来源证据任务 [Issue#737](https://github.com/dongyaotalk/stacks-project-zh/issues/737)，接受基线`25bc3438a091a016f1002631f9d1a50e9613deda`、英文锁定`a04446e57ec1fbc252a871afcec7752fb2807b14`。
  仅epimorphism/monomorphism的003A完整标题、initial-object的002B完整段落证据
  替换旧source_tex_hash见证；真实owner/Section/selector、词形及原字节hash从Git重验。
  所有forms/chapters及其他目录字段不变，无术语批准或译文采用；后续DATA须重新
  prepare/check、完整冻结所有旧新组/context/ancestry并实际生成全部五字段。

- 独立完整来源证据任务 [Issue#746](https://github.com/dongyaotalk/stacks-project-zh/issues/746)，接受基线`38ee235fcfc0dea2ea7035fd9beb83858f991523`，英文锁定`a04446e57ec1fbc252a871afcec7752fb2807b14`。
  仅image的真实002D完整paragraph/1、coproduct的真实002D完整paragraph/3
  （历史002F:p001）替换旧source_tex_hash见证；真实owner/Section/selector、
  词形及完整原字节hash从锁定Git重验。所有forms/chapters/其余目录字段保持，
  无术语批准或事实采用；后续DATA独立重新冻结并完整实际生成五字段。

- 独立来源证据 [Issue#751](https://github.com/dongyaotalk/stacks-project-zh/issues/751)，接受main `7e36bac385974eb9cfaa4088b8e6500ac17851f8`，英文锁定`a04446e57ec1fbc252a871afcec7752fb2807b14`。仅limit/colimit核验真实002D完整section_title/1，index-category核验真实002G完整remark/1及Section002D，替换旧提取hash见证；全部词形/范围/其他目录字段和非数学分类保持。锁定Git owner/Section/selector/完整边界/blob及fragment字节和暴露词形独立重验；无术语批准、模型生成或事实采用，后续DATA748仍需完整prepare/check/freeze及实际五字段输出。

- 独立来源证据 [Issue #766](https://github.com/dongyaotalk/stacks-project-zh/issues/766)，
  接受main `46081556123ab052e0485147fab85d91c9147da2`，英文锁定
  `a04446e57ec1fbc252a871afcec7752fb2807b14`。仅bijection的一项旧分段hash证据
  改为真实001P完整lemma（categories-lemma-yoneda、Section001L、ordinal1），
  完整片段hash为`sha256:2a5052d951cf1e928456104a391eaabfaf366e9dae4c7b7ae9205d410ed9909a`。
  既有locked-source-container工具从锁定Git重验真实owner/Section/selector、
  完整边界/blob和原片段，并在完整保护后的source_projection中核对准确bijection。
  全部forms/chapters、其他evidence/非数学分类及译法批准状态保持；不改事实或历史。
  完整Section001L六批采用前，必须重新核验所有来源目录evidence仍有效，再冻结
  全部新源/旧组/候选/ancestry和新目录context，实际完整生成五字段。工具取证
  不表示术语覆盖完成或批准中文，全部S4与独立S5/S7仍须完成。

### Section0013 六批完整修订的26项来源见证

独立英文来源目录任务 [Issue #782](https://github.com/dongyaotalk/stacks-project-zh/issues/782)
在接受 main `406fbee71af7da43f165b3aff8d1e95c24d0f075` 上核验真实 Definitions Section0013。
完整六批0014–0019有32旧→8新、563来源词；v10已能核验历史parent的真实双锚点。
完整替换后，26项旧碎片hash不再对应未来活跃单元，因此在DATA前独立更新其
evidence绑定。词形、forms、chapters、非数学分类、中文词表批准和全部事实保持。

锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14`；以下六个完整容器均从该提交的Git blob
重新选择，真实parent为0013，位置依据完整语义selector。完整原字节hash为：

| owner Tag | kind/ordinal | 实际owner label | 完整原片段SHA-256 |
| --- | --- | --- | --- |
| 0014 | definition/1 | `categories-definition-category` | `c35031670d5359a2a292434585b10d23418dfd0943422d0fdb83627c50d70a6f` |
| 0013 | paragraph/2 | `categories-section-definition-categories` | `4bc52ac2b785e320fc653001d06bf6f2462cc468fb5b6eb020252c11066c02c4` |
| 0015 | remark/1 | `categories-remark-big-categories` | `67f8624c8987b067e029d9e39dbd82ed79a8ad52a2cde1960a9e566b5c45b7fe` |
| 0016 | remark/1 | `categories-remark-unique-identity` | `43e395eea3041bf63fa88899e3c87ce6b8baa1bcfabef536b136ab4ceeaed1dd` |
| 0013 | paragraph/3 | `categories-section-definition-categories` | `d580537d8c54ae721e787754f200795d7df265e4af11d45c22570ba950850ee1` |
| 0019 | example/1 | `categories-example-group-groupoid` | `50d7f6d49667f153c2560dbdb569f431ad8895ec83f586c4fc67649cd6401b9d` |

每项精确旧词形须在完整保护后的source_projection中实际存在且属于原forms；
数学、引用、comment/literal等保护节点仍不透明。原旧绑定留在Git历史，完整
旧unit/candidate及run/raw、恢复/归档历史保持；不修改候选来提供目录证据。

| concept | 原精确词形 | 原旧unit定位 | 原完整TeX hash | 新完整owner/kind/ordinal |
| --- | --- | --- | --- | --- |
| `abelian` | `abelian` | `tag:0015:item002` | `e65532c7850b3215f9093fe1498bdfad50fd696d8a3268ec3ba0d3970ffc7215` | 0015/remark/1 |
| `abelian-group` | `abelian groups` | `tag:0015:item002` | `e65532c7850b3215f9093fe1498bdfad50fd696d8a3268ec3ba0d3970ffc7215` | 0015/remark/1 |
| `algebra` | `Algebra` | `tag:0015:item008` | `ddfcf0f1df3b2132dd8d98c44e587aaaea9b12c3b3f01165a60a8e470d8920f2` | 0015/remark/1 |
| `associative` | `associative` | `tag:0014:item005` | `a8a2f3a24cff658882a6435f563b0ef9614924a9a24b9178da92a5a04513cd04` | 0014/definition/1 |
| `composition` | `composition` | `tag:0014:item003` | `28ce086dd782a056fbe025b998fee93d25e02a38fa88548b09a426b3874fcd32` | 0014/definition/1 |
| `element` | `element` | `tag:0014:item004` | `52beb10bf31be3f68d45f72804a366b45a5cb8f3cabca1cdaadf06b79ddbe890` | 0014/definition/1 |
| `equivalent` | `equivalent` | `tag:0014:p002` | `c52bc33deafddc56f852fbc50595b2999663cca1c02e0070d84de802f519d341` | 0013/paragraph/2 |
| `field` | `field` | `tag:0015:item006` | `7a74a82eb0cc0588596282dae291225fc22ac561cbfd9b2644b7dbc122dfe5ec` | 0015/remark/1 |
| `functor` | `functors` | `tag:0015:item015` | `54368b4e41403784f12d373607272267e0dd8c03c64f378dc06c1dbb9a26abfb` | 0015/remark/1 |
| `group` | `groups` | `tag:0015:item002` | `e65532c7850b3215f9093fe1498bdfad50fd696d8a3268ec3ba0d3970ffc7215` | 0015/remark/1 |
| `groupoid` | `groupoid` | `tag:0019:statement` | `10d9a73c4c1a015b8aa544d674e0732b80141b18b3daa30c6351505863aba359` | 0019/example/1 |
| `identity-morphism` | `identity morphism` | `tag:0016:statement` | `40f6d112a7cc3b5449a32c6b1da04a5132f48d3e42d379f67c7cda7b500acdfd` | 0016/remark/1 |
| `invertible` | `invertible` | `tag:0017:p001` | `af146d9fab8f1c790b05486ca5cf22c58f4185620a008d1bc3918b75ba038ab9` | 0013/paragraph/3 |
| `isomorphism` | `isomorphism` | `tag:0017:p001` | `af146d9fab8f1c790b05486ca5cf22c58f4185620a008d1bc3918b75ba038ab9` | 0013/paragraph/3 |
| `map` | `map` | `tag:0014:item003` | `28ce086dd782a056fbe025b998fee93d25e02a38fa88548b09a426b3874fcd32` | 0014/definition/1 |
| `morphism` | `morphisms` | `tag:0014:item002` | `0a10d96c2604935aaad29e92d96429a3701b02d3f9c1978881f9f027776bdf81` | 0014/definition/1 |
| `object` | `objects` | `tag:0014:item001` | `392b612edbe2863631407e7bc0089f01a72f797e68d2e3942ea734b1dbd61aa9` | 0014/definition/1 |
| `presheaf` | `presheaves` | `tag:0015:item011` | `457a3515907c3d1bd111b1a16f99e19edf8ca9c821133c05007607247f415200` | 0015/remark/1 |
| `ring` | `ring` | `tag:0015:item005` | `b1578bf82e1c8e3747abd4f5a44fbbca8006db2e330a4f42098780afb1010215` | 0015/remark/1 |
| `scheme` | `schemes` | `tag:0015:item009` | `3021c53888a5c08d2e928fc24cdf04598bcbe50115768a56ff6a4355f89e87bb` | 0015/remark/1 |
| `set` | `set` | `tag:0014:item001` | `392b612edbe2863631407e7bc0089f01a72f797e68d2e3942ea734b1dbd61aa9` | 0014/definition/1 |
| `sheaf` | `sheaves` | `tag:0015:item012` | `2c41888064ea5f477052c4c67f11f51ce663ac8ddf30d0151c6783afc2d549db` | 0015/remark/1 |
| `site` | `site` | `tag:0015:item017` | `0aa91f5497c4c3f7d3be24815791faa553dd5fb9a1a8192ec5c228c17227c85c` | 0015/remark/1 |
| `small` | `small` | `tag:0015:item015` | `54368b4e41403784f12d373607272267e0dd8c03c64f378dc06c1dbb9a26abfb` | 0015/remark/1 |
| `topological-space` | `topological spaces` | `tag:0015:item010` | `5eb4d8ccbd3b734027f5a54effbfbfc4de3463db36e51a27f39e3efa7054d9a4` | 0015/remark/1 |
| `vector-space` | `vector spaces` | `tag:0015:item006` | `7a74a82eb0cc0588596282dae291225fc22ac561cbfd9b2644b7dbc122dfe5ec` | 0015/remark/1 |

只替换这26处原evidence索引，其余条目及根字段原语义保持。只读已核验全部
当前1272英文单元与未来8完整输入的source_inventory逐项相等，变化仅catalog_hash；
未来完整来源集合的全部目录证据也有效。当前术语覆盖诊断和修复队列仍需真实
DATA处理，目录接受不批准任何中文译法、critic、人审或出版，也不启用S5。

后续维护：完整容器重提取前先按未来全来源集合验证每项目录证据；失效旧碎片
须独立认领来源见证任务，从锁定Git重验真实归属/边界/原字节/保护后的精确词形，
保持forms/chapters及分类，不在DATA里顺手放行。目录接受后，DATA重新冻结该次
真实目录、所有政策/旧组/全部候选/ancestry/context及新输入，再由当时实际模型
完整生成每个新单元五字段。未知词保持待决，DATA后独立progress/plan；全部
S4完成后才独立S5强门禁与S7集成。来源见证有效不能代替当前候选逐次覆盖验收。

### 完整函子范围001B–001I的12项来源见证

独立来源目录任务 [Issue #790](https://github.com/dongyaotalk/stacks-project-zh/issues/790)
以接受main `a8bba4eb775afc531920f6747d29970850f30efc` 为基线。PR789的v11已接受，完整八批
27旧→12新/575词从锁定Git和所有有序旧组重新核验，零BLOCKED；完整001I的
前段使用原v6，p002/p003完整链使用独立v11。目录任务只替换以下12处原evidence
索引，不变更forms/chapters/词形/非数学分类/中文批准或任何事实、run与历史。

英文锁定`a04446e57ec1fbc252a871afcec7752fb2807b14`。六个完整Git容器真实parent均为0013；
原片段从真实owner label、kind/ordinal选取，字节位置只用于边界核验：

| owner Tag | kind/ordinal | 实际owner label | 完整原片段SHA-256 |
| --- | --- | --- | --- |
| 001C | definition/1 | `categories-definition-faithful` | `ed7b96856d6a9233e4ed126c39fed76a1571c3043e467aafe9a1c605cf43b477` |
| 001D | definition/1 | `categories-definition-subcategory` | `283fffbc18571586503ce936b0990ebc1f5f0a316d36a39c2a7d993cbef48f57` |
| 0013 | paragraph/5 | `categories-section-definition-categories` | `aa6994bf614df1a05213ede743d8218931836c89904064756385a031bdf411c2` |
| 001F | example/1 | `categories-example-group-homomorphism-functor` | `f98ac2339eb11545b4ca80fdc8fdab070705b99681d5741845f57f005d95834a` |
| 001G | example/1 | `categories-example-category-over-X` | `9a33bf70b81ec79911a7ad97a20802b8740e8c3982b1314e1b68833a49c86626` |
| 001I | definition/1 | `categories-definition-transformation-functors` | `3e368f55ede1495d627857287d14cba74a860edbaa8145509352af96a24b0065` |

每项原精确词形必须实际出现在完整保护后的source_projection且属于原forms；
保护的数学、引用、注释和literal不提供暴露词形。原旧证据和完整unit/candidate/
run/raw/恢复/归档历史原字节保留，不能通过修改候选获得目录证据。

| concept | 原精确词形 | 原旧unit | 原source TeX SHA-256 | 新完整owner/kind/ordinal |
| --- | --- | --- | --- | --- |
| `bijective` | `bijective` | `tag:001C:item002` | `381f102f3b4b7d527715979727240fc3cb4b273df20c99194d5db606e195050e` | 001C/definition/1 |
| `commutative` | `commutative` | `tag:001I:item002` | `37610236bd507ecef1b28fcdd69a1443fb59a9957589a54a8f0fb48f84bc1c59` | 001I/definition/1 |
| `commutes` | `commute` | `tag:001G:p001` | `fd7aef8c35b12f0fc76069625f575bfeaa4fb2369199691b824636e81c31fb5f` | 001G/example/1 |
| `diagram` | `diagram` | `tag:001G:p001` | `fd7aef8c35b12f0fc76069625f575bfeaa4fb2369199691b824636e81c31fb5f` | 001G/example/1 |
| `faithful` | `faithful` | `tag:001D:p003` | `febf69399c91abaa1b5f78c5a02b68e6a7cf43b2c3560c62f04baefa5dba8114` | 0013/paragraph/5 |
| `full-subcategory` | `full subcategory` | `tag:001D:p002` | `efdb6df76edc4d6a2fedd00eb45fce359a33a007b738a8788a5acae393d212ff` | 001D/definition/1 |
| `fully-faithful` | `fully faithful` | `tag:001D:p003` | `febf69399c91abaa1b5f78c5a02b68e6a7cf43b2c3560c62f04baefa5dba8114` | 0013/paragraph/5 |
| `homomorphism` | `homomorphism` | `tag:001F:statement` | `f6d870f0079539ca004899336ef2edd0d998ac9dff9e838ad1ec7cb870146748` | 001F/example/1 |
| `injective` | `injective` | `tag:001C:item001` | `5f2e2dd713fdcd031535a9a6c88bc4531ee3f5058318e65e1bce326739d962f5` | 001C/definition/1 |
| `isomorphic` | `isomorphic` | `tag:001C:item003` | `ce428892a92235d79138dae2be8f795765c6f4c8fae4613235b8ce5a524d81a6` | 001C/definition/1 |
| `subcategories` | `subcategory` | `tag:001D:p002` | `efdb6df76edc4d6a2fedd00eb45fce359a33a007b738a8788a5acae393d212ff` | 001D/definition/1 |
| `subset` | `subsets` | `tag:001D:statement` | `99a6271f48fdf5ccc87721d21fe0d362ea29bca5dc0878e23290cce4a5300133` | 001D/definition/1 |

已只读核验当前1248及未来1233的完整来源库存，变化仅catalog_hash；未来全来源
集合的全部目录证据均有效。全部旧新分组与当前候选术语覆盖仍由后续独立DATA
负责，目录接受不减少当前122问题batch/560术语候选1813诊断，也不启用S5或
授予任何术语、critic、人审、发布批准。零来源审计错误不免除队列中保留的
VERIFY_OR_RESTORE_SOURCE行动。

后续完整八批DATA须重新prepare/check、生成前冻结全部新unit、每个完整旧组和
所有候选/ancestry、政策/风格/词表/prompt/本次目录/context；动态解析Harness和
真实运行model/effort/turn，实际模型完整输出每个新unit的五字段。程序只保护、
序列化、验证和装配；raw逐项相等、token原序/次数/尾空白及全部历史绑定保持。
DATA合并后独立progress/plan；全部S4完成后才独立S5默认强门禁和S7全库验收。
