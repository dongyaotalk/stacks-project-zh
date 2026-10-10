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

- S4 有限极限/余极限完整容器采用：Issue
  [#620](https://github.com/dongyaotalk/stacks-project-zh/issues/620)，分支
  `translate/categories/04as/openai-gpt-6-1-sol`。002O/002Q 的两份完整旧 batch
  （13 条 unit/candidate）恢复为四个完整 R3 单元，真实 Section parent 均为 04AS。
  锁定 Git 核对发现，002O 旧证明输入把 finite products / finite index categories
  改成 products / nonempty index categories；本次恢复真实原文，不把旧提取错误
  当作英文 remark 保留。002Q 第二项补回旧输入遗漏的范畴数学节点；002O 第二项
  按真实原文保持无该节点。002O 的显示公式只在完整 proof 内出现一次，002Q
  保留原文省略证明和对偶提示，proof 风险恢复为 R3，不补证明。
  旧 13 条完整输入/候选与所有历史 run 原字节保留；四份来源证据、两个 v4 分组
  记录及一份共享实际 GPT-6.1-sol/xhigh revision run 保存完整五字段原输出。
  新来源、确切旧分组及全部上下文在模型输出前冻结；动态 Harness 为 0.160.1，
  历史版本不回写。115 来源词记录完整不可拆的两对短引理/证明低于偏好下限的
  例外，37 次双语术语覆盖 33 次来源目录要求，所有未批准译法继续待决。
  四个 source TeX 逐字等于锁定 Git 容器，两个 proof 的完整 8/3 保护节点
  （含环境边界）及片段 hash 一致；四个新单元 BYTE_EXACT，两份队列 actions
  为空。352 项工具测试、239 batch QA、117 章模板/进度/计划、来源/Schema/溯源/
  决策及更新后的全库库存/队列确定性检查通过。render/pdf 零退出，459 页及
  最终 TeX log PASS；正文第 51 页列表、唯一公式和 4.14.10/4.18.6 引用可读。
  当前为 239 batch/1450 unit，proof 187 组/272 单元、173 match/14 mismatch/
  0 unsupported。术语问题候选 849→839，诊断 2797→2782；76 个坐标迁移及
  96 条来源诊断仍保留，其他事实及 S4/S5/S7 继续处理，未授予独立 critic、
  人工语言/数学审校、词表、正式采用或出版批准。

- S3 稳定词汇来源证据：Issue
  [#624](https://github.com/dongyaotalk/stacks-project-zh/issues/624)，分支
  `tool/locked-source-term-evidence`。先写开发合同，再为词汇目录增加互斥的
  locked-source-container 证据；重新读取锁定英文 Git blob、真实 Tag/Section
  归属和完整容器字节，核验原片段 hash 与暴露正文中的精确词形。旧式当前
  unit/hash 证据保持原检查。仅将 cartesian / equivalence 两个锚点迁至 0024
  完整 proof；forms、chapters 和所有其他目录条目保持。CLI 支持显式 harvest，
  统一队列将实际 harvest 传入，报告保存两项正向核验及 Git 字节证据。
  57 项定向回归、361 项完整工具测试、239 batch QA、117 章模板/进度/计划及
  来源/Schema/溯源/决策检查通过；全库库存与队列确定性 check 通过。独立比较
  确认 translation-data 树、全部候选错误、来源和 proof 报告逐项保持，术语
  inventory 仅更新目录 hash；两项证据的真实 Git 原字节及 hash 均核对通过。
  当前候选 render/pdf 零退出，459 页最终日志 PASS，整书 layout 提取文本与
  工具前完全一致。239 batch/1450 unit、839 个术语问题候选/2782 条诊断、
  76 个坐标迁移、96 条来源诊断和 14 组 proof 差异均保留。DATA #623 须在本
  工具合并后重新准备并冻结完整上下文，再进行实际模型修订；S4/S5/S7、全库
  严格门禁和必要的人审仍继续，来源取证不批准中文译法或正式采用/出版。

- S4 可表态射定义及对角引理完整恢复：Issue
  [#623](https://github.com/dongyaotalk/stacks-project-zh/issues/623)，分支
  `translate/categories/0021/openai-gpt-6-1-sol`。前置词汇来源工具 #625 合并后
  重新准备/check并冻结上下文；真实 Section 0021 为 Fibre products and
  representability。0023/0024 的两份完整旧 batch（14 条输入/候选）恢复为
  三个完整 R3 单元，0023 暴露原斜体自然语言并保留 F/G 数学和字体范围，0024
  恢复三个列表条件及完整证明、旧 U/V 数学节点和原段落控制。交换图与显示
  公式链各只出现一次；“Assume the equivalent conditions (2) and (3)” 修正为
  假设已等价的两个条件成立，忠实保留原论证。
  旧 14 条 unit/candidate 和历史 run 原字节保留，两个 v4、三份完整来源证据
  及一份共享实际 GPT-6.1-sol/xhigh revision run 保存完整五字段原输出。最终
  新来源、确切旧分组和全部上下文在模型输出前冻结；动态 Harness 0.160.1，
  历史版本不回写。215 来源词记录同节完整不可拆定义/引理/证明低于偏好下限
  的例外，45 次双语出现覆盖 38 次目录要求，全部未批准译法继续待决。
  三个新 source TeX 逐字等于锁定 Git；proof 完整 39 个保护节点（含边界）和
  片段 hash 一致。三个单元 BYTE_EXACT，两份修复队列 actions 为空，0024
  proof 由 mismatch 转为 match，cartesian/equivalence 锁定证据继续通过。
  361 项工具测试、239 batch QA、117 章模板/进度/计划、来源/Schema/溯源/
  决策及全库库存/队列重建和确定性检查通过。render/pdf 零退出，459 页最终
  TeX 日志 PASS；正文第 37–38 页斜体、列表、交换图、公式链和 4.8.1 引用可读。
  当前 239 batch/1439 unit；proof 187 组/264 单元，174 match、13 mismatch、
  0 unsupported。术语问题候选 839→833，诊断 2782→2770；76 个坐标迁移及
  96 条来源诊断保持。相邻 0022 仍有抽取阻断，03KC 无既有候选，本次不新增；
  其他事实、S4/S5/S7 及独立 critic、人类语言/数学审校、词表、正式采用和出版
  门禁继续处理，本批候选保存不授予这些批准。

- S3 完整引言外围空白核验计划：Issue
  [#629](https://github.com/dongyaotalk/stacks-project-zh/issues/629)，分支
  `tool/paragraph-container-whitespace`。DATA #628 尚未生成模型输出或采用事实；
  0033 引言旧 render 的两个尾换行使单段严格比较失败，而旧 batch 不含后面的
  定义，不能冒充完整 prose_block 的尾边界。先写来源容器 v2 开发合同，再
  在唯一完整段落及真实旧/新 Section 归属下核验外围 ASCII 空白，内部所有
  原字节保持，新来源仍逐字等于锁定 Git。v1 及证明/陈述/长正文原规则保持。
  回归及全库验收后独立工具 PR；合并后 DATA #628 重新准备、冻结并实际重译。
  验收：七项新增回归覆盖外围 ASCII 空白、内部字节/数学/命令/引用/非 ASCII
  差异拒绝、真实 Section 和重复核心、dirty harvest、只读完整准备包、v1 严格
  加载及旧陈述/证明证据兼容。368 项工具测试及 239 batch QA、117 章模板/
  进度/计划、Schema/溯源/决策、全库库存和队列重建/check 通过。独立比较四份
  完整审计报告及 translation-data 树均保持；0033/0034/0035 的五个来源容器
  准备/check 成功，逐字核对实际 Git 片段及 hash，13 个旧输入可恢复为五个
  完整单元而尚未采用事实。render/pdf 零退出，459 页最终 TeX 日志 PASS，
  整书 layout 提取文本与工具前完全相同。当前 1,439 单元、833 个术语问题
  候选/2,770 条诊断、76 个坐标迁移、96 条来源诊断和 13 组 proof 差异均保留。
  工具成功只解除 DATA #628 准备限制；S4/S5/S7 及必要的审校和发布门禁继续。

- S4 正合函子完整小节计划：Issue
  [#628](https://github.com/dongyaotalk/stacks-project-zh/issues/628)，分支
  `translate/categories/0033/openai-gpt-6-1-sol`。前置工具 #630 已验收合并；从
  新 origin 重新准备 Section 0033（Exact functors）的完整标题、单段引言、
  0034 定义及 0035 引理/证明。旧引言只核验外围 ASCII 空白，新 source TeX
  仍逐字等于原 Git 完整段落，不借用缺失的后继定义锚点作为 prose_block 边界。
  三份完整旧 batch 的 13 条输入/候选计划恢复为五个完整单元；标题 R1、引言
  R2、三个数学容器 R3。保留全部旧原字节、真实归属、列表、斜体、proof 内
  唯一显示公式及原引用；新的 parent 均为 0033，引言 ID 在写事实前已声明为
  tag:0033:paragraph-0001。三个 v4、五份来源证据及一份实际 GPT-6.1-sol/xhigh
  revision run 将保存五字段原输出。先 prepare/check、冻结完整新来源、全部
  旧分组、风格/政策/词表和来源术语库存，再由实际模型修订。139 来源词是
  整个不可拆短小节，明确登记偏好下限例外；词条保持待决，历史审校不继承。
  验收覆盖真实 Git 原字节、完整历史、唯一 ID、来源/术语/proof、全部工具与
  QA、模板/进度/计划、库存/队列和当前候选 PDF；验收后推送 PR，根审查远端
  全文及精确 HEAD 两项 CI 后按授权 bypass，保留 DATA trailers，随后同步进度。
  验收：前置工具 #630 合并后从新 origin 重建三份 prepare/check 包，模型输出
  前冻结全部五个新来源及 13 个旧输入/候选的完整分组。实际 GPT-6.1-sol/xhigh
  五字段修订保留原输出，动态 Harness 0.160.1 在冻结前及装配时核验；全部
  45 次双语标注覆盖 39 次来源要求，未批准词条继续待决。五个 source TeX 及
  片段 hash 逐字等于实际 Git；全旧快照、历史 run、冻结 context hash 和五字段
  原输出均独立核对，当前 1,431 个 ID 唯一。标题/引言边界、两份三个条件的
  完整列表及斜体保持，0035 完整 proof 的显示公式只出现一次，保留原引用。
  368 项工具测试、239 batch QA、117 章模板/进度/计划、来源/Schema/溯源/
  决策、全库库存和队列重建/check 通过。render/pdf 零退出，459 页最终日志
  PASS；正文第 68 页定义 4.23.1、引理 4.23.2 的列表、斜体、显示公式与引用
  可读，第 69 页相邻伴随函子小节不受影响。五个新单元均 BYTE_EXACT，三份
  队列 actions 为空；术语问题候选 833→823、诊断 2,770→2,749。proof 187
  组/262 单元，175 match、12 mismatch、0 unsupported。其他术语/证明诊断
  和完整来源审计逐项保持，76 个坐标迁移、96 条来源诊断继续处理。
  本次完整候选保存不授予 critic、人审、术语审批、正式采用或出版；S4/S5/S7
  及全库严格门禁的其余验收继续，合并后按独立任务同步进度。

- S4 的 003O 术语来源前置计划：Issue
  [#633](https://github.com/dongyaotalk/stacks-project-zh/issues/633)，分支
  `tool/locked-2-fibre-product-term-evidence`。完整只读核验确认真实 Section 003O
  可将旧 31 片段恢复为 30 完整单元，1,169 个来源词；长脚注可暴露自然语言，
  align* 公式链可完整保护。实际数据尚未采用。先写来源目录合同，仅将三项
  旧式词汇证据迁至已有 locked-source-container 格式：1-morphism 与
  2-commutative 绑定完整 prose_block ordinal 1，2-fibre-product 绑定完整标题。
  核验真实锁定 Git、完整边界和保护后自然词形，所有 forms/chapters/其他证据
  与非数学分类保持，不批准词条。验收要求全库工具/QA/模板/进度/计划及
  库存/队列检查、所有原诊断和 translation-data 树保持、当前 PDF 零退出且
  整书文本保持。完整来源词汇库存为 227 次要求；and 虽出现在声明候选中，
  已由既有非数学声明目录排除，无须新的工具修复。随后另开完整 DATA 修订
  任务并冻结最终上下文；S4/S5/S7 继续。
  验收：368 项工具测试、239 batch QA、117 章模板/进度/计划、Schema/溯源/
  决策及全库库存、队列重建/check 通过。三项证据在真实锁定 Git 中逐字核对，
  完整来源投影词形均通过；30 容器 prepare/check 为 PREPARED，零阻断。
  全部候选、来源、proof 和 alignment 诊断逐项保持，仅目录 hash 与三项
  来源证据元数据按计划改变，translation-data 树完全不变。当前 1,431 单元、
  823 个术语问题候选/2,749 条诊断、76 个坐标迁移、96 条来源诊断、12 组
  proof 差异保持。render/pdf 零退出，459 页最终日志 PASS，整书 layout
  提取文本与修改前完全一致。完整 DATA 在本前置合并后重新准备并冻结输入。

- S3 的完整正文块对应计划：Issue
  [#637](https://github.com/dongyaotalk/stacks-project-zh/issues/637)，分支
  `tool/complete-prose-source-alignment`。DATA #635 已实际冻结、生成并装配
  30 完整五字段修订，368 工具测试、239 batch QA、真实 Git/原输出/上下文
  核对及 459 页 PDF 通过；尚未提交。当前窗口匹配把逐字相等的长引言误报
  SOURCE_DIFFERENCE，另四个完整正文块因外围空白裁剪误报排版等价。先保存
  40 文件指纹和完整 stash，再单独写报告 v2 合同与工具，不改任何事实。
  仅严格 canonical prose 单元按真实锁定 Git 完整容器、Tag/Section/kind/
  ordinal 和前后锚点定位；完整原字节一致才 BYTE_EXACT，错误和阻断仍失败，
  不回落宽窗口或豁免独立审计。旧窗口/proof、宏与来源恢复权限保持；安全
  重建旧 v1 包而 check 要求 v2。独立真实 Git 回归、主分支全库/原残项保持
  及整书文本保持验收后工具 PR；合并后恢复 DATA 原字节并完成整合验收，
  原模型政策、context hash 和 e4 生成 origin 不回写，S4/S5/S7 继续。
- 完整正文对应工具本地验收：375 工具测试、239 batch QA、117 章模板/
  进度/计划、Schema/溯源/决策及全库库存/队列重建和 check 全部通过。
  独立核对四份主分支审计结果仅报告版本从 v1 升 v2，所有原残项及
  translation-data 树保持。冻结 DATA 的 30 块全部 BYTE_EXACT，逐块重放
  真实 Git 字节及 hash、五个正文边界，包字节保持，尚未采用 DATA。
  render/pdf 零退出，459 页最终日志 PASS，整书 layout 文本与工具前相同。

- S4 的 2-纤维积完整小节计划：Issue
  [#635](https://github.com/dongyaotalk/stacks-project-zh/issues/635)，分支
  `translate/categories/003o/openai-gpt-6-1-sol`。前置来源锚点 #634 已合并；
  从新 origin 重新 prepare/check 并冻结 Section 003O 的全部 30 完整容器及
  31 旧输入/候选完整分组。1,169 来源词符合偏好；标题 R1、五个完整正文块
  R2、所有数学陈述/证明 R3，真实 parent 均为 003O。引言合并 p001/p002，
  其边界由真实 Section 标题与 003P 定义核验；其余正文块也验证原生前后锚点。
  暴露长脚注自然语言，保留原文的不确定措辞；04YR proof 中的完整 align*
  公式链保持原字节并完整保护。修复本批 24 个永久 Tag 错配、隐藏脚注及
  两条未保护 TeX 诊断，逐次补齐术语显示。当前来源库存为 227 次要求，and
  已按既有非数学目录排除，识别政策保持。保留整份旧原字节和历史 run，
  一个 v4、30 份 Git 来源证据及一个实际 GPT-6.1-sol/xhigh revision run 保存
  完整五字段原输出；最终新来源、旧分组、风格/政策/词表、术语库存和 context
  hash 在模型输出前冻结，动态 Harness 在冻结前及装配时核验。词条保持待决，
  旧审校不继承。全库验收及当前 PDF 零退出、视觉核对后推送 PR，根审查全部
  远端文件/patch、native 合同和精确 HEAD 两项 CI 后按授权 bypass，保留六项
  DATA trailers，随后独立同步进度；S4/S5/S7 及实际审校/发布门禁继续。
- 003O 的完整修订整合验收：报告工具 #638 合并后逐字恢复 39 个原事实
  文件；生成 origin e4、实际五字段、冻结 context hash 及历史 run 全部保持。
  375 工具测试、239 batch QA、117 章模板/计划及隔离进度预览、Schema/
  溯源/决策、全库存及统一队列重建/check 全部通过。30 块均 BYTE_EXACT，
  独立逐块重放真实 Git；259 双语记录覆盖 227 来源要求，003O 队列为空。
  全库当前 1,430 单元；坐标迁移 76→52、错误陈述 Tag 36→22、来源诊断
  96→69、未保护节点对 11→10、隐藏脚注 1→0，术语问题候选 823→797、
  诊断 2,749→2,607。187 组/262 单元 proof 仍为 175 匹配、12 差异、
  零未支持；其他所有来源/术语/proof/匹配原结果逐项保持，未批准待决词汇。
  render/pdf 零退出，459 页最终日志 PASS，长脚注、列表/矩阵及完整公式链
  视觉检查通过；整书 layout 文本除真实封面构建日期外与先前 DATA 预览相同。
  合并后另开进度任务，不以本批通过代替全库 S4/S5/S7 或人工审校。
- 003O 后独立进度 Issue #640 / PR #641 已验收合并：117 章 progress/check
  与 plan/check、合并后溯源/决策及 459 页 PDF 通过；仅两份报告改变。
  全书候选完成 104→105 Section，Categories 20/44→21/44，审校/发布仍为零。
- S3 下一组集中准备计划：Issue
  [#642](https://github.com/dongyaotalk/stacks-project-zh/issues/642)，分支
  `tool/locked-cat-fib-source-preparation`。完整预检中 02XG 的两个 Cat 容器
  和 02XJ 的一个 Fib 定义阻断；以真实 003D 与 02XP 标签依据，仅添加
  textit/symbol 的两个精确常量规则，原数学不变。集中迁移后续三节的九项
  旧词汇锚点到既有完整 Git 容器，实际归属、完整边界及准确来源词形独立核对；
  forms/chapters/其他条目和非数学分类不变。先写上述开发合同再改政策与回归。
  全库库存/队列确定性、原术语/来源/proof 残项及事实树保持、真实完整容器
  预检与书稿零错误/text 保持验收后工具 PR。04Z2 公式里的自然语言 and
  保持阻断，须另立自然语言保护/翻译合同；不借记号分类压掉该问题。
  具体模型输入在工具合并后重新准备冻结，历史输入/输出/政策证据不回写，
  S4/S5/S7 继续。
- #642 的准备阶段发现真实 Fib 标签末尾大写 C 被旧 notation source_label
  词法错误拒绝。先更新 Issue 精确范围为七文件，补开发合同，再修正校验器
  保留来源 label 的 ASCII 大写；不编造小写别名，路径/空白/非 ASCII 仍失败，
  回归及独立实际标签证据核对必需。
- #642 本地验收：379 工具测试、239 batch QA、117 章模板/进度/计划、
  Schema/溯源/决策与全库存/队列重建/check 全部通过。九项证据的真实 Git
  完整字节及源词形逐块核对，所有 forms/范围/其他条目和事实树保持；全部
  术语/来源/proof 原残项以及匹配状态/位置保持，四个 readiness 字段只随
  已记录的明确常量分类更新。库存仍 43,257 单元，READY 36,278→36,298、
  BLOCKED 6,979→6,959，51 条原 math-text 转为正向记录（Cat 38、Fib 13），
  总分类 4,647→4,698、诊断 19,542→19,491，116 文件逐字回放保持。
  真实 02XG 的 11 容器/522 来源词与 02XJ 的 31 容器/1,653 来源词均可准备；
  04Z2 七块可准备、一块因自然语言 and 阻断保持。当前 render/pdf 零退出，
  459 页最终日志 PASS，整书 layout 文本与修改前完全相同。具体 DATA 仍
  分别认领并在工具合并后冻结新上下文，不继承旧审校或批准，S4/S5/S7 继续。
- S4 的完整 categories-over-categories 小节计划：Issue
  [#644](https://github.com/dongyaotalk/stacks-project-zh/issues/644)，分支
  `translate/categories/02xg/openai-gpt-6-1-sol`。前置 #643 合并后，从 fe993
  prepare/check 真实 Section 02XG 的全部 11 完整容器；13 旧单元中两组相邻
  正文分别合并，所有陈述/proof 恢复自身永久 Tag 和真实 parent。522 来源词
  符合偏好，标题 R1、完整正文 R2、数学陈述/proof R3；Cat 数学、列表及引用
  保持完整原字节。先冻结新来源、13 旧输入/候选完整分组、风格/政策/词表、
  来源术语与 context hash，再由实际 GPT-6.1-sol/xhigh 生成全部五字段。
  Harness 在冻结前及装配时动态解析。一个 v4、11 份 source-container-v2、
  不可变实际 revision run/原输出保留完整历史；待决术语不批准、旧审校不继承。
  精确 21 文件范围内采用事实，全工具测试/239 batch QA/117 模板、Schema/
  溯源/决策、全库存与统一队列重建/check、独立真实 Git/原字节/模型输出/
  冻结上下文核对；本批队列应为空，其他残项逐项保持。进度/计划仅隔离预览，
  当前书稿 render/pdf 零退出和视觉检查后提交 PR，远端全文/完整 patch/native
  合同与精确 HEAD 两项 CI 通过后按授权 bypass，保留六个 DATA trailers。
  合并后另开进度任务；全库 S4/S5/S7、实际审校及发布门禁继续。
- #644 本地验收：379 工具测试、239 batch QA、117 章模板及隔离进度/计划、
  Schema/溯源/决策、全库存与统一队列重建/check 全部通过。独立核对完整旧
  原字节、11 块真实 Git 原字节、全部实际五字段及生成前冻结 context hash；
  115 双语记录覆盖 100 次来源要求，11 块均 BYTE_EXACT，02XG 队列为空。
  其他所有来源/术语/proof/匹配原结果逐项保持；当前 1,428 单元，坐标迁移
  52→45、错误陈述 Tag 22→17、来源诊断 69→60、未保护节点对 10→9；
  术语问题候选 797→785、诊断 2,607→2,554。187 组/262 单元 proof 保持
  175 匹配、12 差异、零未支持。render/pdf 零退出，459 页最终日志 PASS；
  实际正文页 89–91 的定义、完整列表/嵌套列表、图、两份证明及例子可读，
  无裁切或重叠。原文省略及疑似语法 typo 忠实保留，remark 只在非正文 notes。
  词汇仍待决；数据合并后另开进度任务，不以本批通过代替全库总验收。
- 02XG DATA #645 与独立进度 Issue #646 / PR #647 已验收合并：117 章
  progress/check、plan/check、模板及合并后溯源/决策通过；事实树保持。
  当前通道 render/pdf 零退出，459 页最终日志 PASS，全文与 DATA 验收相同。
  全书候选完成 105→106 Section，Categories 21/44→22/44；人审/发布仍为零。
- S4 的完整纤维化范畴小节计划：Issue
  [#648](https://github.com/dongyaotalk/stacks-project-zh/issues/648)，分支
  `translate/categories/02xj/openai-gpt-6-1-sol`。从最新 main 725a 准备/check
  Section 02XJ 的全部 31 完整 Git 容器，保存完整 32 旧输入/候选原字节；
  最前两旧正文合并为一个完整块，14 陈述和 10 proof 恢复自身永久 Tag，
  parent 均为 02XJ。1,653 来源词明确记录超过偏好上限的例外：v4 要求对
  整份既有 batch 的全部新输出实际完整修订及完整历史重放，不裁切定义、
  证明或正文，也不采用部分 batch。标题 R1、正文 R2、数学陈述/proof R3；
  原列表、图、公式、引用和 Cat/Fib 保持完整原字节。先冻结新来源、完整旧
  分组、风格/政策/词表/来源术语/context hash，再由实际 GPT-6.1-sol/xhigh
  生成全部五字段，Harness 在冻结前和装配时动态解析。一个 v4、31 份
  source-container-v2、不可变模型 correction/原输出/run 保留全部历史，
  待决词汇不批准、旧审校不继承。41 精确文件范围内采用；379 工具测试、
  239 QA、117 模板、Schema/溯源/决策、全库存/队列重建/check、独立 Git/
  旧快照/实际五字段/冻结上下文核对，本批队列应为空、其他结果逐项保持。
  进度/计划仅隔离预览；render/pdf 零退出、视觉检查、远端全文/完整 patch/
  native 合同及精确 HEAD 两项 CI 后按授权 bypass，保留六 DATA trailers。
  合并后另开进度任务，S4/S5/S7 与原八项总验收继续。
- #648 本地验收：32 旧输入/候选原字节保留，31 完整新容器独立对照锁定 Git
  原字节；本次 GPT-6.1-sol/xhigh 的完整五字段与冻结上下文逐项相等。310 条
  双语记录覆盖 295 次来源术语要求，全部待决而未批准。31 块均 BYTE_EXACT，
  本批队列的 actions、来源/术语/proof findings 为空；其他所有匹配、来源诊断、
  术语结果及 proof 结果逐项保持。全库 1,427 单元，坐标迁移 45→21，错误
  陈述 Tag 17→3，来源诊断 60→26，未保护节点对 9→3；术语问题候选
  785→756、诊断 2,554→2,397。187 组/262 单元 proof 仍为 175 匹配、
  12 差异、零未支持；193 个 batch 尚有非空修复队列。
  379 工具测试、239 QA、117 模板及隔离 progress/plan/check、Schema/溯源/
  决策、全库存与队列重建/check 全部通过。render/pdf 零退出，461 页最终
  日志 PASS；物理页 109–117（正文 91–99）的完整定义、列表、证明、图和
  脚注逐页可读，无裁切或重叠。候选进度预览为 107 Section，Categories
  23/44（52.3%）；实际进度在数据合并后另开任务更新。本批验收不替代
  S4/S5/S7、全八项总验收或独立 critic、人工审校及发布记录。
- 数学内自然语言的规范计划：Issue
  [#652](https://github.com/dongyaotalk/stacks-project-zh/issues/652)，分支
  `docs/math-text-translation-contract`，基线 main 677d63e（DATA #649 与
  进度 #651 已合并）。先定义 unit-v2 完整数学 region/锁定 pieces/typed
  text slot、原源回放与译文 skeleton 双重保护、source-container-v3 及
  版本/历史/实际模型/审批绑定；初次实现目标为真实 04Z2 的 and、009B 的
  matrix if 与 000Q proof 的 affine opens of。开发合同及独立拒绝回归矩阵
  见 math-text-translation.md；本任务只写八个规范 Markdown 文件，代码、
  Schema、政策与事实保持。现行数学保护与 BLOCKED 不变，后续工具单独
  Issue/PR，工具合并后 DATA 再冻结完整旧新输入及真实五字段，不继承批准。
  规范验收包括既有工具/239 QA/117 章与当前 lane render/pdf 零退出、整书
  layout 文本保持、远端八文件完整字节/full patch/native 合同、精确 HEAD
  两项 CI 后按用户授权 bypass。基线仍为 193 非空 batch、756/2,397 术语
  候选/诊断、21 坐标、3 错陈述 Tag、26 来源诊断、3 未保护节点对与 12
  proof 差异；不以规范合并减少残项，F1–F8、S4/S5/S7 继续。
- #652 本地规范验收：独立读取锁定 Git/tags，核对五个完整容器的七次
  自然文字及实际归属（000Q 的真实标签为 lemma-bound-size）。八个规范
  入口/本地链接一致，范围外 1,277 个已跟踪文件与基线原字节相等，五件
  全库库存及来源/证明/术语/队列报告 hash 全部保持。379 回归测试通过
  （257.445 秒）；239 QA、117 模板/progress/plan、workflow/harvest/
  upstream-index/Schema/provenance/decision 全部通过。当前 lane render/pdf
  零退出、461 页最终日志 PASS，整书 layout 文本与 DATA #649/进度 #651
  验收完全相等。仅规范设计完成，实际工具、自然 slot 重译与残项继续。
- 数学文字工具实施计划：Issue
  [#654](https://github.com/dongyaotalk/stacks-project-zh/issues/654)，分支
  tool/protected-math-text，基线 main 000dbb7。按已合并合同实现独立 registry/
  math_text 模块、unit-v2/完整 region、源与译文 skeleton 双重保护、slot
  术语/渲染与 v4/source-container-v3 活跃采用门禁；新政策实际 Git 见证
  再核验，历史 unit-v1/容器 v1/v2 的原语义与字节保持。库存 v3 安全升级及
  全库/check→对齐/check、完整 04Z2/000Q 预检、独立拒绝回归、全量工具/
  239 QA/117 章、当前 lane render/pdf/模板及 synthetic 公式渲染先本地
  验收，再核对远端完整内容/native 合同/精确 HEAD 两 CI 后授权 bypass。
  不写事实/历史或实际模型运行，不批准术语/人审；当前193非空 batch 及
  全部审计残项保持，具体 DATA 与进度另开任务，八项总验收继续。
- #654 工具本地验收完成：419 项测试/239 QA/117 章与 workflow、harvest、
  upstream-index、Schema、provenance、decision、progress/plan 全部通过。
  全库抽取/check 和对齐/check 顺序通过；43,257 提议为 36,610 READY /
  6,647 BLOCKED，710 个自然文字 slot、619 条完整公式、533 个 typed 提议
  逐项通过 Schema/region。三个登记见证七次，其他位置只按相同精确语法
  规则分类，221 个含 slot 的提议仍保留其他 blocker。04Z2 完整公式段与
  000Q 完整陈述/证明的旧分组及原字节预检通过。1,056 个事实/配置及三份
  来源/术语/证明审计原字节相同，全部实际残项保持。当前 lane render/pdf
  与模板零退出；461 页最终日志通过、全文 layout 文本保持；synthetic
  v4/v3 三类公式 XeLaTeX/PNG 验收通过，不代表实际模型生成或事实修复。
  具体 DATA、S4/S5/S7 与远端精确 HEAD 合并验收继续按原合同执行。
- 04Z2 DATA #656 的术语核对发现扫描器边界缺陷：斜体定义跨公式后，独立
  of/over 片段被当成概念声明，并误要求同单元普通介词逐次双语。先独立
  工具 Issue [#657](https://github.com/dongyaotalk/stacks-project-zh/issues/657)，
  分支 tool/math-qualified-term-connectors，在三个精确路径内按既有规则
  剥离数学限定声明的独立末尾介词；普通目录扫描、完整非限定声明、内部
  词素及原数学/占位符字节保持。先写五项独立成功/拒绝回归，再修工具，
  核对真实八组提议与全库当前术语/来源/proof 基线；不采用事实或批准术语。
  全量工具/239 QA/117 章与工作流、来源、Schema、溯源、决策、库存/对齐
  顺序重建/check，以及当前 lane render/pdf 零退出和全文保持后提交 PR；
  远端三文件完整字节/patch/native 合同和精确 HEAD 两 CI 后授权 bypass。
  工具合并后 DATA #656 重新准备/check、冻结完整上下文并实际重译，原
  准备与冻结证据保留。S4/S5/S7 与八项总验收继续。
- #657 本地验收：原实现独立回归出现十处失败，边界修复后术语专项 43 项
  及全量 424 项测试通过（334.218 秒）；239 QA、117 章及 workflow、harvest、
  upstream-index、Schema、provenance、decision、progress/plan/check 全部通过。
  对照不可变原实现，当前 1,427 单元的术语库存完全相同；八个 04Z2 提议
  仅 034I 去掉六处纯语法 of/over 要求，全部真术语与来源投影保留。
  全书抽取/check→对齐/check 顺序零退出；所有库存、审计与队列原字节及
  范围外事实/配置/历史保持。当前 lane render/pdf 零退出，461 页最终日志
  PASS，完整 layout 文本与基线相同；物理页 119 的列表、公式与图无裁切
  或重叠。本工具不减少既有事实残项，实际 DATA 与八项总验收继续。
- S4 的完整惯性小节计划：Issue
  [#656](https://github.com/dongyaotalk/stacks-project-zh/issues/656)，分支
  translate/categories/04z2/openai-gpt-6-1-sol，从工具 #658 合并后的 main
  a6f6b42 重新准备完整八组，保留此前未采用的包与冻结证据。旧八个输入/
  候选和原 run 原字节保留，恢复 034H、034I、04Z6 陈述与两份 proof 的
  真实 Tag；parent 均为 04Z2。完整公式正文为 unit-v2/R3、来源容器 v3，
  只暴露三个 and 参数；其他七组为 unit-v1/容器 v2。先冻结全部新来源、
  完整旧分组、风格/政策/词表/真实术语库存及 context hash，再由本次实际
  GPT-6.1-sol/xhigh 生成每个新输出的完整五字段，Harness 在冻结前及装配时
  动态解析。一个 v4、八份来源证据、不可变 correction/run/原输出在十八个
  精确路径内采用；待决术语不批准，旧审校不继承，源文省略忠实保留。
  来源包 check、424 工具测试、239 QA、117 章、Schema/溯源/决策、全库存/
  对齐顺序重建/check 及独立 Git/旧快照/实际五字段/context/数学 skeleton
  核验；本批队列应为空，其他来源/术语/proof/匹配逐项保持。进度/计划仅
  隔离预览；当前 lane render/pdf 零退出及公式/证明视觉检查后提交 PR，
  远端完整文件/patch/native 合同和精确 HEAD 两 CI 后授权 bypass；合并
  保留六 DATA trailers，随后另开进度任务。S4/S5/S7 与八项总验收继续。
- #656 本地验收：八个旧输入/候选原字节、八个新 Git 完整容器及全部实际
  模型五字段/context hash 逐项核对通过。75 条双语记录覆盖 67 次来源术语
  要求，均待决；三个 and slot 译为“以及”，其余数学原字节/skeleton 保持。
  全部八块 BYTE_EXACT，本批队列为空；其他全部匹配、来源/术语/proof
  结果逐项保持。当前仍为 1,427 单元，坐标 21→16，错陈述 Tag 3→0，
  来源诊断 26→17，未保护节点对 3→1；术语问题候选 756→750、诊断
  2,397→2,353。187 组/262 单元 proof 仍为 175 匹配、12 差异、零未支持；
  192 个 batch 尚有非空修复队列，两个歧义及其他来源差异保留。
  424 工具测试（322.849 秒）、239 QA、117 章、workflow/harvest/upstream/
  Schema/溯源/决策、全库存/对齐顺序重建/check、隔离进度/计划/check 均
  通过。render/pdf 零退出，461 页最终日志 PASS；物理页 117–120 的列表、
  完整证明、三处公式文字、图及最后二纤维积引理均可读，无裁切或重叠。
  原文省略证明及细节忠实保留；未增加证明或审批。候选进度预览为
  108/3,299 Section，Categories 24/44（54.5%），在 DATA 合并后另开进度
  任务写入。仅本批候选验收，S4/S5/S7 与八项总验收继续。
- S4 的完整规模界引理计划：Issue
  [#662](https://github.com/dongyaotalk/stacks-project-zh/issues/662)，分支
  translate/sets/000q/openai-gpt-6-1-sol，从 DATA #659 及独立进度 #661 后的
  main 7c723d0 准备完整四输入→两输出。真实 owner 000Q、Section parent
  000H；旧 parent 000Q 只留在完整历史。恢复整份陈述及三段合并的完整
  proof，数学 region 中两处 affine opens of 文字叶开放，其余原数学字节、
  skeleton、环境、引用与原序保持。陈述为 unit-v1/来源容器 v2，证明为
  unit-v2/R3/容器 v3；一个 v4、两份证据及完整实际 GPT-6.1-sol/xhigh
  五字段修订/correction/run 及相应章节模板在十三个精确路径内采用，
  不回写 legacy run。
  先准备/check、冻结完整新输入、旧分组、风格/政策/词表/术语库存及
  context hash，Harness 在冻结前及装配时动态解析；本批完整引理/证明
  低于300来源词时显式记录范围偏好例外，不裁断或混入不相关材料。
  424工具回归、239 QA、117章及来源/Schema/溯源/决策、全库库存/check→
  对齐/check、独立 Git/旧新字节/实际五字段/context/数学骨架核验；两块
  BYTE_EXACT、本批队列为空，其他审计结果逐项保持，进度/计划隔离预览。
  当前 lane render/pdf 零退出及完整证明/公式文字视觉验收后才提交 PR；
  远端完整文件/patch/native合同及精确 HEAD 两项 CI 后授权 bypass，保留
  六 DATA trailers，合并后先另开进度任务。基线仍为192非空 batch、750
  术语问题候选、17来源诊断、12 proof 差异；S4/S5/S7、F1–F8继续，词表/
  critic/语言数学人审及发布不批准，英文原文与全部已有历史保持。
- #662 范围补充：纠正 parent 后 chapter-template-check 实际发现 sets.json
  过期。先在 ignored 目录生成并比较全部117章，仅 sets.json 为 Section
  000H 的 unit_files 新增本批 sets-000Q；其他116章原字节相同。Issue 已
  明确补充这一精确路径，随后同步当前章节模板并重新验收；不扩大英文、
  词表、其他批次或任何已有历史的写入范围。
- #662 本地验收：完整四旧输入/候选、两份锁定 Git 容器和本次两份实际
  五字段/context hash 核对通过；旧三段证明合并为一个完整 unit-v2，单个
  原数学 region 的两处 affine opens of 文字以双语翻译，其他数学原字节/
  skeleton 与引用保持。27条双语记录覆盖19次来源要求，均待决；90来源词
  明确记录完整引理/证明的偏好范围例外。两块均 BYTE_EXACT、本批队列为空；
  全部其他匹配、来源/术语/proof 结果逐项保持。当前1,425单元/239批，
  proof 为187组/260单元、176匹配/11差异/0未支持；术语问题候选750→746、
  诊断2,353→2,346，非空修复批192→191。坐标16、来源17、未保护节点对1、
  错陈述Tag0和两个歧义保持。
  424工具测试通过（291.080秒）；章节模板变更的独立回归及117章核对通过，
  239 QA 的 workflow/harvest/upstream/Schema/provenance/decision 均通过；
  全库抽取/check→对齐/check 零退出，隔离progress/plan/check通过。既有
  三份进度/计划文档逐字相同，候选仍108/3,299 Section、Categories24/44。
  render/pdf 零退出，461页最终日志PASS；物理页32–34逐页核对，完整引理/
  proof、两处公式文字与文献引用均可读，无裁切或重叠。该公式保留48.93825pt
  overfull警告，但完整位于页面内；不改变原数学字节以消除排版警告。范围外
  已跟踪字节保持，远端验收和合并后独立进度任务继续，S4/S5/S7与总验收未完。

- 000Q DATA PR [#663](https://github.com/dongyaotalk/stacks-project-zh/pull/663)
  已合并到 `4f680df40fdf3223046f7a448795ad52de8d3829`；随后独立进度任务 Issue
  [#664](https://github.com/dongyaotalk/stacks-project-zh/issues/664)，分支
  docs/progress-after-000q-container。在下一数据批次前从已合并事实执行
  progress/check及plan/check，117章报告与DATA隔离预览逐字相同；候选仍为
  108/3,299 Section、Categories24/44，人工语言/数学审校和发布仍为零。
  三份生成报告保持原字节，本次只记录实际修复进度：191非空修复batch，
  746术语问题候选/2,346诊断，16坐标、17来源诊断、1未保护节点对、
  0错陈述Tag和2歧义；187组/260单元proof为176匹配、11差异、0未支持。
  239批/1,425活跃单元及全部历史保持；库存43,257提议为36,610 READY/
  6,647 BLOCKED。合并后workflow/harvest/upstream-index、117章模板及
  provenance/decision均通过。当前lane render/pdf零退出、461页最终日志
  PASS；全文layout文本及物理32–34页PNG与DATA验收相同。独立进度同步
  不授予词条/critic/人审或发布；S4/S5/S7与F1–F8总验收继续。

- 四批合并修订计划：[Issue #666](https://github.com/dongyaotalk/stacks-project-zh/issues/666)，
  分支 translate/sets/size-batch/openai-gpt-6-1-sol，基线 main
  `18caffded38292383f705803d2f3d77fa0492a15`（进度 PR #665 已合并）。
  复用全库来源库存和统一修复队列，同一 sets Section 000H 的 000I、000P、
  04T6、04T7 四个完整 batch 九旧单元恢复为八个完整陈述/证明；04T6 两段证明合并。
  每批分别冻结完整旧新包及 v4 来源证据，一次实际 GPT-6.1-sol/xhigh run 对全部
  八新单元生成完整五字段；一个 correction 按 unit 显式映射四个 derivation。
  Harness 冻结前及装配时动态解析。旧 parent 000I/000P/000Q 只留不可变历史，
  chapter template 同步真实 000H 归属；现有数学、引用、标签及原输出/run 不回写。
  04VA 的游离引言没有可核实 Section anchor，独立工具/数据处理，本批不采用。
  统一执行 QA、来源/术语/proof 对齐及确定性 check、完整溯源/范围核验和当前 lane
  render/pdf 与目标页视觉验收；八容器应 BYTE_EXACT、四批队列清空，其他诊断保持。
  完整远端字节/patch/Issue 合同及精确 HEAD CI 后按已有授权 bypass squash，
  合并后统一做一次独立进度任务。偏好词数例外及实际字数在 run 明示；
  F1–F8、S4/S5/S7 总验收继续，不授予术语/critic/人审或发布批准。

- #666 四批实际修订与集中门禁已通过：286来源词，九旧→八新完整容器，
  一个实际修订run/correction、四份v4、八份来源恢复证据；八份新五字段和全部
  冻结context逐项相同，66术语声明覆盖43来源要求，全部未批准词条维持待决。
  424回归通过（311.967秒），239批QA及workflow/harvest/upstream-index/
  117章模板/Schema/provenance/decision通过；四次全库抽取及对齐生成/check通过。
  八容器均BYTE_EXACT，四批队列清空，其他匹配/来源/术语/proof逐项保持。
  非空修复批191→187、术语问题候选746→738、诊断2,346→2,323、
  坐标16→13、来源诊断17→14、proof差异11→8；187组/259proof单元为
  179匹配、8差异、0未支持。活跃事实239批/1,424唯一单元；0错陈述Tag、
  1未保护节点对与2歧义保持。匹配113 BYTE_EXACT/1,057 PRESENTATION/
  252 SOURCE_DIFFERENCE/2 AMBIGUOUS。其他116章模板及范围外原字节保持，
  唯一sets模板增加四批的真实000H归属。进度/计划三文档与隔离预览逐字相同，
  候选仍108/3,299 Section、Categories24/44；原输入/输出/run与全部历史保留。
  提交前实际模型完整重出八单元五字段，去除两处显示公式外的多余中文句号，
  原公式句点及其他源字节保持；初版实际输出/装配/验收原字节留在ignored记录。
  最终五字段、QA、库存check、对齐/check与进度/计划复核再次通过。
  当前lane最终render/pdf零退出、461页最终日志PASS，物理29–35页逐页核对；
  六页PNG保持，第34页两条完整显示公式及其后正文可读，无多余句号/裁切/重叠。
  已有000Q公式48.93825pt overfull警告保持且整式位于页面内，不改变原数学。
  34声明文件之外原字节保持，远端与精确HEAD CI验收、合并后独立进度继续。

- 四批 DATA PR [#667](https://github.com/dongyaotalk/stacks-project-zh/pull/667)
  已合并到 `44be32bf150c9a2468cb35d830a4d9c13484178e`；独立进度 Issue
  [#668](https://github.com/dongyaotalk/stacks-project-zh/issues/668)，分支
  docs/progress-after-size-batch。在下一数据批次前从已合并事实执行
  progress/check及plan/check，117章报告与DATA最终隔离预览逐字相同；
  三份报告保持，候选仍108/3,299 Section、Categories24/44，人工语言/数学
  审校与发布零。当前239批/1,424唯一活跃单元；187组/259 proof单元为
  179匹配、8差异、0未支持。修复队列为187非空batch、738术语问题候选/
  2,323诊断、13坐标、14来源诊断、1未保护节点对、0错陈述Tag和2歧义。
  全来源库存43,257提议为36,610 READY/6,647 BLOCKED；全部run和历史保持。
  合并后workflow/harvest/upstream-index、117章模板和provenance/decision通过；
  当前lane render/pdf零退出，461页最终日志PASS，全文layout文本及物理
  29–35页PNG与DATA最终验收相同。译文事实树与全部范围外已跟踪字节保持。
  独立进度同步不授予词条/critic/人审或发布；F1–F8与S4/S5/S7总验收继续。

- 集中准备加速计划：[Issue #670](https://github.com/dongyaotalk/stacks-project-zh/issues/670)，
  分支 tool/source-containers-many，从独立进度 #669 合并后的 main
  `666f7cba8fcc9a7812a6457ffabbe2a9e091a7fe` 冻结全输入。先在来源容器设计 §9.2
  说明一次真实溯源/冻结快照复用、逐包完整验证及八文件等价，再实现 CLI 与独立
  成功/拒绝回归。至少两份同章互不重叠完整 batch 共用本次内部会话；无跳过或自报
  校验参数、无跨调用磁盘缓存。跨包输入/输出/派生 ID、候选目标与来源容器冲突
  拒绝；所有 BLOCKED 和完整旧输入保留，check 只读，整包临时生成/原子替换/回滚。
  逐 plan 和落盘前核对 HEAD、锁、政策、完整事实/历史/审校、所有已跟踪输入、
  plan 与旧包原字节；变化失败。原单批接口/包版本、所有恢复证据/历史语义保持。
  实际四份完整当前规模界批次分别运行原接口与新接口，逐包八文件相等并测耗时。
  全量工具/239 QA、117章/Schema/溯源/决策、库存/check→对齐/check及进度/计划
  与当前 lane render/pdf 验收；完整远端字节/patch/native合同及精确HEAD两CI后
  授权bypass。只改五个声明工具/文档/回归路径，不采用事实或生成中文/run/批准；
  全部范围外原字节及187修复batch、738术语候选/2,323诊断、13坐标、14来源诊断、
  8 proof差异与2歧义保持，具体DATA及F1–F8、S4/S5/S7总验收继续。

- #670 实际四批只读性能验收：直接加载基线已合并原实现，完整000I/000P/04T6/04T7
  八输入分别准备311.096秒；新接口一次真实溯源并逐包验证，生成99.201秒，3.136倍，
  独立check98.412秒且文件/目录mtime保持。32子包文件与原实现逐字相等；完整事实/
  历史、translation-data树及范围外原字节保持，不采用来源或生成实际模型run。
  33项原来源容器回归及11项新增独立回归通过，含两个各自可准备包的跨来源区间/输出
  冲突拒绝、有效跨章拒绝、完整阻断保留、输入/审校/锁/HEAD/plan/输出并发变化、
  symlink与整包安装失败回滚。全量工具/QA/库存/对齐和当前lane编译验收继续。

- #670 全量本地门禁通过：435项回归（373.603秒）、239批QA及workflow/harvest/
  upstream-index/117章模板/Schema/provenance/decision通过。全库抽取/check→
  对齐/check顺序零退出；库存、来源/术语/proof审计、匹配与队列十文件原字节保持。
  117章隔离模板、三份进度/计划预览及check逐字相同，候选仍108/3,299 Section、
  Categories24/44；范围外1,332已跟踪文件及全部译文事实树保持。187修复batch、
  738术语候选/2,323诊断、13坐标、14来源诊断、8 proof差异与2歧义继续。
  当前lane最终render/pdf、完整远端文件/patch/native合同及精确HEAD两CI继续；
  不将只读准备与性能验收计为实际DATA、人审/词表/critic或发布批准。

- 完整列表批次修复计划：[Issue #672](https://github.com/dongyaotalk/stacks-project-zh/issues/672)，
  分支 translate/sets/000r/openai-gpt-6-1-sol，从工具 #671 合并后的 main
  `f07b5e97139077a6b1bdfdd880d2f455147ca45c` 开始。000R 的完整17段陈述（含两层
  列表）和2段证明恢复为两个锁定 Git 完整容器，真实 Section parent 为000H；
  全部19个旧单元、候选与原始run/祖先原字节留档。先准备/check完整来源，冻结
  新保护输入、完整旧组、政策/风格/词表/提示词/术语目录及实际运行身份，动态解析
  Harness后由当前模型完整生成两个五字段修订；程序只保护、序列化和装配。
  来源约366词，完整语义范围保持。独立核对两个Git容器逐字回放、全部旧新覆盖、
  全部五字段/context/run、全库ID和13个声明路径；执行435回归、239批QA、117章
  模板、来源库存/check及对齐/check、Schema/溯源/决策、进度/计划预览/check，
  当前lane render/pdf零退出并视觉核对修改页后才提交和PR。远端完整字节/patch/
  native Issue合同和精确HEAD两项CI通过后授权bypass，随后独立进度同步。
  000J旧混合parent及未分类数学文字、000U/000X数学文字、04VA/0AHL游离引言和
  Categories残项仍保留；本批仅清理000R，其他来源/术语/proof逐项保持。
  不授予术语/critic/语言或数学人审/发布批准，F1–F8与S4/S5/S7总验收继续。

- #672 实际来源及模型验收：完整19旧→2新，366来源词；完整Git回放、全部五字段/
  context、原旧批/所有历史、85双语声明和56来源必需项均通过。初稿占位符顺序错误
  被门禁拦截后，完整两条输出重新生成，失败稿保存在ignored材料且未采用为事实。
  全库库存/check→对齐/check通过，两个新容器BYTE_EXACT，000R队列清空；其他
  匹配、术语、来源错误与proof逐项保持。当前239批/1,407唯一活跃unit，修复队列
  186非空batch、727术语问题候选/2,302诊断，13坐标和14来源诊断保持；187组/
  258 proof单元为180匹配、7差异、0未支持，2歧义和1未保护节点对仍保留。
  全量回归、QA和最终编译/视觉及远端PR验收继续；候选仍待术语决定和人工审校。

- #672 本地全量回归435项通过（413.371秒），239批QA及Schema/来源/溯源检查
  通过。当前lane render130.590秒、pdf88.287秒均零退出，461页完整日志无错误；
  物理15/16页来源披露及35–38页完整列表/证明与邻接范围视觉通过，无裁切或
  重叠。全文layout仅来源披露计数与000R所在五页变化，其余456页文本保持。
  13个声明文件、117章模板及全库唯一ID复核通过；最终进度/计划预览、完整远端
  PR字节/patch/native合同和精确HEAD CI继续。证明差异7组及其他残项保持，
  不将本批候选或自动检查计为人工批准。

- 完整000R DATA PR [#673](https://github.com/dongyaotalk/stacks-project-zh/pull/673) 已合并到 `fb9d0d3366d4a2dccc9fa83bb7899bb77aa97497`；
  独立进度 Issue [#674](https://github.com/dongyaotalk/stacks-project-zh/issues/674)，
  分支docs/progress-after-000r。在下一DATA前从已合并事实执行progress/check及
  plan/check，117章报告与DATA最终隔离预览逐字相同，三份报告保持；候选仍
  108/3,299 Section、Categories24/44，人工语言/数学审校与发布零。当前239批/
  1,407唯一活跃unit；186修复batch、727术语问题候选/2,302诊断，13坐标/
  14来源诊断、2歧义和1未保护节点对保持。187组/258 proof单元为180匹配、
  7差异、0未支持。全库存43,257提议/36,610 READY/6,647 BLOCKED保持。
  workflow/harvest/index/117模板/provenance/decision通过；当前lane render/pdf
  零退出，461页全文layout及物理15/16/35–38页PNG与DATA接受版本逐字相同。
  完整译文事实树、原始run/历史与所有范围外tracked字节保持。该进度任务不授予
  词表/critic/人审或发布批准；F1–F8/S4/S5/S7继续。

- 集中记号分类计划：[Issue #676](https://github.com/dongyaotalk/stacks-project-zh/issues/676)，
  分支tool/prefixed-set-notations，基线main `cefd3be7f4a8248ccf322309b88b6f2f5b6e01cc`。
  在源码设计中先声明独立size、Cov非空下标与G-Sets前缀记号的精确合同，再实现
  严格政策/真实裸前缀token匹配及独立接受/拒绝回归。前两项保留旧用法优先级；
  -Sets只允许textit与G，其他数学文字仍按原阻断或typed-slot合同处理。完整000U/
  000X的22旧单元只读准备/check四份来源提议，000J旧混合parent限制保持。全部
  事实/历史/源/词表原字节及186修复batch、727术语候选/2,302诊断、13坐标/
  14来源诊断、7proof差异、1未保护节点对与2歧义保持。全回归/239 QA、117章、
  Schema/溯源/决策、全库存/check→对齐/check及进度/计划通过，当前lane编译/
  全文和已接受页面PNG保持后提交PR；远端完整字节/native合同/精确HEAD CI后
  授权bypass。只改声明六个政策/工具/测试/文档路径，不生成中文/run/事实或批准；
  具体DATA、F1–F8及S4/S5/S7继续，不以分类工具代替实际数据修复。
  完整准备须绑定已提交政策：源容器/旧组核验、全部本地门禁及编译先于本地
  工具提交，再以该真实origin执行many prepare/check，成功后才push/PR；保留
  初次未提交政策被严格拒绝的记录，不更改来源准备工具或历史门禁。

- #676 本地445项回归、239批QA及117章模板/进度/计划检查通过。全库43,257
  提议中36,650 READY、6,607 BLOCKED；新增162处记号分类（size 2、Cov 105、
  -Sets 55），40个来源容器解除阻断。原4698分类逐字保持，116份锁定Git回放
  通过；48条匹配及9份队列只变政策hash/抽取状态，来源/术语/proof审计原字节
  保持，186修复batch等事实残项不变。当前lane render/pdf零退出，461页全文
  及15/16/35–38页PNG保持；六路径外1341个已有tracked文件及全部事实/历史
  保持。四个完整新容器源字节/旧组核验通过，many prepare/check在本地工具
  提交冻结政策后继续；仅工具验收，不采用译文或授予批准，S4/S5/S7继续。

- 完整相邻批次修复计划：Issue [#678](https://github.com/dongyaotalk/stacks-project-zh/issues/678)，
  分支translate/sets/000u-000x/openai-gpt-6-1-sol，基线main
  `00bdfdbc658f56397f5e279fae7f859d248f550a`。记号工具PR #677已按精确HEAD
  CI/bypass合并；从已合并政策重新many prepare/check，完整000U/000X的22旧
  单元恢复为四个完整lemma/proof，真实相邻Section000T/000W；X proof沿用
  既有unit-v2数学and slot，其余数学保持。冻结全部新源/完整旧组/政策/风格/
  词表/提示词/术语及实际最新模型turn身份，动态Harness后每新unit实际完整
  五字段修订；共享一个真实run/correction、两份v4/四份来源证据，保留全部
  原run/输出/历史。20声明路径内同步sets模板，445回归/239 QA及117章、
  Schema/溯源/决策、全库存/check→对齐/check与进度/计划隔离预览通过；
  全部旧新/真实Git/五字段/ID/范围独立复核，整书render/pdf和目标页视觉
  验收后push/PR，完整远端/native合同/精确HEAD CI后授权bypass。合并后
  独立progress先于下一DATA。当前186问题batch/727术语候选/2302诊断、
  13坐标/14来源、7proof差异及其他残项继续，不授予术语/critic/人审/发布批准。

- #678 首轮未提交候选的视觉验收发现正文尾部来源换行被省略，AJbook将X证明
  结束方框放在中间列表后；重复整书编译仍复现。独立最小排版对照确认单个尾部
  换行保留正确终止位置。完整首轮事实/run/原输出和失败材料保留在ignored证据，
  第二个实际run `run-20261009-sets-000u-000x-complete-gpt61sol-02` 重新核实冻结
  输入/runtime，完整生成四单元五字段，保留来源尾换行；继续完整数据和视觉验收。
  活跃候选保留两个不同历史run，跨批QA使用本次共享修订run的两份原始候选，
  所有活跃文件仍通过全库QA/溯源核对，不改写历史身份。

- 完整000U/000X DATA PR [#679](https://github.com/dongyaotalk/stacks-project-zh/pull/679) 已合并到 `ab38d30be178caa517ddc0929f3a391b7cb94c44`；
  独立进度 Issue [#680](https://github.com/dongyaotalk/stacks-project-zh/issues/680)，
  分支docs/progress-after-000u-000x。在下一DATA前从已合并事实执行progress/check及
  plan/check，117章报告与DATA最终隔离预览逐字相同，三份报告保持；候选仍
  108/3,299 Section、Categories24/44，人工语言/数学审校与发布零。当前239批/
  1,389唯一活跃unit；184修复batch、714术语问题候选/2,268诊断，13坐标/
  14来源诊断、2歧义和1未保护节点对保持。187组/246 proof单元为182匹配、
  5差异、0未支持。全库存43,257提议/36,650 READY/6,607 BLOCKED保持。
  workflow/harvest/index/117模板/Schema通过；render重验溯源，DATA的decision验收与事实树保持；当前lane render/pdf
  零退出，461页全文layout及物理15/16/37–43页PNG与DATA接受版本逐字相同。
  完整译文事实树、原始run/历史与所有范围外tracked字节保持。该进度任务不授予
  词表/critic/人审或发布批准；F1–F8/S4/S5/S7继续。

## 02C3 词汇证据前置计划（Issue #683）

DATA #682 的四批完整修订在239候选 QA通过后，全库对照发现 axiom-of-choice
与 essentially-surjective 的旧分段来源 hash 消失。全部未合并事实、实际模型
run/raw、来源包和失败报告逐字归档，当前事实恢复基线；不豁免新增两项诊断。
先按已有 locked-source-container 合同分别绑定02C3完整 proof/lemma，真实
Section0013、ordinal1及锁定 Git 完整片段 hash，正文精确词形必须可见。开发
文档先于配置修改，只改两项 evidence，所有 forms/chapters/其他目录、词表和
数据/历史保持。全239 QA、来源/术语/proof/库存/队列逐项及全构建/layout验收
后独立工具 PR；精确HEAD双CI/远端合同后admin bypass，随后DATA从新main
重新prepare/check、完整冻结和实际生成。八项总验收及S4/S5/S7继续。

## Section0013 四批完整修订计划（Issue #682，前置 #684 后）

以新main `dc5a40d0147870687079a52ff60faaef04f38dc5` 为基线，02C3 的两个词汇
锚点已在独立工具PR #684稳定到锁定Git完整容器。原失败试验的全部事实、
输入/run/raw/日志已逐字保留且未采用。重新准备 categories-02C2、001J、05SG、
02C3 四个连续完整batch，共15旧→6新容器、347来源词；真实parent0013，
历史错误parent原字节仅留快照，完整备注/定义/交换图/两对引理证明不能切断。

先many prepare/check，再完整冻结所有新来源、旧组/candidates、政策/风格/词表/
prompt/源词汇目录及动态Harness、本次实际模型身份，当前模型完整生成六单元
全部五字段，用新实际revision run02/correction连接四份v4和六份来源证据。
保留所有历史且不继承批准；每份证明保持源文末尾单换行。验收32路径、Git
字节/五字段/context/祖先/唯一ID、239 QA与完整共享run四批qa-batch、所有来源/
Schema/溯源/决策/117模板、全extract/check→alignment/check及隔离进度/计划。
六新容器BYTE_EXACT、四队列清空，范围外诊断逐项保持，包括词汇取证失败数
不得新增。当前lane render/pdf零退出和目标页视觉验收后commit/push/PR；
完整远端字节/patch/native合同及精确HEAD双CI后按授权admin bypass。DATA
合并后先独立progress任务。基线184修复批、714术语问题候选/2268诊断、
13坐标/14来源诊断、5proof差异及1未保护节点对/2歧义仍保留；总F1–F8/
S4/S5/S7及人审、词汇批准与发布继续，不能计未采用试验为已完成。

- 完整02C2/001J/05SG/02C3 DATA PR [#685](https://github.com/dongyaotalk/stacks-project-zh/pull/685) 已合并到 `a8bd19540dfa45e39a59db76f56899e674d88db5`；
  独立进度 Issue [#686](https://github.com/dongyaotalk/stacks-project-zh/issues/686)，
  分支docs/progress-after-categories-equivalences。在下一DATA前从已合并事实执行progress/check及
  plan/check，117章报告与DATA最终隔离预览逐字相同，三份报告保持；候选仍
  108/3,299 Section、Categories24/44，人工语言/数学审校与发布零。当前239批/
  1,380唯一活跃unit；180修复batch、705术语问题候选/2,246诊断，13坐标/
  14来源诊断、2歧义和1未保护节点对保持。187组/242 proof单元为183匹配、
  4差异、0未支持。全库存43,257提议/36,650 READY/6,607 BLOCKED保持。
  workflow/harvest/index/117模板/Schema通过；render重验溯源，DATA的decision验收与事实树保持；当前lane render/pdf
  零退出，461页全文layout及物理15/16/48–50页PNG与DATA接受版本逐字相同。
  完整译文事实树、原始run/历史与所有范围外tracked字节保持。该进度任务不授予
  词表/critic/人审或发布批准；F1–F8/S4/S5/S7继续。

## 0032 强调语法及稳定来源证据计划（Issue #688）

主分支 ca696ea5337d60aebfc20b942f77d92080f7fcef 已含独立进度 #687。
0032 的真实 Section002Z 完整lemma可准备，完整proof唯一未知命令是显式分组 em；
旧15单元仍是当前事实。本工具先写开发合同，再按明确政策增加 EMPH 字体保护，
保留原开闭组/声明、数学/脚注/引用/空白及既有bf/it语义；旧政策、未分组和伪包装
仍拒绝。cofinal、finitely-generated、ordinal三项 evidence 稳定到真实完整proof，
准确词形/selector/Git hash核验，其他目录及批准状态保持。

九声明路径内执行有意义回归、全工具/239 QA/所有结构化门禁和117模板，全库存/
check→对齐/check，逐项核对全部事实审计和库存匹配增量；progress/plan保持。
当前lane render/pdf零退出及全书layout/目标页保持后本地工具commit，以真实提交
冻结政策再只读prepare/check完整15旧→2新，全部原事实/历史/run/raw保持。远端
全部字节/patch/native合同及精确HEAD双CI成功后授权bypass；具体DATA合并后另开
Issue重新准备、完整冻结并实际生成两单元五字段。当前180修复batch、705术语
候选/2246诊断、13坐标/14来源、4proof及1未保护pair/2歧义和F1–F8/S4/S5/S7继续。

## 0032 完整有向系统陈述与证明修订计划（Issue #690）

前置工具 PR [#689](https://github.com/dongyaotalk/stacks-project-zh/pull/689) 已合并到
`b58b1839b0edb5eb0c5cb92ba8969f52ef5e0e0a`，完整 proof 的 em 已有明确保护政策，
三条术语证据稳定到锁定 Git。按真实 Section002Z 恢复完整0032 lemma/proof，
旧7条陈述与8条证明变为2个完整容器；新ID为tag:0032:statement与tag:0032:proof。
完整15条旧输入/候选及历史、长脚注、强调、交换图、所有数学/引用与尾换行均保留。

先从新main重新prepare/check，再冻结全部新源、旧分组/candidates、政策/风格/
词表/prompt/来源目录、动态Harness及本次真实runtime，实际模型完整生成2单元
全部五字段。一个新revision run/correction连接一份v4与两份来源恢复证据，
程序只保护、序列化、验证及装配。验收13路径、完整Git/五字段/context/来源图、
239 QA与真实当前run qa-batch、全extract/check→alignment/check及117模板/
Schema/溯源/决策/进度计划预览。两个来源BYTE_EXACT、proof match、目标队列
清空，范围外诊断逐项保持；当前lane render/pdf零退出及完整日志/目标页视觉
验收后commit/push/PR，远端字节/完整patch/native合同与精确HEAD双CI后授权
bypass。DATA合并后独立progress。基线180问题batch、705术语候选/2246诊断、
13坐标/14来源、4proof、1未保护pair/2歧义继续；不授予术语、人审或发布批准，
不修英文疑点或补证明，F1–F8/S4/S5/S7总目标保持未完成。

- 完整0032 lemma/proof DATA PR [#692](https://github.com/dongyaotalk/stacks-project-zh/pull/692) 已合并到 `d36e9d7739acb1e6fce1167254db2e0431dfad15`；
  独立进度 Issue [#693](https://github.com/dongyaotalk/stacks-project-zh/issues/693)，
  分支docs/progress-after-categories-directed-0032。在下一DATA前从已合并事实执行progress/check及
  plan/check，117章报告与DATA最终隔离预览逐字相同，三份报告保持；候选仍
  108/3,299 Section、Categories24/44，人工语言/数学审校与发布零。当前239批/
  1,367唯一活跃unit；179修复batch、695术语问题候选/2,194诊断，13坐标/
  14来源诊断、2歧义和1未保护节点对保持。187组/235 proof单元为184匹配、
  3差异、0未支持。全库存43,257提议/36,651 READY/6,606 BLOCKED保持。
  workflow/harvest/index/117模板/Schema通过；render重验溯源，DATA的decision验收与事实树保持；当前lane render/pdf
  零退出，461页全文layout及物理15/16/78–87页PNG与DATA接受版本逐字相同。
  完整译文事实树、原始run/历史与所有范围外tracked字节保持。该进度任务不授予
  词表/critic/人审或发布批准；F1–F8/S4/S5/S7继续。

- 工具 Issue [#695](https://github.com/dongyaotalk/stacks-project-zh/issues/695)，
  分支 tool/source-container-semantic-boundaries，基线
  `f74a853168a8e02990e7329864de754b338046cc`。先写完整来源及模型溯源开发合同，
  再实现独立 source-container-v4 边界 witness；真实 sets-000J 主/子标签和
  0AHL/04VA 引言的紧邻陈述分别核验，旧版本原限制保持，具体 DATA 另开。
  工具不采用事实、不消除诊断、不生成模型输出或批准。验收要求三个完整只读
  包/check、篡改与拒绝回归、整库 QA/117 模板/进度计划和当前 lane render/pdf。
  基线仍179修复批、695术语候选/2194诊断、13坐标/14来源、3proof差异、
  1未保护pair/2歧义；全库存43257/36651 READY/6606 BLOCKED保持。
  八项审查与 S4/S5/S7 总目标继续。
  实际只读准备发现唯一额外前置依赖 transfinite-induction 的旧 proof-p001
  来源证据。在目录写入前扩展 Issue/开发合同/allowed_write_files，只将该 evidence
  迁移到锁定 Git 的完整000J proof；其他目录、词形/范围/批准和全部事实保持。
  该变更后重新验收完整工具/QA、三个包/check、全库库存/对齐及 render/pdf。

  本地验收：460项工具回归及239候选QA通过；117模板和三份进度/计划报告原字节
  保持。三个真实完整只读包为28旧→8新、8组/零BLOCKED，四组需要原生边界
  witness，其余使用原v2；确定性check保留全部文件mtime。整库117章/116 Git
  回放及全部库存原字节保持；仅一个目录取证及其hash变化，所有当前术语/来源/
  proof finding和179问题batch、695术语候选/2194诊断、13坐标/14来源、3proof
  差异保持。范围外1384份既有tracked文件原字节、完整事实树与历史保持。
  render180.130秒、pdf104.938秒均零退出，Final TeX log通过；461页中460页
  全文layout原字节相同，第2页仅构建日期2026-10-09→2026-10-10，实际前后
  PNG已查看；1/3/15/16/78–87页PNG逐字相同，无裁剪或重叠。首次同日比较
  预期拒绝了这一真实日期变化，未修改生成TeX/PDF，完整差异留在ignored验收证据。
  目录验收脚本修正仅顶层hash及文件/语义hash的错误比较口径，逐项核对全部unit
  目录hash和完整finding保持，未降低检查。远端全字节/完整patch/native合同及
  最新精确HEAD两项CI后才按授权bypass；本工具仍未采用实际译文或授予批准。

- TOOL Issue [#702](https://github.com/dongyaotalk/stacks-project-zh/issues/702)，分支tool/pr-contract-large-blobs，基线`fb0ae9ba6e1f3ffb48fcae0d7adcebc5ce5c8ebe`。
  PR701的完整冻结原始输出1061688 bytes触发Contents API大文件空content，CI按现有
  合同拒绝。先规划独立四路径工具任务；Contents仍绑定精确PR head/base及path，
  大文件只按同repo/metadata sha请求blob，严格校验编码、size、Git blob原字节哈希。
  不改历史raw/事实或跳过门禁；真实大文件及负例、全部工具/QA/共享检查、完整
  PR701只读native合同和29字节、当前lane render/pdf零退出后提交工具PR。
  远端完整patch/native单Issue/最新精确HEAD双CI通过后授权bypass；随后普通合并
  main到DATA分支，保留数据原字节，不force；下一DATA前独立progress，700另处理。

  本地验收：466项工具回归、239候选QA及全部共享/117模板/progress/plan检查通过；
  真实PR701全部29远端文件原字节/完整patch及GitHub-native单closing697合同通过，
  其中1061688 bytes原输出通过Contents精确ref→Git blob SHA回放，27结构文件均验证。
  大文件Unicode、fork/head与删除/base及损坏metadata/encoding/size/原字节哈希/UTF-8/
  blob不可用均有意义回归；不追踪metadata任意URL，不删减不可变输出或跳过检查。
  render114.810秒/pdf65.548秒均零退出，
  Final TeX log通过，461页全文layout与fb0已接受基线逐字相同，译文事实树和所有
  范围外tracked字节保持。完整四路径diff根审查通过，不改变任何批准或当前DATA。


- DATA Issue [#697](https://github.com/dongyaotalk/stacks-project-zh/issues/697)，分支 translate/sets/section-000h-proofs-complete/openai-gpt-6-1-sol，基线 `fb0ae9ba6e1f3ffb48fcae0d7adcebc5ce5c8ebe`。
  前置边界工具PR696已合并；先认领及写开发/验收计划，再重新准备三个完整包。
  sets 000J/04VA/0AHL的28旧单元恢复为8个完整Git容器、Section000H，33个旧新ID
  和29文件提前声明。实际冻结完整新源/每个旧组/candidates、政策/风格/词表/prompt/
  来源术语目录、动态Harness和当前真实模型/effort/turn后完整生成每单元五字段。
  三份v4、八来源恢复和一个真实correction/revision run保留全部历史，旧探测不采用。
  239QA、实际run qa-batch、所有Schema/溯源/决策/来源/模板、完整库存与统一队列check、
  隔离进度/计划、本地整书render/pdf与完整受影响页及邻页看图验收后才提交。
  三proof须match、八片段BYTE_EXACT、三个目标队列空，全部范围外事实/诊断保持。
  英文省略忠实保留，疑点只记remark；精确HEAD双CI/远端全字节/native合同后授权bypass。
  DATA后先独立progress；基线179修复批/695术语候选2194诊断/13坐标14来源/3proof，
  全库存43257/36651READY/6606BLOCKED，八项总修复和S4/S5/S7继续，无批准继承。

  本地验收：从已合并main重新prepare/check耗时125.853/123.690秒，冻结后实际模型
  gpt-6.1-sol/xhigh逐单元完整生成五字段；Harness两次动态解析0.162.0-alpha.17.2。
  八份Git容器、28旧→8新、完整冻结/旧组/原字节历史、严格保护token原序及段落尾
  空白通过。178双语声明覆盖137必需术语；1347全局唯一当前ID、117模板、29路径、
  所有范围外字节保持。239QA、真实revision-run qa-batch、全部共享/决策门禁和
  全extract/check→alignment/check通过，8容器BYTE_EXACT、三个目标队列空。
  187证明组/223单元全部匹配，差异3→0；坐标13→3、来源14→4，术语问题候选
  695→672、诊断2194→2119、修复batch179→176；全部范围外finding逐项保持。
  render136.445秒/pdf81.102秒均零退出，Final TeX log通过；461页中445页全文
  layout相同，16变化页及邻页共24页实际看图通过，公式/脚注/列表无裁切或重叠。
  隔离progress/check与plan/check通过；首次预期报告原字节相同的断言发现000H
  真正变化并保留失败日志。独立117章新旧快照确认仅该节变化：31当前unit全部
  有candidate，四个独立列表Tag000K–000N完整保存在验证的000J陈述中，但现行
  进度只认unit身份，prepared_tags17→13，候选Section108→107、翻译中9→10。
  README/进度暂不在DATA改动，合并后独立progress如实同步；工具Issue700单独
  处理经验证完整容器的嵌套Tag覆盖，不能凑重复旧unit或手改数字，plan保持。
  初次本机系统Python3.9缺tomllib，在输出前失败，改用已配置Python3.12；初稿
  两引言尾换行及辅助预检未赋待决状态的问题保留证据后，由模型完整重出八记录；
  第二稿通过，第三稿完整重出澄清000J末句并补三处词汇声明后才采用唯一真实run。
  三份模型草稿/作者字面量保留，程序不修中文。04VA原文未完成条目及Details omitted、
  0AHL下标次序分别留remark Issues698/699，数学/源码忠实保留，无额外翻译阻断。
  远端完整字节/patch/native单Issue合同及最新精确HEAD双CI后按授权bypass。
  术语/critic、人审和发布仍待决，完整全库存不变，F1–F8/S4/S5/S7继续。

  完整raw超过Contents限制的实际CI失败留档；独立TOOL702已合并到`7529c68ac9b1bf22897ee1ddf2c5d8b2ae927c40`，
  DATA正常forward merge该main并保留双方工程记录，27事实路径、source-origin、
  完整冻结/作者原输出/run/历史全部逐字不变。新状态重新render/pdf和完整全文/
  24PNG比对通过后才提交integration commit，不force、不重写已推送历史；随后
  远端29字节/完整patch/native合同与最新精确HEAD两CI、fresh main门禁重新执行。

- 完整sets三证明DATA PR [#701](https://github.com/dongyaotalk/stacks-project-zh/pull/701)已合并到`319cce6179819951b2c7b2cc2a4b41190112c816`；
  独立progress Issue [#704](https://github.com/dongyaotalk/stacks-project-zh/issues/704)，
  分支docs/progress-after-sets-proof-complete，在下一DATA之前从main运行progress/check及plan/check。
  117章报告与DATA最终隔离预览逐字相同，README/translation-progress由现行算法
  生成108→107/3299候选Section、翻译中9→10，Sets12→11/12，其余节与plan保持。
  000H的31当前unit全部有candidate，四原生嵌套Tag在完整Git陈述中原字节保存；
  身份Tag计数的保守低报仍由独立工具Issue700处理，未改数字、重复旧unit或算法。
  当前239批/1347唯一活跃unit；176非空修复batch、672术语问题候选/2119诊断，
  3坐标/4来源，187组/223proof全部匹配，0差异/不支持；1未保护pair/2歧义保持。
  全库存43257提议/36651 READY/6606 BLOCKED保持。人工语言/数学与发布零，
  源码疑点仅留remark698/699；词表/critic/人审/发布无批准。
  共享/117模板/Schema通过，当前lane render/pdf重新零退出，最终TeX日志通过；
  461页全文layout及24已看图PNG与接受DATA逐字相同。完整译文事实树、immutable
  run/raw/历史和全部范围外tracked字节保持；三路径完整根审查后提交，远端
  字节/完整patch/native单Issue及最新精确HEAD双CI后授权bypass。八项及S4/S5/S7继续。

## TOOL Issue700：完整来源容器的进度范围覆盖（2026-10-11）

  先规划并认领Issue700，从已合并独立进度PR705的
  b66740a2eb70a0388558123334239999669cc208开始。开发合同见docs/progress.md：
  只从当前未归档v4完整组、锁定Git和既有来源恢复验证确认嵌套原生列表Tag；
  普通身份口径、全部候选/人工审校/发布条件及全量provenance门禁保持。
  精确来源证据查询复用完整验证，默认全量不变；不以字符串、缓存或旧ID凑覆盖。
  whole/split-title完整组、假标签、改来源/证据/顺序、缺候选及未批准均需回归。
  预期仅sets/000H的准备13→17，候选107→108/3299、Sets11→12/12；
  其余117章快照和计划、239事实批及全部历史原字节保持。验收包含全回归/QA、
  真实全库存与alignment、当前lane实际render/pdf。Oct11重建与Oct10接受基线
  对照，461页只允许物理第2页日期变化，正文和24已验收页PNG保持，实际查看日期页。
  八文件scope声明在Issue，事实、政策、英文、lock和全部范围外tracked禁止修改。
  本工具不生成模型译文，不授予任何批准；整体F1–F8/S4/S5/S7修复继续。

  本地验收：新增10项意义回归、全476工具测试、239候选QA、全部来源/Schema/
  provenance/decision/117模板及progress/check/plan-check通过。全117章Section快照
  唯一变化为000H prepared13→17，候选108/3299、翻译中9，Sets12/12；
  人审/发布仍零。准备范围与缺候选、审批、未绑定/归档输出严格分别处理，
  named split-title完整组及伪标签、改来源/内容/顺序/hash/ownership均已验证。
  真实全库存5文件、alignment/audits/repair queue
  6文件全部原字节相同；43257提议、36651 READY、
  6606 BLOCKED、18618诊断保持。176待修batch、672术语候选/2119诊断、
  3坐标/4来源、1未保护pair/2歧义保持；187组/223proof全匹配、0差异/不支持。
  一次真实进度核验3.251秒，只验证相关容器，不重扫完整历史。
  render126.332秒/pdf68.262秒实际零退出，
  最终TeX PASS；461页正文全文layout和24已看图PNG逐字相同，物理第2页仅
  构建日期Oct10→Oct11，已实际查看前后日期页，无重排/截断，未改生成产物。
  八路径完整diff根审查通过，事实树、历史raw/run及全部范围外tracked bytes保持。
  远端全文件bytes/whole patch/native单closing700及最新exact-head双CI后授权bypass。
  仅调整完整来源的覆盖统计；全部候选仍须术语、critic与人工审校，未授予批准。


- DATA Issue [#707](https://github.com/dongyaotalk/stacks-project-zh/issues/707)，分支 translate/sets/0ahk-complete/openai-gpt-6-1-sol，基线 `ddba31befe8e64e6fdfe73f88c2f7d9ca7112f60`。
  先认领和规划，再重新prepare/check完整0AHK引言/引理/证明；4旧→3新、真实000H，
  6旧新唯一ID及14文件提前声明。170词预计低于偏好下限，显式完整不可拆范围例外。
  冻结所有新来源/完整旧组/候选/政策/词表/风格/prompt/来源词目录、动态Harness
  和实际模型/effort/turn后，模型逐单元完整生成五字段；一份v4/correction/新run
  与三来源证据保留全部历史，程序不生成中文或批准。独立Git片段/边界witness、
  token原序/尾空白、逐次术语、全库ID及范围外字节、239QA/真实run QA/全部共享
  门禁/117模板、全extract/check→alignment/check、隔离progress/plan和整书
  render/pdf及实际变化页/邻页看图全部验收后提交；远端字节/完整patch/native
  合同和最新精确HEAD双CI通过后授权bypass，DATA后先独立progress。
  基线176批/672术语候选2119诊断/3坐标4来源/零proof差异，八项总修复继续。
  用户2026-10-11确认仍须完成全部F1–F8/S4/S5/S7，完成后交付详细开发文档
  及可复制Codex提示词；必须记录最终架构、命令、真实验收与剩余状态，不以
  单批修复或候选合并冒称全目标/人审/发布完成。

  用户补充：由用户稍后自行重开goal；本轮收尾当前0AHK批次及独立进度，
  交付详细开发文档、真实残项和可复制续接提示词。剩余八项由新goal继续，
  不创建新的goal，不把仍有残项的旧总goal虚报完成。

  本地验收：prepare/check实际111.095/106.845秒，三完整Git容器及独立历史边界
  witness通过；冻结后gpt-6.1-sol/xhigh实际完整生成三单元五字段，Harness冻结前及
  装配动态解析0.162.0-alpha.17.2。170来源词显式不可拆范围例外，43双语声明
  覆盖26必需出现；完整4旧→3新、原字节历史/全部旧组/context/raw/token原序及
  尾空白、1346全库唯一当前ID、117模板、14路径及全部范围外字节通过。
  239QA、实际新run分组QA及全部适用来源/Schema/溯源/决策、全extract/check→
  alignment/check、隔离progress/plan与checks通过。三个target BYTE_EXACT且队列
  空，全部范围外finding逐项保持；坐标3→0、来源4→1、术语候选672→668，
  诊断2119→2106、非空批176→175；187组/222proof全部match、零差异/不支持。
  最后未保护来源为categories-05SH，2处歧义属于05PU，另有167术语动作/67来源
  核验动作，计数可重叠。库存43257提议/36651 READY/6606 BLOCKED保持。
  仅000H的当前unit/candidate31→30，prepared17和全部Section候选/人审/发布状态
  保持；三份进度/计划隔离预览逐字不变，DATA后独立进度仍实际生成/check。
  render156.272秒/pdf73.59秒零退出、Final TeX PASS；
  整书461页，457页全文layout不变，
  4变化页及全部邻页共8页实际看图，无公式/列表/脚注裁切或重叠。
  远端全部14文件原字节/完整patch/native单closing707及最新精确HEAD双CI后授权
  bypass squash；不授予术语/critic/人审/发布批准。接下来独立进度与开发文档/
  提示词交付供用户自行新goal继续全部八项，本轮不启动另一DATA或创建goal。
