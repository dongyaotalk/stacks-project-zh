# 术语决策流程

术语表是机器可读政策，不是个人偏好列表。权威文件是
`config/glossary.yml`；本文规定如何提出、批准、废弃和应用术语。

## 1. 术语状态

- `proposed`：有人提出，尚未成为正文强制译法；
- `approved`：经过人工决定，可用于后续候选和 reviewed 译文；
- `deprecated`：不再推荐，必须保留原因和迁移影响。

模型、翻译者和自动 QA 不能把词条从 `proposed` 自动改成 `approved`。术语批准必须
由独立的术语 PR 完成。

## 2. 提交术语 Issue/PR

每个术语或不可分割的同义/反义术语组至少提供：

~~~yaml
source_term: fibre product
target_term: 纤维积
status: proposed
definition_or_context: 上下文中的数学定义、定理或章节语境
evidence:
  - chapter: schemes
    unit_id: tag:0001:p003
    source_commit: a04446e57ec1fbc252a871afcec7752fb2807b14
alternatives:
  - 纤维乘积
reason: 与当前数学语境和项目既有译法一致
retain_english: true
migration_impact: 需要影响的现有 unit 或“无”
~~~

术语 Issue 还应说明英文词形是否包含限定词、复数、大小写或重音命令。不能把
“看起来相似”的英文词默认为同一个术语。

## 3. 决策标准

术语维护者应考虑：

- 当前 Stacks Project 语境中的定义，而不是通用词典释义；
- 与已批准术语的组合关系、反义关系和派生词；
- 中文数学书面语的清晰度；
- 是否需要按语境采用不同译法；
- 是否保留英文原词形；
- 对既有候选、reviewed 数据和 Translation Memory 的影响；
- 上游变化后是否仍然适用。

有歧义时保持 `proposed` 并记录问题，不为了让一个翻译 PR 通过而临时批准。

## 4. 应用规则

批准词条只决定中文译法，不取消数学术语的双语显示要求。正文中每一次数学术语
出现仍必须是：

~~~text
中文（English）
~~~

同一术语出现两次，`term_occurrences` 也必须记录两次。英文部分保留该处的原始
词形；模型不得自行改成词根、单数或另一种大小写。

术语批准和译文应用必须分成两个提交或 PR：

1. `term/*` PR 更新 `config/glossary.yml`；
2. 独立翻译/修订 PR 应用批准译法；
3. 运行全部结构、术语和英文残留检查；
4. 旧候选的 glossary revision 不得被静默覆盖。

## 5. 废弃和冲突

废弃词条不能直接删除。必须保留：

- 原词条及其历史状态；
- 废弃原因；
- 替代词条；
- 受影响 unit、候选和 reviewed 数据；
- 是否需要重新审校或上游同步。

不同语境允许不同词条，但必须在 `definition_or_context` 中写明适用条件。若两个
术语 PR 互相冲突，先暂停受影响翻译，再由术语维护者做一个可审计的决定。

## 6. AI 限制

AI 可以发现并报告未知术语、提出候选译法和生成 `unknown_terms`，但不能：

- 修改 `config/glossary.yml` 的批准状态；
- 把自己的翻译结果当作术语证据；
- 用多数模型投票代替人工决定；
- 在普通翻译 PR 中夹带术语批准；
- 用批准前的 `proposed` 词条作为权威 Translation Memory。

## 7. 正式采用的机器检查

`make decision-check` 从 `config/glossary.yml` 读取真实批准，对所选候选的
`term_occurrences` 和 `unknown_terms` 按精确的 `source_term + target_term` 组合核验。
revision 自报 `CLEAR`、语言/数学审校或候选把未知术语数组清空，都不能批准词条。
候选的术语显示完整性另由来源侧检查负责；这一门禁不声称已经识别所有数学术语。

为保持 Python 标准库运行，词表读取支持当前 `entries: []`、缩进一致的 YAML
block list，以及采用 JSON 语法的完整文档/flow value。字符串可以是普通、单引号或
JSON 双引号形式；定义/语境可用 `|`、`>` 文本块，证据可用 block list 或 JSON
数组。每个 entry 的 `source_term`、`target_term`、`status`、`definition_or_context`
必须是非空字符串，`evidence` 必须是非空数组。证据内容的适用语境仍由术语维护者
核验，证据内部的 `status` 不会被当作词条批准状态。

重复 entries 段、重复字段、不合法的批准状态、缺失证据和无法可靠识别的语法都
导致检查失败。YAML tag、anchor、alias 不属于该读取合同，不能用它们隐藏批准
字段；需要复杂表达式时使用可审查的 JSON 文档，不执行输入中的指令。
