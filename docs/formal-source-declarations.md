# 第90章受保护参数分割的术语声明

独立 TOOL [Issue #1013](https://github.com/dongyaotalk/stacks-project-zh/issues/1013)
为完整斜体声明登记十种有限词汇框架：formal object(s) 的 category、object 和
morphism；带对象及点参数的 tangent space 与 differential；带对象和沿途参数的
lift；groupoid(s) in functors 的 category、object 和 morphism；带对象及表示者
参数的 presentation。连接词 at、along、by 及以 of 开始的片段不独立成为术语。
完整数学词汇核心仍被登记和逐次盘点，不通过登记连接词或删掉真正术语来消除误报。

各框架必须从头至尾匹配，所有参数必须是存在于该单元且拥有完整 inline-dollar
或 inline-paren 原 payload 的 MATH token。错误种类、缺失参数、错误定界符、
未知词汇及不完整声明沿用原解析。已有上同调序数、higher direct image、pseudo
torsors 和 Čech 名称框架保持原权限。source_projection 的正文及投影坐标保持；
原 source_text、数学、环境、保护 token 和 hash 均不修改。

五份完整锁定来源为 06H3、06IK、06JE、06K3、06KX；英文 commit 为
`a04446e57ec1fbc252a871afcec7752fb2807b14`。真实 selector、完整 Git blob/容器
hash、canonical unit、来源投影和原库存见
[完整来源 fixture](../tests/fixtures/formal-source-declarations.json)。

这是来源术语工具修复，不批准中文，不生成或采用候选，不改词表、来源目录、
宏政策、Schema、lock 或旧 freeze/raw/run。实现正常验收并合并后，DATA #1010
另行冻结确切输入并实际生成完整五字段；候选、人类审校及发布各自保持门禁。
