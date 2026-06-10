# 阶段四：工程化和开源包装开发文档

## 阶段目标

把核心功能包装成一个容易理解、容易试用、容易信任的开源项目，让它具备在 GitHub 上传播和被实际使用的基础。

## 阶段价值

一个工具要在 GitHub 上流行，除了功能有用，还需要：

- 定位一句话清楚；
- 快速 demo 能跑通；
- README 第一屏有吸引力；
- 安装方式简单；
- 示例真实；
- 安全边界写清楚；
- CI 和测试让用户信任；
- MCP 客户端接入文档完整。

## 开源定位文案

建议 tagline：

> OpenAPI to MCP, safely.

建议一句话介绍：

> `safe-oas2mcp` turns OpenAPI specs into MCP tools with secure defaults, risk inspection, confirmation gates, and secret redaction.

中文介绍：

> `safe-oas2mcp` 是一个安全的 OpenAPI-to-MCP 网关，可以把 REST API 暴露给 AI Agent，同时默认禁用高危操作、保护 Token，并输出可解释的风险结果。

## 工程化范围

支持：

- README；
- 安装文档；
- 快速开始；
- 示例 OpenAPI；
- MCP 客户端配置；
- GitHub Actions；
- 测试覆盖；
- Docker；
- release 流程；
- 安全策略文档；
- 贡献指南。

暂不支持：

- 商业官网；
- 云服务；
- Web 控制台；
- 复杂 logo/品牌系统；
- 多语言文档站。

## 示例工程

至少准备：

- Todo SaaS Demo：展示 GET/POST/PATCH/DELETE 风险差异。
- Petstore Demo：展示通用 OpenAPI 兼容能力。
- GitHub API readonly Demo：展示真实 SaaS readonly 接入。

## README 结构

建议结构：

```text
# safe-oas2mcp

OpenAPI to MCP, safely.

## Why
## Quick Start
## Inspect Your API
## Serve as MCP Server
## Security Defaults
## Configuration
## Examples
## MCP Client Setup
## Roadmap
## Security
## License
```

README 第一屏必须包含：

- 项目是什么；
- 为什么不是普通 converter；
- 一条 inspect 命令；
- 一条 serve 命令；
- 安全默认策略摘要。

## GitHub 传播要点

- inspect 表格输出截图或终端 GIF；
- 一个能 1 分钟跑通的 Todo demo；
- 清楚说明 DELETE 默认 disabled；
- 清楚说明 Token 不暴露给模型；
- 支持 `uvx safe-oas2mcp ...`；
- README 中有 Claude Desktop / Cursor 配置示例；
- 有 `SECURITY.md` 和威胁模型；
- issue 模板收集 OpenAPI 兼容问题；
- roadmap 展示后续 diff、audit、CI gate 能力。

## 开发清单

### 1. README

- [ ] 写项目 tagline
- [ ] 写 Why
- [ ] 写 Quick Start
- [ ] 写 inspect 示例
- [ ] 写 serve 示例
- [ ] 写安全默认策略
- [ ] 写配置示例
- [ ] 写 MCP 客户端配置
- [ ] 写 Roadmap

### 2. 示例

- [ ] 创建 Todo SaaS Demo OpenAPI
- [ ] 创建 Todo SaaS mock server
- [ ] 创建 Petstore 子集 OpenAPI
- [ ] 创建 GitHub readonly 示例配置
- [ ] 为每个示例写 README

### 3. 打包发布

- [ ] 完善 `pyproject.toml`
- [ ] 配置 console script `safe-oas2mcp`
- [ ] 验证 `pipx install .`
- [ ] 验证 `uvx --from . safe-oas2mcp`
- [ ] 准备 PyPI 包元数据
- [ ] 发布前确认包名可用

### 4. CI

- [ ] 配置 GitHub Actions
- [ ] 运行 pytest
- [ ] 运行 lint
- [ ] 运行 type check
- [ ] 运行安全脱敏测试
- [ ] 上传覆盖率报告

### 5. Docker

- [ ] 创建 Dockerfile
- [ ] 支持 inspect
- [ ] 支持 serve
- [ ] 文档说明 env 注入 token
- [ ] 验证容器内不打印 secret

### 6. MCP 客户端文档

- [ ] Claude Desktop 配置
- [ ] Cursor 配置
- [ ] Windsurf 配置
- [ ] 本地 stdio 使用说明
- [ ] 常见错误排查

### 7. 安全文档

- [ ] 创建 `SECURITY.md`
- [ ] 写威胁模型
- [ ] 写默认策略说明
- [ ] 写 Token 处理说明
- [ ] 写响应脱敏说明
- [ ] 写漏洞报告方式

### 8. 社区文件

- [ ] 创建 `CONTRIBUTING.md`
- [ ] 创建 issue 模板
- [ ] 创建 bug report 模板
- [ ] 创建 feature request 模板
- [ ] 创建 pull request 模板
- [ ] 创建 changelog
- [ ] 确认许可证

## 验收标准

- [ ] 新用户可以按 README 在 5 分钟内跑通 Todo demo
- [ ] README 清楚表达 Safe OpenAPI to MCP Gateway 定位
- [ ] CI 通过
- [ ] 示例能执行
- [ ] MCP 客户端配置可用
- [ ] 安全文档完整
- [ ] 发布流程清晰

## 需要确认后才能继续的事项

- [ ] 开源许可证选择
- [ ] 是否发布到 PyPI
- [ ] 是否创建 Docker Hub/GHCR 镜像
- [ ] 是否创建项目 logo
- [ ] 是否把 GitHub readonly demo 放入第一批示例

