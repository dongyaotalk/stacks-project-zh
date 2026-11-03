# 尚未采用事实时的普通措辞来源证据

`nonmathematical_occurrences` 仍按章节、精确 `unit_id`、完整
`source_tex_hash`、来源词形和零起点 `occurrence_index` 登记单次普通措辞。
存在当前同 ID 单元时，必须唯一且锁定提交、完整 TeX hash 和可见词序号一致；
失配直接失败。该记录不能豁免同词的其他出现，也不批准中文译法。
来源盘点先限定相同章节及单元 ID，再计算例外的完整 TeX hash；不同 ID 即使
原 TeX 相同也不能借用该例外。无关注册不触发其他单元的额外占位符回放。

当前尚无该 ID 时，校验器可从锁定英文 Git 独立扫描实际章节，复用整章预检的
完整容器枚举。必须有唯一 canonical ID 对应的完整语义坐标，真实
`Containers.select` 核验 owner Tag/label、Section parent、kind、ordinal 和
来源边界，再按 `whole` 执行 `lower_container`。完整单元的 ID、来源提交、
TeX hash 和词序号必须逐项匹配。完整正文块不能拿首段库存或局部片段代替。
其余数学节点、引用键、URL 和未知宏门禁保持；词形只从受保护后的可见正文
投影读取，不能靠原 TeX 搜索数学、注释或引用参数取得见证。

审计返回实际 selector、Git blob 和完整片段位置/hash，区分 `current-unit`
与 `locked-source-container` 路径。选取与 lowering 只在本次调用内复用，结束时
再次检查政策、锁定来源、Tag 和已读 Git blob 未变，没有磁盘 PASS 缓存。
旧数学术语的 legacy evidence 和 `nonmathematical_chapters` 不获得此回退权限。

此入口只验证目录的英文来源证据，不生成 unit、候选或 run，不改变 Schema、
词表、宏政策或历史。独立政策任务登记普通用法，独立数据任务冻结并实际生成
五字段，之后仍须通过来源结构、逐次术语、完整溯源及人审/发布门禁。
