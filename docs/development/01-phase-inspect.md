# 阶段一：inspect 分析能力开发文档

## 阶段目标

实现：

```bash
safe-oas2mcp inspect ./openapi.yaml
```

输出 OpenAPI 文件中将会生成的 MCP tools，并展示：

- tool name
- method
- path
- risk
- status
- reasons

示例：

```text
Tool             Method   Path              Risk       Status     Reasons
list_tasks       GET      /tasks            low        enabled    read-only method
create_task      POST     /tasks            medium     confirm    write method requires confirmation
delete_task      DELETE   /tasks/{id}       critical   disabled   DELETE disabled by default
```

## 阶段价值

`inspect` 是整个项目的安全入口。用户必须先知道哪些接口会暴露给 Agent、为什么暴露、哪些被禁用。

这一阶段不调用真实 API，不启动 MCP Server，只做分析和可解释输出。

## 功能范围

支持：

- OpenAPI 3.x；
- YAML / JSON；
- `GET / POST / PUT / PATCH / DELETE`；
- `operationId`；
- `summary` / `description`；
- path/query/header 参数解析；
- JSON requestBody 的基础解析；
- 本地 `$ref` 的最小解析；
- tool name 生成；
- tool description 生成；
- inputSchema 生成；
- risk/status/reasons 判断；
- table 输出；
- JSON 输出。

暂不支持：

- 完整 schema 兼容；
- OAuth2；
- multipart/form-data；
- streaming；
- callbacks/webhooks；
- 真实 HTTP 请求；
- MCP Server。

## 建议模块

```text
safe_oas2mcp/
  cli.py
  models.py
  openapi/
    loader.py
    parser.py
    schema.py
  policy/
    engine.py
    rules.py
```

## 输入输出设计

默认表格输出：

```bash
safe-oas2mcp inspect ./openapi.yaml
```

JSON 输出：

```bash
safe-oas2mcp inspect ./openapi.yaml --format json
```

建议 JSON 结构：

```json
{
  "tools": [
    {
      "name": "list_tasks",
      "method": "GET",
      "path": "/tasks",
      "risk": "low",
      "status": "enabled",
      "reasons": ["GET is enabled by default"]
    }
  ]
}
```

## 风险策略 MVP

默认方法策略：

- GET：`low` + `enabled`
- POST：`medium` + `confirm`
- PUT：`high` + `confirm`
- PATCH：`high` + `confirm`
- DELETE：`critical` + `disabled`

默认高危关键词：

- payment
- refund
- transfer
- payout
- invoice
- admin
- root
- role
- permission
- user
- delete
- remove
- export
- bulk
- batch
- secret
- token
- key

关键词匹配范围：

- path
- operationId
- summary
- description
- tag

## 开发清单

### 1. 项目骨架

- [x] 创建 `pyproject.toml`
- [x] 创建 `safe_oas2mcp` 包
- [x] 创建 `tests` 目录
- [x] 配置 pytest
- [x] 配置基础 lint/type check 命令

### 2. OpenAPI loader

- [x] 支持读取 `.yaml`
- [x] 支持读取 `.yml`
- [x] 支持读取 `.json`
- [x] 文件不存在时输出清晰错误
- [x] 非法 YAML/JSON 时输出清晰错误
- [x] 非 OpenAPI 3.x 时输出清晰错误

### 3. OpenAPI parser

- [x] 解析 `servers`
- [x] 解析 `paths`
- [x] 解析 HTTP method
- [x] 解析 `operationId`
- [x] 解析 `summary`
- [x] 解析 `description`
- [x] 解析 `tags`
- [x] 解析 path parameters
- [x] 解析 query parameters
- [x] 解析 header parameters
- [x] 解析 JSON requestBody
- [x] 支持本地 `$ref` 的最小解析

### 4. Tool 生成

- [x] 优先使用 `operationId` 生成 tool name
- [x] 没有 `operationId` 时根据 method + path 生成 tool name
- [x] tool name 只保留 MCP 友好的字符
- [x] tool name 冲突时自动追加后缀
- [x] 根据 summary/description 生成 tool description
- [x] 根据 path/query/body 生成 inputSchema
- [x] 不把 Authorization、API Key、Token 放入 inputSchema

### 5. Policy engine

- [x] 实现 method 默认策略
- [x] 实现高危关键词检测
- [x] 输出 risk
- [x] 输出 status
- [x] 输出 reasons
- [x] GET 命中高危关键词时提升风险
- [x] DELETE 默认 disabled
- [x] POST/PUT/PATCH 默认 confirm

### 6. inspect CLI

- [x] 实现 `safe-oas2mcp inspect <file>`
- [x] 实现表格输出
- [x] 实现 `--format json`
- [x] 支持按 status 统计数量
- [x] 出错时返回非 0 exit code
- [x] 输出中展示 reasons

### 7. 测试

- [x] 添加 Todo SaaS OpenAPI fixture
- [x] 添加 Petstore 子集 fixture
- [x] 测试 YAML 加载
- [x] 测试 JSON 加载
- [x] 测试 GET enabled
- [x] 测试 POST confirm
- [x] 测试 PUT confirm
- [x] 测试 PATCH confirm
- [x] 测试 DELETE disabled
- [x] 测试高危关键词提升风险
- [x] 测试 inputSchema 不泄露认证字段
- [x] 测试 inspect JSON 输出

## 验收标准

- [x] `safe-oas2mcp inspect examples/todo/openapi.yaml` 可以输出表格
- [x] `safe-oas2mcp inspect examples/todo/openapi.yaml --format json` 可以输出合法 JSON
- [x] DELETE 接口默认 disabled
- [x] POST/PUT/PATCH 默认 confirm
- [x] GET 默认 enabled，但高危 GET 会提升风险
- [x] 输出包含 reasons
- [x] 测试通过

## 需要确认后才能继续的事项

- [x] 是否调整默认高危关键词列表
- [x] 是否要求第一阶段就支持配置文件
- [x] 是否把 header parameters 暴露为 tool input
- [x] inspect 默认是否显示 disabled tools
