# 整章来源预检与恢复

`chapter-preflight` 沿锁定 Git 的完整容器选择与现行 lowering，准备整章来源能力、
Section/Tag、阻断原因及有序语义包。它不生成译文、模型 run、采用记录或批准事实。
来源准备 READY、已有候选当前 QA、人工审校分别报告；候选缺失不使完整来源变成未准备。

## 实际入口

先动态解析并确认 Python3.12：

```sh
TASK_PYTHON="$(PYENV_VERSION=3.12.6 pyenv which python)"
"$TASK_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12)'
"$TASK_PYTHON" stacks_zh.py chapter-preflight --help
"$TASK_PYTHON" stacks_zh.py chapter-preflight \
  --root . --harvest ../stacks-project --chapter 7 --json
```

章参数接受锁定目录中的序号或 slug，例如 `7` / `sites`。默认产物位于
`build/chapter-preflight/<chapter>/<input-fingerprint>/`，固定状态位于
`build/chapter-preflight-state/status.json` 和短 `handoff.md`。可分别以 `--output`、
`--state-dir` 指定专用 build 子目录。拒绝事实/英文目录、符号链接及陌生输出。

默认退出0表示完整预检报告已生成，报告仍可能 BLOCKED；`--require-ready` 在任一
来源阻断时返回非零。真实输入、状态或写出错误也返回非零，保留原报告和失败记录。

## 内容和边界

五个确定性文件为 manifest.json、preflight.json、containers.jsonl、packages.json、
report.md。manifest 绑定实际 root/HEAD、英文 Git root/HEAD/origin及受跟踪原字节、
政策/当前事实/实现/Schema/Python、来源库存及完整路径集合。指纹保守覆盖所有当前
unit/candidate/章节骨架/决定与审校文件，因此其他章当前事实变化也会使预检过期。
预检不读取模型 raw/freeze 历史；完整历史仍由独立最终 QA 验证。所有实际读取另行
登记并核对是否属于所绑定的依赖库存；陌生动态依赖拒绝复用或写出。

每个完整容器保存真实 owner/parent/kind/ordinal selector、Git blob/span/hash、无损
lowering 的来源单元及阻断原因。未知宏/环境、数学文字和边界问题继续 BLOCKED。
当前进度的 Section/Tag 规则从锁定 Git 文本复用；完整陈述内原生列表 Tag 使用与
progress_coverage 相同的 helper，章首使用完整 title/header 容器。

计划保持完整容器不可分割、每个提议文件单 Section、同章相邻有序包，沿用2–8文件和
300–1500来源词偏好。完整章首、超长不可分割容器、阻断或章末留下的语义余量会明确
列出例外。contract_support 另列首次采用形状是否受支持；非 Section parent 的正文
不能借章首 v4 权限首次采用，来源 lowering READY 不代表该数据转换已获授权。
文件名/所有权是后续数据任务的提案，现有文件保持只读；不能直接将新
路径作为重叠首次采用。涉及现有来源的改写仍需完整旧 batch、合法 v4 恢复/历史及
显式数据任务。章首首次采用仅由独立 source-adoption-v4 合同授权。

候选状态复用 CurrentSourceQA 的当前来源/保护结构/术语检查；已有库存必须重新核验
其实际 hash 与所用章的锁定 Git 内容。缺少库存不隐式重建全库，报告候选检查未完成。
本命令不授予完整模型溯源、选择、人审或发布权限；各独立 QA/采用/构建门禁照常运行。
reviewed 仅列出现有 current 记录，不由候选 stage 猜造人审批准。

## 恢复与检查

```sh
"$TASK_PYTHON" stacks_zh.py chapter-preflight \
  --root . --harvest ../stacks-project --chapter sites --resume --json
"$TASK_PYTHON" stacks_zh.py chapter-preflight \
  --root . --harvest ../stacks-project --chapter sites --check --json
```

同一状态目录使用进程锁。`--resume` 核对实际 PID/start/command/cwd及输入指纹；原作业
仍活着时返回 RUNNING 和原进程身份，不启动第二份。状态文件或 PID 本身不证明存活；
锁被占用但身份无法确认时保守拒绝重复启动，等待原进程并核实日志。

原进程停止后，同指纹的已验证来源 checkpoint 可继续复用。来源结果按内容 hash
独立保存，每个 attempt 仅更新引用索引，保留原 attempt、结果和事件，
处理剩余来源；当前候选 QA仍独立执行。输入/政策/实现变化拒绝旧 resume，显式开启
新预检会使用新 fingerprint 和独立输出，保留旧包。保存的准备证据不是磁盘 PASS，
不能跳过独立的候选 QA、完整历史或真实来源采用验证。

`--check` 重新计算完整报告并只读比较已有五文件，不改变状态/报告字节或 mtime。
重复普通预检产生相同内容时也不重写内容寻址的报告；执行日志和 attempt 如实另记。
任何输入变化在使用/安装边界失败，新输出失败回滚，旧成功包保持。

状态独立于候选 Schema，仅表达 PREFLIGHT、SOURCE_READY、阻断/中断/失败及下一动作。
不自动进入 GENERATING、采用或发布。记录阶段秒数、实际退出、重试 attempt、hash 和
进程身份；无模型调用时 usage 为不可得，不以字符冒充 token，不记录全会话镜像。
阶段计时与总耗时各自保留，不将嵌套或并发时间重复求和。
