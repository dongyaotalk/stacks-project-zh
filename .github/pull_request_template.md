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
- Chapter / Section / Tag(s)：
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

章节候选按 [当前章节合同](../docs/chapter-current-validation.md) 集中验收。

- [ ] workflow/harvest 与 git diff --check 通过
- [ ] 已说明完整 diff 分类、可信 base/head、实际章节/lane 和所有 run 范围
- [ ] 纯章节已执行一次 qa-chapter 或联合 pdf-chapter；没有遗漏共享参与者
- [ ] 公共实现/政策/Schema/来源或未知变化已执行 qa-current-all 和适用工具回归
- [ ] 历史语义变化已运行对应历史回归；显式审计需要时另附 audit-history 证据
- [ ] 精确 scope_manifest 路径/hash、来源、文件和 IDs 完整；旧内联 batch 限制保持
- [ ] 章节/适用集成编译零退出，最终日志无缺字、未定义引用/引用键或重复标签
- [ ] 默认未截图；没有编辑生成 TeX/PDF/日志绕过失败
- [ ] 结果按实际范围标记；章节用 chapter-current/history_audit=not_run，纯生成报告用 generated-reports/data_qa=not_run/history_audit=not_run/tool_tests=not_run；没有冒称人工审校通过
- [ ] 纯生成报告完成两个实际 check、workflow/harvest/diff，完整输入与可信 base 绑定；公共/混合变更扩大验证
- [ ] 如复用编译证据，已按 docs/ci.md 核验相关渲染输入/行为未变以及原命令、hash、零退出和最终日志
- [ ] progress/plan 变更已执行对应 check；远端必需状态据实记录

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
