# 有限罗马数字 item 标签

独立工具任务 [#1019](https://github.com/dongyaotalk/stacks-project-zh/issues/1019)
仅实现锁定英文 `a04446e57ec1fbc252a871afcec7752fb2807b14` 的四个完整
`\item[(\romannumeral1)]` 至 `\item[(\romannumeral4)]` 标签。
完整来源为 defos / lemma0DIT / parent0DIS / `defos-lemma-lift-complex`。
来源 fixture 保存最初 accepted base、完整引理、真实 selector、Git/container hash
及四次精确 UTF-8 范围；旧准备和失败历史保留。

政策入口为可选 `locked_numeric_item_labels`；默认缺省时关闭。唯一有限登记含
`literals`、`usage`、`source_label` 三个 JSON 值字段，分别为四个完整 literal
的固定有序数组、`"finite-roman-item-label"`、`"defos-lemma-lift-complex"`。
缺字段、未知或重复字段、重复/空段、未知用途、错误类型、非四标签顺序和无效来源
标识均拒绝。此实现任务保持生产 `config/macro-policy.yml` 原字节；实际登记须在
实现接受后以独立政策任务验收，不能把测试中的 opt-in 当成生产权限。

来源解析独立要求实际锁定 Git 中唯一完整 lemma/0001、永久 Tag0DIT、完整容器
无损回放，以及四个完整标签各一次并按原序出现。标签的整体 source/hash/Git span
均独立核验。未解析来源见证的政策不得在 Scanner 中启用；已知但其他来源标签也
不能借用权限。无需 TeX 执行或整数求值。

Scanner 只在当前局部 walk 已实际进入的 `enumerate` 正文中启用，且仅由真实
scaffold `item` 分支匹配完整可选标签。命令、方括号、括号、宏及整数数字作为一个
既有 `STRUCT` token 原字节保存。递归文字参数、可选参数、裸命令、其他列表、
片段中缺少列表开头的局部 item、math/literal/comment 和未知命令参数不继承权限。
缺数字、其他数字、符号、数值表达式、花括号、额外宏、空白变体及不完整标签仍阻断。
所有 item 可选标签不得越过当前 source walk 结束边界，避免旧分支读入范围外字节。

完整 native select/lower 使用既有 unit 合同，无新 Schema 或通用整数语法。
来源全部原字节回放；模型只接收受保护的自然语言。既有候选门禁验证每个完整标签
的 token 顺序和次数，删除、改变、重复或重排均拒绝。数学字节和永久 Tag 不变。

公共接入还须执行适用提取/来源/保护及历史回归、workflow/harvest、fresh accepted
base 的 qa-current-all、完整 diff 审查和适用编译或严格 hash/最终日志绑定的复用。
通过实际必需 CI 与规定审查或另行授权 bypass 后才接受实现。独立生产政策采用与
章节实际模型生成随后各自守门，不改变旧 freeze/raw/run、词表、人审或发布状态。
