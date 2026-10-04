# 译文替换和模型升级

出现更好的模型时，可以替换任意稳定翻译单元，而不必重翻整章。替换必须追加新
候选和新 revision，不能覆盖旧候选或重写已发布历史。
历史坐标/提取/显示的工具修复遵循 `docs/model-provenance.md` 的独立派生合同：
原文件保存原字节快照，活跃候选显式引用派生记录，原 run 保持不变。这不是模型
升级或正式译文替换，不继承旧人工审校，也不能夹带自由重译。
自由重译的候选修订另建真实模型 run，并保存冻结 unit 和完整原输出；原生成与
新增修订通过复合来源证据分别披露。该新合同按 `docs/model-provenance.md` §7
先实现工具再应用数据，不能通过放宽纯工具变换来冒充真实模型运行。

## 替换流程

```text
新 Harness/模型运行
  → 固定同一 source_commit 和 unit_id
  → 生成候选和中英 diff
  → 检查术语、引用、上下文和数学结构
  → 维护者选择
  → 必要的语言/数学审校
  → 新 revision supersedes 旧 revision
```

如果英文来源没有变化，这是 `translation replacement`；如果英文来源也变化，
则必须使用独立的 upstream synchronization PR。二者不能混为一次普通翻译提交。

## 替换粒度

替换单位是 `unit_id`，不是整章。例如只改进
`tag:001M:p002` 时，只替换该单元，但必须检查相邻单元的术语、指代和证明连贯性。

新候选必须使用当前的：

- `source_commit`；
- source text、structure、math hash；
- prompt 和 glossary revision；
- 目标 unit 的上下文包。

## Revision 记录

新版本应记录：

```text
revision_id
unit_id
source_text_hash
translation
translation_hash
origin_run_id
selection_id
supersedes_revision_id
selected_by
review_ids
stage / risk_level / source_status / qa_status / term_status / publication_status
reason
review_ids
```

旧 revision 可以标记为 `superseded`，但不能删除。这样可以回答：谁用什么模型
翻译了什么、为什么替换、替换后哪些审校需要重新完成。

同一 unit 的 revision 构成一条有向无环链。第一版的 `supersedes_revision_id` 为
`null`，后续版本引用真实的前驱；第一版不会因为新增第二版而被要求补造前驱。
每个 unit 最多有一个无前驱的首版本，每版最多有一个后继，被替换的前驱必须标记
为 `superseded`。`superseded` 记录必须存在对应后继；单独退休的首版本可以保留。
自引用、循环、跨 unit 替换、多个首版本和分叉均被 `make decision-check` 拒绝。

## 不自动继承审校

新模型即使整体质量更高，也不能自动继承旧译文的语言或数学审校。只有变化确实
不涉及某类审校，并且维护者有明确记录时，才可以按项目政策保留相应决定。
