# 八项审查修复开发与交接指南

> 2026-10-14 用户最新执行指示：利用全库抽取与统一修复队列，集中完成全部剩余修复，取消逐批 Issue/PR 及重复整书验收。复用 claimed Issue #808、分支 `docs/progress-categories-cofinal-initial` 和草稿 PR #809，最终以一个 PR 验收全部 F1–F8（S4 → S5 → S7）。原文中的“下一批前独立进度 PR”“工具必须先单独合并”等是保留的旧执行记录，不再作为本次集中任务的步骤。各类改动保留可审查的逻辑提交，开发期按影响范围检查，最终集中执行完整门禁和 render/pdf、全书文字与全部变化及邻页 PNG 验收。范围变更仍先更新同一 Issue 的精确路径/完整新旧 ID/run/model；未知来源继续 BLOCKED，原输入、raw、历史、保护结构及真实模型生成要求保持。

> 集中任务的唯一必要前置为 claimed [Issue #810](https://github.com/dongyaotalk/stacks-project-zh/issues/810) / [PR #811](https://github.com/dongyaotalk/stacks-project-zh/pull/811)，分支 `tool/bulk-task-scope-validator`，精确范围已先更新为35文件：已完成的来源恢复/组合数学文字基础30文件，加上哈希范围清单合同5文件。原因有二：pr-contract固定从可信main加载且原合同限100文件/单章2–8 parents；恢复历史还强制origin为HEAD可达祖先，并从该提交读取宏政策，故不能把最终squash会丢弃的feature提交作为DATA origin。先接受这一个完整工具前置，再在其实际squash main的干净工作区一次prepare/check全部107批，将包按原字节带回#809生成/装配；不猜未合并SHA，不削弱祖先或政策核验。#809统一完成全部DATA、S5、S7及最终文档，不重新逐批拆任务。e6e1f05/8566396/466e24d原工作保留；未生成或采用新DATA，不改英文lock、CI信任来源或保护规则。

本文是开发方法和交接材料；事实状态必须从当前分支的结构化数据、审计与 GitHub
重新读取。它不代替 `WORKFLOW.md`、`config/` 政策或不可变溯源证据。

## 当前集中任务在制状态（未合并）

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
做直接 QA，以免只核对兼容旧 lane；路径以对应 correction record 为准。例如：

```bash
TASK_CORRECTION=categories-yoneda-bilingual-followup-gpt61sol-20261012
"$TASK_PYTHON" stacks_zh.py validate-many \
  --units "translation-data/retired/model-corrections/$TASK_CORRECTION/units.jsonl" \
  --candidates "translation-data/retired/model-corrections/$TASK_CORRECTION/candidates.jsonl" \
  --lock upstream.lock
```

历史 raw 的 QA 不授予当前采用或术语批准；当前 source-term 审计另验证活跃候选。
每个 target 容器必须
BYTE_EXACT；对应 actions/findings 清空；所有未声明范围的来源、术语、proof
及事实变化逐项解释或保持。错误不能靠归档当前问题、改状态或跳检查消失。

数据 PR 中只在 ignored 目录生成进度/计划预览并 check；实际报告在 DATA 合并
后用独立进度 Issue/PR 更新，必须先于下一 DATA。验证完整 117 章 Section
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
| 旧术语证据在合并分段后消失 | 独立任务将明确来源锚点迁移到完整锁定容器，验收合并后重新prepare/freeze/实际生成 |
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
