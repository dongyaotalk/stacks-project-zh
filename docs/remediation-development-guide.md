# 八项审查修复开发与交接指南

> 2026-10-14 用户最新执行指示：利用全库抽取与统一修复队列，集中完成全部剩余修复，取消逐批 Issue/PR 及重复整书验收。复用 claimed Issue #808、分支 `docs/progress-categories-cofinal-initial` 和草稿 PR #809，最终以一个 PR 验收全部 F1–F8（S4 → S5 → S7）。原文中的“下一批前独立进度 PR”“工具必须先单独合并”等是保留的旧执行记录，不再作为本次集中任务的步骤。各类改动保留可审查的逻辑提交，开发期按影响范围检查，最终集中执行完整门禁和 render/pdf、全书文字与全部变化及邻页 PNG 验收。范围变更仍先更新同一 Issue 的精确路径/完整新旧 ID/run/model；未知来源继续 BLOCKED，原输入、raw、历史、保护结构及真实模型生成要求保持。

> 工具前置 [Issue #810](https://github.com/dongyaotalk/stacks-project-zh/issues/810) / [PR #811](https://github.com/dongyaotalk/stacks-project-zh/pull/811) 已完成并合并，接受 main 为 `5b527d9cf753ba3f589d1cc7fe9d18be31ddfd81`。完整来源恢复、组合数学文字和哈希范围清单合同已接受；原工具提交与文档历史保留，不重做此前置。后续 DATA 的 origin 使用该已接受提交，英文锁不变；现有 Issue #808 / PR #809 统一收尾全部 DATA、S5、S7和最终文档。

本文是开发方法和交接材料；事实状态必须从当前分支的结构化数据、审计与 GitHub
重新读取。它不代替 `WORKFLOW.md`、`config/` 政策或不可变溯源证据。

## 当前集中任务：2026-10-19，本地验收通过，待精确远端验收

本节是最新状态；以下带日期的阶段记录保留原有证据，不代表当前仍在运行。
远端 main 于本日重新核实为 `5b527d9cf753ba3f589d1cc7fe9d18be31ddfd81`；
Issue808 仍由 dongyaotalk 认领，PR809 仍 OPEN/DRAFT、仅 closing Issue808。
本地分支及 HEAD 未换，全部修改尚未提交或合并。main 的事实仍为239批/1208单元。

本地已完成165批、1049旧→683完整新单元、172个新实际 revision run，全库为
239批/842唯一活跃单元。旧输入、原候选、run/raw 和完整递归恢复/派生/归档保留；
五字段逐项等于实际不可变原输出，范围外事实原字节保持。此前162批/677单元的
第三次完整 `qa-all` 已终态通过，实测1564.582秒；该证据不冒称覆盖后来的6个新单元。

严格尾空白门禁试运行另外发现 categories-002T、categories-04AR、sets-000I 三个
完整批次共6单元。每批完整冻结旧组、候选、历史和上下文后，实际模型重新生成全部
五字段，未用程序补换行。新生成保持原英文单元不变，220来源词的短批次例外明确
记录，不填充无关文本。冻结包含56份 ancestry；生成输入为当时v16目录，后续目录
不能回写为当时的模型输入。最新字面输出核验包含286份尝试文件、93份完整记录
装配、844条实际完整记录（含失败/重试，不能当作活跃数）。

当前精确范围清单为 `task-scopes/integrated-remediation-f1-f8-20261015.json`，
2591条精确路径，hash
`sha256:b65670ce591f2cb8cfe64199c161281d928236675221d52512e594a1a923aea6`。
此前所有scope原字节保存；既有实际生成仍绑定各自原冻结。远端Issue/PR的最终
精确范围更新按授权在本地验收后统一完成。

当前英文目录v18的hash为
`sha256:4223840c7e8259e889e2c5b45adc3c848f322c2e3704df70ccf94534491943fe`。
对全842单元识别6507次来源出现，688份锁定Git见证。新词形 affines 和原文拼法
glueing 逐字来自 sets / 000I / Section000H / proof1；完整片段hash为
`772cb19314e31636609b48c640216f70eef18c794fca53b6ba4ee4aa592223b5`。
仅扩展英文识别，不批准中文、不改历史输入。当前239批严格来源/结构/术语探测
零错误，实测上下文10.103秒、验证47.369秒，共57.473秒；此探测不包含全历史溯源。

### S5 已实现的默认路径

`current_qa.py` 独立约束当前候选，历史事实仍按各自版本合同重放。
validate、validate-many、validate-all、assemble、assemble-many、render 默认核验
锁定Git来源、永久Tag、未保护TeX、展开脚注/命名标题、英文目录证据、逐次术语覆盖、
保护token原序/次数及精确尾空白。装配与渲染先拒绝不合格输入，再调用写出函数；
这些检查不产生中文、selection或人工批准。工作流的九项当前门禁必须全部开启。

`repository_validation.py` 在一个进程内依次执行完整Schema、完整递归溯源、决策绑定
和全部当前候选检查。`InputSnapshot` 绑定实际HEAD、文件集合及原字节，期间新增、
删除、篡改或符号链接导致失败。仅同次调用里实际完整溯源通过后才发出私有内存
凭证；决策检查据此避免重复递归重放。独立 `decision-check` 仍执行完整溯源，
不存在磁盘PASS缓存、skip开关或持久凭证。只为真实selection引用的候选计算昂贵的
复合绑定hash，但所有未被选择的历史事实仍经过完整溯源验证。

锁定英文容器、数学重复计数和正则编译仅作同次调用内的纯计算复用。来源库存
必须从锁定Git重新验证实际使用章节，过期或篡改库存失败；缺失库存首次完整生成。
`make qa-all` 与CI调用同一 `check-repository` 入口，完整检查没有删减，也不按
changed paths漏掉其他lane。CI与本地统一Python3.12。开发时仍可选章预览，最终
验收保留整库QA与整书构建。

截至本检查点，原34项定点回归通过，覆盖六个CLI实际拒绝、关闭政策/篡改库存绕过、
来源词漏报、伪CLEAR、保护顺序/尾空白、输入竞态、伪会话凭证和独立决策溯源。
新的统一 `make qa-all` 已完整退出0，实测989.962秒，Schema、完整递归溯源、
决策及239批当前严格QA全部通过，受观察输入hash在调用期间保持不变。完整工具
测试实际执行653项，651通过、2个旧CLI fixture失败；原失败日志保留。成功样例已
换为独立锁定Git的两个完整来源节点，配对错误测试隔离来源门禁以保留原有计数
断言；没有降低生产门禁。随后对CLI、当前QA、会话、决策、全lane聚合41项回归
全部通过。其余651项的生产实现和用例保持，最终远端精确HEAD仍须真实运行全套。
S7构建/视觉及远端验收未完成，F1–F8总goal保持进行中。

此次仅为适配旧测试增加 `tests/test_cli.py` 和此前scope的原字节快照，精确范围
2591路径。既有模型冻结不重新绑定当前scope。CI时限为60分钟，以容纳实际完整
工具测试和统一QA，检查项目不减少；Python3.12和单进程默认门禁保持。

本次全部172个实际新revision run的完整冻结输入已另行结构QA通过：683条完整
记录，与每份correction中声明的unit/candidate原字节hash一致，实测29.382秒。
此证据覆盖实际新作者输出，不只检查兼容lane；版本化历史、原输出绑定和完整
递归溯源仍由统一验收负责。最新实际 `progress`、`progress-check`、`plan`、
`plan-check` 均退出0；另在隔离目录真实生成并check全部117章，README及两份
报告逐字等于规范输出。没有手改统计数字，也没有授予人工审校或发布状态。

### F1–F8 当前证据矩阵

| 项目 | 本地最终直接证据 | 远端剩余验证 |
| --- | --- | --- |
| F1 永久坐标 | 原六批44个数学陈述及842个活跃单元核验；全库对齐/check通过，零错坐标、零重复ID。 | 精确远端文件与合并后原字节。 |
| F2 来源术语 | 独立6507次要求/688份Git见证零错误；完整239批统一QA通过；六入口漏报回归通过。 | 最新精确HEAD完整CI；不授予词表批准。 |
| F3 决策门禁 | 正反决策回归及完整全库决策通过，独立命令仍重放完整溯源。 | 最新精确HEAD CI。 |
| F4 结构与来源 | 683新五字段/raw相等；172新run QA、完整历史、独立source/proof及最终render通过。 | 远端全部原字节与历史绑定。 |
| F5 替换链 | 正常链及自引用/循环/跨unit/冲突后继回归通过；完整全库决策通过。 | 最新精确HEAD完整工具测试。 |
| F6 脚注引用 | 两目标脚注实际PDF及邻页已查看，链接注释均指向注记4.2.2；最终引用日志通过。 | 合并后数据原字节。 |
| F7 字体构建 | render/pdf/template均退出0，457页/13页FinalTeX通过；全部变化及邻页实际查看。 | 远端树与已验收树一致。 |
| F8 进度计划 | progress/check、plan/check及隔离117章生成/check通过；三报告原字节不变。 | 合并后报告与最终事实一致。 |

最终全库抽取与check现均通过（72.585/72.889秒），117章、116份Git原字节回放，
43223提议中38422 READY/4801 BLOCKED、12491来源诊断。该库存是全英文准备状态；
未知语法/数学文字保持BLOCKED，不等于当前842单元失败，也不表示全英文已经翻译。
本次最终输出使用独立ignored目录，保留前次库存；完整对齐与check继续读取最新事实。

最终对齐生成已完成，实测99.414秒；239批/842单元中745 BYTE_EXACT、97
PRESENTATION_EQUIVALENT，零坐标迁移、来源错误、术语候选失败/诊断和proof不匹配。
独立术语审计6507次要求、688份锁定目录见证全部通过；独立来源审计错statement
Tag、未保护TeX、隐藏脚注、隐藏标题均为0；proof审计187组/187单元全部match，
unsupported为0。239条统一队列的四类actions/findings均为空。对齐check已退出0，实测102.135秒；最终抽取/对齐四个命令全部通过。
审计中的目录hash按规范JSON计算为
`sha256:899a668e50f3487b37dd8781e9b5a88e3e16d272ad91b4078ac6b9d847935c12`，
与上文文件原字节hash的表示方法不同，所指目录相同；复核时不能混用两种hash。

### 定位失败与后续维护

| 失败位置 | 处理方法与边界 |
| --- | --- |
| 当前来源/Tag/保护节点 | 从英文锁定Git重选完整容器，核对真实owner、Section及selector；未知语法继续BLOCKED，不能放宽规则让错误通过。 |
| 来源目录证据 | 核实整份原片段与hash、可见英文词形和分类；分段变化先迁移英文见证，不能删词或从译文数组反推来源。 |
| 候选逐次术语/尾空白 | 对声明的完整语义批次冻结全部旧输入和历史，重新实际生成完整五字段；程序不补中文或拼接旧句。 |
| 历史run/raw/派生重放 | 保留失败原字节；按对应版本合同定位。当前门禁不能重解释旧context，缓存、改hash或删归档不能替代重放。 |
| selection/revision | 保持真实待决词对与glossary批准、人审和复合来源hash要求；模型无权把CLEAR写成批准。 |
| TeX/PDF | 修复结构化事实、渲染器或已声明模板的真实原因，再构建；生成TeX和PDF仅作证据，不直接修生成物。 |
| 进度/计划 | 实际调用生成器和check；在隔离目录逐字比较，再采用生成结果，不手填数字。 |

维护时先按受影响完整batch或章节定位；代码、政策、来源或事实输入未变的成功
结果不无理由重跑。最终使用统一 `make qa-all` 完整验收，来源清单与队列另行
重建/check，整书按规定render/pdf并查看全部变化及邻页。私有会话凭证不跨调用
保存；新run必须重新动态解析Harness和当前实际model/effort/turn，不复制本次身份。

### S7 本地最终构建与视觉证据

当前lane真实render退出0，1215.720秒，119份TeX中仅声明的九章及metadata改变。
真实pdf退出0，69.975秒，457页；适用template退出0，16.217秒，13页；两个最终
TeX日志门禁均通过，无缺字、未定义引用或编译错误。首次沙箱PDF构建未能访问
本机已安装的Noto CJK字体，失败日志保留；访问本机字体服务重试同一Make命令
成功，未修改模板、译文、生成TeX、字体配置或日志来绕过错误。

整书当前PDF原字节SHA-256为
`15679221ebf8616cfbb726f661b493593662216375da4c780bb57711490e3b15`，
模板为`722d8d127019efd8a9dafcf0e79a571a888de8724350f2b4f9b3fca29421e709`。
接受基线为此前实际查看过的463页PDF，原字节hash为
`eb5566d1906e989dc97ea867e6aa8dd0a66049dbad4e75a5762266957071cc5b`。

已比较全部书页文字及119份TeX，并实际查看新版237页变化及邻页PNG（119组
双页图）。另外查看目录第7/8页、书末第457页，合计240个不同新版页；两处脚注
另作原分辨率检查。其余220个原未入选页与已查看基线的正文文字、字体、坐标及
矢量绘图逐页等同（排除页眉页码区域，坐标精度0.001pt，且没有栅格图）；其中
三页又已实际查看，因此剩余217页复用明确绑定的既有视觉证据。没有用缩略抽样
替代变化及邻页检查。模板全部13页实际查看，包括正文常规、粗体、斜体Greek
字符及公式、矩阵、交换图和书末表，字形正常；全书文字边界检查无越出纸面的行。

F6的`tag:0AHN:statement`与`tag:0FWX:statement`分别排在当前PDF第88/90页，
脚注均为中文，相关页及邻页实际查看；同时读取PDF实际链接注释，目标为PDF第44页
的注记4.2.2，对应aux标签`categories-remark-big-categories`，原引用payload保持。
书末原文疑点表仍位于最后，明确锁定英文版本及691/698/699留档，不修改原数学。
这些PDF页仅是验收定位，任务范围始终用永久Tag及完整来源容器。

本地通过的生产代码、政策与事实在统一QA之后保持原字节；随后只适配两个旧CLI
测试fixture、扩大声明测试路径、调整CI时限和补文档。完整工具测试的原失败和
后续41项成功均如实保留，远端最新精确HEAD必须再真实执行完整工具测试和全部QA。
当前尚未提交/推送这份集中数据，远端基线main仍为5b527d9；最终推送、完整远端
原字节/patch/native合同、双CI run/job以及授权squash与合并后验证是剩余步骤。
最终接受main及精确门禁证据通过PR809和下列命令取得，不猜测尚未产生的合并SHA。

```sh
git ls-remote origin refs/heads/main
gh pr view 809 --json state,mergeCommit,headRefOid,baseRefOid,closingIssuesReferences
gh issue view 808 --json state,assignees,labels
gh pr checks 809
```

完整原字节、来源/历史绑定均由跟踪的unit、candidate、run/raw、derivation/archive
和restoration记录提供；本机ignored回执、PDF和PNG只是额外现场证据，不提交。
新克隆按本文命令重新生成并验收，不依赖本机绝对路径、缓存PASS或预先存在的build。

## 历史阶段记录：2026-10-16，本地装配后待完整验收

继续使用 claimed Issue808、草稿PR809及原分支。最新只读核验的远端main为
`5b527d9cf753ba3f589d1cc7fe9d18be31ddfd81`，已包含前置PR811；本地HEAD为
`3af29b005b648a0f4ceaf04d366712323f340488`。原文档提交、所有已合并数据和历史保留。
远端main仍为239批/1208活跃unit。本地已装配162批/1043旧→677完整新单元，
全库239批/842个唯一活跃unit；尚未提交或合并，完整递归溯源及S4全量验收正在进行，
不能把本地提议或审计成功当作main残项已经清零。

原定107批的849旧→483完整来源新单元已经全部取得实际模型五字段。
在新英文来源词目录v12下，全483单元来源术语检查为0问题单元/0诊断。
其中55个单元完成了术语或可移植上下文的完整重生成；失败尝试、旧冻结和
实际模型身份保留。实际会话字面输出绑定检查通过：200个原始尝试文件、
79个完整记录选择装配文件、624条实际完整记录，包含保留的失败与重试，
不能将624当作当前活跃unit数。所有最新选择记录的非覆盖类核心检查无错误；
未变记录复用绑定原字节hash的检查，新记录单独复核，并非新跑了一次239全量QA。

目录扩展后，对原范围外359单元的独立检查还发现55批/73问题单元/109诊断。
完整范围为Categories45批、Sets10批，共194个当前单元，不能只改73个标记单元。
55批完整来源预检已通过：194旧→194新、11698来源词、0 BLOCKED。
与原483提议及范围外数据合并预检后为842个唯一活跃ID，无冲突。
52份v4及3份v2当前历史均须保留并重放；这些是新目录下的追加术语修订，
不重复宣称原0AHK等完整来源恢复尚未完成。

追加范围已在本地精确声明：同一owner/branch/英文lock，合计1043旧/677新ID，
2536条精确允许路径，范围清单hash
`sha256:77fabf3a694ac0d4925c59f780d179e049cc729ba6dc6d3c9b1eba417ec9fa7a`。
旧清单原字节保存为`task-scopes/integrated-remediation-f1-f8-20261015-scope-before-extra-v12.json`；
此前全部实际生成继续绑定原冻结，不回写其模型、run或上下文。
追加55批计划使用当时实际可见的`gpt-6.1-sol/xhigh`，每次生成前仍动态核验真实
model/effort/turn及Harness，运行前的计划值不充当生成证据。

未来英文目录v14仅将4条现有见证重新绑定到独立锁定Git完整片段及新坐标，
hash为`sha256:d5a8e729960fec8dfee0473991cf09f094c74977a9c3729aaed568798b102671`。
全部词形、分类、章节范围及其他见证保持；实际逐条比较4个受影响库存，
未对677个匹配输入未变的提议重新进行全量术语扫描。没有中文词条批准。

追加55批的完整来源包已统一prepare/check通过：prepare 610.175秒、check 590.350秒；
完整194组、全库ID与来源区间不重叠，check期间包的字节及mtime不变，回传副本原字节
一致。原107批的已通过包未重跑。追加194新单元、完整有序旧组/候选、832份ancestry、
政策/词表/风格/prompt/来源目录及hash已全部冻结，冻结回执hash为
`sha256:db6af97e1eadf76f02745a5ec005ae0ede88efb962ab82ec954ef08ca2a5e897`。

追加55批/194完整单元已全部取得实际模型五字段，与原483单元合计677/677，
不再有未生成单元。最新实际字面绑定核验为283份原始尝试文件、93份完整记录选择
装配、838条实际完整记录，包含保留的失败与重试，不能当作活跃unit数。全部新记录
结构、token顺序/次数、尾空白、完整五字段和实际冻结上下文绑定均无非覆盖类错误；
旧检查绑定原文件hash复用，未重复运行未变239全量QA。

未来英文目录v15对9个完整词形增加独立锁定Git见证，涉及8个完整来源容器、7个
新concept；原词形、证据、排除项全部保留。目录hash为
`sha256:2b41a8f200779fb996a47a6c673b7296e316b1266ba05b03ba64903bfe633fe1`。
除前述词形外还覆盖`categorically compact object(s)`与`transition morphisms`。
完整新目录下实测677个提议单元及165个范围外单元，共842个单元、6502次来源出现，
均为0问题单元/0诊断。该结果只证明所声明来源清单的覆盖，不构成人工数学审校。
原v14的13问题单元/14诊断历史回执保留，不回写实际生成冻结或把新目录冒称生成输入。

已事务化装配2338个声明范围内文件，共162批、169个实际revision run；完整旧输入及
52份v4、3份v2追加历史和原范围全部祖先保留。所有新run/raw的结构QA通过，全部
677个新候选五字段逐项等于不可变实际原输出，全库842个ID唯一，范围外事实原字节
不变。首次qa-all在三个章节挂载清单过期处停止，已经生成器刷新全部117模板，仅
categories、sets、guide三个文件改变。随后重新执行完整qa-all，尚未宣称最终通过。

生成时Harness版本和装配时动态解析版本分别记录；不以后来安装版本覆盖生成记录。
新run的置信度标签遵从冻结注册表的declared，真实model/turn/effort逐单元保留，
snapshot未暴露且不猜测。身份标签规范化只涉及尚未提交的新run/raw/绑定hash，
全部五字段、context、历史和当前活跃候选内容保持；初始装配原字节及回执另存。

正式装配后的独立v16完整术语审计已通过，实测178.847秒：239批/842单元、6502次
来源术语出现、0问题候选/0诊断，686条锁定Git目录见证全部通过。此次结果包括完整
目录证据及范围外候选，不只检查译文自报数组。8条旧003G证据已重新绑定完整003J
和003N容器，目录hash见来源清单文档；没有改变匹配词形或任何实际生成输入。
来源结构审计零坐标/未保护TeX/隐藏脚注/命名标题问题；187组/187完整proof全部match。
这些检查不重跑，除非相应输入或工具改变。完整qa-all/递归溯源仍须取得终态结果。

此次完整重生成还观察到以下来源记号疑点，仅在本开发文档作为 source-only remark
留档，不改译文、公式或证明，也不独立阻塞忠实候选。英文版本仍为锁定提交
`a04446e57ec1fbc252a871afcec7752fb2807b14`；均逐字核对该提交的完整 Git 容器。

| 完整语义容器 | 原文观察，均待数学核验 | 完整片段 SHA-256 |
| --- | --- | --- |
| categories / 0FWY / Section0FWW / proof1 / categories-lemma-extend-functor-by-colim | `Y = \colim_{j \in J} Y_i` 同时使用 j 与 i；后文 `F(\alpha) : F(X) = \colim F(X_i) \to F(Y)` 与延拓构造中的记号也值得核对。这里只记录字样，不判定结论错误。 | 06495b33551549f438a6b16775ef79a719abac9e70676849f488e751e0d94b61 |
| categories / 02XR / Section02XJ / proof1 / categories-lemma-cute | `p'(\psi') : W/U \to V/U` 的目标与此前带撇号的记号可能不一致，留待核验；候选原样保留。 | 96a3035aa9363cac17fd1f519740fae27b03f71a1c4a82bc7ebf0dc18bf5547c |

既有691/698/699仍由版本化书末表留档；上述新增观察没有冒充上游勘误确认、
模型数学审校或新正文说明。

完整全库抽取及对齐已重新生成并check通过：extract-all 62.704秒、check 52.776秒；
source-alignment 188.066秒、check 198.885秒。当前842个单元中745 BYTE_EXACT、
97 PRESENTATION_EQUIVALENT；本次677新单元有668字节相等，另外9个是各章标题的
既有原生标题／渲染包装投影，仍受来源与溯源合同约束，不是检查豁免。239条统一队列
的actions、source_findings、term_findings、proof_findings全部为空；零坐标、来源、
术语和proof诊断。全英文库存43223提议/38422 READY/4801 BLOCKED，117章、116次Git
roundtrip、12491诊断；这是来源准备库存，不是所有英文已经翻译或采用的声明。

第二次完整qa-all在631.709秒后发现三个章末来源恢复记录错误标记v2，拒绝原文正文
之外的input。已修复准备器的版本选择，并为完整章末正文补齐v13原生边界见证；
原宏拒绝保持，旧v2不被重新解释。三个完整批次定点重放与输出原字节相等，全部
五字段和上下文/runtime不变。原错误准备记录逐字保存在跟踪证据文档，原冻结/包
及失败日志保留；详细合同见来源恢复设计的2026-10-16节。15项原生边界回归通过，
另103项source-container/v4分组/archives/pre-adoption/model-correction历史回归在
291.370秒通过。第三次完整qa-all的完整递归溯源已通过；继续同一命令的决策及239批候选检查，
尚未取得整体终态，不能把前两次失败写成通过。

当前精确范围扩为2538条路径，仅增加原清单快照和原始准备记录留档；所有旧新ID、
run/model及实际生成冻结保持。新范围清单hash为
`sha256:3c085f4bd772ad256efda0acbe65e7b8ba3dcb767b125d346b67d6cf00029035`。
实际生成仍绑定当时的77fabf3等原scope，不回写为新清单hash。

只有全部S4装配及验收通过后，才独立实现
S5默认强门禁并完成S7、真实render/pdf、全书文字/变化及邻页PNG和远端精确HEAD验收。
仍使用同一个最终PR，不逐批新开Issue/PR。远端Issue/PR最终精确范围更新尚待本地完成。

ignored证据目录`build/task-integrated-remediation/`中的`generation-checkpoint.json`、
`current-v13-source-coverage.json`、`actual-draft-authorship.json`、
`extra-v12-full-preflight.json`、`extra-v12-complete-source-plans-index.json`、
`scope-extra-v14-install-receipt.json`、`catalog-v14-extra-witness-receipt.json`、
`extra-v12-complete-package-preparation.json`、`extra-v14-generation-checkpoint-194.json`及
`catalog-v15-complete-witness-receipt.json`、`canonical-assembly-readiness.json`、
`canonical-data-install-receipt.json`、`new-run-registry-metadata-normalization.json`
保存可复核输入hash、实际原输出及追加范围。最终交付仍须把必要证据和复现命令
写入跟踪文档与事实溯源；不能要求新克隆依赖本机ignored文件。S5、S7及总goal未完成。

## 历史阶段记录：首次集中来源准备（未采用 DATA）

用户最新指示要求集中修复，已复用 [Issue #808](https://github.com/dongyaotalk/stacks-project-zh/issues/808)
及 [草稿 PR #809](https://github.com/dongyaotalk/stacks-project-zh/pull/809)。分支仍为
`docs/progress-categories-cofinal-initial`，已有文档 commit `466e24da0112d3bb40126c1c26183df8f6ac7e10`；
main 接受值仍为下文 DATA804。不要合并本草稿或重建分支覆盖在制改动。

全部107问题batch已按当前工具/政策重新一次只读预检：107/107具有完整来源计划，
849旧单元提议483完整新单元，27490英文词；其中unit-v1 473、v2 9、v3 1。
全体提议与范围外活跃ID无冲突。准备数历程36→51→57→66→80→92→104→105→106→107。
这是来源准备，不是中文生成/采用；接受事实仍107问题batch、529候选、1740诊断，
全部translation-data及原历史原字节保持。Issue808已提前声明29个精确文件。

v13支持完整原生prose/heading/章头见证、真实层级、文档首尾、明确逐处记录的
历史提取排版差异；Sets046U另从完整原生方程label证明真实Section000H及000I
proof至000J lemma的整个语义区间，不以历史parent误值授权来源。FDL完整章头/
center/前言包的10项回归，以及包含完整方程历史重放的14项来源边界回归通过。
29项新增精确数学记号的43种有效配对均有锁定Git见证，Vect/Lift三种未见证
笛卡尔组合由contexts拒绝，8项独立记号测试通过。

最后两处含TeX控制空格的自然文字使用独立unit-v3/schema及source-container-v14，
不放宽v2纯参数合同。完整父参数内两纯叶仍分属同一region/unit，中间控制空格
原字节锁定；3个新纯文字角色沿用v2。5项复合文字测试、另1项真实prepare/check
和ordinary assembly拒绝入口测试通过，含双代完整v4历史、来源/Schema/溯源、
实际结构化render及逐次待决术语；原v2的40项回归通过。测试修复和失败日志保留。
相关全组重放入口现在识别v13 typed证据及v3/v14，普通装配不能绕过typed来源。

基础工具兼容性集合171项中169先通过；另两项为旧Aut(X)拒绝预期及完整proof
拒绝信息被新入口覆盖，已分别修正并定点2项通过，未重跑169个未受影响项。新v3
6项及原v2 40项通过；全库对齐另发现零参数copyright入口遗漏，已同步两个解析
入口并增加针对性1项通过。全部失败/修复日志保留，没有弱化数学或完整组门禁。

当前全库实际extract-all/check通过：117章、116 Git原字节回放，43223来源提议，
READY38422/BLOCKED4801，12491诊断；仍非全库翻译就绪。实际alignment/check通过：
239/1208，BYTE_EXACT243、PRESENTATION_EQUIVALENT911、SOURCE_DIFFERENCE54，
529候选/1740诊断、零坐标/来源错误/proof mismatch，107问题batch保持。当前活跃
数学探针未分类0、11个旧typed迁移节点，4条历史分片异常仍须完整容器恢复。

workflow/Schema/decision/index/117模板通过。当前lane真实render240.793秒、
pdf66.590秒，FinalTeX PASS；119生成TeX原字节不变，463页整书文字、绘图流与
页面几何均相同，9张此前实际查看页面PNG重生成后逐字相同，因此没有变化页。
模板未变，不重复template。全体translation-data及范围外字节保持；没有新run/
raw/中文生成或采用。217个不同测试方法的现有通过证据由上述集合与定点修复
组成，不冒称一次完整全绿运行。239 QA及最终全库验收仍留待全部S4完成后集中做。

在制证据目录 `build/task-integrated-remediation/`（ignored）保存完整107预检、
各阶段差异、真实Git见证、测试日志及continuation-state。真正DATA前仍先在同一
Issue声明完整新旧ID/精确写路径/真实run-model，机器核验、冻结全部输入和历史。
只做一个最终PR；没有逐批进度PR、工具PR或人审/术语/发布批准。

## 最新接受检查点：2026-10-14，DATA804

[PR #807](https://github.com/dongyaotalk/stacks-project-zh/pull/807) 已合并，
[Issue #804](https://github.com/dongyaotalk/stacks-project-zh/issues/804) 已关闭。
DATA接受main `80463ead15a4e52bf9dea6cc01255da70a9d24c3`，精确feature
`762b57aa997629d10bff3c317680345d0265cca5`，base
`bca6b855e4fcc0e37876787ca0802c214c16a3bd`。随后独立进度
[Issue #808](https://github.com/dongyaotalk/stacks-project-zh/issues/808)必须先于下一DATA完成；
其文档提交会形成更晚的main。续接先查实时GitHub main、分支、开放PR/claimed Issue和
实际审计，保留已合并成果与本地改动，本段不是覆盖工作区的依据。

| 实测审计 | 接受值 |
| --- | ---: |
| batches / 活跃唯一 unit | 239 / 1208 |
| 问题 batches | 107 |
| 术语问题 candidates / 诊断 | 529 / 1740 |
| 坐标 / 来源错误 / proof mismatch | 0 / 0 / 0 |
| proof groups / units / match / unsupported | 187 / 218 / 187 / 0 |
| 来源库存 / READY / BLOCKED | 43242 / 37198 / 6044 |
| 库存诊断 / Git roundtrip / 章节 | 16888 / 116 / 117 |
| BYTE_EXACT / PRESENTATION_EQUIVALENT / SOURCE_DIFFERENCE | 243 / 757 / 208 |

真实Section09WN的完整四batch04E6、04E7、09WP、002R，从23旧单元恢复为6完整Git容器：
04E6定义、04E7引理及证明、09WP定义、002R引理及证明。完整185来源词偏好例外提前
写入Issue和生成范围，没有加入已接受批次凑词数。四份v4完整有序分组覆盖全部旧输入和
候选，六份source-container-v2恢复绑定真实owner/Section/selector及原字节，完整12份
ancestry与原run/raw保留。六目标全部BYTE_EXACT、四批queue清空；范围外matches、
terms、source和proof findings逐项相同。DATA的单位数1225→1208、问题批111→107、
术语候选535→529、诊断1753→1740，不能把单位合并当作丢弃旧问题。

前置[PR #806](https://github.com/dongyaotalk/stacks-project-zh/pull/806)属于独立来源词目录
工具任务：equivalence class/classes各有完整锁定Git容器见证，目录诊断1756→1753，
535问题候选不变；它没有采用DATA或批准译法。DATA804原gpt-6.1-sol未生成计划、原34
文件来源包及stash `644dd0588ca8861a28e2e507115715167b46e353`保持原字节，恢复检查
同时核验mtime与stash；不要pop/drop或把未生成计划冒称实际run。DATA800后的独立
进度[PR #803](https://github.com/dongyaotalk/stacks-project-zh/pull/803)已完成，历史记录保留。

来源prepare220.743秒/check224.606秒，包原字节和mtime相同。实际生成前冻结全部六新
unit、23旧输入及全部候选、完整有序组、12份ancestry、政策/style/glossary/prompt/来源
词目录/model/Harness/context hashes，并预检未来完整来源集合的全部目录见证。
冻结时间`2026-10-14T03:40:48.261790+00:00`。实际模型
`gpt-6-astra / xhigh`，turn `01a13861-c45a-74b3-ba4c-1f9874803a61`，run
`run-20261014-categories-cofinal-initial-gpt6astra`；生成前和装配时动态Codex
`0.162.0-alpha.17.2`，snapshot未暴露。下一次重新读真实元数据与动态版本，不复制本值。

模型实际生成六份完整五字段；首次装配前逐句核对发现04E6的generated也需双语，实际
完整重生该unit五字段并保留首稿，程序只选择完整记录。最终44双语声明覆盖37目录要求，
额外逐句覆盖sequence两处、pairs、canonical两处、002R的initial及generated；04E6的
is cofinal和09WP的is initial各两处保留完整源词形。五字段逐项等于真实会话工具字面输出、
不可变raw及活跃候选，保护token原序/次数/尾空白、冻结先后与全部上下文绑定通过。
这是一次实际采用run；未装配草稿选择不能用于隐藏已经装配或采用的前驱，后者仍须按
§8.5完整临时重放或Git archive合同处理。两个proof原文均Omitted，忠实译“略。”，
source-only remark只在notes/版本勘误表留档，不补证、改公式或在正文加译者说明。

独立Git片段/五字段/context/旧组/完整历史/范围外bytes校验通过，全库1208唯一unit、
239batch与117模板一致。239QA390.678秒、实际run QA0.305秒，Schema/溯源/决策/
workflow/harvest/index通过；全库extract59.581秒/check61.181秒、alignment34.009秒/
check34.185秒。隔离progress/plan及各check通过，三报告原字节未变仍在独立任务真实复核。
纯DATA未重复运行未变工具测试或make template，远端CI实际执行完整检查。

实际render233.862秒/pdf72.184秒，FinalTeX PASS。463页整书layout文字比较，458页相等；
变化页15/16/64/65/66，全部变化及邻页14/15/16/17/63/64/65/66/67共9 PNG已逐张实际查看，
未见裁切、重叠、缺字或数学内容缺失。65/66公式外句号各占一行，一处双语词跨页；这是
保留的版式观察，不为孤行/分页改写模型输出、来源或生成TeX。后续文档构建只有在全文
及重新渲染的PNG逐字相等时才能复用这些实际视觉证据。

完整32文件staged内容已审查；远端head全部原字节相等，base中10旧路径原字节相等、
22新路径不存在。未经归一化的完整patch两端均2,968,359 bytes、逐字相等，SHA256
`24f769b348c7ee61c61722a9091e07d6f2847cfa441c4bdd75be68f864c75e98`。
native唯一closing804、owner/claimed/branch/路径及30机器管理文件合同通过；精确HEAD
pr-contract run/job `38508881647/115672565629`与policy-and-data
`38508881660/115672564537`均SUCCESS，实际API核验run/job/head一致。
fresh main等于base后授权admin squash；合并后main/feature tree、32路径和范围外字节、
实际run trailers、PR MERGED、Issue CLOSED及clean通过，无Reviewed-By伪人审。

本次开发证据目录为ignored `build/task-categories-cofinal-initial/`；其中scope、冻结/
authorship/independent/integration/validation/visual/staged/remote/CI/postmerge清单保存
完整证据，新克隆需按跟踪的事实历史和下文命令重新核验，不依赖这些本机生成物存在。
独立进度任务使用`build/task-progress-cofinal-initial/`。当前余下问题章分布为Categories9、
Sets17、Conventions5、Coding2、Desirables18、FDL2、Guide21、Introduction2、Obsolete31。
Categories剩0012、002S、002U、002Z、0036、003D、04AQ、04AX、04AY；仅VERIFY来源
也不能遗漏。重新核实真实完整分组，旧粗略预检的“整组歧义”不是修改来源规则的依据。
002U/003D正文中未分类数学自然文字仍BLOCKED，先独立必要前置，不裁去正文或归成记号。
本次进一步只读重扫确认：0012章标题真实parent0011可唯一定位；002Z的0CN1完整remark、
04AX的002Y完整proof亦含未分类数学自然文字，保持BLOCKED。04AQ首段、002S完整定义
和0036完整标题可准备，其他所列段落仍须完整分组/边界核验；预检没有改变事实。
全部S4后才独立S5默认强门禁、S7和F1–F8最终文档/复制提示词。术语、critic、语言/数学
人审和发布均未批准；当前总goal继续，不能凭单批或qa-all通过声称全部来源术语完整。

## 历史接受检查点：2026-10-14，DATA800

[PR #801](https://github.com/dongyaotalk/stacks-project-zh/pull/801) 已合并，
[Issue #800](https://github.com/dongyaotalk/stacks-project-zh/issues/800) 已关闭。
DATA 接受 main `6c648a861a15f015c35cdf6e177161b9c41b1bb7`；精确 feature `df6e7fd91a2976e67cc3fdacbe514a330936b7e3`；
base `60b14fe7d608a0142b825f7a37f79b13824ce006`。其后独立进度
[Issue #802](https://github.com/dongyaotalk/stacks-project-zh/issues/802)须完成后再认领下一DATA。
续接时重新读取实时main、分支、开放任务和实际审计；本段不是覆盖工作区的依据。

| 实测审计 | 接受值 |
| --- | ---: |
| batches / 活跃唯一 unit | 239 / 1225 |
| 问题 batches | 111 |
| 术语问题 candidates / 诊断 | 535 / 1756 |
| 坐标 / 来源错误 / proof mismatch | 0 / 0 / 0 |
| proof groups / units / match / unsupported | 187 / 218 / 187 / 0 |
| 来源库存 / READY / BLOCKED | 43242 / 37198 / 6044 |
| 库存诊断 / Git roundtrip / 章节 | 16888 / 116 / 117 |

真实Sections0020/0021的完整三batch0020/0021/0022，13旧→5完整新单元：两个标题、
Section0020完整正文、0022完整引理及完整证明。正文完整包括三段和四项列表，五组
有序覆盖全部13旧unit及candidate，没有裁掉未处理输入。222来源词的完整范围偏好
例外在Issue及生成前声明，未补入已接受批次凑300词。最终五目标BYTE_EXACT、三批
repair queue为空；范围外source/terms/proof/matches逐项不变。问题batch114→111、
术语候选543→535、诊断1774→1756、unit1233→1225来自完整语义分组。

前置[PR #797](https://github.com/dongyaotalk/stacks-project-zh/pull/797)接受严格v12双Section
完整末端见证：前标题和真实后标题独立绑定，整个旧正文有序链与最大原Git正文的全部
76节点、数学/引用/结构/注释保持，普通ASCII prose外空白有唯一完整依据；旧v1–v11
权限不变。前标题的历史命名空间仅用既有v7规则核验，正文不获得标签改写权限。
[PR #799](https://github.com/dongyaotalk/stacks-project-zh/pull/799)只把module的modules
来源见证从旧item004迁到完整锁定Git正文；192目录证据有效，词形/中文批准不变。
READY表示来源准备状态，两个前置没有采用DATA。

第一次完整冻结5新/13旧、完整有序组与候选、9份原历史、policy/style/glossary/prompt/
catalog/context hashes，实际模型生成全部五字段。正文一次token错序被拒后完整重生，
初稿保留。第一次实际run装配后逐句核对发现pairs两处和structure一处仍需双语；
第二次生成前扩展Issue为42精确文件、两个实际run与三完整pre-adoption-replay-v1历史，
重冻原run/raw/correction和三个完整临时batch共13文件原字节，所有新context保存
`prior_actual_revision`和`pre_adoption_snapshot_bindings`。第二次模型完整重生全部5新unit
五字段；程序只选择完整记录、保护、序列化、验证和装配，不生成中文或机械补术语。
新旧v4只改变完整组correction指针和候选输出hash，来源、原输入、分组、边界、身份
完全相同；完整当前重放先通过，再严格重放三个历史，原run/raw均不可变。

两个实际run为`run-20261014-categories-fibre-examples-gpt61sol`和同名`-complete`；
实际`gpt-6.1-sol / xhigh`、turn `01a137ad-1a69-7613-8bc4-b53d291c919f`，动态Harness
`0.162.0-alpha.17.2`，snapshot未暴露、replayable false。下一次必须重读实际运行元数据，
不能复制本值。最终54次双语声明覆盖46来源目录要求；五字段与实际会话字面输出及
immutable raw逐项相等，保护token原序/次数/尾空白相等。额外逐句检查不能仅靠QA代替。
原证明Omitted忠实译为“略。”；source-only疑点留书末版本勘误表，不补证明或改数学。

来源prepare205.809秒/check202.654秒且原字节/mtime不变；239QA379.236秒、第二run
QA0.177秒、第一runQA0.146秒，Schema/溯源/决策/workflow/harvest/index/117模板通过。
全库extract61.52秒/check61.155秒、alignment34.382秒/check35.174秒；隔离progress/plan
生成及各check通过，三报告原字节无变化仍须独立真实check。实际render227.406秒、
pdf71.957秒、FinalTeX PASS；463页整书layout比较，458页文字布局完全相同；变化页
4/15/16/54/55及全部邻页/相关页共11 PNG逐张查看。页14是正常空白背页。
完整42文件8,236,606-byte patch与远端head原字节相等；base中8旧路径原字节相等，
34新路径不存在。native唯一closing800通过。精确HEAD的pr-contract run/job
`38489660042/115612232365`、policy-and-data
`38489659878/115611595029`均SUCCESS；fresh main==base后
授权squash，合并后tree、42文件字节、两个run trailers、MERGED/CLOSED和clean核验。

首轮pr-contract因新增16路径的YAML列表位置错误而失败：同样路径已在第二次生成前
写入Issue，但机器allowed_write_files只读到26项。纠正列表位置，不改变DATA HEAD或
路径内容；本地机器合同与远端原生合同重新通过，同HEAD只重跑失败合同job后成功。
失败日志保留，未放宽规则或伪造审校。今后生成前同时检查Issue文本与机器解析结果：

```bash
gh issue view "$ISSUE" --json body > build/claimed-issue-body.json
"$PYTHON" - <<'PY'
import json
from stacks_zh.pr_contract import _field_value, _list_values
issue = json.load(open("build/claimed-issue-body.json"))
scope = json.load(open("build/task-scope.json"))
assert _list_values(_field_value(issue["body"], "allowed_write_files")) == scope["allowed_write_files"]
PY
```

将当前任务完整scope副本放在上述生成目录；不要改公共解析器来迁就错误清单。
下一只读预检002R/002S真实parent为09WN/04AQ。002U完整正文含数学里的
`\text{ in }`，未在当前自然文字规则内，整正文仍BLOCKED；不能只采用标题或把文字
归为记号。先独立精确政策/工具来源前置，再重新核验完整批次、目录证据及模型输入。
当前剩余Categories13、Sets17、Conventions5、Coding2、Desirables18、FDL2、Guide21、
Introduction2、Obsolete31问题batch。全部S4之后才独立S5默认强门禁和S7；仅VERIFY
来源的批次也必须处理。术语、critic、语言/数学人审和发布均未批准。F1–F8总目标继续。

## 历史接受检查点：2026-10-14，DATA792

[PR #793](https://github.com/dongyaotalk/stacks-project-zh/pull/793) 已合并，
[Issue #792](https://github.com/dongyaotalk/stacks-project-zh/issues/792) 已关闭。
DATA 接受 main 为 `9ae8d621b35e33e3c299fbfbc9460e17f4262c6e`，精确 feature 为
`a4b0760949c74a73ff188f4e95ca1b2bd26dc1cc`，接受 base 为
`e2b88edfea594ad6a8505d57a5f31183b0cf3264`。之后独立进度
[Issue #794](https://github.com/dongyaotalk/stacks-project-zh/issues/794) 会形成新的
main；每次续接必须重读实时 GitHub、本地分支和实际审计，不用本段 SHA 覆盖工作区。

| 当前实际审计 | 接受值 |
| --- | ---: |
| candidate batches / 活跃唯一 unit | 239 / 1233 |
| 问题 batches | 114 |
| 术语问题 candidates / 诊断 | 543 / 1774 |
| 坐标 / 来源错误 / proof mismatch | 0 / 0 / 0 |
| proof groups / proof units / match / unsupported | 187 / 218 / 187 / 0 |
| 锁定来源库存 / READY / BLOCKED | 43242 / 37198 / 6044 |
| 库存诊断 / Git roundtrip 文件 / 章节 | 16888 / 116 / 117 |

真实 Section0013 的八个完整连续 batch001B–001I，从27旧单元恢复为12完整新单元，
575来源词、八份v4完整有序分组、十二份锁定Git容器证据。001B、001D各包含完整定义
和其后完整段落；001I完整六旧输入对应 definition001I、paragraph6及由p002/p003组成的
完整paragraph7。新单元为001B–001I各自的statement，及0013的paragraph-0004–0007。
已接受的0014–0019、001L米田范围及其他批次不重复；全部旧输入/候选、八个原run/raw、
24份完整ancestry和政策/context原字节保留。全部12目标BYTE_EXACT、八批队列清空，
范围外matches/术语/source/proof findings逐项相同；问题batch122→114、候选560→543、
诊断1813→1774，unit1248→1233来自完整语义分组。

来源前置[PR #789](https://github.com/dongyaotalk/stacks-project-zh/pull/789)已接受严格
`source-container-v11`，绑定完整前陈述、前段和其后最大完整有序旧分段链，两处原生
相邻关系、章内唯一性和v5/v6嵌套见证独立重算；旧v1–v10权限保持。
[PR #791](https://github.com/dongyaotalk/stacks-project-zh/pull/791)将12项英语来源词证据
迁移至六完整锁定Git容器。两者只准备来源，未批准词形译法或采用事实。

实际模型 `gpt-6.1-sol / xhigh` 在全部源/旧组/候选/历史/context
冻结后生成12份完整五字段，run为`run-20261014-categories-functors-complete-gpt61sol`，
turn为`01a1365a-5f28-7563-b184-8e9a34a63b92`。动态Codex为`0.162.0-alpha.17.2`，snapshot未暴露、
replayable false；下一次生成必须重新读取当时真实元数据和运行时版本。
首稿六unit token错序被拒，完整重出六份五字段后001D仍错序，再完整重出该unit；
全部失败草稿在首次装配前保留，程序仅选择完整记录。12最终五字段与rollout字面输出
及immutable raw逐项相等，133来源要求/145双语声明、token原序/次数/尾空白通过。
已创建run或已采用的前驱不能套用本次未采用草稿选择，仍须完整历史重放和独立修订run。

来源prepare233.778秒/check231.584秒，包八文件bytes/mtime保持。239QA362.357秒、
实际run QA0.2秒及Schema/溯源/决策/workflow/harvest/index/117模板通过；全库
extract60.315秒/check61.106秒、alignment34.71秒/check33.505秒通过。实际render216.034秒、
pdf73.499秒，FinalTeX PASS；463页整书全文比较，447页layout相同，16变化物理页及
全部邻页/相关页共25 PNG实际查看。完整58文件6,923,227-byte patch及远端head/base原字节
核验，18旧路径字节一致、40新路径在base不存在，native唯一closing792通过。
精确HEAD的pr-contract run/job `38445285631/115461939479`、
policy-and-data `38445285685/115463172925`均SUCCESS。
首轮CI仅在TemporaryDirectory清理Git objects目录时报Errno39，完整失败日志保留；相同HEAD
单次重跑后实际全门禁成功，未放宽规则。此清理故障已重复出现，需要独立维护调查及证据，
不能在DATA中隐藏错误或用重试代替实际成功。fresh main==base后授权squash，合并后tree、
58文件字节、全部实际run trailers、MERGED/CLOSED及干净状态核验。

剩余问题批次为Categories16、Sets17、Conventions5、Coding2、Desirables18、FDL2、Guide21、
Introduction2、Obsolete31。必须继续repair-queue的完整语义范围；仅VERIFY来源的batch也
不能遗漏。独立progress/plan完成后再认领下一DATA；全部S4后独立S5默认强门禁和S7。
未知语法/数学文字继续BLOCKED，未知术语及所有critic/语言/数学审校/发布仍未批准。
F1–F8总目标及最终详细文档提示词尚未完成，不能凭QA通过或单批修复宣告完成。

下一完整同章范围0020/0021/0022的只读预检：完整13旧输入包括0020标题、三段与四项列表，0021标题和0022完整lemma/proof。四个来源容器（两标题/lemma/proof）可核验，但0020完整prose_block因真实前后语义锚点与原冻结batch边界不同而拒绝；分段替代也严格拒绝第二/三段历史wrapper及未经独立指定lowering的standalone enumerate。来源库存READY不提供事实采用权限；不裁去七旧输入，不将40已核验来源词/四新单元当作完整范围。完整失败原因已保留，后续先独立来源合同/工具及回归，再核验未来全目录并完整DATA。此预检没有认领/生成生产中文/run/改事实。

## 历史接受检查点：2026-10-13，DATA784

[PR #785](https://github.com/dongyaotalk/stacks-project-zh/pull/785) 已合并，
[Issue #784](https://github.com/dongyaotalk/stacks-project-zh/issues/784) 已关闭。
DATA 接受 main 为 `8cd73b2b1edc31ec4fe3af6711cc5d221d2f515e`，精确 feature
`d7e10de63b955b2047eed55caa8d92db79b3782c`，接受 base
`b45ff995026d00ad6a5ef4285d2b660d89b1665a`。当前独立进度任务为
[Issue #786](https://github.com/dongyaotalk/stacks-project-zh/issues/786)；其文档合并
会产生后续 main，续接须读实时状态，不固定使用本段 SHA 覆盖工作区。

| 当前实际审计 | 接受值 |
| --- | ---: |
| candidate batches / 活跃唯一 unit | 239 / 1248 |
| 问题 batches | 122 |
| 术语问题 candidates / 诊断 | 560 / 1813 |
| 坐标 / 来源错误 / proof mismatch | 0 / 0 / 0 |
| proof groups / proof units / match / unsupported | 187 / 218 / 187 / 0 |
| 锁定来源库存 / READY / BLOCKED | 43242 / 37198 / 6044 |
| 库存诊断 / Git roundtrip 文件 / 章节 | 16888 / 116 / 117 |

本次真实 Section0013 的六个连续完整问题 batch 0014–0019，从32旧单元恢复为
8个完整新单元，包含完整定义、17项列表注记、两段无标签正文及后续注记/定义/例。
全部旧输入与候选原字节、18份历史文件、原run/raw保留；八份source restoration
和六份v4完整有序分组证明无遗漏、无重复。八目标全部BYTE_EXACT、六批队列清空；
其他来源、术语和proof findings逐项相同。问题批次`128→122`、术语候选`583→560`、
诊断`1871→1813`；活跃unit减少来自完整语义分组，不是归档未解决问题。

前置[PR #779](https://github.com/dongyaotalk/stacks-project-zh/pull/779)登记严格
数学记号，[PR #781](https://github.com/dongyaotalk/stacks-project-zh/pull/781)
新增`source-container-v10`历史parent双锚点见证，[PR #783](https://github.com/dongyaotalk/stacks-project-zh/pull/783)
将26项英文来源证据绑定完整锁定容器；三者均未采用译文或批准中文词表。
v10保留不同历史parent与真实Section的区别，绑定完整前陈述、段落和同批完整
后陈述，不能把其特定权限推给旧v1–v9或任意段落。

实际`gpt-6-astra / xhigh`生成8份完整五字段，run为
`run-20261013-categories-definitions-complete-gpt6astra`；对应turn为
`01a13305-e58d-7b52-88a2-18a6aff75f1f`。原计划模型尚未生成生产结果；先更新
同一claimed Issue的branch/model/run及四个路径，保留原计划，再冻结和生成。
本次动态Harness为`0.162.0-alpha.17.2`，snapshot未暴露、replayable false。
每个新run必须重新读取实际元数据和动态版本，不能复制本次值。

首稿paragraph-0003的保护token错序被拒，完整失败草稿保留；实际模型重新输出
该unit全部五字段，程序仅选择七份原完整记录与这份完整修订再序列化。失败草稿
此前未装配、未采用，不冒充已接受前驱；若已有实际run或采用记录，必须按
完整历史重放合同保存，不能套用本次“未采用草稿”处理。最终五字段与真实rollout
字面输出及immutable raw逐项相等，125来源要求、141双语声明、token次序/次数/
尾空白均通过。全部术语、critic、语言/数学审校和发布仍未批准。

239全量QA、新run QA、Schema/溯源/决策/117模板、全库抽取和对齐各check通过。
当前lane实际render209.034秒、pdf78.543秒，Final TeX PASS；整书463页，450页
layout文字相同。13变化页2/15/16/17/43–51与全部邻页/相关页共21张PNG实际查看。
44文件完整4,782,828-byte patch及远端head/base原字节核验，原生唯一closing784
通过；精确HEAD的`pr-contract` run/job `38338190848/115102982155`和
`policy-and-data` `38338190780/115102981052`均SUCCESS。fresh main等于接受base
后授权squash；合并后tree、44文件原字节、DATA trailers、MERGED/CLOSED/clean核验。

独立进度Issue786已实际执行progress/progress-check（4.057/3.635秒）及plan/plan-check
（0.594/0.607秒），三个报告与DATA隔离预览逐字相同。来源库存和对齐check也通过，
实际render176.539秒/pdf68.522秒、Final TeX PASS；463页全文及21张接受PNG原字节
相等，复用此前实际看图证据。其PR仍须核对远端合同、精确HEAD双CI和合并状态。
剩余问题批次按最新队列为Categories24、Sets17、Conventions5、Coding2、Desirables18、
FDL2、Guide21、Introduction2、Obsolete31。下一组001B–001I只读预检尚未认领：
27旧单元拟恢复为12个完整新单元、575来源词；001I的p002/p003实际共同属于原生
paragraph/7，现行单段及split-preceding合同拒绝其边界。完整范围继续待核验，
不能只采用可通过的11个提议单元或裁掉残段。完整未来库存另有12项旧来源词证据
需独立迁移到锁定完整容器；词形和中文批准不随迁移改变。先处理完整语义范围
所需前置，再冻结实际模型修订。全部S4之后才独立S5/S7，
本指南和提示词是持续更新的开发材料，不表示F1–F8总目标已完成。

## 历史接受检查点：2026-10-12，DATA770

[PR #775](https://github.com/dongyaotalk/stacks-project-zh/pull/775) 已合并，
[Issue #770](https://github.com/dongyaotalk/stacks-project-zh/issues/770) 已关闭；
DATA 接受 main 为 `06ed9b2d8f7afdd7b790a59ae8e33b0c71152ed2`，精确 feature
`169ccbfbad7c14838ee9f8736e5d4285adb1627f`，前置接受 base
`40f7f988f7627781da451362ad0158c9f2bc92e4`。本独立进度文档还会产生后续
main，续接须读取实时 HEAD，保留全部已合并数据、工具及进度成果。

| 当前实际审计 | 接受值 |
| --- | ---: |
| candidate batches / 活跃唯一 unit | 239 / 1272 |
| 问题 batches | 128 |
| 术语问题 candidates / 诊断 | 583 / 1871 |
| 坐标 / 来源错误 / proof mismatch | 0 / 0 / 0 |
| proof groups / proof units / match / unsupported | 187 / 218 / 187 / 0 |
| 锁定来源库存 / READY / BLOCKED | 43250 / 36724 / 6526 |
| 库存诊断 / Git roundtrip 文件 / 章节 | 18394 / 116 / 117 |

六个完整当前 batch 为 001M、001N、02X6、001O、001P、001Q，真实 Section001L。
16 旧 unit 恢复为 10 个完整新 unit；十目标全部 BYTE_EXACT，六队列清空，其他
来源、术语和 proof findings 保持。全库问题 `134→128`、术语候选 `592→583`、
诊断 `1893→1871`。05SH/05PU 已在后续已合并任务修复，下面 0AHK 表格是历史
交接记录。当前 S4 未完成，全部 S4 后独立实施 S5 默认强门禁及 S7；F1–F8 总
goal 持续执行，不因当前批次或新聊天完成而提前结束。

完整五字段来自两个实际 gpt-6.1-sol/xhigh run：
`run-20261012-categories-yoneda-complete-gpt61sol`（完整十 unit）和
`run-20261012-categories-yoneda-bilingual-followup-gpt61sol`（完整 001O/001Q）。
当前八份采用原十-unit raw，另两份采用后续 raw，全部字段/context/保护 token/
尾空白相等。动态 Harness 0.162.0-alpha.17.2 是本次证据，新 run 仍须实际解析；
snapshot 未暴露、不可宣称权重级重现，所有术语与 critic/人审/发布均未批准。

完整复合词目录 [PR #772](https://github.com/dongyaotalk/stacks-project-zh/pull/772)
只登记锁定来源的英语概念；发现短标注后实际模型完整重译。首次 Git 采用前的
完整历史重放 [PR #774](https://github.com/dongyaotalk/stacks-project-zh/pull/774)
实现 `pre-adoption-replay-v1`，合同见 [model-provenance §8.5](model-provenance.md#85-首次-git-采用前的完整临时-v4-重放)。
保存两组旧完整记录和 unit/candidate 原字节；新 run 生成前的完整 context 和
文件 hash 已绑定这些状态。旧、当前 v4 分别重放，原 run/raw 不改写，既有
001P v2 及全部归档/恢复历史保留；不假造 Git 前驱，也不删除未消费原输出。
此历史一旦接受须随普通后续 archive 保留，sidecar 与三快照须随派生首次 Git
加入，之后不得补造或重算 hash 覆盖。

548 工具回归及 239 候选 QA、两实际 run QA、全部 Schema/溯源/决策/117 模板、
全库抽取/对齐 check 均有实际通过证据。DATA 当前 lane render 159.134 秒、pdf
65.550 秒，Final TeX PASS；463 页全文比较，四变化页 15/16/50/51 及邻页/相关
页共 14 张 PNG 实际查看。独立 progress/plan 必须在下一 DATA 前真实生成/check，
即使报告原字节没有变化；此次独立任务为 [Issue #776](https://github.com/dongyaotalk/stacks-project-zh/issues/776)。

精确 HEAD 的 GitHub 原生唯一 closing 合同、61 文件两端原字节及 8,507,239-byte
完整 patch 已核验；CI `pr-contract` run/job `38221724533/114719328450`、
`policy-and-data` `38221724310/114719326900` 都 SUCCESS。fresh main 等于验收
base 后授权 squash；合并后 main/feature tree、全部 61 文件、两个 run trailers、
MERGED/CLOSED/干净状态核验。这里只记录候选修复，没有语言或数学人审结论。


## 0. 2026-10-11 交接检查点

本轮DATA [0AHK PR](https://github.com/dongyaotalk/stacks-project-zh/pull/708)已合并，接受基线`d58a76498aedb6b5ab6ec528bf7032e8e2f76684`，
英文仍锁定`a04446e57ec1fbc252a871afcec7752fb2807b14`。
本指南所属文档PR还会产生后续main提交，新goal开始时须核实fresh main及工作区，
不把这里的SHA当作永不变化的当前HEAD。用户自行创建新goal，本轮不再开启下一DATA。

前置工具[PR696](https://github.com/dongyaotalk/stacks-project-zh/pull/696)支持真实
完整边界；[PR703](https://github.com/dongyaotalk/stacks-project-zh/pull/703)支持PR
合同的大文件完整blob核验；[PR706](https://github.com/dongyaotalk/stacks-project-zh/pull/706)
修复完整容器内原生嵌套Tag进度覆盖，均已接受合并。不要重复开发或撤销这些实现。

本轮0AHK恢复4旧→3新，完整引言/引理/proof在真实000H，6旧新唯一ID和14允许
文件，1份v4/correction/实际run及3来源恢复。旧输入原字节保留，实际
`run-20261011-sets-0ahk-complete-gpt61sol`由gpt-6.1-sol/xhigh在冻结后完整生成，
43双语声明覆盖26来源要求。170词不可拆范围例外已明确，Harness实际动态版本
0.162.0-alpha.17.2仅是本轮运行证据；新run必须重新解析而不能沿用。
239候选QA、真实新run分组QA及全部共享门禁、全库提取/对齐checks通过；整书461页，
457页全文layout相同，4变化页及邻页共8页实际看图通过，FinalTeX PASS。
完整远端文件/patch/native合同、最新精确HEAD双CI及受保护bypass后合并核验通过。

| 当前审计 | 交接值 |
| --- | ---: |
| 活跃candidate batch / 唯一unit | 239 / 1,346 |
| 非空修复batch | 175 |
| 有术语问题candidate / 诊断 | 668 / 2,106 |
| 坐标待迁移 / 错误带标签陈述 | 0 / 0 |
| 来源结构诊断 / 未保护node pair | 1 / 1 |
| 来源对应歧义 | 2（均在categories-05PU） |
| proof组 / 当前proof单元 | 187 / 222 |
| proof match / mismatch / unsupported | 187 / 0 / 0 |
| 隐藏脚注 / 环境标题 | 0 / 0 |
| 来源提议 / READY / BLOCKED | 43,257 / 36,651 / 6,606 |
| 库存诊断 / Git逐字回放文件 | 18,618 / 116（117章均报告） |
| 候选Section / 全部Section | 108 / 3,299 |
| 人工审校Section / 正式发布Section | 0 / 0 |

175个非空batch的分布：Categories77、Sets17、Conventions5、Coding2、Desirables18、
FDL2、Guide21、Introduction2、Obsolete31。动作计数是167个术语修订、67个来源核验/
恢复、1个结构/显示修订；一个batch可含多个动作，不能将动作相加作为剩余batch。
242个SOURCE_DIFFERENCE及964个PRESENTATION_EQUIVALENT是诊断分类，不直接
等于已确认的数学错误；2个AMBIGUOUS须独立处理，138个BYTE_EXACT保持。

| 八项状态 | 本检查点的结论 |
| --- | --- |
| F1 | 当前坐标及statement-Tag审计零残项；仍需S7最终全量核验 |
| F2 | 未完成：668个候选/2106诊断；独立来源术语审计尚未进入默认全量硬门禁 |
| F3 / F5 | 相应门禁和替换链工具已实现并有接受回归，最终集成仍需重验 |
| F4 | 全部proof匹配、保护工具已实现；05SH仍有1来源未保护控制问题 |
| F6 | 既有脚注/引用修复已采用，隐藏脚注为零；最终整书验收仍需覆盖指定位置 |
| F7 | 当前461页构建FinalTeX通过；最终数据变动后仍需整书/适用模板验收 |
| F8 | 当前progress/plan check及独立同步通过，最终事实完成后须再次生成 |

下一步建议先处理`categories-05SH`完整旧statement/proof，消除最后的未保护TeX
控制问题和该陈述8条术语诊断；再核对`categories-05PU`完整7旧单元、两处嵌套
item歧义及identity自报词形。先独立准备完整来源，遇到未支持语法另开前置工具/
政策任务，不在DATA中弱化规则。随后按同章相邻完整范围集中修订其余术语；
全部S4真正完成后独立实施S5，最后S7。当前未批准词表entries为空，不在普通
数据任务授予批准。

完整已接受工程记录见[engineering-remediation.md](engineering-remediation.md)。
可复制续接提示词见[codex-remediation-prompts.md](codex-remediation-prompts.md)。
本机ignored证据目录`build/task-sets-0ahk-complete/`及
`build/task-remediation-handoff/`保存冻结、完整checks/差异/PDF/PNG/remote/CI/
postmerge；新克隆不含这些产物，必须从已跟踪事实重新生成并核验，不依赖旧缓存。
source-only remark Issues691/698/699保留历史，非翻译修复或审批，不需补源码证明。
用户要求在书末独立收录这些记录并注明锁定英文版本；模板任务 Issue758 接入
“勘误与原文疑点”表，来源坐标、完整原字节 hash、复现与维护边界见
[source-errata.md](source-errata.md)。三个 remark 只在表格合并并核验后以
“已收录留档”关闭；关闭不表示数学疑点已裁定或原文已修复。


## 1. 总目标和完成定义

完成 `docs/engineering-remediation.md` 的 F1–F8；保留已合并结果，继续 S4 数据修复，
随后完成 S5 强制门禁及 S7 集成验收。当前 goal 接续全部八项，持续修复直至最终
证据齐备并交付详细开发文档和完整可复制提示词。PR 的 bypass 仅是合并授权，不构成术语、critic、人工
语言/数学审校或发布批准。候选修复的完成与正式译本的完成分开记录。

| 问题 | 最终验收 |
| --- | --- |
| F1 永久坐标 | 来源 Tag/Section、陈述及 proof 链与锁定 Git 相符，无迁移残项和重复 ID |
| F2 来源术语覆盖 | 独立来源清单完整覆盖，逐次双语/申报正确，缺项在默认 QA/CI 被拒绝 |
| F3 待决术语绕过 | selection/revision 不能自报 CLEAR 绕过真实词表批准 |
| F4 保护结构和旧源遗漏 | 未保护 TeX 被拒绝；完整英文来源恢复有独立证据，全部 proof 链匹配 |
| F5 替换链 | 正常多版链通过，自引用/循环/跨 unit/冲突后继被拒绝 |
| F6 脚注和引用 | 指定脚注完整可译，引用解析正确，不能把全文藏在锁定 token |
| F7 字体及编译 | 最终整书和所需模板无缺字、未定义引用或编译错误 |
| F8 进度与计划 | 从最终事实重建，progress-check/plan-check 通过 |

原开发计划的复选框只在最终真实证据齐备时勾选。一次工具合并、一个数据批次或
全库提取成功均不能替代总验收；审计中排版差异也不能未经证据一概豁免。

### 指定F1与F6目标的独立核验

原F1六批003G、02X8、003O、02XG、02XJ、04Z2共44个自身带标签的数学陈述，
已从锁定Git永久Tag表逐项核对，均使用各自真实Tag；六批及全库坐标迁移残项为零。
不能只抽查新批次或以相同内部hash代替来源归属核验。

F6目标 `tag:0AHN:statement` 与 `tag:0FWX:statement` 各有一处展开脚注，源文均为
`See Remark <REF_0001>.`，当前候选分别为“见注 <REF_0001>。”与“见注记 <REF_0001>。”。
两处引用payload均保持 `\ref{remark-big-categories}`，保护token顺序与次数不变，
没有把整段自然语言锁进不透明脚注token。引用的最终限定与解析仍须通过真实整书
渲染和FinalTeX未定义引用门禁，当前数据检查不冒充构建结果。

### S5 开发与验收计划（S4完整验收后执行）

1. 为活跃候选增加默认当前来源检查：锁定Git定位、永久Tag、原保护结构、隐藏自然
   语言和来源术语出现均须通过；CLI validate/validate-many/validate-all、assemble和
   render入口默认执行。历史raw与旧派生继续使用各自版本合同，不按新目录重写历史。
2. 独立目录证据核验覆盖全部词形见证，不仅检查候选自报数组；目录缺失、错误版本、
   过期证据和范围缺失均失败。按章开发检查只减少选定事实范围，不构成最终全库验收。
3. 用单进程全库验收入口串联Schema、溯源、决策、活跃候选和来源检查，避免Make与
   决策层重复执行同一次完整历史重放。复用仅限同进程内已验证且未变的输入快照，
   不接受用户可写缓存作为跳过依据，不提供跳过严格检查的CLI开关。独立溯源／决策
   命令保留完整默认检查，选定候选仍绑定完整来源与修订历史。
4. Make与CI默认调用严格入口。补充真实失败回归：漏报／少报／重复术语、错误Tag、
   未保护TeX、来源内容／hash／证据篡改、范围外最后一批错误、输入检查中变化、
   待决词条自报CLEAR和历史绑定绕过均须拒绝；合法旧历史继续通过。
5. 更新同一claimed Issue808的精确范围和任务scope，逻辑上独立实现／审查S5；再执行
   S7总验收、生成并check进度计划、真实整书构建与全部变化及邻页PNG、文档及提示词。
   最终仍是一个PR809，不恢复逐批Issue/PR和重复整书验收。

## 2. 仓库与数据层

英文 `../stacks-project` 是只读 harvest，`upstream.lock` 决定来源 commit，本机
路径不决定版本。中文仓库独立历史，不引入英文 remote 或合并英文历史。

| 层 | 文件/模块 | 用途 |
| --- | --- | --- |
| 来源政策 | upstream.lock、config/macro-policy.yml | 来源身份和明确语法权限 |
| 全库库存 | source-ir/extraction/{manifest,units,segments,diagnostics,report} | 来源提议、完整原字节与阻断；ignored |
| 来源定位 | stacks_zh/source_alignment.py、build/source-alignment/ | 当前全部事实的定位与统一修复队列；ignored |
| 当前事实 | translation-data/units、candidates | 活跃 source 和候选，仅此层进入当前统计 |
| 完整恢复 | source_containers.py、source-container-restorations | 锁定 Git 片段、selector、历史边界及独立恢复证据 |
| 历史及修订 | derivations.py、model_corrections.py、runs、retired | 完整旧输入、全部祖先及实际新模型五字段 |
| 审批 | selection/reviewed、decisions.py | 正式人审和发布，模型无权替代 |
| 报告 | chapter-templates、progress.py、progress_coverage.py、plan | 确定性任务骨架和当前统计 |
| 预览 | workflow.py、ajbook-template/translations、output/pdf | 从当前候选生成，生成 TeX/PDF 不是事实 |

库存的 `units.jsonl` 一行是库存记录，提议 unit 在 `record.unit`；顶层不保证有
chapter。库存 ID 与活跃 unit ID 分开，不可按库存序号覆盖历史事实。
READY 表示当前提取支持，BLOCKED 仍有未知语法/数学文字/归属等待办。
116 个 Git 文件逐字回放只证明字节覆盖，不证明所有语义都已正确或可翻译。
自动生成索引没有独立章源，必须明确报告。

## 3. 一次抽取与集中修复

在中文仓库根目录使用用户要求的 pyenv Python 3.12，确认 TeX/XeLaTeX、Biber、makeindex 及 Poppler
可用。不提交本机路径或 config/local.mk。

```bash
TASK_PYTHON="$(PYENV_VERSION=3.12.6 pyenv which python)"
"$TASK_PYTHON" -c 'import sys; print(sys.version); assert sys.version_info[:2] == (3, 12)'
make workflow-check harvest-check PYTHON="$TASK_PYTHON"
make extract-all PYTHON="$TASK_PYTHON"
make extract-all-check PYTHON="$TASK_PYTHON"
make source-alignment PYTHON="$TASK_PYTHON"
make source-alignment-check PYTHON="$TASK_PYTHON"
```

3.12.6 是本次实际环境；维护时可替换为本机已安装的 3.12.x，每条 Make 显式
传同一解释器，不把本机绝对路径写进跟踪文件。

输出统一库存和 `build/source-alignment/repair-queue.jsonl`。抽取一次即可集中查看
来源；模型生成按同章、完整语义容器及上下文容量分组。全库不等于一次把原 TeX
送入模型。修复现有事实后必须重建、check 当前队列；当前事实 hash 改变意味着
旧报告不能继续作为本次验收证据。

```bash
"$TASK_PYTHON" - <<'PY'
import json
from pathlib import Path
root = Path('build/source-alignment')
alignment = json.loads((root / 'alignment.json').read_text())
queue = [json.loads(line) for line in (root / 'repair-queue.jsonl').read_text().splitlines()]
print({key: alignment[key] for key in (
    'unit_count', 'coordinates_to_remap', 'source_error_count',
    'term_candidate_failures', 'term_error_count', 'proof_mismatches')})
print('remaining_batches', sum(bool(row['actions']) for row in queue))
for row in queue:
    if row['actions']:
        print(row['chapter'], row['batch'], row['actions'])
PY
```

这是来源和候选诊断，不是人工审校进度。不能用仍未启用来源术语硬门禁的
`qa-all` 成功证明 F2 已完成。直接核对 term-audit、source-audit、proof-audit
和队列 target/outside 的逐项增量。

## 4. Issue、范围与来源准备

先只读检查工作区、最新 main、当前 PR/claimed Issue，保护用户改动。每个任务
必须声明 chapter、真实 parent Tag、历史 parent、完整旧新 ID、精确所有允许
文件、禁止范围、具体模型及 run；一个单元和候选文件只能有一个 writer。

先创建 assigned/claimed Issue，记录 owner/branch/allowed_write_files，再从最新
main 建分支，先写开发及验收计划。PR 必须原生关闭这一个早于 PR 的 Issue。
改变允许范围必须先更新 Issue，不能事后补认领。数据、工具、政策、术语批准、
模板和进度分别成任务/PR。

完整来源 plan 覆盖完整上一 batch 的所有有序输入，各归唯一 group；使用真实
owner label/Tag/Section、kind 和 ordinal。不得按 PDF 页码、源行号定义写入范围。
原始 byte span 用于验证完整片段，不授予切片或借用其他 owner 的权限。

```bash
make source-containers \
  SOURCE_CONTAINER_PLAN=build/task/plan.json \
  SOURCE_CONTAINER_DIR=build/task/source-package PYTHON="$TASK_PYTHON"
make source-containers-check \
  SOURCE_CONTAINER_PLAN=build/task/plan.json \
  SOURCE_CONTAINER_DIR=build/task/source-package PYTHON="$TASK_PYTHON"
```

包有八份文件：manifest/groups/restorations/diagnostics/units/input-units/
input-candidates/report。检查完整 batch、PREPARED、零 BLOCKED、原字节 hashes
及 check 不改变文件/mtime。多份同章、互不重叠的完整 batch 可用
`prepare-source-containers-many` 减少同次调用的重复溯源校验；每份 plan 仍完整
验证。没有跨调用“已验证”缓存或跳过 provenance 的许可。

v4 派生与 source-container-v4 是不同版本。后者仅为确有原生历史边界 witness
的完整段落/列表组提供核验；旧 source-container-v1/v2/v3 按各自历史政策重放。
每个新 source 仍逐字等于完整锁定 Git 片段。不能扩大外围空白或段落签名比较
到数学、proof 或普通未知语法。

## 5. 冻结、实际生成与不可变装配

任何译文输出之前冻结完整新 unit、所有完整旧组及候选、实际政策/风格/词表/
translator prompt/来源术语目录。上下文保留每组所有旧成员，不能只拿身份锚点
代表全部历史。记录冻文件/hash/context_hash、Git origin、来源词数及时间。

```bash
make harness-check HARNESS_ID=codex PYTHON="$TASK_PYTHON"
```

Harness 每次动态解析，在装配时再次解析；具体模型/effort/turn 来自真实运行
元数据，不从 Harness 名、分支或旧 run 猜。snapshot 不暴露就如实记录；实际
交互运行不可重放就写 replayable:false。超出 300–1500 来源词偏好需记录完整
语义范围和显式例外，不能拼无关文本或切断证明凑词数。

当前模型必须对每个新 unit 实际生成全部五字段：translation、allowed_english、
term_occurrences、unknown_terms、notes。程序只序列化/保护/验证/装配，不能生成
中文、机械补词或把旧输出复制称为新模型生成。每次重新完整输出保留旧草稿，
只把明确通过检查的一份与唯一实际新 run/raw 绑定。

严格保留保护 token 的次数、原序及来源尾空白。数学术语每次显示
`中文（English）`，保留实际源词形和单复数，申报顺序与正文一致。unknown_terms
明确未批准的译法及语境；候选继续 DECISION_REQUIRED。源码疑点只在 remark
Issue/非正文元数据记录，忠实保留公式、遗漏或未完成条目，不补证明或说明。

装配将完整旧 unit/candidate 原字节存入 retired/derivations，新冻结来源和完整
实际五字段 raw 存入 retired/model-corrections，记录 source-restoration、v4
unit_groups、correction 和 revision run，使用已合并验证器 replay 后更新活跃
pair。已有派生的 batch 还需完整前一输出归档和所有 ancestry 验证。不可改写
历史 run/raw/证据，不能靠重算 hash 或只留代表单元隐藏历史。

兼容活跃 lane 可能仍为 openai-gpt-5.6-sol，历史身份锚点不是当前译文作者；
新修订要完整披露实际模型和 run。每个活跃五字段必须逐项等于新 raw/draft，
上下文、group、完整旧成员及 source 要独立验证。具体 v4 采用没有“一条命令
自动翻译并批准”的接口；任务装配脚本仍要审查、声明范围并调用现有验证器。

## 6. 验收与 GitHub 合并

频繁查看排版时，可以使用已实现的完整章节预览，节省整书 TeX 构建等待：

```bash
make pdf-chapter CHAPTER=categories MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"
```

输出独立 `-chapter-categories` 通道；来源语义范围仍按真实 Tag/Section/完整
batch 选择。章节预览先执行对应 render，无须再单独重复 render-chapter。
它不能替代提交前要求的全库 QA/来源检查、整书 render/pdf 和全部变化邻页验收。
代码、政策或事实未变且已有检查充分时不重复跑；真实数据改变仍须重新测量。

数据任务先独立验证全部新 Git 片段、selector/witness、每个完整旧组、五字段/
context/raw、所有 hashes、全库唯一 ID 及范围外字节。生成全部章节模板到 ignored
目录，核对并只采用任务章的真实变化。工具变化运行有意义的回归；纯数据修复
不为未变工具反复增加与实现镜像的测试。

```bash
make qa-all PYTHON="$TASK_PYTHON"
make extract-all PYTHON="$TASK_PYTHON"
make extract-all-check PYTHON="$TASK_PYTHON"
make source-alignment PYTHON="$TASK_PYTHON"
make source-alignment-check PYTHON="$TASK_PYTHON"
```

`qa-all` 已包含 workflow/harvest/index/117 模板/Schema/provenance/decision，
这组命令不再另跑同一批共享检查。另对每个实际新 run 的完整 frozen unit/raw
做直接结构QA，以免只核对兼容旧lane；路径以对应correction record为准。历史
冻结输入使用其版本合同，不能交给默认当前候选CLI重新解释。例如：

```bash
"$TASK_PYTHON" - <<'PY'
from pathlib import Path
from stacks_zh.workflow import validate_batch

correction = 'categories-yoneda-bilingual-followup-gpt61sol-20261012'
frozen = Path('translation-data/retired/model-corrections') / correction
count, errors = validate_batch(frozen / 'units.jsonl', frozen / 'candidates.jsonl',
                               Path('upstream.lock'))
assert not errors, errors
print(f'Frozen revision structural QA: PASS ({count} units)')
PY
```

历史 raw 的 QA 不授予当前采用或术语批准；当前 source-term 审计另验证活跃候选。
每个 target 容器必须
BYTE_EXACT；对应 actions/findings 清空；所有未声明范围的来源、术语、proof
及事实变化逐项解释或保持。错误不能靠归档当前问题、改状态或跳检查消失。

日常独立DATA PR中先在ignored目录生成进度/计划预览并check，合并后独立同步；
本次Issue808整合任务按用户后续授权统一更新报告、隔离复核，不逐批新开PR。
验证完整117章Section
差异，完整容器的嵌套 Tag 覆盖要依赖可重放来源证据，不能从候选字符串授予。

```bash
make render MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"
make pdf MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"
git diff --check
```

任何提交/PR 前实际 render/pdf 零退出、Final TeX PASS。模板/样式/Make/render
路径改动才追加 make template。不能编辑生成 TeX/PDF/日志绕过失败。
整书 pdftotext -layout 比较全部物理页；所有变化页及邻页转 PNG 实际看图，核对
公式、列表、脚注、分页和引用。之前实际看过的接受 PNG 若逐字一致可复用视觉
依据，但仍记录当前构建和全书比较。不因候选预览的留白或孤行改写忠实译文。

只暂存声明文件，审查完整 staged diff，提交所需 trailers，再推送当前分支并
创建 PR、附加到聊天。核对精确 PR head/base 的全部远端文件原字节和完整 diff，
GitHub-native 单 closing Issue/创建时间/owner/claimed/branch/paths/坐标。
Contents 大文件 encoding=none 时按同 repo metadata SHA 请求 blob，校验 size、
base64、Git blob hash；不能跳大文件、截 raw 或跟随任意 URL。

只有最新精确 HEAD 的 pr-contract、policy-and-data 的 run 和 job 均 SUCCESS，
且 fresh remote main 等于验收 base，才按用户授权 bypass squash：

```bash
gh pr merge "$PR_NUMBER" --repo dongyaotalk/stacks-project-zh \
  --admin --squash --match-head-commit "$VERIFIED_HEAD" \
  --subject "$VERIFIED_TITLE" --body-file build/task/merge-body.md
```

merge-body 保留实际 trailers，中文正文用 body-file 保留换行。main 变化时普通
合并前置再重新验收 HEAD/CI，不 force、不伪造 origin。合并后验证 PR MERGED、
Issue CLOSED、native remote/main SHA、reviewed feature tree、允许文件原字节、
全范围外 bytes、trailers 和干净工作区，再完成独立进度。

## 7. 常见失败与恢复

| 现象 | 下一步 |
| --- | --- |
| tomllib 导入失败 | 使用 pyenv 3.12，每条 Make 显式 PYTHON；失败前没有输出也要保留日志，不改政策 |
| 首次入库前重译导致原 raw 未消费 | 保存旧完整 v4 三文件，实际新 run 在生成前冻结全部原 run/raw/候选/字节绑定，按 §8.5 完整历史重放；已入库历史仍用原 Git archive，不删原输出 |
| 辅助后处理因日志名或续接变量失败 | 保留原失败脚本与已通过日志/产物，补齐确切依赖并从通过阶段继续；不伪造结果、不重跑未变已通过检查、不改生成物 |
| 来源包 BLOCKED | 查看完整 diagnostics/selector/源窗口，未知语法另开前置工具或政策任务，不降级或裁源 |
| 旧术语证据在合并分段后消失 | 独立核验并迁移到完整锁定Git容器，保留旧目录与冻结；只改证据且匹配输入不变时不重生成中文，实际来源／文字变化才重新完整冻结与实际生成 |
| 章末来源包误标旧v2、回放读到input | 保留拒绝和原始准备元数据；核验完整原生文档尾边界并取得v13见证，证明单元／五字段不变，完整批次重放；不允许未知宏 |
| 原保护 token、尾空白或完整五字段失败 | 保留原草稿，由实际模型完整重出并复核，不由脚本修中文或冒用旧run |
| 原 source 缺公式，内部 hash 却一致 | 比较完整锁定 Git 容器，走明确来源恢复/完整模型修订，不只在中文补数学 |
| progress 与预期数字不同 | 比较117章完整快照及真正来源覆盖，改正独立工具或事实范围，不手调生成表格 |
| 远端 main/PR HEAD 已变 | 停止旧HEAD合并，保护工作区，普通整合依赖并重验完整diff/检查/CI，不force或改origin |
| Contents API 对大文件返回空内容 | 使用已合并完整blob读取/size/Git hash核验，不删raw或跳文件 |
| PDF关键字找不到目标页 | 查看真实pdftotext排版空白和源目标数学，修正只读页选择，仍检查所有变化页及邻页 |
| 缺字、未定义引用或FinalTeX失败 | 专门修模板/字体/渲染引用并重新构建；不把成功输出PDF或修改日志当作通过 |

新克隆缺少本机ignored包时，按锁定来源及已跟踪历史重新生成；不存在可盲信的
“上次通过”缓存。冻输入或policy在生成过程中变化时，应作废本次未采用输出、
保留诊断，重新声明/prepare/freeze；不能改已有不可变证据使它看起来一致。

## 8. 完成后的交付

最终重建所有审计、默认强门禁和进度计划，保存 F1–F8 逐项证据、实际测试数、
最终编译/PDF视觉及最新 main/PR/CI。整理这里的开发步骤和复现命令，更新
Codex 提示词中的当前接受基线、未完成项、下一动作、禁止范围和验收条件。
文档与提示词使用独立 claimed Issue→本地验收→PR→精确 HEAD CI 顺序。

如仍有残项，写真实未完成状态；不要为新建 goal、换聊天、预算或长历史把现有
总 goal 标为完成。当前 goal 继续直至目标实现；若用户自行选择新建聊天/goal，
粘贴完整提示词后仍须先重新核实状态并保留已合并成果。

- 集中工具CI补充：e6e1f05远端全tool-test 613项中609通过、4失败（两未知宏前缀拒绝被新增arrow-target分支绕过，两旧policy夹具假设失效）。保留全部原拒绝样例，限定新分支独立前缀语法，只增锁定preamble中确认为零参数的Sh/etale；默认旧prefixed-symbol语义不变。18项定点回归通过，真实obsolete09AQ完整28旧分组预检通过，全库extract/check输出不变。实际再次render/pdf、FinalTeX PASS，119生成TeX及463页文字原字节相同；远端新HEAD CI仍须重查，不据局部证据冒称613全绿。

提交合同收尾：将 categories、sets 各按完整批次的英文 unit 文件是否实际进入 Git 差异分为两组，9 章共 11 个机器范围；未改动的源 unit 不伪造差异。全部 165 个完整 batch、旧新及历史 ID、真实/历史 parent、run/model 和原允许路径均保留，原 2590 路径清单按原字节另存 scope-before-pr-partition 快照，现 2591 路径。首次本地完整合同的两项 active-unit 集合错误与完整 1.8GB patch 的单次 Git 重放大小错误均留档；修正仅作用于范围声明和完整差异的分块验证，不改数据或放宽门禁。
