# 译文替换和模型升级

出现更好的模型时，可以替换任意稳定翻译单元，而不必重翻整章。替换必须追加新
候选和新 revision，不能覆盖旧候选或重写已发布历史。

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

## 不自动继承审校

新模型即使整体质量更高，也不能自动继承旧译文的语言或数学审校。只有变化确实
不涉及某类审校，并且维护者有明确记录时，才可以按项目政策保留相应决定。
