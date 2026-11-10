# v1.1.0：Windows Hayes PROCESS Model 4 适配

本版本基于 `flupke91/spss-studio-mcp` 的 Windows v1.0.0，保留原有工具，新增
一个公开 MCP 工具：`spss_process`。

## 新增能力

- 单一中介和多个并行中介的 PROCESS Model 4
- 1,000–100,000 次 Bootstrap 与可配置置信水平
- 协变量、总效应、直接效应、间接效应与间接效应成对比较
- 中介效应量、标准化系数与可复现随机种子
- `spss_check_status` 显示 PROCESS 路径与版本

## Windows 集成

- 优先读取 `SPSS_PROCESS_MACRO_PATH`
- 也会在 SPSS 安装目录以及用户的 Downloads、Documents、Desktop 中查找
  `process.sps`
- 通过 SPSS 自带 Python3 XD API，在持久引擎内先加载可信宏，再执行 PROCESS 命令
- 保留宏文件物理行边界，兼容大型 PROCESS 宏定义

## 安全与版权

本项目不分发 Hayes PROCESS 本体。用户应从
[Andrew F. Hayes 官方网站](https://www.afhayes.com/download.html)下载，并遵守其
版权与使用条款。工具调用者不能指定任意宏文件，通用 `INSERT FILE` 仍被安全层拦截。

## 验证状态

- 自动测试覆盖参数校验、Windows 路径语法、宏版本检测、可信预加载和引擎行边界
- 原 Windows v1.0.0 能力沿用上游的 SPSS 32 真机验证
- PROCESS 执行需要在安装了 PROCESS 的 Windows SPSS 上完成最终真机复核
