# 可复制的 Codex 提示词

> 2026-10-19 唯一必要纯工具前置 [Issue812](https://github.com/dongyaotalk/stacks-project-zh/issues/812) / [PR813](https://github.com/dongyaotalk/stacks-project-zh/pull/813) 已合并；最终集成接受 main 为 `991e3ed2efc22b35dbef028e0cdb5b0ae28fd187`。用户已明确授权此例外。仅修复可信门禁的大文件可空分类、回归及实测时限，完整原字节/来源/审批要求保持。全部集中DATA仍在原PR809；实际生成的DATA origin与上下文继续绑定5b527d9，不回写历史。

> 工具前置 [Issue #810](https://github.com/dongyaotalk/stacks-project-zh/issues/810) / [PR #811](https://github.com/dongyaotalk/stacks-project-zh/pull/811) 已完成并合并，接受 main 为 `5b527d9cf753ba3f589d1cc7fe9d18be31ddfd81`。完整来源恢复、组合数学文字和哈希范围清单合同已接受；原工具提交与文档历史保留，不重做此前置。后续 DATA 的 origin 使用该已接受提交，英文锁不变；现有 Issue #808 / PR #809 统一收尾全部 DATA、S5、S7和最终文档。

> 2026-10-14 用户最新执行指示：利用全库抽取与统一修复队列，集中完成全部剩余修复，取消逐批 Issue/PR 及重复整书验收。复用 claimed Issue #808、分支 `docs/progress-categories-cofinal-initial` 和草稿 PR #809，最终以一个 PR 验收全部 F1–F8（S4 → S5 → S7）。原文中的“下一批前独立进度 PR”“工具必须先单独合并”等是保留的旧执行记录，不再作为本次集中任务的步骤。各类改动保留可审查的逻辑提交，开发期按影响范围检查，最终集中执行完整门禁和 render/pdf、全书文字与全部变化及邻页 PNG 验收。范围变更仍先更新同一 Issue 的精确路径/完整新旧 ID/run/model；未知来源继续 BLOCKED，原输入、raw、历史、保护结构及真实模型生成要求保持。

使用方式：第一段可续接当前 goal；如你自行选择新建 goal，也可完整粘贴。
旧 goal 的未完成工作须如实记录；不为了交接替你创建新聊天/goal或虚报完成。
第二段用于同一集中任务内的完整数据范围；不新开逐批 Issue/PR。实际状态仍须重查。

## 1. 续接当前集中 goal：完成全部八项修复

```text
本 goal 的目标是完成 stacks-project-zh 项目的全部八项审查修复 F1–F8，
本次按用户最新指示集中修复：复用 Issue808/PR809，一个最终PR完成全部剩余S4，
随后S5默认强门禁、S7总验收及文档提示词；不再逐批开Issue/PR或重复全量验收。
原始数学、完整历史、逐次双语及真实模型完整五字段等要求保持；只改变组织与检查节奏。
包括 S4 数据修订、S5 默认强制门禁和 S7 全库集成验收。完成后写详细开发文档
和可复制的 Codex 提示词，记录架构、复现命令、验收证据和后续维护方法。

用中文回复。最终集成接受main为991e3ed2efc22b35dbef028e0cdb5b0ae28fd187，
已含工具前置PR811及唯一必要前置PR813；最近已接受DATA仍为Issue804/PR807的80463ead15a4e52bf9dea6cc01255da70a9d24c3。
英文锁定a04446e57ec1fbc252a871afcec7752fb2807b14。所有已合并成果、独立文档/进度
提交及用户未提交改动保留；实时重查Git和GitHub，不据此检查点覆盖文件。
复用claimed Issue808、分支docs/progress-categories-cofinal-initial及ready PR809。

本地已完成165批/1049旧→683完整新单元的真实模型五字段生成及装配，
全库239批/842唯一活跃unit；main仍239批/1208单元。172个新revision run的五字段
逐项等于实际不可变原输出，范围外事实原字节保持。完整旧输入、候选、run/raw及
全部递归派生/来源恢复/归档保留。不要重复生成或另领已装配的unit。

精确范围task-scopes/integrated-remediation-f1-f8-20261015.json，2591条允许路径，
hash sha256:b65670ce591f2cb8cfe64199c161281d928236675221d52512e594a1a923aea6。
所有历史scope、实际生成冻结及当时model/effort/turn/context原字节保留。
新run置信度按冻结注册表declared；snapshot未暴露不猜；Harness生成时与装配时
动态解析分别记录，不能以后来版本或当前会话身份改写既有run。

当前英文目录v18 hash为
sha256:4223840c7e8259e889e2c5b45adc3c848f322c2e3704df70ccf94534491943fe；
842单元识别6507次来源出现、688份Git见证。v16旧证据迁移保留，v18增加有完整
独立Git见证的affines/glueing，不批准中文，不回写生成时实际目录。
原162批/677单元第三次完整qa-all已终态通过1564.582秒；其后严格探测另发现
002T/04AR/000I三个完整批次共6单元尾空白不等，已冻结完整旧组/56份ancestry并
实际重新生成完整五字段，未程序补换行。最新239批/842单元严格来源探测0错误，
实测57.473秒；该探测不包含完整历史溯源。全库独立源结构、术语及proof审计已对最新842单元通过，零坐标/未保护TeX/
隐藏脚注/标题/术语错误，187组/187完整proof全部match。不能把旧677单元qa-all
冒称后6单元或最终S7证据；当前事实hash不变时保留最新实际通过的独立审计。

S5已在本地实现：current_qa.py默认覆盖六个validate/assemble/render入口；
repository_validation.py让make qa-all/CI在同次调用执行Schema、完整递归溯源、
决策与全部当前候选。InputSnapshot绑定实际HEAD/文件集合/原字节；只有本次实际
完整溯源通过的私有内存凭证可复用，不存在磁盘PASS缓存或skip选项。独立
决策命令仍完整验证历史。历史快照仍按原版本合同，不用当前门禁重解释旧raw。
统一make qa-all已完整退出0，989.962秒，Schema/全部历史溯源/决策/239批严格
当前QA全通过，输入hash不变。完整工具测试执行653项，651通过、2个旧CLI
fixture失败；保持生产代码，成功样例补锁定Git来源，配对测试保留原断言，随后
CLI/当前QA/会话/决策/全lane聚合41项全部通过。原失败记录保留，其余生产输入
未变，不无理由重跑已通过的全库QA；最终远端精确HEAD仍真实执行全部测试。
全部172新run/683记录的完整冻结输入结构QA通过29.382秒。

最新S7全库extract-all/check和source-alignment/check四项均退出0，分别
72.585/72.889/99.414/102.135秒。239队列actions及source/term/proof findings全空；
745BYTE_EXACT/97PRESENTATION_EQUIVALENT，零坐标/来源/术语/proof诊断；
6507次术语要求/688Git见证全通过，187组/187proof全部match。
生成器progress/check、plan/check及隔离117章生成/check通过，README与两报告
原字节一致，未手改数字。本地render/pdf/template全部已终态通过，分别1215.720/69.975/16.217秒，
整书457页、模板13页，最终日志均通过。首次沙箱字体失败保留，同命令访问本机
字体服务成功，未改模板/译文/生成物。新版237变化及邻页、另3页目录/书末及
全部13模板页已实际查看；其余页面正文与已查看的接受基线逐页文字/字体/位置/
矢量等同。两处F6脚注中文可读，PDF实际内链到注记4.2.2（PDF44）。
inspect-final-pdf.py及s7-visual/manifest.json为本机现场证据，不能把旧PENDING
快照当作当前状态。不要重启已完成的QA/工具测试/抽取对齐或构建。
这些修复已按8个逻辑提交普通推送到PR809（ready），feature HEAD为
a17f465633986a9578ac3cef6eac283841fd87c8，tree为7e82b1669690e5fdad6c72d17af64d0da75af8e7。
完整staged diff、2362文件远端head/base原字节、完整patch分块重放及唯一native closing808均通过。
最新policy-and-data run39160048942/attempt2/job117772514093真实SUCCESS：653测试全绿，
完整239批QA及117章progress/plan check通过。首次临时Git清理失败日志保留。
远端pr-contract run39160074588/job117771399704失败：12MB文件isTruncated=true/
isBinary=null被main旧工具拒绝。只允许truncated时分类null的草案仍校验完整blob长度、
Git hash及UTF-8，42回归、真实12MB完整字节和整份PR native复验均通过；整份读取
1325.148秒，总1386.017秒，2362文件/2327完整内容，零合同错误，不冒充远端job成功。
草案/计划在build/task-integrated-remediation/trusted-large-blob-fix.patch及
trusted-large-blob-plan.md，包含可信job时限30分钟，可信main来源和权限保持。
用户已明确允许唯一必要纯工具前置PR813，它已MERGED、Issue812已CLOSED，
接受main991e3ed2efc22b35dbef028e0cdb5b0ae28fd187；tool head39d5464的
policy-and-data run39179060126/job117827741453、pr-contract run39179060156/
job117827742071均成功，完整远端bytes/patch/native合同、实际render/pdf、全书
文字/像素及日期变化页/邻页视觉和postmerge tree/bytes/clean通过。工具4文件
不改任何DATA，原生成origin5b与全部冻结/run/raw不重绑。无需再次询问此前置。
继续原PR809，普通合入已接受main，不force。完成最终文档、实际lane render/pdf
和全书差异对照，保留未变完整验收；最终最新精确HEAD双CI run/job真实成功、
完整remote bytes/patch/native单closing与fresh main正确后，已授权admin squash，
不再问确认，验MERGED/CLOSED/main-feature树/原字节/clean和最终progress/plan。
先只读查PR809实时状态：如已MERGED且最终证据齐备，转维护，不重做165批；
如仍OPEN，完成以上原任务收尾，不新增DATA任务或模型生成。
总goal仍未完成，不重复生成数据或重跑未变完整本地验收。
用已保存的accepted-main-5b-render-baseline作为旧视觉基线，不能覆盖基线或改
生成物绕过失败。最终更新详细指南、全部F1–F8证据和可复制命令/维护提示词。
当前本地S7及构建视觉已完成，远端验收与合并未完成，保持总goal进行中。远端808/809精确scope
按授权在本地验收完成后统一更新，不再逐批建Issue/PR。

PR811所有35工具路径和627测试/239QA/全库抽取对齐/实际构建已接受。
05SH/05PU、0AHK以及DATA770/PR775与进度PR777均已完成，不重复恢复或认领。
691/698/699已由PR759书末版本勘误表留档关闭，不表示英文数学被修改。
原DATA804未生成计划和stash 644dd0588ca8861a28e2e507115715167b46e353保留，不pop/drop。
未支持语法仍BLOCKED；来源疑点只source-only remark，忠实保留公式与证明，不补证。
词表批准、critic、语言/数学人审及发布全部待决，当前goal继续全部F1–F8。

本地使用pyenv已安装的Python3.12，每条Make显式传同一PYTHON；本检查点实际
3.12.6。频繁排版可用make pdf-chapter CHAPTER=categories MODEL=openai-gpt-5.6-sol，
但不能替代提交前规定的全库检查和整书render/pdf。未知语法/数学文字仍BLOCKED。

这是已开展项目的续接，不是重新从零开发。先只读核实当前工作区、Git 分支及
HEAD、GitHub 最新 main、打开 PR/claimed Issue 和实际审计；保留已合并成果及
用户未提交改动，不根据交接快照直接覆盖文件或重复做已完成任务。

先读 AGENTS.md、WORKFLOW.md、docs/engineering-remediation.md、
docs/remediation-development-guide.md、docs/source-extraction.md、
docs/source-alignment.md、docs/source-container-restoration.md、
docs/model-provenance.md、docs/source-term-inventory.md、
docs/task-allocation.md、docs/translation-priority.md、docs/github-collaboration.md、
docs/git-conventions.md 以及任务相关 docs/config。存在未合并数据任务时先核实
并收尾，不新认领相同 unit/candidate 文件。

继续原 F1–F8 的全部范围，不把当前单批或通用抽取器完成当作总目标完成。
全库抽取器已实现，可一次生成锁定 Git 来源库存及统一修复队列；READY/BLOCKED
仅是来源准备状态，不能自动改事实。从最新事实重建 extract-all/check 和
source-alignment/check，按 repair-queue 的真实完整语义范围继续修复。
优先收尾尚存坐标/未保护 TeX/来源诊断，然后集中完成来源术语覆盖，全部数据
修复后才启用 S5 强门禁和完成 S7。不能仅凭 qa-all 通过就声称来源术语已经完整。

复用已claimed Issue808和现有分支/草稿PR809，保持完整开发/验收计划。
范围变更先在同一Issue声明owner、branch、锁定source、真实chapter/历史与当前parent、
完整旧新unit IDs、精确allowed_write_files和真实run/model，再机器核验。工具/政策、
实际数据、S5和文档保留可审查逻辑边界，全部在同一个最终PR验收，不另开逐批任务。

英文 harvest 和 upstream.lock 保持；不用行号或页码作为范围，不送原 TeX
整文件给模型。完整来源容器从锁定 Git 重新核验真实 owner/Section/selector/
边界及原字节；未知语法/数学文字继续 BLOCKED，不调整规则来掩盖残项。

每次实际生成前冻结完整新 unit、每个完整有序旧组及全部候选、完整 ancestry、
政策/风格/词表/prompt/来源词目录及 context hashes。Harness 运行时动态解析，
模型/effort/turn 根据真实元数据记录；不要复制旧值或猜 snapshot。
当前模型必须实际生成每个新单元完整五字段，程序只保护、序列化、验证和装配，
不能生成中文、机械补术语或把旧输出冒称新模型输出。每个五字段与不可变 raw
逐项相等，保护 token 原序/次数/尾空白严格保持。所有数学术语逐次中文（English），
未知词待决，不授予术语/critic/语言/数学审校或发布批准。
完整旧输入、原输出/run、派生及所有恢复/归档历史原字节保留；有证据地重放
v4 完整分组，不遗弃、重复或归档当前问题以减少残项。

源码 typo、缺失证明或数学疑点只记录 source-only remark；忠实保留原数学，
不补证明、改公式或在正文添加译者说明。remark 不单独阻塞忠实候选。

本地核验 target Git 原片段、全部五字段/context/历史绑定、术语覆盖、全库唯一
ID 和范围外字节；239 全量候选 QA、实际新 run QA、全部所需 Schema/溯源/
决策/来源/117 模板、全库抽取和对齐 check、隔离进度/计划及适用测试通过。
不要无理由反复运行已通过的未变测试。任何 commit/PR 前实际执行当前 lane
make render MODEL=openai-gpt-5.6-sol 和 make pdf MODEL=openai-gpt-5.6-sol，
最终 TeX 无错误；适用模板变化才 make template。比较整书文字，实际查看所有
变化页及邻页 PNG，不能修改生成物绕过失败。generated/build/PDF/本机路径不提交。

集中本地完成后审查完整 staged diff，只提交允许文件；推送当前分支并更新已附加的
草稿PR809，只有全部S4/S5/S7与文档验收完成才转ready。核对精确 head/base 的全部远端文件原字节、完整 patch、GitHub-native
单一 closing Issue 合同，以及最新精确 HEAD 的 pr-contract 和 policy-and-data
run/job 均成功、fresh main 等于接受基线。达到上述条件时，已授权使用 admin
bypass squash 合并，无须再问确认，merge body 保留所需 trailers；不直接推 main、
不 force、改 remote/保护规则或伪造人审。合并后核实 main/feature tree、PR MERGED、
Issue CLOSED、原字节和干净工作区。本次只做一个最终合并；集中真实生成/check
progress/plan，即使报告不变也保存真实检查，不手改数字，不再逐批进度PR。

除非我明确要求或适用 AGENTS/skill 明确要求，不创建子代理或新聊天，不安装无关
依赖。每约 60 秒用简洁中文汇报真实进展，报告修复前后 counts、下一动作和实际
阻断；不要给未经测量的百分比或工期。只在 F1–F8 最终证据齐备后把 goal 标完成。
如因真实外部条件阻断，遵守 goal 的连续阻断判定，不用困难/耗时代替阻断。
最后交付可审查的详细开发文档与完整可复制提示词，包含最新 main、已合并 PR、
剩余/最终审计、运行命令、门禁及维护边界；未完成部分必须如实列出。
```

## 2. 同一集中任务中的完整数据范围

替换尖括号时只用实时完整队列/锁定 Git/实际元数据，不发明 ID 或路径。

```text
在现有Issue808、分支docs/progress-categories-cofinal-initial、草稿PR809内集中修复
<完整chapter/语义范围>，总目标保持全部F1–F8/S4/S5/S7。不要为每批新开Issue/PR。
先核对Git/main/当前在制工作，读取所有完整旧unit/candidate/全部ancestry，用锁定Git
确认真实owner、Section、标题层级和完整边界。先更新同一Issue的完整旧新ID、精确
允许路径和真实run/model，再机器校验。来源与工具支持须先通过适用独立回归，未知
仍BLOCKED；准备状态不能自动采用或降低事实残项。

实际生成前冻结完整新来源、完整有序旧组/全部候选/历史、policy/style/glossary/
prompt/catalog/context hashes；Harness动态解析，实际model/effort/turn逐次读取。
实际模型每新unit完整生成五字段，和immutable raw逐项相等，保护token原序/次数/
尾空白保持，数学术语逐次双语且待决。程序只保护/序列化/验证/装配，不生成中文。
全部旧source/raw/run/所有历史保留并完整重放，不截短、遗弃或归档当前问题。

开发期做影响范围检查，及时记录真实变化/阻断；按章构建用于频繁排版。全部S4后
才启用S5，再集中做239QA/各新run QA/Schema/溯源/决策/来源/117模板/全库抽取及对齐
checks/progress-plan/S7总验收、整书render/pdf/全文及全部变化和邻页PNG实际查看。
提交时仍遵守适用AGENTS和本goal的构建要求；不为每批重复创建提交/完整验收。
最终完整staged和远端字节/patch/native唯一closing808、精确HEAD双CI run/job和fresh
base通过后，才按已有授权admin squash一次；postmerge tree/bytes/MERGED/CLOSED/clean。
没有独立术语、critic、语言/数学审校或发布批准，不以单个范围完成结束总goal。
```

## 3. 最终文档验收

```text
在全部 F1–F8 实际验收完成后，整理详细开发文档和可复制 Codex 提示词。
从最终当前事实重建来源/术语/proof 审计、默认 QA/CI、进度/计划，不靠历史数字。
逐项列 F1–F8 的实现位置、来源依据、拒绝回归、真实命令结果、最终 main/PR/CI，
说明候选修复与人工审校/正式发布的边界。提供 Python/TeX 等环境要求、可复制
运行步骤、完整容器与模型修订/历史流程、常见失败和恢复方法、后续维护提示词。
文档在同一Issue808/PR809内形成可审查的独立逻辑改动，不授予批准；最终实际
render/pdf、完整远端diff/native合同及最新精确HEAD双CI run/job通过后按授权合并。
只有所有必需工作和文档交付均完成，才把总 goal 标 complete。
```

- 集中工具CI补充：e6e1f05远端全tool-test 613项中609通过、4失败（两未知宏前缀拒绝被新增arrow-target分支绕过，两旧policy夹具假设失效）。保留全部原拒绝样例，限定新分支独立前缀语法，只增锁定preamble中确认为零参数的Sh/etale；默认旧prefixed-symbol语义不变。18项定点回归通过，真实obsolete09AQ完整28旧分组预检通过，全库extract/check输出不变。实际再次render/pdf、FinalTeX PASS，119生成TeX及463页文字原字节相同；远端新HEAD CI仍须重查，不据局部证据冒称613全绿。

## 4. 验收后维护的完整提示词

```text
用中文维护 stacks-project-zh。先只读核实 Git 状态、分支、HEAD、fresh remote
main、打开/claimed Issue和PR809的实际状态，不据旧文档覆盖当前文件。
如果PR809已MERGED且合并后证据齐备，不重做此前165完整批次、683新单元和
172实际run。239批/842单元及零残项是本次检查点，必须从当前事实重新测量。

先读AGENTS.md、WORKFLOW.md和docs/remediation-development-guide.md、
engineering-remediation、source-extraction、source-alignment、source-container-restoration、
model-provenance、source-term-inventory、task-allocation、translation-priority、
github-collaboration、git-conventions及相关config；可信大文件门禁另读
docs/pr-contract-large-blobs.md。保留已合并成果、用户改动、所有独立文档/进度
提交和不可变历史。未经明确要求，不创建子代理、新聊天或安装无关依赖。

本地用已安装pyenv3.12；本次实测3.12.6。先设置
TASK_PYTHON="$(PYENV_VERSION=3.12.6 pyenv which python)"，每条Make显式传同一PYTHON。英文
harvest只读、upstream.lock锁定a04446e57ec1fbc252a871afcec7752fb2807b14；
没有专门上游同步授权不改来源。READY/BLOCKED只表示准备状态。

先写开发/验收计划；需要变更时先claimed Issue，声明owner、分支、source commit、
真实chapter/owner/Section/selector、真实和历史parent Tags、完整旧新/历史IDs、
精确allowed_write_files及实际run/model范围，再建分支实施。范围扩大先更新Issue。
存在未合并同unit/candidate任务时先核实收尾，不重复认领；按任务授权组织PR，
不为同一个完整修复范围逐条开Issue/PR或重复整书验收。

从锁定Git重新验证完整来源容器、边界和原字节，不用行号/页码当范围，不送
原TeX整文件给模型；未知语法或未分类数学文字继续BLOCKED，不降规则掩盖问题。
实际生成前冻结完整新unit、每个完整有序旧组/全部候选、全部ancestry、政策/
风格/词表/prompt/英文目录/context hashes。Harness动态解析，model/effort/turn
依实际元数据记录，不复制旧值或猜snapshot。实际模型完整生成每个新unit五字段；
程序只保护、序列化、验证、装配，不能生成中文或机械补词冒称模型输出。
逐项等于immutable raw，保护token原序/次数/尾空白保持，数学术语逐次双语，
未知词待决，不批准术语、critic、语言/数学审校或发布。全部旧source/input/raw/
run/派生/恢复/归档原字节保留，完整v4组重放，不遗弃或归档当前问题减少残项。

源码typo、缺失证明或疑点只source-only remark；书末勘误表注明锁定英文版本，
不改公式、补证或在正文插译者说明，remark不单独阻断忠实候选。

日常排版用完整章节预览make pdf-chapter CHAPTER=categories
MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"。按实际影响范围回归，未变且已
通过的检查不无理由重跑。最终统一make qa-all执行完整Schema/历史溯源/决策/
全部当前严格QA，独立extract-all/check、source-alignment/check及来源/术语/
proof审计另行核对；不能仅靠qa-all认定术语完整。当前六CLI默认强门禁及
九项政策保持；不得加入skip或磁盘PASS缓存，独立decision仍完整溯源。

真实生成/check progress和plan，必要时隔离117章核验，不能手改统计。提交前
实际make render MODEL=openai-gpt-5.6-sol和make pdf同lane，FinalTeX无错误；
模板/样式/Make/渲染路径改变才追加template。比较全部TeX及整书文字，实际
查看所有变化及邻页PNG；无变化页须绑定真实视觉基线，不抽样冒充完整检查。
不改生成物绕过失败；build、PDF、PNG、生成TeX、本机路径和凭据不提交。

审查完整staged diff，仅允许文件提交；当前分支普通推送。核对精确head/base
全部远端原字节、完整patch与重放树、GitHub-native唯一closing Issue合同和
最新精确HEAD的pr-contract与policy-and-data真实run/job成功，fresh main等于
接受base；合并权限依本次任务明确授权执行。当前PR809的admin squash已获授权，
无需重复询问；未来任务按其授权边界执行。不得直接推main、force、改remote/
保护规则或伪造人审。合并后验MERGED/CLOSED、main/feature树、原字节和clean。

用简洁中文报告真实计数、下一步和实际阻断，不猜百分比或工期。最终交付详细
开发说明、实际命令和验收证据、main/PR/CI精确值、维护边界与可复制提示词；
未完成如实列出，全部目标真实完成后才标goal complete。
```
