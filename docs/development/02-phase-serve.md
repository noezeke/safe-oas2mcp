# 阶段二：serve 运行能力开发文档

## 阶段目标

实现：

```bash
safe-oas2mcp serve ./openapi.yaml
```

启动 MCP Server，把符合策略的 OpenAPI operations 注册为 MCP tools，并在 tool call 时转换为真实 HTTP API 请求。

主链路：

```text
Agent tool call
  -> MCP Server
  -> safe-oas2mcp tool handler
  -> parameter validation
  -> HTTP request build
  -> auth/header injection
  -> HTTP API
  -> redacted response
  -> Agent
```

## 阶段价值

这一阶段让项目从分析工具变成可用网关。重点是跑通主链路，同时保持安全默认值。

## 功能范围

支持：

- 启动 MCP stdio server；
- 注册 enabled tools；
- 处理 tool call；
- 校验输入参数；
- 映射 path/query/json body；
- 注入认证和固定 headers；
- 调用 HTTP API；
- 返回 JSON/text 响应；
- 响应基础脱敏；
- HTTP 错误返回结构化结果。

默认行为：

- `enabled` tools 可以执行；
- `confirm` tools 默认只返回 request preview，不直接执行真实请求；
- `disabled` tools 不注册；
- base URL 来自 OpenAPI servers 或配置；
- 模型不能传入任意 base URL；
- Token 不进入 tool schema、description、日志或响应。

## 建议模块

```text
safe_oas2mcp/
  cli.py
  config.py
  mcp/
    server.py
    tools.py
  http/
    executor.py
    auth.py
  security/
    redactor.py
```

## 最小配置文件

建议从这一阶段开始支持：

```yaml
base_url: https://api.example.com

auth:
  type: bearer
  token_env: EXAMPLE_API_TOKEN

headers:
  X-Workspace-Id:
    env: WORKSPACE_ID
```

配置文件默认查找：

```text
safe-oas2mcp.config.yaml
```

也支持显式指定：

```bash
safe-oas2mcp serve ./openapi.yaml --config ./safe-oas2mcp.config.yaml
```

## confirm 状态设计

MVP 默认策略：

- `confirm` tools 可以在 inspect 中展示；
- 是否注册为 MCP tool 需要实现前确认；
- 如果注册，默认执行结果只返回 request preview；
- 不直接请求真实 API；
- 后续再设计明确的审批或二次确认机制。

request preview 示例：

```json
{
  "status": "confirmation_required",
  "method": "POST",
  "url": "https://api.example.com/tasks",
  "body_preview": {
    "title": "Example"
  },
  "message": "This operation requires confirmation and was not executed."
}
```

## 开发清单

### 1. MCP Server

- [x] 引入官方 MCP Python SDK
- [x] 实现 stdio server 启动
- [x] 实现 tools/list
- [x] 实现 tools/call
- [x] 注册 enabled tools
- [x] disabled tools 不注册
- [x] 为 confirm tools 实现 preview 行为

### 2. Config loader

- [x] 支持读取 `safe-oas2mcp.config.yaml`
- [x] 支持 `--config`
- [x] 支持 `base_url`
- [x] 支持 bearer token env
- [x] 支持 api key env
- [x] 支持固定 headers
- [x] 缺失必需 env 时输出清晰错误
- [x] 不在错误信息中泄露 secret 值

### 3. HTTP request 构建

- [x] path 参数替换
- [x] query 参数构建
- [x] JSON body 构建
- [x] header 构建
- [x] base URL 合并
- [x] timeout 设置
- [x] 禁止模型覆盖 base URL
- [x] 禁止模型传入 Authorization/API Key

### 4. HTTP executor

- [x] 使用 httpx 执行请求
- [x] 支持 GET
- [x] 支持 POST
- [x] 支持 PUT
- [x] 支持 PATCH
- [x] 支持 DELETE 逻辑存在但默认不可达
- [x] 处理 2xx 响应
- [x] 处理 4xx 响应
- [x] 处理 5xx 响应
- [x] 处理网络异常
- [x] 处理超时

### 5. 响应处理

- [x] JSON 响应返回结构化结果
- [x] text 响应返回文本结果
- [x] 空响应正常返回
- [x] 响应大小限制
- [x] 基础敏感字段脱敏
- [x] HTTP status code 返回给 Agent

### 6. 测试

- [x] 添加 mock HTTP server 测试
- [x] 测试 enabled GET 可以执行
- [x] 测试 POST 默认返回 preview
- [x] 测试 DELETE 不注册
- [x] 测试 token 从 env 注入
- [x] 测试 token 不出现在 tool schema
- [x] 测试 token 不出现在返回结果
- [x] 测试 path 参数替换
- [x] 测试 query 参数
- [x] 测试 JSON body
- [x] 测试 HTTP 错误
- [x] 测试超时

## 验收标准

- [x] `safe-oas2mcp serve examples/todo/openapi.yaml` 可以启动 MCP Server
- [x] Agent 可以 list tools
- [x] Agent 可以调用 enabled GET tool
- [x] POST/PUT/PATCH 默认不会直接执行真实请求
- [x] DELETE tool 不会出现在 tools/list
- [x] Token 不出现在 tool schema、description、日志或响应
- [x] 测试通过

## 需要确认后才能继续的事项

- [x] confirm tools 是否默认注册
- [x] confirm tools 的二次确认机制如何设计
- [x] 第一版支持 stdio 还是同时支持 HTTP transport
- [x] 配置文件字段命名是否固定
- [x] 默认 timeout 时长
