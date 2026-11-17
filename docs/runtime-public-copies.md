# 不含本机路径的公开执行回执

独立工具任务 #1038 为尚未首次加入 Git 的 runtime 辅助副本提供确定性公开投影。
本地原始执行回执继续原字节保留；既有模型输入、raw、run、freeze、候选和身份不修改。
已经进入 Git 的不可变执行回执不允许使用本工具重新发布。

`scripts/project-runtime-copy.py --root <task-root> --input <original-runtime>
--freeze <original-freeze> --output <task-root/build/public-copy>` 只写新的 ignored 产物。
它按原 freeze 的真实 origin 注册表核验旧 Make argv、零退出、唯一版本和登记命令
输出，完整模型/Harness/turn/effort 必须一致；不执行今天的命令证明过去身份。
失败、重复、矛盾、陌生命令和未解释 stderr 拒绝投影。只有与原 argv 一致的
本机 Python Make 命令回显可省略；其他 stdout、额外捕获字段、布尔/浮点退出值及
非整数投影版本均拒绝，不能用投影隐藏这些内容。

公开副本仅省略 Make 的本机 PYTHON/HARVEST_DIR 参数及带本机路径的命令回显。
保留完整 runtime、原 turn 元数据、时间、provider（原有时）、零退出及实际唯一
Harness 版本/登记命令输出。`execution_capture_projection` 明确披露固定投影方法、
原回执字节哈希及原 argv/stdout/stderr 哈希。哈希仅用于追踪本地原件，不提供私有
日志重放、生成成功或祖先权限。原有可选摘要不发明；其他绝对路径仍使公开副本失败。

接受工具后，具体 DATA 在独立交付视图中使用相同 scope 已预留的 runtime 路径
保存公开副本，本地原始任务视图保持不变。提交前核对完整公开树及投影，记录原件
和公开副本哈希；新增公开表示由当前章节检查绑定原 freeze 及真实生成链。
不得把公开副本称为原执行日志的完整字节。不得改写已经进入 Git 的 runtime，
也不得把本工具用于任何模型文字、raw、run、freeze、scope 或审校记录。

这不是新的模型生成或来源采用合同，不放宽来源、保护、术语、完整五字段、实际
输出、Issue/PR、CI、人审或出版门禁；相关章节数据仍须独立完成当前验收。
