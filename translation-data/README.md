# Translation data

本目录保存结构化翻译事实，而不是生成后的 TeX。

当前布局：

```text
translation-data/
├── units/
├── runs/<run-id>.json
├── candidates/<model-lane>/
├── selections/
├── reviewed/
└── retired/
```

所有记录必须遵守 `WORKFLOW.md`、`docs/data-model.md` 和版本化 Schema。每个候选
必须关联一个不可变 run manifest，并记录实际 Harness 和具体模型。模型候选不能
直接写入 `reviewed/`；只有维护者选择、满足人工审校要求并具有 revision 记录的
`PUBLISHED` 数据可以进入权威 Translation Memory。
