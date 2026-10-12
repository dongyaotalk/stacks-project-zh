# 书末勘误与原文疑点表

本表把来源 `remark` 收录到可随书阅读的独立记录中。收录或关闭留档 Issue 表示
记录工作完成，不表示英文原文已纠正、数学疑点已裁定或译文已获人工审校批准。
正文、公式、证明、当前候选及所有原始 run/raw 保持其原版本。

## 英文证据版本

本次三条记录均针对 The Stacks Project 的锁定英文提交
[`a04446e57ec1fbc252a871afcec7752fb2807b14`](https://github.com/stacks/stacks-project/commit/a04446e57ec1fbc252a871afcec7752fb2807b14)，
提交日期为 `2026-07-28`，与 `upstream.lock` 相同。证据取自该提交的 Git blob；
harvest 当前分支或工作区不决定来源版本。永久 Tag 链接用于定位，在线 Tag 页面
可能已经变化，核验时必须使用表中明确列出的 commit。

| Tag／真实 Section | 观察 | 状态／留档 |
| --- | --- | --- |
| categories／0032／002Z | 证明先在积范畴中构造有限生成子范畴和扩充，随后使用 I 的子范畴表述。可能缺少投影或环境记号说明。 | 待核验；[#691](https://github.com/dongyaotalk/stacks-project-zh/issues/691) |
| sets／04VA／000H | 引理第三项为 `add more here as needed.`，证明有 `Details omitted.`。不添加性质或证明。 | 原文待补／省略；[#698](https://github.com/dongyaotalk/stacks-project-zh/issues/698) |
| sets／0AHL／000H | 证明先定义 `W_{a, i}`，最后的余积公式使用 `W_{i, a}`。不交换原下标。 | 待核验；[#699](https://github.com/dongyaotalk/stacks-project-zh/issues/699) |

0032 和 0AHL 的记录只陈述字样与环境差异，不判断论证错误。04VA 的待补项和
省略细节是明确可见的原文事实，也不因此认定其结论错误。

## 完整语义坐标与原字节

每个 selector 都包含 `file`、`owner_tag`、`owner_label`、`parent_tag`、`kind`
和 `ordinal`。下列五个完整容器已经由 `Containers.select` 从锁定 Git 重扫，真实
owner／Section／边界、完整原片段、blob OID 与历史恢复记录逐项相等。
行号和 PDF 页码不用于声明范围。

| 文件 | owner Tag／label | parent Tag | kind／ordinal | 完整原片段 SHA-256 |
| --- | --- | --- | --- | --- |
| categories.tex | 0032／categories-lemma-directed-category-system | 002Z | proof／1 | dd43b745fc160c13d02dc409dfa249c9d2bb0d2ab0bcaf2a12153800394f5007 |
| sets.tex | 04VA／sets-lemma-bound-monomorphism | 000H | lemma／1 | ebf36dc3d436f5a9e74151d202e7dcf04fb04c18e46373fdf2958753a78c52c2 |
| sets.tex | 04VA／sets-lemma-bound-monomorphism | 000H | proof／1 | 99765b5b134920fb452f8eca6d45548d93c30e65f02c0f06abdb30cabbcf71e6 |
| sets.tex | 0AHL／sets-lemma-bound-fppf-covering | 000H | lemma／1 | bac2c99a6f03c522b2f56f41324793bc4df181cf2a63012dfa01853918ef431b |
| sets.tex | 0AHL／sets-lemma-bound-fppf-covering | 000H | proof／1 | 2daa1f099382f0b97aa4dfa3909c71e7e3430f943d87f2e08ae7123092cc8b4b |

原记录是 `translation-data/source-container-restorations/` 中的
`audit-categories-0032-complete-20261009-0032-proof.json`、
`audit-sets-04va-complete-20261010-04va-{lemma,proof}.json` 和
`audit-sets-0ahl-complete-20261010-0ahl-{lemma,proof}.json`。
它们连同原 Issue、旧输入、候选、run/raw、派生与恢复历史继续保留原字节。

可以从仓库根目录用 pyenv 的 Python 3.12 重现容器核验，无需修改文件或安装依赖：

```sh
PYENV_VERSION=3.12.6 pyenv exec python - <<'PY'
import hashlib
import json
from pathlib import Path
from stacks_zh.source_containers import Containers

root = Path.cwd()
source = Containers(root, root.parent / 'stacks-project')
names = [
    'audit-categories-0032-complete-20261009-0032-proof',
    'audit-sets-04va-complete-20261010-04va-lemma',
    'audit-sets-04va-complete-20261010-04va-proof',
    'audit-sets-0ahl-complete-20261010-0ahl-lemma',
    'audit-sets-0ahl-complete-20261010-0ahl-proof',
]
for name in names:
    path = root / 'translation-data/source-container-restorations' / (name + '.json')
    record = json.loads(path.read_text())
    selected = source.select(record['selector'])
    assert selected['source_commit'] == record['source_commit']
    assert selected['fragment'] == record['fragment']
    assert selected['location'] == record['location']
    assert selected['blob_oid'] == record['blob_oid']
    digest = 'sha256:' + hashlib.sha256(selected['fragment'].encode()).hexdigest()
    assert digest == record['location']['fragment_hash']
    print(record['selector'], digest)
source.assert_unchanged()
PY
```

## 排版架构与验收

共享手写文件 `ajbook-template/backmatter/source-errata.tex` 保存表格。
`ajbook-template/stacks-project-zh.tex` 加载 `longtable`，在 `printindex` 之后
引入该文件，因此它位于整书最后，也进入目录。整书、完整按章预览和模板冒烟
构建共享此入口。Makefile 把它登记为模板依赖。各模型生成的 TeX 目录仍然只是
预览，表格不会被装配进 `translation-data` 或新模型 run。

```sh
PYENV_VERSION=3.12.6 pyenv exec make render MODEL=openai-gpt-5.6-sol PYTHON=python
PYENV_VERSION=3.12.6 pyenv exec make pdf MODEL=openai-gpt-5.6-sol PYTHON=python
PYENV_VERSION=3.12.6 pyenv exec make template PYTHON=python
```

提交前检查 Final TeX 无错误、整书文字变化、所有变化页与邻页 PNG，确认表格、
英文版本、链接和目录可读且表位于最后。完整翻译事实与历史 tree、英文 lock、政策、
词表及范围外字节必须保持。生成物不提交。仅通过 QA 或编译不构成人工数学批准。

## 后续维护

1. 新发现先创建来源 `remark`，注明锁定英文 commit、完整语义 selector、原文观察
   和确定程度。与译文错误混合的 Issue 仍须处理译文错误部分。
2. 在独立模板／文档任务中声明 owner、branch、准确允许文件及来源证据。重新核验
   完整锁定 Git 容器，再补表格与本文件；不得把疑点直接改入译文或原公式。
3. 条目标注“待核验”“原文待补／省略”，或在获得可追溯确认依据后注明确认状态。
   记录观察、确认依据和适用英文版本；不把模型判断写成数学审校结论。
4. 英文锁变更属于独立 upstream sync。保留旧版表及证据，按新 commit 重新定位并
   核验所有条目，明确哪些仍适用、哪些已由上游更正。不得替换旧 hash 冒称旧证据。
5. 表格合并并核验后，以“已收录留档”关闭单纯记录任务，关闭说明链接表、维护
   文档和合并 PR，并声明原文是否有实际变动。三个既有 Issue 的收尾不表示数学
   疑点已判定或原文已修复，不替代语言、数学、术语、critic 或发布门禁。

若要修复英文原文、向上游提交勘误或采用新数学内容，另开明确授权的源文／同步
任务。本表的维护不扩展为修复原文或批准候选。

## 本次开发与本地验收记录

本任务从 main `43c36dbb0d0d192acea2daaf3c271c883d398415` 独立开展，关联
[#758](https://github.com/dongyaotalk/stacks-project-zh/issues/758)。实际239候选QA、
抽取/对齐及各check、隔离进度/计划原字节检查通过；翻译事实与历史、来源锁、政策
和所有范围外字节保持。最终当前lane render 150.214秒、pdf
69.811秒，template 16.616秒，FinalTeX均PASS。
整书461→463页，实际变化页13/462/463及全部邻页已查看，最终版本行换行后
第463页再次查看，其余原图字节保持；本表在书末，正文和公式未改。
源码、完整hash与复现命令可在本文件和关联PR审查；PDF/PNG/本机路径不提交。
