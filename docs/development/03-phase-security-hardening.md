# 阶段三：安全强化能力开发文档

## 阶段目标

在 inspect 和 serve 主链路跑通后，强化安全策略、脱敏、限制和审计能力，让项目真正区别于普通 OpenAPI-to-MCP converter。

## 阶段价值

Agent 调用真实业务 API 的主要风险不是协议转换，而是：

- 误调用写操作；
- 调用高危接口；
- 泄露 Token；
- 泄露敏感响应数据；
- 返回过大数据；
- 缺少审计记录；
- 无法解释为什么某个接口被暴露。

这一阶段围绕这些风险补强。

## 功能范围

支持：

- 更完整的高危关键词策略；
- method + keyword + schema + path 的综合风险判断；
- include/exclude 配置；
- per-operation policy override；
- request preview；
- secret/header/token 脱敏；
- 响应字段脱敏；
- 响应大小限制；
- 基础审计日志；
- 安全策略测试集。

暂不支持：

- Web 审批流；
- 企业 RBAC；
- 多人审批；
- SIEM 集成；
- 完整 DLP。

## 高危关键词策略

默认高危关键词分组：

```text
money:
  payment, pay, refund, transfer, payout, invoice, billing, charge

identity:
  user, account, member, customer, password, credential, token, secret, key

permission:
  admin, root, role, permission, policy, access, invite

destructive:
  delete, remove, destroy, revoke, disable, suspend, terminate

bulk_data:
  export, bulk, batch, dump, report, download
```

匹配范围：

- path；
- operationId；
- summary；
- description；
- tags；
- parameter names；
- requestBody schema property names。

## 配置策略

建议配置：

```yaml
policy:
  include:
    - "GET /tasks"

  exclude:
    - "DELETE /*"

  overrides:
    "POST /tasks":
      status: confirm
      risk: medium
      reason: "Task creation is allowed with confirmation"
```

配置规则：

- exclude 优先级高于 include；
- disabled 优先级高于 confirm；
- 配置不能让认证字段暴露给模型；
- 配置如果放宽默认安全策略，inspect 必须显示原因。

## 脱敏策略

请求和响应中默认脱敏字段：

- authorization
- api_key
- apikey
- token
- access_token
- refresh_token
- secret
- password
- credential
- private_key
- email
- phone

脱敏结果示例：

```json
{
  "email": "u***@example.com",
  "token": "[REDACTED]"
}
```

## 审计日志

MVP 审计字段：

- timestamp
- tool name
- method
- path
- risk
- status
- executed
- http status code
- duration ms
- error category

审计日志不能包含：

- Authorization 原文；
- API Key 原文；
- Token 原文；
- 未脱敏敏感响应字段。

## 开发清单

### 1. 风险策略强化

- [x] 实现关键词分组
- [x] 支持从 path 匹配关键词
- [x] 支持从 operationId 匹配关键词
- [x] 支持从 summary/description 匹配关键词
- [x] 支持从 tags 匹配关键词
- [x] 支持从 parameter names 匹配关键词
- [x] 支持从 requestBody property names 匹配关键词
- [x] 输出命中的关键词和来源
- [x] GET 命中 bulk/export 时提升为 high
- [x] money/permission/destructive 命中时提升为 high 或 critical

### 2. include/exclude/override

- [x] 支持 include 规则
- [x] 支持 exclude 规则
- [x] 支持 policy overrides
- [x] exclude 优先于 include
- [x] override 必须写入 reasons
- [x] inspect 输出策略来源
- [x] 测试配置放宽策略时的输出

### 3. Request preview

- [x] 实现 preview 数据结构
- [x] preview 包含 method
- [x] preview 包含 URL 但不包含 secret
- [x] preview 包含 query
- [x] preview 包含 body preview
- [x] preview 包含 risk/status/reasons
- [x] confirm tool 默认返回 preview

### 4. 请求脱敏

- [x] 脱敏 Authorization header
- [x] 脱敏 API Key header
- [x] 脱敏 query 中的 token/key
- [x] 脱敏 body 中的 password/token/secret
- [x] 错误信息中不泄露 secret
- [x] 日志中不泄露 secret

### 5. 响应脱敏

- [x] JSON 对象递归脱敏
- [x] JSON 数组递归脱敏
- [x] text 响应做基础 secret pattern 脱敏
- [x] email 脱敏
- [x] phone 脱敏
- [x] token/secret/password 脱敏

### 6. 响应大小限制

- [x] 配置默认最大响应大小
- [x] 超出限制时截断或拒绝
- [x] 返回结果标记 truncated
- [x] 审计日志记录 truncated

### 7. 审计日志

- [x] 实现 JSON Lines 审计日志
- [x] 记录 tool call
- [x] 记录 preview-only call
- [x] 记录 executed call
- [x] 记录 HTTP status code
- [x] 记录 duration
- [x] 记录 error category
- [x] 确认日志不包含 secret

### 8. 安全测试

- [x] 添加高危关键词测试集
- [x] 添加认证脱敏测试
- [x] 添加响应脱敏测试
- [x] 添加审计日志脱敏测试
- [x] 添加响应大小限制测试
- [x] 添加 override 策略测试

## 验收标准

- [x] inspect 能解释高危关键词来源
- [x] include/exclude/override 生效
- [x] confirm tool 默认返回 request preview
- [x] Token 不泄露到输出、日志、schema、description
- [x] 响应敏感字段被脱敏
- [x] 大响应被限制
- [x] 审计日志可用且不泄露 secret
- [x] 安全测试通过

## 需要确认后才能继续的事项

- [x] 默认关键词列表是否调整
- [x] email/phone 是否默认脱敏
- [x] 大响应是截断还是拒绝
- [x] 审计日志默认开启还是配置开启
- [x] policy override 是否允许把 DELETE 从 disabled 改成 confirm
