# Retired translation records

保存被上游删除、被新译文替换或明确退休的历史记录。退休记录不能被重写或重新
分配给其他 unit。

`derivations/<derivation-id>/` 保存工具修复前的原始 unit/candidate 文件，必须保留
原字节。配套 `translation-data/derivations/<derivation-id>.json` 记录快照 hash、
当前输出 hash、坐标映射和可重放操作。历史 run manifest 不移动、不修改。
这些快照排除于活跃 QA、进度、渲染和 TM，但仍接受溯源检查。
该合同的工具实现由独立 PR 提供；本规范修改不迁移事实数据。
