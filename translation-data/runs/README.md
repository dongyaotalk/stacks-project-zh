# Translation runs

每个模型运行一个独立的 `<run-id>.json` 文件，内容符合
`schema/run-manifest.schema.json`。候选记录中的 `run_id` 必须能在这里找到对应
manifest。

运行清单是不可变溯源事实。模型下架、替换模型或重新运行都不能覆盖旧 manifest。
