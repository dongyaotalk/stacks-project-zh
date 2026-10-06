# 2026-10 项目审查修复开发计划

计划任务：[Issue #530](https://github.com/dongyaotalk/stacks-project-zh/issues/530)。

## 1. 目标与基线

按项目审查发现的八项问题完成规范、工具、数据和构建修复。执行顺序为：
开发设计 → claimed Issue → 实现与回归测试 → 本地验收 → 分支推送 → PR。
每个 PR 只关闭其对应的一个、早于 PR 创建的 Issue；不向 `main` 直接推送。
本计划的完成标准是全部八项修复通过验收并提交 GitHub PR，不以只修工具或只更新
进度作为完成，也不自行宣告术语批准、人工审校或正式发布。

基线中文 commit：`736d74c3c6eea947fb9c16436f6296b54c13807b`。
英文来源固定为 `a04446e57ec1fbc252a871afcec7752fb2807b14`，不修改英文 harvest
或 `upstream.lock`。基线包含 239 个 candidate batch、1,480 个 unit/candidate。
98 项工具测试和全量候选 QA 通过；整书 AJbook PDF 能编译，但仍有两处未定义
引用和正文 `δ` 缺字。`progress-check` 失败，`plan-check` 通过。

## 2. 问题、设计与完成证据

| 编号 | 问题 | 实现设计 | 验收证据 |
| --- | --- | --- | --- |
| F1 | 6 个 Categories batch 的 44 个带标签数学陈述使用外围 Section Tag | 校验所有自身带标签的数学陈述；按真实永久 Tag 迁移陈述及其证明、邻居坐标；保留旧→新映射 | 对锁定 `tags/tags` 全量核对，无错配、冲突或重复；准备范围和进度识别真实 Tag |
| F2 | 数学术语漏报仍被标为 `TERM_OK` | 建立来源侧术语出现清单，校验器独立核对覆盖、次数和显示；补齐现有候选的双语文字和记录；未批准词条维持待决 | 删除、漏报、少报、重复或改写任一要求的术语均失败；现有候选完整通过强制检查 |
| F3 | revision 自报 `CLEAR` 可绕过候选待决术语 | 正式门禁检查所选候选及词表批准依据；没有可验证批准时拒绝正式 revision | 原复现中的 `DECISION_REQUIRED → PUBLISHED` 被拒绝；有真实批准依据的合法路径通过 |
| F4 | `%` 等 TeX 控制字符可吞掉受保护正文；后续发现旧提取已遗漏上游公式 | 校验未保护 TeX；对旧提取缺陷另建锁定 Git 来源恢复合同/工具及实际重译，保留原输入 | 控制符、分组、math delimiter 回归被阻断；全部当前证明/链对照锁定英文，来源遗漏有完整恢复证据并通过验收 |
| F5 | 替换链首版本被误要求提供前驱 | 以 unit 为边界验证单一首版本、前驱引用、状态和有向无环替换链 | 两版及多版正常替换通过；自引用、循环、跨 unit、多个首版本或冲突后继失败 |
| F6 | 两处脚注全文作为占位符锁定，且内部局部引用失效 | 只保护脚注包装和引用，把自然语言提取为翻译节点；规范渲染引用，保留原文指向 | `0AHN`、`0FWX` 脚注有中文正文，无 `See Remark` 残留，引用解析成功；包装与标签不变 |
| F7 | 正文 Unicode `δ` 缺少字体字形 | 使用已有可再分发字体/模板机制覆盖正文希腊字母；构建检查缺字日志 | 整书最终日志无 `Missing character`；模板烟测和含希腊字母的回归书稿通过 |
| F8 | README 与详细进度报告落后于数据 | 数据修复完成后确定性生成报告；同时核对翻译计划 | `progress-check`、`plan-check` 均通过，报告仅依据已采用的分支事实数据 |

术语清单必须由源节点和可审查的提取规则提供，不能重新使用候选自报的空数组
作为完成依据。自动清单与语义范围的局限须明确记录，不能声称确定性程序已经完成
全部人工数学审校。词表目前无 approved 条目；本任务不新增任何 approved 状态。

## 3. 先解决历史迁移规范冲突

`docs/data-model.md` §2.2 现要求坐标迁移同时改写 candidate 和 run manifest，
但 `AGENTS.md` 和 `docs/model-provenance.md` 又规定历史 manifest 不可覆盖。
在涉及历史数据的实现前，先提交独立规范修复，统一采用以下合同：

1. 原始 run manifest 和原始模型输出保留原字节及 hash，不把新改动归于旧模型生成。
2. 坐标变更、来源节点重提取、双语文字补齐分别保存可审查的迁移/派生记录，记录
   输入快照、变换规则、工具版本、输出 hash、旧→新坐标及受影响范围。
3. 活跃数据只能存在一个当前版本。保留的原始输出属于历史，不计入当前进度或 TM。
4. 机械变换有独立派生来源；若需要模型重新生成自然语言，必须创建实际模型身份
   和动态 Harness 版本可验证的新 run，不能冒用原 GPT-5.6-sol 身份。
5. 修复候选仍为未经人工审校的预览。语义或内容 hash 变化不会继承人工批准。

Schema、读取接口和 provenance checker 必须同步实现这一合同。不能靠修改历史
manifest 的 hash、忽略旧数据或放宽 QA 来取得通过结果。

## 4. 分阶段实施与 PR 边界

| 阶段 | 工作 | 分支/PR 类型 | 依赖 |
| --- | --- | --- | --- |
| S0 | 写入本开发计划、问题矩阵和验收合同 | `docs/review-remediation-plan` | 无 |
| S1 | F3 正式术语门禁、F5 替换链及独立回归 | `tool/decision-gates` | S0 |
| S2 | 历史迁移规范、派生记录 Schema 与溯源支持 | `docs/*` 与 `tool/*`，规范和工具分别提交 | S0 |
| S3 | F1/F2/F4/F6 的来源检查、迁移工具和失败回归 | `tool/*`；工具与事实数据分开提交/PR | S2 |
| S4 | 对相邻 Section 分组迁移坐标、脚注、术语记录及候选；保留原始快照 | 按 chapter/相邻 Tag 拆分的数据 PR | S3 |
| S5 | 在全部当前数据上启用严格门禁，补充 CLI/Make/CI 集成 | `tool/*` 或 `build/*` | S4 |
| S6 | F7 字体覆盖与最终编译日志检查；渲染引用验收 | `template/*`、`build/*`，保持可回退边界 | S3；最终验收依赖 S4/S5 |
| S7 | F8 进度/计划再生成和八项总验收 | 独立 `docs(progress)` PR | S1–S6 |

Issue 创建时必须包含 `task_id`、owner、branch、精确 `allowed_write_files` 和验收
条件。数据 Issue 还必须声明锁定 source commit、chapter、一个 parent Tag 或
2–8 个相邻 parent Tags、完整旧/新 unit 范围、快照与派生路径。范围变化时先更新
Issue，再写入新增路径。

F1 已确认的 batch 为 `categories-003G`、`categories-02X8`、`categories-003O`、
`categories-02XG`、`categories-02XJ`、`categories-04Z2`；先核对其 Section 顺序，
再拆分相邻组。F6 为 `categories-0AHM` 与 `categories-0FWW`。F2 的全量扫描还
必须覆盖其余当前章节，不能只修最新两个 batch。词表、模型注册、来源锁和 reviewed
数据不属于普通数据迁移的写入范围。

有依赖且尚未合并的 PR 使用明确的前序分支作为 base，并在正文说明依赖顺序。
完成的含义包括最终集成分支通过全部验收和 GitHub 检查；不把尚未完成的前置或
后续 PR 标为已修复。PR 合并仍由维护者处理。

## 5. 本地验收与发布到 GitHub

每个提交/PR 前执行适用的检查并保存命令结果：

```bash
make workflow-check
make harvest-check
make upstream-index-check
make tool-test
make schema-check
make provenance-check
make decision-check
make qa-all
make render MODEL=openai-gpt-5.6-sol
make pdf MODEL=openai-gpt-5.6-sol
git diff --check
```

修改模板、Makefile 或渲染路径时额外执行 `make template`。进度阶段运行
`make progress` 后必须执行 `make progress-check`；计划内容变更时执行 `make plan`
和 `make plan-check`。构建日志、TeX、PDF、缓存和本地绝对路径不提交。

S0/S1 的编译可以保留已知、尚待 S4/S6 修复的两处引用与缺字，但必须以零状态
退出并在 PR 中明确列出剩余事项。最终集成验收必须没有这些问题，不以“PDF 已输出”
代替完整检查。

本地验收成功后，只暂存声明范围内的文件，检查暂存 diff，按项目格式提交，再
推送当前任务分支并创建 PR。PR 关联且只关闭对应的 claimed Issue，填写真实 QA
结果，不填写虚假的 Reviewed-By 或模型/Harness 版本。最后检查 GitHub 的
`pr-contract` 和 `policy-and-data`，并将每个创建的 PR 附加到本聊天。

## 6. 完成审计清单

- [ ] F1：所有当前带标签数学陈述均使用正确永久 Tag，证明和邻居坐标一致。
- [ ] F2：当前译文术语覆盖完整，遗漏不能通过，待决状态有来源依据。
- [ ] F3：缺少术语批准的正式 revision 被拒绝。
- [ ] F4：特殊字符不能静默吞掉正文或改变保护结构。
- [ ] F5：合法替换链通过，非法链被拒绝。
- [ ] F6：两处脚注翻译完整，内部引用正确。
- [ ] F7：最终整书无缺字和未定义引用，模板烟测通过。
- [ ] F8：生成报告和计划与最终当前数据一致。
- [ ] 原始 run/candidate 快照可核验，派生结果未冒充原模型生成或人工审校。
- [ ] 最终集成分支所有本地必需检查通过，生成产物未提交。
- [ ] 每个 PR 都有更早的 claimed Issue，已推送且 GitHub 必需检查通过。

此清单只有取得对应的实际文件、命令和 GitHub 状态证据后才能勾选。

## 7. 执行记录

- 完整来源容器与分组修订工具：Issue
  [#605](https://github.com/dongyaotalk/stacks-project-zh/issues/605)，分支
  `tool/source-container-restoration`，落实已合并的规范 PR #604。新增完整锁定 Git
  来源证据、确定性事实 lowering、独立 v4 分组及完整历史重放；陈述/列表、复杂命名
  标题、多段/多份证明和长正文/脚注保留原字节，未知宏和未分类数学文字继续阻断。
  每个新输出需要实际模型五字段与全部旧组 revision context；来源/审批绑定及预览
  披露全部原生成和修订身份，锚点只兼容历史字段，不授予任何审校或术语批准。
  只读准备/check 输出完整旧批次和新来源提议；生成期间的事实、政策、plan、输出
  或 symlink 变化拒绝，旧包篡改/无关文件拒绝，失败替换可回滚。PR 范围覆盖全部
  旧新 ID、新 unit/selector；旧错误 parent 仅限显式关联的历史快照/直接前继归档。
  本地337项工具回归通过，包含 v1/v2/v3/v4 祖先、拆分/合并、篡改/孤立/冲突、
  来源类型/风险/模型/Harness及旧审批绑定；239批QA、117章模板/progress/plan与
  全部适用门禁通过。459页当前整书、12页模板最终编译日志 PASS；真实001Y完整
  来源的2页独立生成层 smoke 也无编译/引用/缺字错误，不是实际新译文或模型输出。
  重新生成并check全库43,270提议单元与当前239批/1480输入修复队列；逐项核对全部
  21组proof差异，10组SOURCE_PREPARED、11组BLOCKED，均继续计为原mismatch。
  001Y完整14个旧单元已只读准备为陈述/证明2个提议单元，其他列表/长脚注证据保留。
  本工具不修改真实unit/candidate、run、政策、英文或lock；861个术语问题候选、
  76个坐标、96条source诊断与21组proof差异不减少。工具验收合并后另开数据任务，
  S4/S5/S7及原八项最终验收继续，不以工具或库存成功代替事实修复。

- 完整容器恢复与分组历史合同：Issue
  [#603](https://github.com/dongyaotalk/stacks-project-zh/issues/603)，分支
  `docs/source-container-restoration-contract`。本任务基线 main 为
  `6a5c6c817d9d2ab7e82d900babcef3fc747adb82`；最近相邻 09WN/04AS 与 04AX/04AY
  数据修订及独立进度复核已合并/完成。当前仍有861个术语问题候选、76个坐标、
  96条source诊断和21组proof差异，原八项总验收未完成。
  现有§9只支持单单元简单证明，无法采用全库库存中的完整定义/列表及分段proof。
  先在 `docs/source-container-restoration.md` 写明锁定Git完整容器、原字节证据、
  旧新多对多分组、全部祖先历史、真实完整模型修订、审批绑定和失败回归，再另开
  Schema/工具任务实现v4。当前版本与数据不变，未实现前禁止写真实v4记录；
  具体数据仍另开任务，不能用更小的可通过范围代替F1–F8、S4/S5/S7的全量目标。
  本次六份规范/开发文档范围验收通过：304项既有工具测试、239batch QA、117章
  progress/plan和全部适用来源/Schema/溯源门禁成功，当前通道459页整书最终日志
  PASS；Schema/工具/事实尚未按新合同改变，完整容器采用留待第2/3步实现。

- 当前译文来源对应与统一修订队列：Issue
  [#595](https://github.com/dongyaotalk/stacks-project-zh/issues/595)，分支
  `tool/source-alignment-repair-queue`。先写 `docs/source-alignment.md`，再实现只读
  对应和集中清单。全库库存保持锁定英文来源；当前239batch/1480unit按真实
  owner/proof链限定、唯一连续token定位，数学、网址、引用键和literal按原字节。
  当前文件/审计政策hash、来源byte span、真实Tag提案和三份原审计集中保存，
  不改写任何事实、历史run或来源恢复合同。对应1个BYTE_EXACT、1209个
  PRESENTATION_EQUIVALENT、267个SOURCE_DIFFERENCE、3个AMBIGUOUS；79个坐标、
  907个坏术语候选/3027条术语诊断、99条来源诊断和21组proof差异均保留。
  proof差异14组可作排版/已核实别名定位、7组仍有严格来源差异，全部原mismatch
  与节点/正文diff仍保留；工具成功不表示来源修复、译文修订或人工审校完成。
  独立synthetic回归验证owner/重复/顺序、多proof与split链、保护参数、缓存和
  快照篡改、安全输出及确定性check；本任务不创建实际模型run或授予词条批准。
  完整239batch/1480unit清单生成及check通过，三份原审计全部残项保持可追踪；
  当前通道457页整书和12页模板编译通过，最终日志门禁通过。

- 全库通用来源抽取：Issue [#592](https://github.com/dongyaotalk/stacks-project-zh/issues/592)，
  分支 `tool/universal-source-extractor`。按用户要求先集中准备来源与问题库存，新增
  `extract-all`/确定性 check；默认枚举锁定 Git 的全部 117 章，产物只写 ignored
  source-ir/build，提议单元、完整字节覆盖片段、永久 Tag 归属和诊断分离保存。
  标题、正文、完整陈述/列表/证明、嵌套字体和脚注自然语言显式抽取；数学/引用/
  环境保留原字节。未知命令/环境、数学内显式文字、index 特殊记录及不确定归属
  明确 BLOCKED；不修改现有事实或任何历史 run，不自动采用、审校或批准词条。
  先写 `docs/source-extraction.md` 设计与验收合同，再实现工具；真实全库扫描与
  BYTE_EXACT 回放已通过：117 章完整报告、116 个 Git 文件逐字相等；43,270 个
  提议单元（34,985 READY、8,285 BLOCKED），24,189 条诊断以数学内显式文字
  分类为主，另有归属/未知命令/环境及生成 index。全库生成与确定性复核均成功，
  17 项抽取回归和完整工具门禁、457 页整书及12页模板本地验收；现有译文事实不变。
  八项全库修订仍未完成，之后使用统一来源/诊断清单集中修复，避免每个小批次
  重复准备；来源库存成功不等于全库译文、词条或人工审校通过。

- 002Z 永久坐标/术语修订：Issue [#588](https://github.com/dongyaotalk/stacks-project-zh/issues/588)，
  分支 `translate/categories/002z/openai-gpt-6-1-sol`。完整冻结 22 个旧 unit/candidate
  的原 Git 字节及原 run；定义的末段从 `tag:002Z:p003` 重映射到
  `tag:0030:p003`，其余 ID 不变，完整定义/列表/证明归属重新核验。全部 22 单元
  保存实际 GPT-6.1-sol/xhigh revision，动态 Harness 为 0.160.0；v2 重放消费
  五字段完整原输出，原生成身份保留，新修订与精确旧输入另行披露。source TeX、
  公式、系统/逆系统方向、量词、引用及完整证明均不变。所辖 160 次来源术语
  出现通过，086J 证明组匹配锁定英文；其他数学用词按实际原词形双语，术语待决，
  不伪造独立 critic、人工审校、术语或出版批准。
  全库独立审计降为 3027 个 term 问题/907 个不合格候选，6488 次要求出现；source
  99 问题（36 陈述 Tag、11 raw TeX pairs、1 长脚注、0 隐藏标题）；proof
  187 组/291 单元仍为 166 匹配、21 差异、0 未支持。F1/F2/F4/F6 与
  S4/S5/S7 的其他范围继续处理，不把本批通过当作全库严格验收。

- 控制空格渲染边界：Issue [#589](https://github.com/dongyaotalk/stacks-project-zh/issues/589)，
  分支 `tool/legacy-control-space-boundaries`。002Z 完整实际修订的首次编译把
  legacy SPACE 的裸反斜线与中文连成未定义命令，数据未提交；完整新 run/原输出
  已冻结并保存在恢复快照，另开工具修复。渲染仅对 `SPACE_####` 的裸反斜线补
  TeX 控制空格，先核对 source_text 中真实 ASCII 空白证据；证据缺失直接报错，
  不把误标的未知命令改成空格。已有 TeX 空白不重复，全角空白不冒充词法分隔，
  其他角色/控制序列保持。默认源文恢复、payload、所有 hash 与原输出不变。
  回归先复现中文/ASCII/字体组/数学边界错误，再核验修复、源证据阻断和正式
  renderer 集成；已核对完整冻结 002Z 原输出的两处控制空格及所有当前来源证据。
  工具不修改真实数据，Issue #588 须在工具合并后恢复原输出并重跑完整验收；
  F4/S4/S5/S7 与其他批次继续处理。

- 0AHM 后续标题修订：Issue [#585](https://github.com/dongyaotalk/stacks-project-zh/issues/585)，
  分支 `translate/categories/0ahm-title/openai-gpt-6-1-sol`。首次真实使用 §8 归档合同，
  保存前一派生 `audit-categories-0ahm-20261005` 的完整七个输出原字节、原记录
  hash 和 Git 来源，原 run、全部此前模型修订与快照保留。v3 唯一后继冻结确切
  上一完整 unit/candidate，逐单元消费实际 GPT-6.1-sol/xhigh 新修订的全部五字段；
  动态 Harness 为 0.160.0，模型 snapshot 未暴露，不能保证供应商重放。只对
  0AHQ statement 无损暴露 Adjoint functor theorem 标题，全部七个 source TeX、
  数学、引用及永久 ID 不变；标题的 Adjoint、functor 与正文术语逐次双语核对。
  所辖 110 次来源术语出现通过，两段证明均匹配锁定英文；术语仍待决，当前
  来源绑定包含完整历史，预览披露原生成及两次实际修订，无人工审校或出版批准。
  全库独立审计为 3091 个 term 问题/924 个不合格候选、6488 次要求出现；source
  100 问题（36 陈述 Tag、11 raw TeX pairs、1 长脚注、0 隐藏标题）；proof
  187 组/291 单元仍为 166 匹配、21 差异、0 未支持。其他数据与 S4/S5/S7
  继续处理，不把本批通过或历史 QA 通过当作全库严格验收。

- 001P 实际来源/标题修订：Issue [#582](https://github.com/dongyaotalk/stacks-project-zh/issues/582)，
  分支 `translate/categories/001p/openai-gpt-6-1-sol`。保留三个旧 unit/candidate
  原字节及 legacy run，暴露 Yoneda lemma 标题并双语翻译；证明通过锁定 Git
  `categories.tex` / `lemma-yoneda` / Tag 001P / proof index 1 的不可变恢复证据
  保留七处内联公式，补回旧提取丢失的 `$s$` 和原词/公式关系。其 source TeX
  恰等于完整 Git 片段，陈述/display 的 source TeX 不变，三个永久 ID 不变。
  实际 GPT-6.1-sol/xhigh revision 冻结完整新 source 与确切旧输入，动态 Harness
  为 0.160.0，原输出全部五字段由 v2 重放消费；原模型仅表示原生成，预览披露
  新修订和来源恢复。10 次所辖来源术语出现全部匹配，未批准译法只报告待决。
  全库独立审计仍有 3091 个 term 问题/924 个不合格候选、6486 次要求出现；
  source 101 问题（36 陈述 Tag、11 raw TeX pairs、1 长脚注、1 隐藏标题）；
  proof 187 组/291 单元为 166 匹配、21 差异、0 未支持。本范围已清零，其他数据
  及 S4/S5/S7 继续处理，不据旧 QA 成功宣称全库验收或人工批准。

- 锁定来源恢复工具：Issue [#580](https://github.com/dongyaotalk/stacks-project-zh/issues/580)，
  分支 `tool/locked-source-restoration`。新增不可变来源证据、锁定 English Git
  selector、简单单单元证明的确定性内联数学提取，以及 v2/v3 的受限恢复例外；
  全部五字段实际新模型修订及完整冻结 batch 的 ownership 仍是强制门禁。
  来源绑定与预览覆盖所有祖先恢复，配置 harvest 传至 provenance/decision/render。
  独立全库 proof audit 覆盖 187 组/291 单元，初步为 165 匹配、22 原字节/节点差异、
  0 未支持。001P 缺 `$s$` 独立检出；其他差异包含公式换行、引用章前缀和真实遗漏，
  需要逐项复核，不能一概视为数学错误或自动批准。工具不改真实 unit/candidate/run/
  archive/source-reextraction，不启用默认严格来源门禁。具体数据、S4/S5/S7 仍未完成。

- 锁定来源恢复规范：Issue [#578](https://github.com/dongyaotalk/stacks-project-zh/issues/578)，
  分支 `docs/locked-source-restoration`。对照英文锁定 Git blob 确认 001P proof 应有
  七处内联公式，当前 source unit 仅六处，漏掉 `$s$`，相关关系也被重排；属于
  提取输入缺陷，原英文未改。规划独立不可变来源恢复证据、Git selector/片段
  验证、完整新 source 及实际模型修订，并要求复核全部当前证明链。后续工具任务
  落实受限例外；未声明操作仍要求旧 source TeX 相等，真实数据另开任务，F4/S4/S5 未完成。

- 命名环境标题工具：Issue [#576](https://github.com/dongyaotalk/stacks-project-zh/issues/576)，
  分支 `tool/named-environment-titles`。source helper 无损暴露简单英文词组标题，
  保留 own label 的严格边界与陈述/证明归属；只读来源审计增加隐藏/无效标题计数。
  标题术语和正文术语分别逐次核对，复杂标题不猜测。当前 001P/0AHQ 标题尚未
  实际修订，本工具不改写候选、run 或归档；具体数据及全库 S4/S5 仍待后续完成。

- 后续修订工具：Issue [#574](https://github.com/dongyaotalk/stacks-project-zh/issues/574)，
  分支 `tool/derivation-archives`。归档绑定前一记录、Git 活跃输出和确定性重放；
  v3 完整替换上一 batch，逐单元要求新的实际模型修订，保留原始模型 origin。
  来源 hash 与预览包含全部历史模型修订，Schema 覆盖历史输出，旧证据首次加入
  Git 后不可改写。回归仅使用 synthetic Git Fixture，未创建真实归档或修改候选。
  命名标题提取与具体数据另开任务，S4/S5 及八项最终验收仍未完成。

- 后续修订规范：Issue [#572](https://github.com/dongyaotalk/stacks-project-zh/issues/572)，
  分支 `docs/revision-archive-provenance`。核对发现 001P 的 Yoneda lemma 与 0AHQ 的
  Adjoint functor theorem 仍在命名环境包装内。已派生 0AHM 不能回写冻结输出或
  删除旧修订证据；先定义不可变归档、历史重放及唯一当前后继合同，Schema/工具
  与标题提取/数据修订另开任务。在配套工具合并前不生成归档或 v3 数据。

- S6 编译日志门禁：Issue [#570](https://github.com/dongyaotalk/stacks-project-zh/issues/570)，
  分支 `build/final-tex-log-gate`。最后一轮日志必须完整，无缺字、未定义引用/引用键
  或重复标签；PDF 复制前强制执行，普通字体回退不误报。模拟零退出编译器回归
  验证阻断及旧产物保持，CI 的 tool-test 运行这些回归但仍不完成整书 TeX 编译。
- S4 固定短脚注：数据 PR [#565](https://github.com/dongyaotalk/stacks-project-zh/pull/565)
  与 [#568](https://github.com/dongyaotalk/stacks-project-zh/pull/568) 分别修订 0AHM、0FWW，
  完整保留原快照与实际模型修订溯源。两处脚注有中文正文和正确引用；整书最终
  日志无缺字、未定义引用或重复标签。独立进度 Issue #566、#569 在合并后的 main
  生成并核验报告，无差异，不制造空 PR。其他来源/术语数据与最终集成仍未完成。

- S3 数学语境校准：Issue [#562](https://github.com/dongyaotalk/stacks-project-zh/issues/562)，
  分支 `tool/source-math-contexts`。区分赋值 set 与集合名词；FDL 普通法律/文档
  用词及两处明确普通用法以英语标题/TeX hash/逐次证据分类。splitting 的英语
  证据改为 02XJ 的真实概念说明，保留全部 191 个概念及 coding 的数学引用。
  分类证据过期必须失败，本任务不改译文、术语批准或把有限分类当作人工审校。

- S3 声明语法边界：Issue [#557](https://github.com/dongyaotalk/stacks-project-zh/issues/557)，
  分支 `tool/source-declaration-quotes`。02X8 的真实斜体措辞句在无损包装重提取后
  被拆成 let、be the 等伪声明；区分带数学参数的祈使措辞句与概念命名，仍强制
  句内目录术语及同单元其他真实新声明。仅真实字体 payload 可产生斜体声明。
  数据 Issue #556 独立保存来源快照，本工具修复不生成译文或改变词表批准。

- S3/F4 渲染边界：Issue [#551](https://github.com/dongyaotalk/stacks-project-zh/issues/551)，
  分支 `tool/tex-command-boundaries`。003G 的冻结实际修订通过结构/术语/溯源，
  但编译发现 `\item` 与中文拼成新命令。恢复时补充分隔，由 TeX 吞掉空白；
  默认源文恢复和派生 source TeX 比对保持原字节。数据在 Issue #549 独立保存，
  本工具修复不改写模型输出，也不把未通过整书验收的数据提交或合并。

- S3 显示边界：Issue [#548](https://github.com/dongyaotalk/stacks-project-zh/issues/548)，
  分支 `tool/term-format-display`。003G 的垂直/水平复合跨斜体边界，需要在显示
  核对中忽略字体包装，避免把单元专用 token 塞进词条；公式、引用、结构和
  脚注保持不透明。数据尚未修订，占位符结构校验及真实术语批准门禁不变。

- S3 术语工具：Issue [#546](https://github.com/dongyaotalk/stacks-project-zh/issues/546)，
  分支 `tool/source-term-inventory`。独立英语目录及定义声明产生逐次来源清单，
  校验候选显示、原词形、重复/漏报和真实待决证据。报告绑定来源/目录 hash，
  英文证据按完整 source TeX 核验；本次提供只读审计，不改变当前翻译事实，也
  不把尚未完成的数据修复或强制 QA/CI 接入标为完成。

- S0：Issue [#530](https://github.com/dongyaotalk/stacks-project-zh/issues/530)，
  PR [#532](https://github.com/dongyaotalk/stacks-project-zh/pull/532)。计划文档完成本地
  workflow/harvest/index/tools/schema/provenance/decision/qa-all 和当前候选整书编译；
  98 项测试、239 个候选 batch 通过，保留已知 F6/F7/F8 后续事项。
- S1：Issue [#531](https://github.com/dongyaotalk/stacks-project-zh/issues/531)，
  分支 `tool/decision-gates`。实现 F3/F5 和独立回归，已通过 121 项工具测试、239 个
  batch 的全量 QA 与当前候选整书编译；GitHub 验收随 PR 记录；
  词表、模型输出、run manifest、reviewed 数据与英文来源均不改写。
- F4 后续扫描：当前有 7 个 unit/candidate 的原始 TeX 控制序列不一致，涉及控制
  空格、分组括号和图表换行。因此 S3/S4 还必须修复现存提取/包装遗漏，并以锁定
  英文源结构核对，不能只新增针对 `%` 的检测后宣称结构保护已完成。
- S1：PR [#534](https://github.com/dongyaotalk/stacks-project-zh/pull/534) 使用前序
  分支为 base；已通过 GitHub 原生关联连接 Issue #531，保留一个关闭 Issue 的合同。
- S2 规范：Issue [#533](https://github.com/dongyaotalk/stacks-project-zh/issues/533)，
  分支 `docs/immutable-derivations`。统一原 run/原输出不可变、工具派生须快照与重放、
  活跃目录单版本及旧人工批准不继承的合同。Schema/工具另开 Issue/PR，本次不迁移
  unit/candidate/run 数据，不将尚未实现的接口描述为现有机器能力。
- S2 工具：Issue [#535](https://github.com/dongyaotalk/stacks-project-zh/issues/535)，
  分支 `tool/immutable-derivations`。实现独立 Schema、原字节/Git 来源绑定、受限
  机械重放和预览标记；17 项独立派生回归覆盖篡改、身份伪造、自由重译、路径逃逸、
  术语伪批准和孤立/重复记录。不修改现有 unit、candidate、run 或词表。
- S3 来源工具：Issue [#537](https://github.com/dongyaotalk/stacks-project-zh/issues/537)，
  分支 `tool/source-integrity`。增加带标签节点/结构子节点/证明归属、所有未保护
  TeX 控制字符和整段锁定脚注审计；固定短语脚注展开、显式保护跨度提案及已译
  引用的章限定名解析。旧永久 Tag 迁移脚本改为只读提案，不能再覆盖历史 run。
  新增 23 项独立回归；合并前审查补齐证明内列表、公式、段落的归属及跨范围拒绝。
  不修改事实数据；严格整库门禁仍待数据修复后启用。
- 扩展审计发现：Sets 五个旧 label batch 仍有已知永久 Tag 的子坐标；
  Categories `003O:p002` 的长脚注仍被整段锁定，`02XJ:definition-003` 的长脚注
  只被译成摘要。它们纳入 F1/F6 的完整来源验收；长脚注必须另建真实模型 run，
  不能借机械派生夹带自由重译。最初 F6 两处固定脚注可用受限工具变换。
- S6 字体：Issue [#540](https://github.com/dongyaotalk/stacks-project-zh/issues/540)，
  分支 `template/greek-text-font`。正文字体使用 TeX Live 提供的 Libertinus Serif，
  模板添加 Unicode 希腊字母普通/粗体/斜体/粗斜体烟测；不改数学字体和译文事实，
  不复制第三方字体二进制。最终构建日志硬门禁另行提交，不以字体修复代替 F6。
- 模型修订规范：Issue [#542](https://github.com/dongyaotalk/stacks-project-zh/issues/542)，
  分支 `docs/model-correction-provenance`。长脚注和自由自然语言修订另建实际模型
  revision run、冻结输入与完整原输出；原生成及新增修订同时披露，纯工具变换仍
  禁止自由重译。当前 turn 元数据确认 `gpt-6.1-sol`，注册 declared 身份、null
  snapshot 与不可保证重放，不虚构原 GPT-5.6 的新输出。机器实现另开 Issue。

- 已集成的前置 PR：#532、#534、#536、#538、#539、#541、#544 在各自最新检查通过后，
  按依赖顺序由维护者授权的管理员 bypass squash 合并到 main。后续分支同步 main，
  没有重写公开历史；#539 合并前补齐证明子节点归属并通过 161 项测试。
- 模型修订工具：Issue [#543](https://github.com/dongyaotalk/stacks-project-zh/issues/543)，
  分支 `tool/model-corrections`。v2 重放核对完整冻结输入、新原输出及两个来源；
  selection/review/revision 绑定完整来源 hash，预览披露复合来源。新证据保留首次
  Git 加入字节；本次仅 Schema/工具/测试/文档，尚未产生或迁移修订 run/事实数据。
  已通过 177 项工具测试（新增 16 项修订回归）、239 批 qa-all、全部来源/Schema/
  决策检查及整书 render/pdf 和模板烟测；数据修复仍属后续阶段。

- S4 完整容器采用：Issue [#607](https://github.com/dongyaotalk/stacks-project-zh/issues/607)，
  分支 `translate/categories/001y/openai-gpt-6-1-sol`。工具 #606 合并后，首次实际采用
  v4：001Y 的完整陈述及 13 个旧证明片段恢复为两个 R3 单元，Section parent 改为
  锁定来源的 001U，并更新 categories chapter-template。旧 14 条 unit/candidate
  原字节及 legacy run 全部保留；两份完整 Git 容器证据、一份动态 Harness 0.160.0
  的真实 GPT-6.1-sol/xhigh revision run 和两条完整五字段原输出可逐层重放。
  两个新来源逐字等于锁定 Git 原容器；独立 proof 审计的 35 个保护节点及片段 hash
  一致，001Y 从 mismatch 变为 match。原提取的数学扩写、引用命名和遗漏的
  “Therefore” 按英文原字节恢复；原文论证疑点忠实保留为非正文元数据。
  新输入为 145 来源词，记录完整引理/证明低于偏好下限的例外；28 次双语术语覆盖
  18 次目录要求，未批准术语全部待决。337 项工具测试、239 batch QA、117 章模板/
  进度/计划检查、来源/Schema/决策检查、全库库存及队列确定性检查成功；整书 PDF
  459 页、最终日志通过，正文第 34–36 页及目录已核对，交换图、引用和 δ 可读。
  当前事实为 239 batch/1468 unit；全库 proof 为 187 组/279 单元，167 match、
  20 mismatch、0 unsupported。统一队列仍有 859 个术语问题候选、2814 条术语诊断、
  76 个坐标迁移及 96 条来源诊断；本批两个单元为 BYTE_EXACT，未豁免其他残项，
  不将模型修订或候选合并称为独立 critic、人工审校、术语批准或正式出版。

- S3 完整证明的游离数学分组：Issue
  [#610](https://github.com/dongyaotalk/stacks-project-zh/issues/610)，分支
  `tool/detached-proof-display-groups`。先补充容器开发合同，再实现旧完整 proof 链与
  紧邻纯显示数学单元的连续、有序全组校验；真实 Git proof/章库存及完整章字节提供
  唯一数学归属。相邻游离节点必须纳入恢复组，禁止另留独立输出而重复公式。
  夹带正文/包装、跨范围、部分证明、重复、错序、不同数学字节及不唯一归属均拒绝；
  v1/v2/v3、提取/lowering 版本和既有 001Y 不可变证据保持原合同。
  真实 002T 只读待审包保留完整旧 5 条输入，得到陈述/证明两个完整 Git 单元、
  两组 PREPARED/零 BLOCKED，公式仅在证明内出现一次；实际数据及完整模型修订
  由后续独立任务采用。344 项工具测试、239 batch QA、117 章模板/进度/计划及
  来源/Schema/溯源/决策检查成功，全库库存和队列确定性 check 通过；当前候选
  render/pdf 成功，459 页及最终 TeX 日志通过，既有 001Y 图表/引用/δ 可读。
  本工具未改变事实：239 batch/1468 unit、20 组 proof 差异、859 个术语问题候选、
  2814 条术语诊断、76 个坐标迁移及 96 条来源诊断仍保留，S4/S5/S7 继续处理。

- S4 同节完整容器采用：Issue
  [#612](https://github.com/dongyaotalk/stacks-project-zh/issues/612)，分支
  `translate/categories/04aq/openai-gpt-6-1-sol`。工具 #611 合并后，002T/04AR 的完整
  两份旧 batch（7 条 unit/candidate）恢复为四个完整 R3 单元，真实 Section parent
  均为 04AQ，并更新该章模板。002T 的游离显示公式与三段旧 proof 一起冻结、
  保留四个原生成来源；新公式仅在完整 proof 中出现一次。04AR 的原文省略证明和
  对偶提示忠实保留，不补写论证；引用的原节点恢复为锁定 Git 原字节。
  旧 7 条输入/候选及 legacy run 原字节保留，四份来源容器证据、两个 v4 分组记录、
  一份共享的实际 GPT-6.1-sol/xhigh revision run 和完整五字段原输出可重放。
  模型生成前冻结完整新输入、确切旧分组和全部上下文；动态 Harness 为 0.160.0，
  173 来源词记录完整不可拆的两对引理/证明低于偏好下限的例外。40 次双语出现
  覆盖 33 次来源目录要求，未批准译法全部待决。四个新 source TeX 逐字等于
  锁定 Git 容器；两个 proof 的完整 22/3 个保护节点和片段 hash 均一致。
  344 项工具测试、239 batch QA、117 章模板/进度/计划、来源/Schema/溯源/决策及
  更新后的全库库存/队列确定性检查通过；render/pdf 零退出，459 页及最终日志
  成功，正文第 45–46 页的公式、完整证明及引理 4.16.2 引用可读。
  当前为 239 batch/1465 unit，proof 187 组/277 单元、169 match/18 mismatch/
  0 unsupported。术语问题候选 859→855，术语诊断 2814→2810；76 个坐标迁移及
  96 条来源诊断仍保留。本批四个单元 BYTE_EXACT，两个 batch 的修复队列 actions
  为空，不据此豁免其他数据、S5/S7 或授予独立 critic、人工审校、词表/发布批准。

- S4 伴随函子完整容器采用：Issue
  [#615](https://github.com/dongyaotalk/stacks-project-zh/issues/615)，分支
  `translate/categories/0036/openai-gpt-6-1-sol`。0038/0039 的两份完整旧 batch
  （10 条 unit/candidate）恢复为四个完整 R3 单元，真实 Section parent 均为 0036。
  两个列表陈述各保留全部列表结构，0038 的三条旧 proof 输入包含内部显示公式，
  新公式仅在完整证明内出现一次；0039 忠实保留简短证明。原文在余极限论证中
  使用的 limit 保持原词，措辞疑点仅记入非正文审校元数据，未自行修正英文。
  旧 10 条输入/候选和历史 run 原字节保留，四份来源证据、两个 v4 分组记录及
  一份共享实际 GPT-6.1-sol/xhigh revision run 保存完整五字段原输出并可验证重放。
  完整新来源、确切旧分组及全部上下文在模型输出前冻结；动态 Harness 为 0.160.1，
  历史版本不改写。122 来源词记录完整不可拆的两对短引理/证明低于偏好下限的
  例外。33 次双语术语覆盖 21 次来源目录要求，未批准译法全部待决。
  四个 source TeX 逐字等于锁定 Git 容器，两个 proof 的全部 5/3 个保护节点
  （含环境边界）及片段 hash 均一致；四个新单元 BYTE_EXACT，两份修复队列的
  actions 为空。344 项工具测试、239 batch QA、117 章模板/进度/计划、来源/Schema/溯源/决策及
  更新后的全库库存/队列确定性检查通过。render/pdf 零退出，459 页及最终 TeX
  日志成功；正文第 69 页两个列表、证明公式和 4.24.1/4.14.4/4.24.2 引用可读。
  当前为 239 batch/1459 unit，proof 187 组/275 单元、171 match/16 mismatch/
  0 unsupported。术语问题候选 855→849，术语诊断 2810→2797；76 个坐标迁移
  和 96 条来源诊断仍保留。其他数据及 S4/S5/S7 继续处理，未授予独立 critic、
  人工审校、词表或发布批准。

- S3 数学内记号分类：Issue
  [#618](https://github.com/dongyaotalk/stacks-project-zh/issues/618)，分支
  `tool/math-text-notation-classification`。先补充来源抽取/完整容器开发合同，再以
  明确政策登记 pr、id、Arrows、Sets、size、Cov、Supp、cf 八个记号的精确字面量、
  命令和函数调用/下标/独立符号用法。接受项保存完整命令原字节、使用证据、
  UTF-8 byte/line 位置和来源 label；自然语言、未知名称、错误命令/词形、嵌套
  文本和不匹配用法继续阻断。数学 token 和原公式不改写，词条/人审不因此批准。
  v2 库存记录正向分类，纯数学无自然语言的 13 个片段回归 locked segment，
  所有原字节和分类证据仍保存，临时库存 ID 不能冒充事实 ID。合法 v1 ignored
  库存按完整文件/hash 安全再生成；旧政策无分类表时保持原阻断语义，历史容器
  和 v1/v2/v3/v4 不可变记录保持原合同。来源对应器另核验分类字段，篡改并重算
  缓存 hash 仍被拒绝。
  352 项工具测试、68 项定向回归、239 batch QA、117 章模板/进度/计划及来源/
  Schema/溯源/决策检查成功。全库库存及修复队列重建/check 通过；117 章报告、
  116 个 Git blob 逐字回放，43,257 个提议单元（36,278 READY、6,979 BLOCKED），
  19,542 条诊断含 19,421 条未分类数学文字。4,647 次记号分类逐项核对命令字节、
  使用证据和八个来源 owner；原诊断恰好等于剩余诊断加这 4,647 次分类。
  剩余 16 组 proof 均重读真实 Git 容器，13 组 SOURCE_PREPARED、3 组 BLOCKED，
  仍全部计为当前 mismatch；准备成功不表示修订或采用。当前候选 render/pdf 和
  模板 smoke 零退出，459/12 页最终日志 PASS，整书提取文本与工具前完全一致。
  本工具未改动 translation-data 树：239 batch/1459 unit、849 个术语问题候选/
  2797 条诊断、76 个坐标迁移、96 条来源诊断和 16 组 proof 差异均保持；具体
  完整来源采用与实际模型修订、S4/S5/S7 继续处理。
