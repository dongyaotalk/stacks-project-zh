# Translation data

本目录保存结构化翻译事实，而不是生成后的 TeX。

当前布局：

```text
translation-data/
├── chapter-templates/           # 锁定上游的章节/Section 任务骨架，不含译文
├── units/
├── runs/<run-id>.json
├── candidates/<model-lane>/
├── selections/
├── reviewed/
└── retired/
```

`chapter-templates/<chapter>.json` 由 `make init-chapters` 确定性生成，列出该章按上游
顺序排列的 Section、永久 Tag、建议 batch 路径和当前准备状态。它用于发现、认领和
拆分任意后续章节，不是候选译文，也不能用空模板替代稳定 unit。`READY` 表示已有
对应 unit 文件；`UNPREPARED` 必须先完成结构化提取；`BLOCKED_NO_TAG` 必须先解决
稳定坐标。运行 `make chapter-template-check` 可验证模板与锁定上游及现有 unit 一致。

所有记录必须遵守 `WORKFLOW.md`、`docs/data-model.md` 和版本化 Schema。每个候选
必须关联一个不可变 run manifest，并记录实际 Harness 和具体模型。模型候选不能
直接写入 `reviewed/`；只有维护者选择、满足人工审校要求并具有 revision 记录的
`PUBLISHED` 数据可以进入权威 Translation Memory。
