# Review records

本目录保存自动问题、语言审校和数学审校记录。审校记录必须引用不可变的候选 hash
和 `run_id`；
候选内容改变后，旧审校不得继续生效。

当前布局：

```text
review/
├── language/
└── mathematics/
```

`review/issues/` 是 critic 问题记录的预留目录，当前尚未实现对应 Schema 和命令，
因此不能声称 critic 自动门禁已经落地。

维护者对候选的接受、拒绝或要求修改不写入审校记录，而写入
`translation-data/selections/`；正式采用和替换关系写入 translation revision。
候选进入 `main` 只表示实验记录被保存。

模型或自动化工具不得填写人工审校者身份。详细规则见
`docs/review-and-qa.md`。人工审校记录必须符合 `schema/review.schema.json`，并引用
不可变的 `candidate_hash`、英文 `source_commit` 和结果译文 hash。语言审校与数学
审校分别保存记录；候选内容改变后，旧记录不再有效。
