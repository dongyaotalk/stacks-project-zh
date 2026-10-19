# PR 合同的大文件原字节读取

本工具修正对应 Issue812，是 PR809 的唯一必要前置。来源锁仍为
`a04446e57ec1fbc252a871afcec7752fb2807b14`；不修改任何翻译事实、历史、词表批准或来源。

## 实际问题与处理

PR809 的精确 head `a17f465633986a9578ac3cef6eac283841fd87c8`、base
`5b527d9cf753ba3f589d1cc7fe9d18be31ddfd81` 中，一个12,543,447字节的UTF-8
JSONL由GitHub返回 `isTruncated=true`、`isBinary=null`。原可信校验器要求分类为
false，因而在读取完整blob之前误拒绝。失败记录为PR Contract run39160074588、
job117771399704。`pull_request_target`从main执行可信代码，不能让未合并的PR自行
替换其校验器，因此用户明确允许这一项独立纯工具前置。

仅在分类字段实际存在、`isTruncated`确为布尔true时接受null分类，并调用既有的
锁定Git blob回退。明确二进制true、缺分类字段、非截断null仍拒绝。回退按已固定
仓库和blob SHA请求完整原字节，强制base64格式、长度、Git blob hash和UTF-8一致；
随后仍解析全部结构化记录、范围及来源合同。不得用截断API文本、短patch、跳过
大文件或缓存PASS代替检查，也不跟随数据提供的任意URL。

## 验收证据

- 新增可空分类及非截断/缺字段/明确二进制/错hash/错长度/非UTF-8的正反回归；
  全部42项合同测试通过，测试仅使用合成内容，不生成译文事实。
- 真实GitHub API对上述12MB文件完整回退通过，SHA256为
  `6dbcc7cb5324de0ca0da754c6fc43a2bcd15ca90c9a6d6aa05dd7a316588ace1`，
  与已验收工作区原字节相等。
- 修正草案对整份PR809的实际GitHub-native复验通过：2362文件、2327完整内容，
  零合同错误；实际461次API读取，读取1325.148秒，总1386.017秒。每份返回内容
  与已验收原字节相等。此为本机实际验证，不冒称GitHub Actions成功。
- 原job的5分钟时限不能容纳此次实测；改为30分钟，仍只读权限、从main运行可信
  工具、完整内容/原生分页/精确head-base/唯一closing和范围合同均保持。

## 复现与后续维护

本地使用已安装pyenv3.12.6：

```sh
TASK_PYTHON="$(PYENV_VERSION=3.12.6 pyenv which python)"
PYTHONPATH=tests "$TASK_PYTHON" -m unittest test_pr_contract
make workflow-check harvest-check PYTHON="$TASK_PYTHON"
make render MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"
make pdf MODEL=openai-gpt-5.6-sol PYTHON="$TASK_PYTHON"
```

真实远端检查由 `scripts/check_pr_contract.py` 执行，需运行环境已有
GITHUB_REPOSITORY、PR_NUMBER及GITHUB_TOKEN；不得输出token。查看对应PR的最新
`pr-contract`与`policy-and-data`真实run/job，不能把本机成功写成远端门禁通过。
仅调时限不使失败变成通过，语法、来源、数据或审批错误仍应失败。

本次四个允许文件为校验器、其回归、可信workflow时限和本文。适用本地构建、
整书文字/原字节及视觉对照、完整staged diff、精确远端文件和双门禁均须通过才
合并。合并后普通合入PR809，重新核对最新精确HEAD/base及全部原字节/完整patch/
原生合同；既有数据和生成冻结不回写，不创建逐批DATA任务。

## 此工具分支的实际本地构建

42项合同测试通过2.694秒，workflow117必需文件和锁定harvest检查通过。实际
`make render MODEL=openai-gpt-5.6-sol`退出0（211.820秒）、`make pdf`同lane退出0
（66.800秒），463页FinalTeX日志通过。全部119 TeX与接受main原字节相等；整书
全文和逐页120dpi像素对照仅第2页构建日期由2026-10-15变为2026-10-19，其余462页
完全相同。新版1/2/3页及旧版第2页已实际查看，排版正常；其余页复用已绑定的
接受视觉基线。PDF SHA256为
`4e274792e6682c9912c825cde31a43b4cc3330d9a4a0cebd5fcabdd8bb7a006e`。
本次不修改模板、Make或渲染路径，无需额外template；生成物和现场回执不提交。
