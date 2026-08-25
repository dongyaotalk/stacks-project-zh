# Upstream index snapshots

每个锁定的英文 commit 至少对应一个 `manifests/<full-sha>.json`。manifest 保存
`tags/tags` 和章节清单的 hash、永久 Tag 数量、解析器和规范化版本；原始 Tag 索引
仍来自同一 commit 的英文 harvest，不在这里复制整份 TeX。

上游同步时应为 old/new 两个 commit 导出 `translation-data/units/` 和 Tag 索引，
使用 `scripts/upstream_diff.py` 生成 `sync-reports/`。Tag 变化或 unit 匹配有歧义时
报告必须阻断，不能由相似度猜测。
