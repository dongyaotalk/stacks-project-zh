# 第4章候选完成阶段续接提示词

复制以下完整内容到后续会话。先核实实时状态；候选完成不授予critic、人工语言/
数学审校、术语或发布批准。详细原始历史保留在开发记录和不可变数据中。

```text
用中文回复。读取工作区AGENTS.md、目标仓库AGENTS.md、WORKFLOW.md和
 docs/categories-candidate-completion.md、docs/source-adoption.md、
 docs/model-provenance.md、docs/task-allocation.md、docs/github-collaboration.md、
 docs/git-conventions.md及实际涉及的Schema/政策。

任务只涉及stacks-project-zh第4章categories候选阶段。英文harvest只读，锁定
 a04446e57ec1fbc252a871afcec7752fb2807b14。保留全部已接受数据、原run/raw/freeze、
 全部递归历史、无关dirty改动和8个stash。不重开F1–F8/S4/S5/S7。不创建子代理或
 新聊天，不安装无关依赖。使用已安装pyenv Python3.12.6，每条Make显式PYTHON。
 不直接push main、force push或改变remote/保护/发布设置。

先只读核实当前分支/HEAD、fresh main、集中Issue814及其唯一DATA PR、独立进度
 PR和claimed冲突。已接受工具基线为e1ca00c228c1194186a065450c1b2c33cc4b8ae9
 （PR829）；PR827/825/823/822/818/816也已接受。它不是数据合并后的最新main，
 不据此覆盖后续成果。工具事实合同以fresh main为准，不重开已接受前置任务。

DATA分支translate/categories/remaining/openai-gpt-6-1-sol。精确scope路径为
 task-scopes/categories-candidate-completion-20261019.json，v14原字节SHA256为
 585608301bf021aead3eb09648c1de33583c8c4e448ba2721780e58f8e386bba；678允许路径，
 本地实际637路径，active unit/candidate各244 ID精确等于完整scope输出集。
 历史scope原字节及冻结内清单保持，不为预留却未产生的raw/run制造文件。

完整生成和装配已完成。全库418批、1086唯一活跃unit；categories574，原330加244。
 全章44实际Section和独立章头0011共614个锁定Git语义行全部覆盖、遗漏0。
 普通24run加source-adoption11run共35个真实run；后者全部历史90个完整五字段
 输出不等于90个新增活跃unit。原24处确认术语缺陷涉及19个unit，最终复核失败0。
 不扩大检索词表，不把普通方位/赋值词或有效分解覆盖的复合词当作重译缺陷。

source-adoption v1/v2/v3按各自已接受权限使用。g008完整重译g005-resumed，
 g009完整重译g007，g010完整重译g008；旧record/input/run/raw及全部有序输出
 归档不改，唯一当前末端。g011-resumed为v3完整生成两个命名标题statement/proof
 batch共4unit；shared_run_histories绑定g009全部8批原输出，只用于原p019参与者
 回放，不消费外部候选。失败g005/g011冻结、全部失败及重试原输出都保留，不把
 未产生输出的冻结伪称run。每个真实身份/turn/Harness以各自实际冻结及原记录为准，
 不复制旧身份用于新生成；程序不能生成或机械补中文、修改raw或冒称人审。

最终本地验收已通过：after-g011 qa-all完整418批，两个lane各render119个TeX。
 实际openai-gpt-6.1-sol PDF313页、集成openai-gpt-5.6-sol PDF457页，最终编译
 exit0和最终TeX日志PASS。实际候选lane179批精确包含全部244输出ID。
 续接后旧qa/render进程handle不可用，复用已完成PASS日志，没有冒称新跑。
 最后两次PDF各有实际持久化退出回执。

独立来源审计0问题；来源术语目录8518次要求0问题；source-alignment/check为
 989 BYTE_EXACT、97 PRESENTATION_EQUIVALENT，术语候选失败0、proof差异0。
 每个真实run的结构、完整五字段/raw/context及全部递归历史均已验证。3907个
 范围外tracked文件原字节保持。全库extract/check与252组完整证明可信通过证据
 按未变source/config/input hash绑定复用，不冒称新运行；全库未采用库存中的
 BLOCKED不是categories漏源。117章模板及隔离progress/plan真实生成/check通过。
 DATA无工具变更，复用PR829相同工具703测试通过证据，不重复无关回归。

证据位于ignored build/task-categories-completion-20261019：
 final-independent-acceptance-after-g011.json、final-local-build-acceptance.json、
 accepted-qa-all-after-g011.log、accepted-render-gpt61/gpt56-after-g011.log、
 accepted-pdf-gpt61/gpt56-after-g011.log和各自-receipt.json。
 final-complete-source-coverage.json、final-byte-history-run-audit.json、
 accepted-term-audit-after-g011.json、reused-extract-proof-after-g011.json、
 reused-confirmed-term-after-g011.json和staged-full-data-review-after-g011.json。
 公开开发/验收摘要见docs/categories-candidate-completion.md和
 docs/evidence/categories-completion-source.json。旧失败日志不能算PASS。

用户明确要求：排版只检查实际render/pdf编译及最终日志，不截图、不生成检查PNG、
 不做逐页/抽页视觉检查或PDF全文/像素比较。只在模板、样式、Makefile或渲染路径
 改变时追加template。不得改生成物绕过失败；编译通过不代表语言或数学审校。
 开发期批量推进和局部检查；输入未变的可信通过证据直接绑定复用。qa-all包含
 Schema、完整溯源及决策，不在同轮重复子检查。

若DATA未合并，只收尾该同一集中PR：复核完整staged diff、scope、精确head/base
 全部远端原字节及完整patch、唯一GitHub-native Closes814、latest exact HEAD的
 pr-contract和policy-and-data真实成功run/job、fresh main等于最终接受base。
 全部条件满足后按既有用户授权admin bypass squash，无须再次确认。保留真实
 翻译trailers，不伪造Reviewed-By。main漂移正常整合并复核受影响证据。

DATA合并后核验MERGED、814 CLOSED、main/feature对应树、原字节和工作区。
 随后只做一次独立progress/plan Issue/分支/PR，实际运行progress、progress-check、
 plan、plan-check，不手改数字。按仓库要求完成当前集成lane的本地render/pdf及
 最新精确远端门禁后，按已授权squash合并；核实最终main和Issue关闭。
 如果两项PR均已合并且交付验收齐全，不再重复翻译或重开候选任务。

最终交付44节及章头完整覆盖、新旧实测统计、最新main、DATA和进度Issue/PR、
 精确CI run/job、实际命令及证据、完整可复制续接提示词。候选仍待独立critic、
 人工语言/数学审校、术语批准和正式发布。只有全部目标条件逐项有证据，包括
 DATA及独立同步均合并，才把goal标为complete；否则继续可独立推进的工作。
 约60秒用简洁中文报告实测进展，不逐包询问继续。
```
