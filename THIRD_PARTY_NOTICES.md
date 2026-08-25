# Third-Party Notices（初步清单）

本文件是公开发布前的核查清单，不是许可证授权，也不表示下列文件已经可以公开
再分发。最终结论必须在每一项中填写来源、许可证和处理方式，并由发布维护者确认。

| 文件或目录 | 已知来源/用途 | 当前状态 | 公开发布前处理 |
| --- | --- | --- | --- |
| `stacks-project` 英文来源及结构化快照 | Stacks Project；GFDL 1.2 或更高版本 | 来源许可已知，修改版本义务待完整落实 | 随发行物附 GFDL 全文、来源和修改声明 |
| `springer-template/svmono.cls` | Springer SVMono 5.10 模板类 | 文件头未见明确再分发许可 | 确认书面许可，或从公开仓库移除并要求用户自行取得 |
| `springer-template/fonts/` | 模板附带字体 | 来源和授权范围待核实 | 逐个记录字体作者、来源和许可；未确认项移除 |
| `springer-template/images/Springer-logo.png` | Springer logo 兼容资源 | 版权和商标使用待核实 | 不用于成品；公开分发前确认或移除 |
| `springer-template/images/figure.eps` | 模板示例图片 | 来源和许可待核实 | 确认或移除 |
| `springer-template/styles/*.bst` | Springer/BibTeX 样式 | 文件声明和再分发条件待核实 | 逐个登记来源、版权和许可证 |
| `springer-template/styles/*.ist` | 索引样式及中文适配 | 上游与自有修改边界待核实 | 记录来源和修改 |
| `springer-template/styles/*.sty` | 模板、兼容层和项目适配 | 混合来源 | 逐个标明自有文件和第三方来源 |

当前结论：

- 根目录 `LICENSE` 提供 GFDL 1.2 全文，独立软件工具的 MIT 全文位于
  `LICENSES/MIT.txt`；
- 上述许可证不覆盖本表中授权尚未确认的第三方文件；
- `svmono.cls`、字体、logo 和示例资源仍是公开发布 blocker；
- 在 blocker 关闭前，仓库和 PDF 不应被描述为可自由再分发的正式出版物；
- 删除、替换或取得授权后，必须更新本清单和 `docs/licensing.md`。

正式清单应为每个第三方组件补充：

~~~text
组件：
路径：
版权所有者：
原始来源 URL：
许可证及版本：
许可证全文或链接：
本仓库是否修改：
分发决定：
确认人和日期：
~~~
