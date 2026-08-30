# 工作流文档索引

`WORKFLOW.md` 是规范入口；本目录保存各环节细则。

- `data-model.md`：翻译数据、稳定 ID、来源 hash、上下文包和记忆；
- `translation-rules.md`：中文风格、数学语义和 LaTeX 节点规则；
- `review-and-qa.md`：状态授权、风险分级、自动检查和人工审校；
- `upstream-sync.md`：英文 harvest 更新和失效译文处理；
- `model-provenance.md`：Harness、具体模型、run 和模型下架；
- `progress.md`：全书与逐章翻译进度的固定分母、生成命令和更新门禁；
- `translation-progress.md`：从当前结构化数据确定性生成的 117 章进度表；
- `translation-priority.md`：P0–P4 政策、显式选择和任务调度规则；
- `translation-plan.md`：从优先级与当前数据确定性生成的 117 章行动队列；
- `candidate-selection.md`：候选保存、维护者选择和正式采用；
- `translation-replacement.md`：新模型替换旧译文和 revision；
- `git-conventions.md`：分支、提交、PR、合并和仓库卫生；
- `codex-workflow.md`：Codex 任务合同、并行和失败策略；
- `github-collaboration.md`：GitHub 角色、Issue、PR、权限和分支保护；
- `task-allocation.md`：使用 source commit、Tag 和 unit_id 指定翻译范围；
- `terminology.md`：术语提议、批准、废弃和迁移；
- `licensing.md`：许可证、模板资源和第三方文件清单；
- `ci.md`：GitHub Actions、来源 checkout 和自动门禁合同；
- `release.md`：正式发布门禁、版本和许可证。

Prompt 版本见 [`../prompts/README.md`](../prompts/README.md)；新任务必须使用
`translator-v2`，`translator-v1` 仅保留用于历史复现和测试兼容。

修改任一规范时必须检查其他文档、`AGENTS.md` 和 `config/` 是否需要同步更新。
