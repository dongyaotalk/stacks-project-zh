# 八项审查修复开发与交接指南

本文是开发方法和交接材料；事实状态必须从当前分支的结构化数据、审计与 GitHub
重新读取。它不代替 `WORKFLOW.md`、`config/` 政策或不可变溯源证据。


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


## 1. 总目标和完成定义

完成 `docs/engineering-remediation.md` 的 F1–F8；保留已合并结果，继续 S4 数据修复，
随后完成 S5 强制门禁及 S7 集成验收。用户确认仍需全部八项，本轮收尾当前批次后交付详细开发
文档和可复制 Codex 续接提示词，由用户自行新建 goal 继续八项任务。PR 的 bypass 仅是合并授权，不构成术语、critic、人工
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

在中文仓库根目录选用 Python 3.11+，确认 TeX/XeLaTeX、Biber、makeindex 及 Poppler
可用。不提交本机路径或 config/local.mk。

```bash
python3 --version
make workflow-check harvest-check PYTHON=python3
make extract-all PYTHON=python3
make extract-all-check PYTHON=python3
make source-alignment PYTHON=python3
make source-alignment-check PYTHON=python3
```

输出统一库存和 `build/source-alignment/repair-queue.jsonl`。抽取一次即可集中查看
来源；模型生成按同章、完整语义容器及上下文容量分组。全库不等于一次把原 TeX
送入模型。修复现有事实后必须重建、check 当前队列；当前事实 hash 改变意味着
旧报告不能继续作为本次验收证据。

```bash
python3 - <<'PY'
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
  SOURCE_CONTAINER_DIR=build/task/source-package PYTHON=python3
make source-containers-check \
  SOURCE_CONTAINER_PLAN=build/task/plan.json \
  SOURCE_CONTAINER_DIR=build/task/source-package PYTHON=python3
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
make harness-check HARNESS_ID=codex PYTHON=python3
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

数据任务先独立验证全部新 Git 片段、selector/witness、每个完整旧组、五字段/
context/raw、所有 hashes、全库唯一 ID 及范围外字节。生成全部章节模板到 ignored
目录，核对并只采用任务章的真实变化。工具变化运行有意义的回归；纯数据修复
不为未变工具反复增加与实现镜像的测试。

```bash
make qa-all PYTHON=python3
make workflow-check harvest-check upstream-index-check schema-check \
  chapter-template-check PYTHON=python3
make decision-check PYTHON=python3
make extract-all PYTHON=python3
make extract-all-check PYTHON=python3
make source-alignment PYTHON=python3
make source-alignment-check PYTHON=python3
```

`qa-all` 包含共享 provenance/decision，按依赖避免无理由重复。另对实际新 run
的 frozen unit/raw 做 qa-batch，以免只核对兼容旧 lane。每个 target 容器必须
BYTE_EXACT；对应 actions/findings 清空；所有未声明范围的来源、术语、proof
及事实变化逐项解释或保持。错误不能靠归档当前问题、改状态或跳检查消失。

数据 PR 中只在 ignored 目录生成进度/计划预览并 check；实际报告在 DATA 合并
后用独立进度 Issue/PR 更新，必须先于下一 DATA。验证完整 117 章 Section
差异，完整容器的嵌套 Tag 覆盖要依赖可重放来源证据，不能从候选字符串授予。

```bash
make render MODEL=openai-gpt-5.6-sol PYTHON=python3
make pdf MODEL=openai-gpt-5.6-sol PYTHON=python3
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
| tomllib 导入失败 | 使用 Python 3.11+，每条 Make 显式 PYTHON；失败前没有输出也要保留日志，不改政策 |
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
总 goal 标为完成。由用户自行新建聊天/goal，再粘贴提示词，
先重新核实仓库状态并继续已合并成果。
