# safe-oas2mcp 整体开发文档

## 项目名含义

`safe-oas2mcp` 由四部分组成：

- `safe`：安全默认开启。项目重点不是简单转换接口，而是控制哪些 API 能被 Agent 调用、如何调用、何时需要确认、哪些必须禁用。
- `oas`：OpenAPI Specification，也就是 OpenAPI/Swagger 描述文件。
- `2`：to，表示转换。
- `mcp`：Model Context Protocol，Agent 调用外部工具的协议。

一句话解释：

> `safe-oas2mcp` 是一个把 OpenAPI 安全转换为 MCP Tools 的网关工具。

项目的核心表达是：

> OpenAPI to MCP, safely.

## 项目目标

开发一个开源 Python 工具，让用户可以用一份 `openapi.yaml` 或 `openapi.json` 启动一个安全的 MCP Server。

目标命令：

```bash
safe-oas2mcp inspect ./openapi.yaml
safe-oas2mcp serve ./openapi.yaml
```

`inspect` 用于分析将会生成哪些 MCP tools，并输出风险、状态和原因。

`serve` 用于启动 MCP Server，把 Agent 的 tool call 转换为真实 HTTP API 请求。

## 项目定位

本项目不是普通的 OpenAPI to MCP converter，而是：

> Safe OpenAPI to MCP Gateway

核心差异不在“能不能把接口变成 tool”，而在：

- 是否默认安全；
- 是否避免把危险接口直接暴露给 Agent；
- 是否能解释每个 tool 为什么 enabled、confirm 或 disabled；
- 是否能保护 Token、Header 和敏感响应字段；
- 是否适合 SaaS、企业内部系统和生产 API 接入 Agent。

## 目标用户

- Agent 应用开发者：希望快速把现有 REST API 接入 MCP。
- SaaS 厂商：希望把产品 API 安全地开放给 AI 工具。
- 企业内部平台团队：希望把内部系统 API 以可控方式提供给 Agent。
- 安全和平台工程团队：希望有 inspect、policy、audit、diff 等治理能力。

## 非目标

MVP 不做以下事情：

- 完整 OAuth2 流程；
- Web UI；
- RBAC 管理平台；
- 多语言代码生成；
- 复杂审批流；
- 完整 OpenAPI schema 兼容；
- 大而全的 API 治理平台。

## 技术选择

第一版使用 Python。

建议技术栈：

- CLI：Typer
- 终端输出：Rich
- OpenAPI YAML/JSON：PyYAML
- 数据模型：Pydantic
- HTTP 请求：httpx
- MCP Server：官方 MCP Python SDK
- 测试：pytest
- 打包：pyproject.toml，支持 `uvx` 和 `pipx`

## 核心架构

```text
OpenAPI file
  -> loader
  -> parser
  -> Operation model
  -> policy engine
  -> Tool definition
  -> MCP server
  -> HTTP executor
  -> redacted response
```

建议模块：

```text
safe_oas2mcp/
  cli.py
  config.py
  models.py
  openapi/
    loader.py
    parser.py
    schema.py
  policy/
    engine.py
    rules.py
  mcp/
    server.py
    tools.py
  http/
    executor.py
    auth.py
  security/
    redactor.py
```

## 核心数据模型

内部应至少有以下模型：

- `Operation`：从 OpenAPI 解析出的接口操作。
- `ToolDefinition`：面向 MCP 暴露的 tool 定义。
- `RiskResult`：风险等级、状态和原因。
- `ExecutionPlan`：一次 tool call 将要形成的 HTTP 请求。
- `Config`：base URL、认证、header、include/exclude、policy override。

## 默认安全策略

默认策略必须保守。

| 条件 | 默认风险 | 默认状态 |
| --- | --- | --- |
| GET | low | enabled |
| POST | medium | confirm |
| PUT | high | confirm |
| PATCH | high | confirm |
| DELETE | critical | disabled |
| 命中 payment/refund/transfer/admin/role/permission/export/bulk 等关键词 | high 或 critical | confirm 或 disabled |
| 不可识别或缺少关键信息的接口 | high | confirm |

注意：GET 不天然安全。GET 如果命中导出、敏感数据、批量读取等关键词，也必须提升风险。

## 状态语义

- `enabled`：可以注册为 MCP tool，并允许执行。
- `confirm`：可以被展示或注册，但执行前必须走确认机制；MVP 可先返回 request preview，不直接请求真实 API。
- `disabled`：默认不注册为 MCP tool。

## 开源成功标准

项目要在 GitHub 上更容易被理解、试用和信任，需要满足：

- 一条命令能跑通 demo；
- README 第一屏说清楚项目价值；
- inspect 输出足够直观；
- 默认策略明显保守；
- 有 Petstore、Todo SaaS、GitHub readonly 示例；
- 有清楚的安全边界和威胁模型；
- 有 CI、测试、类型检查；
- 有 MCP 客户端配置示例；
- 不把 Token 泄露到 tool schema、日志或响应里。

## 分阶段路线

- 阶段一：inspect 分析能力，见 `01-phase-inspect.md`
- 阶段二：serve 运行能力，见 `02-phase-serve.md`
- 阶段三：安全强化能力，见 `03-phase-security-hardening.md`
- 阶段四：工程化和开源包装，见 `04-phase-open-source.md`

## 确认规则

遇到以下情况必须停下来让项目负责人确认：

- 项目名称、定位、默认安全策略发生变化；
- 是否放宽 DELETE、POST、PUT、PATCH 的默认行为；
- 是否引入大型依赖或改变主要技术栈；
- 是否把 confirm tool 改成默认可执行；
- 是否把 Token、Header、响应脱敏策略变弱；
- 是否新增 Web UI、平台化、OAuth2、RBAC 等超出 MVP 的功能；
- 是否发布到 PyPI、创建 GitHub release 或改变开源许可证；
- 是否删除、重命名、迁移已有重要文件。

## 总体开发清单

- [x] 初始化 Python 项目结构
- [x] 完成阶段一 inspect
- [x] 完成阶段二 serve
- [x] 完成阶段三安全强化
- [ ] 完成阶段四开源包装
- [ ] 发布第一个可试用版本
