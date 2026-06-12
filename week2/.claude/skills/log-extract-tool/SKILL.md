---
name: log-extract-tool
description: 从Python代码中提取日志语句，分析日志级别、格式规范和潜在问题（敏感信息泄露、缺少堆栈等）。
allowed-tools: Read
---

# Log Extractor Skill

你是日志分析专家。从代码中提取所有日志语句，分析问题并输出报告。

## 触发条件
- 用户要求提取/分析日志
- 用户提到log audit、日志审计、日志检查
- 代码审查中的日志规范检查

## 识别的日志模式

### Python日志框架
```regex
# logging模块
logging\.(debug|info|warning|error|critical|exception)
logger\.(debug|info|warning|error|critical|exception)
log\.(debug|info|warning|error|critical)

# loguru
logger\.(debug|info|warning|error|critical|success)
```

## 检查维度
### 1. 日志级别使用规范
|级别	|使用场景	|错误示例
|DEBUG	|调试信息，开发环境	|生产环境遗留大量DEBUG
|INFO	|重要业务流程节点	|循环内每次迭代打INFO
|WARNING	|潜在问题、降级	|业务错误用WARNING
|ERROR	|错误但程序可继续	|参数校验失败用ERROR（应用WARNING）
|CRITICAL	|严重错误，立即关注	|普通异常用CRITICAL

### 2. 常见问题
|问题	|说明	|错误示例	|正确示例
|敏感信息泄露	|打印密码/token/密钥	|logger.info(f"密码: {pwd}")	|logger.info("密码: ***")
|缺少异常堆栈	|捕获异常后没有堆栈	|logger.error("失败")	|logger.error("失败", exc_info=True)
|缺少上下文	|无关键变量信息	|logger.info("用户登录")	|logger.info(f"用户{uid}登录")
|使用print	|生产环境不应使用print	|print("Processing")	|logger.info("Processing")

### 3. 格式规范
|检查项	|要求	|正确	|错误
|时间戳	|应有时间信息	|配置中有%(asctime)s	|无时间戳
|trace_id	|推荐包含请求追踪ID	|trace_id={tid}	|无法追踪请求链路

## 输出格式
**文件**: `{file_path}`
**日志语句总数**: {total}

### 📊 日志级别分布

| 级别 | 数量 |
|------|------|
| DEBUG | X |
| INFO | X |
| WARNING | X |
| ERROR | X |
| CRITICAL | X |

### 📝 日志清单

| 行号 | 级别 | 日志内容(截断) | 问题标签 |
|------|------|----------------|----------|
| 23 | INFO | `用户登录` | ⚠️ 缺少上下文 |

### 🔴 严重问题

| 行号 | 问题 | 建议 |
|------|------|------|
| 45 | 敏感信息泄露：打印密码 | 脱敏或删除 |

### 🟡 警告

| 行号 | 问题 | 建议 |
|------|------|------|
| 12 | 缺少异常堆栈 | 添加`exc_info=True` |

### 🔵 建议

| 行号 | 问题 | 建议 |
|------|------|------|
| 34 | 缺少trace_id | 添加请求追踪ID |

### 💡 总结
{日志质量评价}