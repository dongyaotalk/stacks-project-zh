# 当前译文来源对应与统一修订队列

全库来源库存与现有事实单元采用不同分段。来源对应工具只准备可审查的定位与修订任务，不直接变更现有unit、candidate、run或来源恢复证据。

## 输入与边界

`make source-alignment` 读取 `source-ir/extraction` 和当前全部unit/candidate，输出 `build/source-alignment/`；`make source-alignment-check` 重新计算并比较完整结果。缓存按锁定英文commit、宏政策、抽取器版本和产物hash验证；实际使用章从锁定Git重新扫描，逐项验证容器保护内容、位置、owner与parent。历史existing_unit_id和库存生成时的当前数据hash不是匹配依据；当前事实由本次快照独立绑定，因此修订队列更新不要求重复扫描没有变化的其余英文。

## 唯一定位

完整batch按锁定Tags重放永久坐标和statement/proof链。以真实owner选择英文容器，证明按所属陈述与第几份proof约束；不能因为同一句话在全章只出现一次就越过owner范围。列表自身拥有Tag时，由其在完整容器中的真实label提供候选范围。只接受唯一、连续且源顺序一致的对应；重复短句或不确定范围标为AMBIGUOUS/UNSUPPORTED。

扫描不执行宏，保留数学和literal原字节。自然语言词序、环境、控制符和所有非空白节点必须一致；只有锁定Tag索引确认相同引用目标时，才将本章未限定与明确限定namespace作为定位别名。数学内部引用、空白及公式不宽松归并。注释和正文排版空白用于定位时单独披露，不能改变原hash、继承审校或免除现有来源检查。

每个结果保存旧ID/真实Tag提案、当前source TeX hash、英文容器与byte span/hash、BYTE_EXACT/PRESENTATION_EQUIVALENT/SOURCE_DIFFERENCE/AMBIGUOUS/UNSUPPORTED分类。差异结果仍提供候选容器原范围、结构窗口范围与有界原文摘录，便于集中检查。网址、引用键、图表、literal等保护参数也按原字节比较。非逐字匹配的结果只提供诊断，采用仍须独立声明的来源证据及实际模型修订。

## 清单与验收

alignment.json覆盖全部当前单元；repair-queue.jsonl以每个事实batch为边界，记录完整unit/candidate路径与hash、来源范围、坐标提案、术语/TeX/脚注/标题/证明待办；report.md提供汇总。原terms/source/proof三个独立审计的完整结果与错误均保留，21组proof差异附有界节点/正文diff，不以别名或排版分类覆盖旧审计结论。队列成功仅表示准备完成，907个坏术语候选等仍待真实修订。

只写专用ignored build子目录，拒绝越界、symlink、陌生目录及无关文件；先完整生成再整体替换，写入/swap失败保留上一包。check只读，当前任何事实、来源包或审计政策变化使队列失效；术语目录、词表、macro-policy与source lock也绑定本次输入hash。来源结构审计读锁定Git的tags，而非工作树文件。生成期间事实/政策/来源包变化则失败，避免混合不同快照。工具不会创建Issue、模型run、审批或新的事实ID。

CLI：`python3 stacks_zh.py source-alignment --root . --harvest ../stacks-project [--inventory source-ir/extraction] [--output build/source-alignment] [--check]`。Make支持`EXTRACTION_DIR`、`SOURCE_ALIGNMENT_DIR`覆盖；成功只表示清单准备/复核完成，打印未采用与修订未完成状态。

真实对应覆盖239batch/1480unit：1个BYTE_EXACT、1209个PRESENTATION_EQUIVALENT、267个SOURCE_DIFFERENCE、3个AMBIGUOUS。没有真实proof selector的单元不能借同Tag证明正文匹配。79个坐标待迁移，907个候选有3027条术语诊断，来源审计99条、proof审计21组差异。21组中14组可作排版/已核实引用别名定位，7组仍有严格来源差异；全部21组原mismatch结论与完整diff仍保存。267个定位差异包含数学空白等严格字节差异，数量不等于已确认语义错误；必须看来源证据后修订。

独立synthetic回归覆盖owner限制、别名与未知引用、数学/脚注/顺序差异、重复匹配、多proof与split链、comments/UTF-8、缓存篡改、事实变化及安全原子写入。真实验收必须覆盖239batch/1480unit并保留原三审计非零残项；完整工具/QA/本地模型PDF和模板门禁按仓库流程执行。

Issue [#624](https://github.com/dongyaotalk/stacks-project-zh/issues/624) 为词汇目录新增
锁定完整 Git 容器证据，合同见 `source-term-inventory.md`。统一队列向独立术语
审计传入同一个实际 harvest，核验真实 selector、commit、原片段 hash 和仅在
暴露正文中的词形；不能以默认 checkout、旧分段或候选文字提供证据。目录仍
绑定 input hash，新格式报告完整保留在 term-audit.json 中。词汇来源证据通过
不减少当前候选、来源或证明残项，不批准译法或豁免未来严格门禁。
