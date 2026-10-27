# 同进程严格验证会话

`qa`、`qa-batch` 和 `render-batch` 使用同次真实验证的私有结果。独立命令仍自行
验证；没有磁盘 PASS、跨进程成功缓存或 skip 参数。历史 v1/v2/v3/v4、修订、
shared histories、typed 数学、完整首次采用及章首合同保持。

## 入口与兼容性

先动态解析并确认 Python 3.12，再显式传给每条 Make：

```sh
TASK_PYTHON="$(PYENV_VERSION=3.12.6 pyenv which python)"
"$TASK_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12)'
make qa MODEL=<lane> BATCH=<batch> PYTHON="$TASK_PYTHON"
make qa-batch MODEL=<lane> BATCHES="batch-a batch-b" PYTHON="$TASK_PYTHON"
make render-batch MODEL=<lane> BATCHES="batch-a batch-b" PYTHON="$TASK_PYTHON"
```

Make 的 workflow、harvest、upstream-index 和 chapter-template 检查覆盖保持。
两个 Python 入口可用 `--help` 查看完整参数：

- `check-batches --units ... --candidates ... --lock upstream.lock --harvest ...`
  在一次调用执行完整 Schema、全历史溯源、决策链接及所选完整有序 pair 的当前 QA。
- `check-and-render` 支持 `render` 的参数，先执行上述严格会话，再消费同一真实结果
  渲染。它不接受章选择；章节开发预览继续使用 `render --chapter`/`make render-chapter`。

原有 Make、CLI 与 Python 接口保持；`validate`/`validate-many` 默认仍只做严格的
当前来源和候选定位，不额外升级为每次完整历史验收。独立 `decision-check` 或需要
完整来源权限的独立 `render` 仍实际完整回放。普通 render/章节预览在同次调用内
共享其真实采用结果。`qa-all` 遍历全部 lane、全部真实 run 和最后一个 batch，
不套用单 run 限制或 changed-path 筛选。

## 信任与依赖

只有完整真实回放成功后才能发行 `_ProvenancePass`，只有全部共享门禁和所选当前
来源 QA 成功后才能发行批次结果。消费时核对发行对象身份、实际 Git root、HEAD、
完整有序 pair、当前原字节及路径集合、英文 harvest 身份、政策和实现字节。
发行时另保存原始依赖与范围声明；删除快照条目或修改凭证清单也失败。
复制对象、调用者字典、其他 root、旧 HEAD、错配/倒序/重复 pair、混 lane/model/
Harness/run 都不能提供凭证。首次采用的私有结果另绑定原 record/input、当前 unit/
candidate、全部历史候选、文件 hash 和实际解析政策，不能只凭来源 pointer 通过。

依赖登记有三部分，固定目录清单不是完整性证明的唯一依据：

1. 在回放前冻结合同允许的事实/政策/实现及路径库存：`translation-data`（含全部
   retired/freeze/嵌套历史）、`review`、`config`、`schema`、`task-scopes`、
   `docs/evidence`（含 raw、prompt 和冻结输入）、`prompts`、Python 源码和锁。
2. 实际解析器收到的字节及枚举结果逐次登记到同进程 `InputReads`，与初始树库存核对，
   因此读取/枚举期间短暂替换后恢复也不能通过。私有回放期间的真实 JSONL/manifest
   读取同时进入 snapshot；来源采用 `Reads`
   记录的动态 raw、冻结输入、递归历史及实际路径集合并入会话。合并保留原始 hash，
   不能把后读到的新字节当作最初凭证。采用对象另持固定的独立实际读取账本，仍自行检查自己的快照和内容绑定。
3. 当前 QA 读取的实际 extraction inventory 在首次使用时登记完整目录/原字节，
   英文 Git 工作树另绑定实际 root、HEAD、origin 身份、受跟踪路径及原字节。锁定 Git
   容器的原有递归验证继续执行。批次跨文件顺序使用本次真实来源对应的字节位置核对，
   普通 run 不需要伪造首次采用 pointer；qa-all 不套用这个单批次顺序门禁。
   实际加载的工具 Python 源码及 Schema 另行绑定，
   因此 Python 调用者验证其他 root 时也不能借目标目录里的同名文件代替实现。
   源码在导入后变化须用新调用加载，Schema 解析在完整会话起点重新绑定。

任一相关内容、路径集合、符号链接、HEAD 或来源身份变化都失败。验证边界和输出
安装边界再次读取原字节；不以 mtime 代替内容。独立调用不复用任何磁盘成功记录。

## 写出与回归

渲染先在内存构造完整 TeX，再暂存整个输出集合；安装前后核对输入。安装故障或
中途输入变化时恢复原输出文件，移除新输出，不打印新的最终成功。该事务是同进程
失败恢复，不是跨进程缓存或崩溃后事务日志。

`tests/test_validation_session.py` 用独立 synthetic Git/英文来源及真实验证器检查
同一结果共享、独立接口、历史/typed/首次采用/章首/预览、假或过期对象、依赖变化、
批次边界、瞬时字节/目录枚举变化和输出恢复。synthetic 数据不宣称真实模型作者。当前真实代表包的前后
测量及一次完整本地验收保存于本任务 ignored build 证据；耗时只报告实测，不继承
旧环境的提速倍率。本地可审查 diff 不代表已提交、已合并或通过远端 CI。
