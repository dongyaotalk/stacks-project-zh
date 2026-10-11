# AJbook 模板适配

本目录是 `stacks-project-zh` 默认使用的中文数学书模板。核心文件来自项目维护者提供的
AJbook 模板快照，其上游为 Wen-Wei Li（李文威）的
[AlJabr-1](https://github.com/wenweili/AlJabr-1)。上游模板按 CC BY 4.0
许可；完整许可见 [`LICENSE`](LICENSE)。本项目保留原作者署名，并修改了入口、
封面、定理计数和 Stacks Project 宏兼容层。封面保留 AlJabr-1 的非对称标题组和
渐变竖条，主图则重绘为层叠文稿与真实永久 Tag 构成的交叉引用网络，以对应
Stacks Project 的开放章节结构和稳定链接系统。

不要在本目录直接运行模板自带的示例命令。请从仓库根目录构建：

```sh
make template
make render MODEL=<model-lane>
make pdf MODEL=<model-lane>
```

修改过程只看某一完整章节时，在仓库根目录运行：

```sh
make pdf-chapter CHAPTER=categories MODEL=openai-gpt-5.6-sol PYTHON="$(pyenv which python)"
```

这会读取该章全部候选，生成独立的 `<model>-chapter-<chapter>` TeX lane，入口只
`input` 该章，保留原书章节编号，跨章引用显示永久 Tag 链接。PDF 位于
`output/pdf/chapter-preview/`，辅助文件位于 `build/chapter-preview/`；整书 TeX/PDF
保持。预览不代表全库通过或正式发布，提交前仍运行完整 `make render`、`make pdf`
及所有门禁。`make render-chapter` 可只生成该章 TeX。复合来源的全库溯源检查和
最终 TeX 日志检查仍会执行，因此按章编译的节省不等于省掉全部检查。

默认构建使用 XeLaTeX、Biber 和 makeindex。字体配置使用 TeX Live 自带的 Fandol
字体以及系统字体 `Noto Sans CJK SC`；缺少 Noto 字体时应先安装字体，不能把生成的
TeX 或日志改成绕过编译门禁。

目录职责：

- `AJbook.cls`、`font-setup-open.tex`、`titles-setup.tex`：AJbook 核心；
- `stacks-project-zh.tex`、`cover.tex`、`project-metadata.tex`：本项目入口与元数据；
- `styles/`：Stacks 数学宏、渲染兼容层和索引样式；
- `frontmatter/`：来源、许可和翻译状态说明；
- `translations/template/`：唯一手工维护的模板冒烟测试；
- `translations/<model-lane>/`：由结构化数据生成的预览，不是翻译事实来源。

旧的 `springer-template/` 目前仅保留作兼容参考，不再是默认编译模板。
