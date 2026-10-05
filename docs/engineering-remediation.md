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
| F4 | `%` 等 TeX 控制字符可吞掉受保护正文 | 按源结构校验占位符之外的 TeX 控制字符；新增符号需拒绝或由文本渲染安全转义，不能吞掉公式、参数或环境 | `%` 静默注释、额外分组、对齐、控制符及 math delimiter 回归均被阻断；原有合法包装可编译 |
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
