# 英文上游同步

## 1. 基本原则

普通翻译任务基于冻结的 `upstream.lock`。禁止把 `git pull`、checkout 新提交和
修改锁文件作为普通翻译脚本的隐含步骤。上游同步是独立、可审查、可回退的工作。

## 2. 获取更新

同步任务可以对英文 harvest 执行只读 `git fetch`，但不得立即改变中文项目所
接受的版本。先记录：

```text
old_commit
candidate_new_commit
英文提交范围
解析器版本
```

工作分支命名为：

```text
sync/<old-short-sha>-<new-short-sha>
```

## 3. 节点匹配

新旧版本按以下顺序匹配：

1. Stacks Project 永久 Tag；
2. 已保存的稳定 `unit_id`；
3. 父级 Tag、节点类型和 AST 路径；
4. 文本、结构、数学及邻居指纹；
5. 人工映射。

匹配有歧义时不得选择相似度最高者后静默继续，必须生成人工映射问题。

同步前先用锁定 harvest 的 `tags/tags` 检查本地 unit 是否仍把有永久 Tag 的自身
label 写成 `label:` ID。若发现这种历史坐标，先运行
`python3 scripts/migrate_permanent_tags.py --root . --tags <harvest>/tags/tags
--map migration/unit-id-map.json`，并把映射作为独立迁移事实审查；不要在同步 diff
中把坐标迁移误报成英文内容变化。

## 4. 变化分类

| 英文变化 | 处理 |
|---|---|
| 仅移动、空白或无语义格式变化 | 保持有效，更新位置元数据 |
| 自然语言变化，数学不变 | `STALE_TEXT` |
| 任一数学 AST 变化 | `STALE_MATH` |
| 单元增加部分句子或子节点 | `PARTIAL_STALE` |
| 上游删除 | `RETIRED` |
| 新增单元 | `UNTRANSLATED` |
| 匹配不确定 | blocker，人工处理 |

`STALE_MATH` 必须重新进行数学审校。不能仅因文字改动很小就沿用旧批准。

## 5. 最小修订

更新译文时向修订模型提供：

```text
OLD EN
OLD ZH
NEW EN
STRUCTURED DIFF
当前已批准术语
```

要求只修改受影响部分。修订后重新计算候选 hash，并使依赖旧 hash 的审校失效。
若结构变化导致无法安全局部修订，则退回完整翻译，而不是拼接不确定片段。

## 6. 同步 PR 内容

同步 PR 必须包含：

- 旧、新英文完整 commit；
- 英文提交摘要；
- 变化单元数量及分类统计；
- 人工映射列表；
- stale、retired 和新增单元清单；
- 已更新译文及重新审校结果；
- `upstream.lock` 修改；
- 完整 QA 和 PDF 构建结果。

每次同步还必须追加：

- `UPSTREAM_HISTORY.md` 中的一条人类可读摘要；
- `sync-reports/<old-short>-<new-short>.json` 机器事实；
- 同名 Markdown 详细报告；
- 新 commit 的 `upstream-index/manifests/<full-sha>.json` 索引清单。

Markdown 应从机器事实生成或逐项核对。报告必须列出英文提交范围、Tag 的新增、
退休、移动或重映射、unit 变化分类、译文处理、失效审校和未解决映射。旧报告只能
追加，不能静默重写。

实际生成报告使用 `scripts/upstream_diff.py`（或 `make upstream-diff`）。它接收旧、
新版本导出的 `translation-data/units/`，可同时接收两版 `tags/tags` 和
`chapters.tex`，输出 `sync-reports/<old-short>-<new-short>.json` 与同名 Markdown。
`--unit-id-map migration/unit-id-map.json` 用于显式坐标迁移；报告器不会自动把相似
文本当成同一单元，也不会修改 `upstream.lock`。

`upstream.lock` 应在同步 PR 的最后阶段更新，不能先更新 lock 再把大量旧译文留在
看似 `CURRENT` 的状态。

## 7. 接受和回退

同步合并后，所有构建必须使用新 lock。若发现严重问题，使用正常 revert 提交恢复
旧 lock 和对应状态；不得重写已发布历史。回退也必须保证翻译数据与锁定英文提交
一致。

## 8. 定期检查

自动任务可以定期 fetch 并生成“有新提交”报告，但不得自动：

- 更新 `upstream.lock`；
- 批量重翻；
- 提升审校状态；
- 发布 PDF。

所有这些动作都需要独立分支和审查。

## 9. 基线和历史校验

新仓库第一次记录使用 `report_kind: baseline`，`old_commit` 为 `null`；它不伪装成
一次同步。以后每次报告必须满足：

```text
report.old_commit == 同步前 upstream.lock.commit
report.new_commit == 同步后 upstream.lock.commit
```

CI 必须检查 lock、新索引 manifest、机器报告和 `UPSTREAM_HISTORY.md` 相互一致。
存在 unresolved mapping 或 `qa_result: FAIL` 时不得合并。

上述合同由 `make upstream-index-check` 执行：它按
`schema/upstream-index-manifest.schema.json` 验证锁定 commit 的 manifest，并将
repository/commit/date、`tags/tags` hash、`chapters.tex` hash、永久 Tag 数量、同步
报告和人类历史链接交叉核对。
