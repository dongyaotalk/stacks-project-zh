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
