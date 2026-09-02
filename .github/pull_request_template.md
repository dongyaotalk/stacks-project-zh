## 类型

- [ ] 翻译候选
- [ ] 人工语言审校
- [ ] 人工数学审校
- [ ] 术语
- [ ] 上游同步
- [ ] 工具/Schema
- [ ] LaTeX 模板
- [ ] 规范/文档
- [ ] 构建/发布

## 范围和来源

- 关闭并关联的任务 Issue / task ID：`Closes #<issue>` / `<task_id>`
- 英文完整 commit：
- Chapter / Section / Tag：
- Translation unit：
- Unit/batch 文件：
- 允许写入文件：
- 模型/通道（如适用）：
- Harness / 版本（如适用）：
- [ ] 新运行的 Harness 版本已通过 `make harness-check HARNESS_ID=<harness-id>` 动态获取（历史 manifest 不回写）
- 具体 provider/model ID（如适用）：
- Model record / snapshot（如适用）：
- Translation run ID（如适用）：
- Prompt version（如适用）：
- Glossary revision（如适用）：

## 修改说明

说明为什么需要修改、包含什么，以及明确不包含什么。

## 翻译和结构检查

- [ ] 没有修改英文 harvest
- [ ] `upstream.lock` 与任务来源一致
- [ ] 所有 unit 和文件都在 Issue/任务声明范围内
- [ ] Issue 早于 PR 创建，状态为 `OPEN` 且带有 `claimed` 标签
- [ ] Issue 中的 owner、branch、`allowed_write_files` 与本 PR 一致
- [ ] 本 PR 是对应 unit/batch 的唯一写入者
- [ ] 公式、环境、标签、引用和引用键保持不变
- [ ] 占位符数量、类型和顺序一致
- [ ] 没有直接把模型生成的整份 TeX 当作翻译事实数据
- [ ] 新术语已报告；本 PR 没有偷偷批准术语
- [ ] 每个模型候选都关联了不可变 run manifest
- [ ] 每次数学术语出现均为 `中文（English）`，重复项也未省略英文
- [ ] 没有未说明的英文残留或模型附加解释

## QA

- [ ] `make workflow-check`
- [ ] `make harvest-check`
- [ ] `make upstream-index-check`
- [ ] `make tool-test`
- [ ] `make schema-check`
- [ ] `make provenance-check`（模型候选/run 变更必需）
- [ ] `make decision-check`（selection/review/revision 变更必需）
- [ ] `make qa BATCH=<batch> MODEL=<model-lane>`（翻译候选必需）
- [ ] 若使用开发阶段 batch：`make qa-batch BATCHES="<batch-a> <batch-b>" MODEL=<model-lane>`；各 batch 文件仍独立
- [ ] `make progress-check`（独立进度报告 PR 必需）
- [ ] `git diff --check`
- [ ] 结构检查（如适用）
- [ ] 术语检查（如适用）
- [ ] 已说明独立 critic 状态（当前无自动 critic 命令）
- [ ] 提交前已执行 `make render MODEL=<model-lane>` 和 `make pdf MODEL=<model-lane>`（翻译候选必需）
- [ ] 提交前已针对当前候选通道执行 `make render MODEL=<model-lane>` 和 `make pdf MODEL=<model-lane>`（翻译候选及其他文档/工具修改必需）
- [ ] 若修改模板、样式、Makefile 或渲染路径，已额外执行 `make template`
- [ ] 适用的本地 LaTeX 编译以零状态退出；无错误且未修改生成文件绕过失败
- [ ] 已检查未定义引用、重复标签、目录、链接、字体和索引

## 审校

- 风险等级：R0 / R1 / R2 / R3
- 语言审校者及结论：
- 数学审校者及结论：
- 未解决 blocker/critical/major：

## 审查材料

- 双语 diff：
- QA 报告：
- PDF/CI 预览：
- 术语或上游变化报告：

## Git

- [ ] 分支名符合 `docs/git-conventions.md`
- [ ] `pr-contract` 已验证 closing Issue 和 changed-path/unit scope
- [ ] 提交原子且标题符合约定
- [ ] 必需 trailers 完整
- [ ] 未提交生成文件、凭据、本地路径或无关修改
- [ ] 没有伪造人工审校、许可证授权或 GitHub 权限

## 许可证影响

- [ ] 本 PR 没有新增第三方模板、字体、图片或其他二进制资源
- [ ] 如有新增，已更新许可证来源和第三方文件清单
- [ ] 本 PR 不把候选译文描述为正式发布版
- [ ] 若替换旧译文，已提供 supersedes、selection 和必要的重新审校记录
