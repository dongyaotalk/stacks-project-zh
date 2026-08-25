# CI 门禁合同

本文定义 GitHub Actions 应实现的确定性检查。它描述的是门禁合同；在 workflow 文件
实际提交和 GitHub 分支保护启用前，不能声称 CI 已经生效。

## 1. 必须检查的内容

每个 PR 至少应执行：

~~~bash
make workflow-check
make tool-test
make harvest-check
make provenance-check
make decision-check
git diff --check
~~~

上游同步 PR 还必须用 `make upstream-diff OLD_UNITS=... NEW_UNITS=...
NEW_COMMIT=... OUTPUT_JSON=... OUTPUT_MD=...` 生成并审查 old/new 报告；报告出现
未解决映射时不得更新 `upstream.lock`。

翻译数据 PR 还必须对变更涉及的每个 batch 执行：

~~~bash
make qa BATCH=<batch> MODEL=<model-lane>
~~~

修改模板、样式、Makefile 或渲染逻辑时，还必须执行目标模板或 PDF 构建。构建失败
不能通过编辑生成的 TeX 绕过。

## 2. 来源 checkout

Runner 必须：

1. checkout 中文 PR；
2. 从 `upstream.lock` 读取规范 URL 和完整 commit；
3. 单独 checkout 英文 harvest 到 `HARVEST_DIR`；
4. 验证 remote、HEAD、commit date 和 tracked working tree；
5. 禁止自动更新或切换来源版本。

CI 不应把英文仓库作为中文仓库的 Git remote，也不应把英文源码复制进中文仓库
提交。

## 3. PR 范围和覆盖率

CI 应根据 PR diff 和候选记录检查：

- 声明的 `Translation-Unit` 与实际 unit 一致；
- candidate 和 unit 文件成对存在；
- unit_id 在任务范围内且不重复；
- source commit 和 hash 与 `upstream.lock` 一致；
- Harness、具体模型、model record、run ID 与不可变 run manifest 一致；
- protected placeholder、公式、标签、引用和环境没有变化；
- 未解释的英文残留、待决术语和非法状态被阻断；
- 没有修改 build、output、生成模型 TeX 或本地路径；
- 翻译 PR 没有夹带 glossary、upstream lock 或 reviewed 汇总变更。

只运行一个手工指定的 `make qa` 不足以覆盖多文件 PR；CI 需要遍历所有受影响
batch。合并到 `main` 后还应运行全量数据检查。

## 4. Artifact 和权限

候选渲染、日志、双语 diff、QA 摘要和 PDF 只能作为 CI artifact 保存，不能写回
仓库事实数据。正式 PDF 和 manifest 作为 GitHub Release 产物上传。

Actions 默认使用最小权限：

~~~yaml
permissions:
  contents: read
~~~

第三方 Actions 必须固定到完整 commit SHA，并在行尾注释对应主版本；不能只使用
可移动的分支名。升级 Action 使用独立构建/CI PR，并重新运行门禁。

不在 workflow、Issue、PR 评论、日志或候选 JSONL 中输出模型凭据、API key、SSH
私钥、访问令牌或个人隐私。

## 5. 分支保护

GitHub 仓库配置完成后，`main` 至少需要：

- required status checks；
- 禁止直接 push；
- 至少一名维护者批准；
- R1 以上翻译的语言审校；
- R3 和指定 R2 的数学审校；
- 禁止 force-push；
- 已发布 tag 不可移动。

CODEOWNERS 必须与 `MAINTAINERS.md` 一致。CODEOWNERS 审批不能替代语言或数学
审校；对应 reviewer 仍须按风险等级留下结构化记录。

## 6. 失败处理

- 来源 checkout 失败：阻断，不降级到其他 commit；
- Schema、结构或占位符失败：拒绝候选；
- 待决术语：保持 `DECISION_REQUIRED`；
- critic 出现 blocker/critical：不能提升阶段；
- TeX 失败：区分数据、渲染器、模板和环境责任；
- 许可证不确定：阻断公开 Release，但不应由自动检查猜测授权。

## 7. 当前状态

本地 `make workflow-check`、`make tool-test`、`make harvest-check`、单批次
`make provenance-check`、单批次 `make qa` 和全量 `make qa-all` 已可执行。仓库包含基础 GitHub Actions workflow，
但只有推送到配置好的 GitHub 仓库后才会实际运行。changed-path 范围机器人、
CODEOWNERS 已登记当前维护者；分支保护仍需在远程仓库创建并推送后配置。
