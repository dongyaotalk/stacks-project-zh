# CI 门禁合同

本文定义 GitHub Actions 的确定性检查和门禁合同。当前仓库的
`.github/workflows/ci.yml` 已启用，并在 PR 和 `main` push 上运行；远程 `main` 规则集
要求 `policy-and-data` 成功后才能合并。本文中的“应”表示需要保持的仓库合同，而不是
尚未实现的计划。

## 1. 必须检查的内容

每个 PR 至少应执行：

~~~bash
make workflow-check
make tool-test
make harvest-check
make upstream-index-check
make schema-check
make provenance-check
make decision-check
make qa-all
git diff --check
~~~

上游同步 PR 还必须用 `make upstream-diff OLD_UNITS=... NEW_UNITS=...
NEW_COMMIT=... OUTPUT_JSON=... OUTPUT_MD=...` 生成并审查 old/new 报告；报告出现
未解决映射时不得更新 `upstream.lock`。

贡献者在提交翻译数据 PR 前还应对目标 batch 执行：

~~~bash
make qa BATCH=<batch> MODEL=<model-lane>
make render MODEL=<model-lane>
make pdf MODEL=<model-lane>
~~~

当前 GitHub workflow 随后以 `make qa-all` 复查仓库内全部候选 batch，而不是只检查
changed path。任何修改在创建 Git 提交或 PR 前都必须完成适用的本地 LaTeX 编译：
翻译候选编译对应模型通道，其他修改至少执行 `make template`。当前
`policy-and-data` job 不安装 TeX，也不会自动完成该构建，因此 PR 清单中的本地编译
结果是必需声明，不是 CI 已代为执行的项目。缺少工具链或构建失败时不得提交、推送
或创建 PR，也不能通过编辑生成的 TeX 绕过。管理员 PR-only bypass 不豁免此门禁。

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

完整的 PR 范围合同要求核对：

- 声明的 `Translation-Unit` 与实际 unit 一致；
- candidate 和 unit 文件成对存在；
- unit_id 在任务范围内且不重复；
- source commit 和 hash 与 `upstream.lock` 一致；
- Harness、具体模型、model record、run ID 与不可变 run manifest 一致；
- protected placeholder、公式、标签、引用和环境没有变化；
- 未解释的英文残留、待决术语和非法状态被阻断；
- 没有修改 build、output、生成模型 TeX 或本地路径；
- 翻译 PR 没有夹带 glossary、upstream lock 或 reviewed 汇总变更。

当前自动化已经检查所有已跟踪候选的 Schema 相关字段、来源、run 溯源、
selection/review/revision 链、候选覆盖率、占位符、英文残留、术语和状态。它通过
`make qa-all` 全量遍历候选，而不是根据 diff 只遍历受影响 batch。

当前自动化尚未解析 Issue/PR 声明，也没有 changed-path/task-scope 机器人，因此
“声明的 Translation-Unit 与实际变更一致”“翻译 PR 没有夹带其他类别修改”等
diff 级范围仍由维护者人工核对。只运行一个手工指定的 `make qa` 不足以覆盖多文件
PR；合并到 `main` 后的 workflow 仍会重新运行全量检查。

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

当前远程 `main-protection` 规则集实际配置为：

- 所有普通变更通过 Pull Request；
- 至少一项批准和 CODEOWNER 审核，并解决 review threads；
- strict required status check `policy-and-data`；
- 禁止删除 `main` 和非快进更新；
- `@dongyaotalk` 仅可在 PR 上使用管理员 bypass，不能绕过 PR 直接 push。

R1 以上语言审校、R3 和指定 R2 数学审校由结构化审校记录和
`make decision-check` 负责；已发布 tag 不可移动是仓库治理政策。它们不是 GitHub
ruleset 中独立的 reviewer/status/tag 规则，不能把平台设置描述成已经自动完成这些
语义判断。

CODEOWNERS 必须与 `MAINTAINERS.md` 一致。CODEOWNERS 审批不能替代语言或数学
审校；对应 reviewer 仍须按风险等级留下结构化记录。

## 6. 失败处理

- 来源 checkout 失败：阻断，不降级到其他 commit；
- Schema、结构或占位符失败：拒绝候选；
- 待决术语：保持 `DECISION_REQUIRED`；
- critic 出现 blocker/critical：不能提升阶段；当前自动 critic 门禁尚未实现，
  `CRITIC_OK` 不得由贡献者手工宣称；
- TeX 失败：区分数据、渲染器、模板和环境责任；
- 许可证不确定：阻断公开 Release，但不应由自动检查猜测授权。

## 7. 当前状态

本地 `make workflow-check`、`make tool-test`、`make harvest-check`、
`make upstream-index-check`、`make schema-check`、`make provenance-check`、
`make decision-check` 和全量
`make qa-all` 已可执行，且同一组
检查由 GitHub Actions 的 `policy-and-data` job 运行。CI 当前对全部已跟踪候选 batch
执行 QA（目前为 108 个 batch），不是按 PR changed-path 做增量筛选。

当前没有自动的 changed-path/task-scope 机器人；PR 模板中的范围声明仍须由贡献者填写，
并由维护者和 CI 的数据检查核对。R1/R2/R3 所需的语言、数学和术语审校仍通过人工
审校记录及 `make decision-check` 作为数据门禁，不是 GitHub 自动替代的批准。管理员
的 PR-only bypass 只解决平台合并权限，不替代这些审校记录或许可证、发布门禁。
