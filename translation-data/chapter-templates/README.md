# 全章节翻译任务模板

本目录为锁定英文来源中的每一章保存一个确定性 JSON 任务骨架。每个文件按原书顺序
列出 Section 标题、永久 Tag、建议 batch/unit 文件和现有准备状态，便于贡献者从任意
章节选择不重叠的翻译范围。

- `READY`：已有稳定 unit，按 `unit_files` 创建翻译任务；
- `UNPREPARED`：Tag 与建议路径已确定，先进行独立的 scope preparation；
- `BLOCKED_NO_TAG`：缺少稳定坐标，不能手工创建 unit ID；
- `SOURCE_UNAVAILABLE`：上游没有独立章源文件，不能直接认领。

这些 JSON 不是译文容器，不要手工编辑。使用 `make init-chapters` 从锁定 harvest 和
现有 unit 重新生成，使用 `make chapter-template-check` 验证它们没有过期。译文仍写入
`translation-data/candidates/<model-lane>/`，并遵守 `docs/task-allocation.md`。
