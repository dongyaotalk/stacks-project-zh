# 许可证和第三方文件

本文是公开 GitHub、源代码包和正式 PDF 的许可证检查清单。它不替代法律意见；
存在不确定性时必须暂停公开发布。

## 1. 英文来源和中文修改版本

Stacks Project 英文内容依照 GNU Free Documentation License 1.2 或更高版本发布。
中文翻译是修改版本，正式发布必须：

- 保留来源、版权和许可证说明；
- 随发行物提供 GFDL 全文；
- 明确标识翻译和修改；
- 不暗示英文作者、Stacks Project 或 Springer 批准、保证或出版了中文译本；
- 提供可修改的透明格式或其获取方式；
- 满足 GFDL 对修改版本的其他要求。

根目录 `LICENSE` 保存 GFDL 1.2 全文。本项目的中文译文、翻译数据和以英文原作为
基础的文档按 GFDL 1.2 或更高版本分发，无不变章节、无封面文字、无封底文字。
`upstream.lock` 只锁定英文来源版本，不自动授予中文仓库内其他文件的再分发权。

项目新增翻译与文档声明：

```text
Copyright (c) 2026 OpenSSL and contributors.
Permission is granted to copy, distribute and/or modify this document under
the terms of the GNU Free Documentation License, Version 1.2 or any later
version published by the Free Software Foundation; with no Invariant
Sections, no Front-Cover Texts, and no Back-Cover Texts.
```

由本项目独立编写且不包含英文原作衍生内容的软件工具采用更宽松的 MIT
License；MIT 全文位于 `LICENSES/MIT.txt`。当前范围包括：

- `stacks_zh.py` 和 `stacks_zh/`；
- `tests/`；
- `.github/` 自动化配置；
- 本项目独立编写的构建与校验逻辑。

文件同时包含第三方或 GFDL 衍生内容时，以对应第三方许可或 GFDL 为准；MIT 不会
覆盖或重新许可这些内容。

## 2. 当前需要核实的文件

| 路径或类别 | 处理要求 |
| --- | --- |
| `translation-data/` 中基于英文 harvest 的事实数据 | 按 Stacks Project 许可和翻译修改版本要求处理 |
| `springer-template/svmono.cls` | 当前文件头没有明确再分发许可；在确认前是发布 blocker |
| `springer-template/styles/` | 逐个确认自有改写、上游模板和第三方样式的许可证 |
| `springer-template/fonts/` | 记录字体名称、来源、授权范围和是否允许随源包分发 |
| `springer-template/images/Springer-logo.png` | 核实版权和商标使用；没有必要时不随公开成品分发 |
| `springer-template/images/figure.eps` | 核实来源、许可和是否属于模板示例资源 |
| `.bst`、`.ist`、`.bib` 和其他模板资源 | 保留原始声明，并记录再分发条件 |

不能因为文件曾经存在于本地模板或旧项目中，就推断它可以公开上传。

## 3. 必须新增的发布材料

公开仓库至少应有：

~~~text
LICENSE
THIRD_PARTY_NOTICES.md
~~~

当前 `THIRD_PARTY_NOTICES.md` 是待核实的初步清单；最终版本至少记录：

- 文件或目录；
- 原始作者和来源 URL；
- 许可证名称和版本；
- 是否修改；
- 本仓库的分发方式；
- 必要的版权、商标或免责声明。

根目录许可证和 MIT 工具许可证已经建立，但它们不解决第三方模板、字体、图片和
商标的授权问题，也不能覆盖 `THIRD_PARTY_NOTICES.md` 中的待决项。

## 4. 解决不确定文件的可选方案

对于无法确认再分发权的模板或资源，可以：

1. 从仓库移除，并在构建文档中要求使用者自行取得；
2. 改用许可证清楚的替代模板或字体；
3. 只保留必要的自有适配文件；
4. 在 private 仓库中暂存，公开仓库只发布不含受限资源的源代码；
5. 取得书面授权后，连同授权记录和 NOTICE 一起分发。

不能用“仅供学习”“非商业用途”或 README 声明规避第三方许可证限制。

## 5. CI 和 Release 门禁

CI 可以检查文件清单、来源页、PDF 元数据和 manifest 是否齐全，但不能自动判断
一个未确认文件是否有再分发许可。正式 Release 前由发布维护者确认：

- `docs/release.md` 的许可证门禁已满足；
- `LICENSE` 和 `THIRD_PARTY_NOTICES.md` 已提交；
- PDF、源代码包和 Release artifact 使用一致的许可声明；
- 没有 API key、私有字体、访问令牌或本地绝对路径；
- 不会把 Springer logo 或出版关系表述成官方授权。

当前模板许可不明确时，状态必须保持为发布 blocker。
