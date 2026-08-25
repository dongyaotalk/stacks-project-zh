# Translator prompts

本目录保存模型翻译器的版本化 Prompt。Prompt 版本是候选记录和 run manifest 的一部分，
不能把 Harness 名称（例如 `codex` 或 `claude-code`）当作 Prompt 或模型版本。

## 当前版本

- `translator-v2.md`：当前生产版本。所有新翻译任务和 `config/models.yml` 中
  `kind: model_candidate` 的 lane 都必须使用 `prompt_version: translator-v2`。它要求每一处数学术语都写成
  `中文（English）`，并按译文顺序填写 `term_occurrences`。
- `translator-v1.md`：历史兼容版本。仅用于复现旧候选和测试 fixture，不得用于新运行，
  也不得把 v1 候选伪装成 v2 候选。

## 选择和记录

开始任务前先确认模型 lane、Harness 和 Prompt 版本均已登记：

```bash
make list-models
sed -n '1,220p' config/models.yml
sed -n '1,220p' config/harnesses.yml
```

候选 JSONL 和不可变 run manifest 必须写入实际使用的 `prompt_version`。升级 Prompt
时应新增版本文件并单独提交，保留旧版本内容和历史记录；不要就地改写已使用的版本。
新版本上线前应更新模型配置、Schema/测试（如有合同变化）和本目录说明。
