# 上游基线报告：a04446e5

## 来源

- Repository：`https://github.com/stacks/stacks-project.git`
- Commit：`a04446e57ec1fbc252a871afcec7752fb2807b14`
- Commit date：`2026-07-28`
- 报告类型：基线，不是同步更新

## 索引快照

- `tags/tags`：21,446 个永久 Tag
- `tags/tags` SHA-256：`098f77cce75f8359f1eacb22b7aa0088099b09e5b3ffcad2de513cbd1a8a9f1c`
- `chapters.tex` SHA-256：`8ffe9d9c3273b29d07e3998f4cd8f363e84b95c9e00b85cc89e56eff4259dc66`

## 中文数据

- unit batch：108
- 翻译单元：473
- candidate batch：108
- 模型候选：473
- Harness：Codex
- 具体模型：OpenAI GPT-5.6-sol
- 身份依据：项目所有者确认
- 模型 snapshot：上游运行时未暴露

## 当前能力边界

本基线保存的是永久 Tag、章节清单、来源 hash 和候选来源。当前
`source_math_hash` 是规范化 LaTeX 数学片段 hash，并非数学语义 AST 等价证明。
`scripts/upstream_diff.py` 已可以对导出的 old/new unit 和 Tag 索引生成分类报告；
上游单元导入、拆分/合并 lineage 和数学语义 AST 仍需由同步任务提供。同步遇到歧义
时必须阻断并人工映射。历史上 5 个自身拥有永久 Tag 的 `label:` 单元已按
[`migration/unit-id-map.json`](../migration/unit-id-map.json) 规范化为 `tag:` ID。

机器可读版本：[baseline-a04446e5.json](baseline-a04446e5.json)。
