# 构建与发布规范

## 1. 发布通道

项目区分：

- `template`：只验证 Springer 模板，不含正式译文；
- `<model-lane>`：具体模型候选预览，必须显示 Harness、具体模型和“未经完整人工审校”；
- `reviewed`：满足人工审校要求的正式通道；
- `release`：从 `reviewed` 的冻结 Git commit 构建的发布产物。

候选模型输出不得使用容易让读者误认为正式译本的封面、状态或文件名。

## 2. 发布版本

建议 Git tag：

```text
zh-YYYY.MM.rN-stacks-<source-short-sha>
```

例如：

```text
zh-2026.09.r1-stacks-a04446e
```

正式版本必须同时记录：

- 中文仓库完整 commit；
- 英文 `upstream.lock` 完整 commit；
- 翻译数据 Schema；
- 词表 revision；
- 渲染器和模板版本；
- 构建环境摘要；
- 发布日期和状态。

## 3. 发布门禁

正式发布前必须确认：

- `make workflow-check`、`make harvest-check`、`make upstream-index-check`、
  `make schema-check`、`make provenance-check`、`make decision-check` 和全量
  `make qa-all` 通过；
- 所有包含单元 `source_status=CURRENT`；
- R1 以上单元完成语言审校；
- R3 及指定 R2 单元完成数学审校；
- 没有未关闭 blocker、critical 或待决术语；
- 数据 Schema、结构、术语和语义检查通过；
- XeLaTeX、BibTeX、makeindex 全流程成功；
- 没有未定义引用、引用键或重复标签；
- 目录、蓝色链接、索引、字体、公式和分页完成视觉检查；
- PDF 元数据和来源页准确；
- 许可证和非官方翻译声明完整；
- release manifest 与产物 hash 已生成。

## 4. Release manifest

每个正式产物应生成机器可读 manifest，至少包含：

```json
{
  "release": "zh-2026.09.r1-stacks-a04446e",
  "translation_commit": "full sha",
  "source_commit": "full sha",
  "channel": "reviewed",
  "origin_runs": ["run-id"],
  "selection_ids": ["selection-id"],
  "translation_revision_ids": ["revision-id"],
  "schema_version": 1,
  "glossary_revision": "git sha",
  "built_at": "RFC3339 timestamp",
  "pdf_sha256": "sha256:..."
}
```

manifest 与 PDF 一起作为 Release 产物，不依赖本机绝对路径。

## 5. 许可证和声明

英文 Stacks Project 采用 GNU Free Documentation License 1.2 或更高版本。
中文翻译属于修改版本，发布时必须：

- 保留来源、版权和许可证说明；
- 提供许可证全文；
- 明确标识翻译和修改；
- 不暗示 Stacks Project 作者批准或保证中文译文；
- 提供可修改的透明格式或其获取方式；
- 满足 GFDL 对修改版本的其他要求。

根目录 `LICENSE` 提供 GFDL 1.2 全文；独立软件工具的 MIT 许可见
`LICENSES/MIT.txt`。两者均不覆盖许可未确认的第三方模板、字体、图片或商标。

当前 `springer-template/svmono.cls` 文件头没有明确再分发许可。正式公开仓库或发布
包含该文件的源包前，必须确认授权，或改为由使用者自行取得兼容模板。该事项是
发布 blocker，不能通过技术 QA 自动关闭。第三方文件核查和当前待决清单见
`docs/licensing.md` 与 `THIRD_PARTY_NOTICES.md`。

## 6. 产物管理

- PDF、日志、IR、SQLite 和生成 TeX 不提交主仓库；
- CI 预览设置有限保留期；
- 正式 PDF 和 manifest 上传到 Release；
- 发布后不得覆盖同名文件；修订使用新的 `rN`；
- 需要撤回时保留历史记录并发布说明，不重写 tag。

## 7. 可复现性

同一发布应能通过 lock、翻译 commit、配置和工具版本重新生成语义等价的 PDF。
时间戳等非确定字段应由 release manifest 明确记录或在可复现构建中固定。构建
不得从网络隐式下载未锁定字体、模板或数据。
