# RAG系统错误处理和重试机制

本文档描述RAG系统的错误处理策略和重试机制。

## 概述

RAG系统实现了完善的错误处理和重试机制，确保在面对临时性错误（如网络问题、API速率限制）时能够自动恢复，同时为用户提供清晰的错误消息和解决建议。

## 错误类型

系统定义了以下异常类层次结构（位于 `rag/exceptions.py`）：

```python
RAGException                    # 基础异常类
├── DocumentProcessingError     # 文档处理错误
├── LLMAPIError                # LLM API调用错误
├── IndexLoadError             # 索引加载错误
└── ConfigurationError         # 配置错误
```

### 1. ConfigurationError（配置错误）

**触发条件：**
- 配置文件不存在或格式错误
- 缺少必需的配置项
- 环境变量未设置
- LLM客户端创建失败

**用户建议：**
- 检查配置文件路径和格式
- 确认所有必需字段已配置
- 验证环境变量已正确设置

### 2. DocumentProcessingError（文档处理错误）

**触发条件：**
- 文件不存在或无法读取
- 文件格式不支持
- PageIndex处理失败

**用户建议：**
- 确认文件路径正确
- 检查文件格式是否为PDF或Markdown
- 验证文件未损坏

### 3. LLMAPIError（LLM API调用错误）

**触发条件：**
- API密钥无效或过期
- 网络连接失败
- API请求超时
- 速率限制超限
- 模型不存在或无权访问

**用户建议：**
根据具体错误类型，系统会提供针对性的建议（见下文"用户友好的错误消息"部分）

### 4. IndexLoadError（索引加载错误）

**触发条件：**
- 索引文件不存在
- 索引文件格式错误
- JSON解析失败

**用户建议：**
- 确认已运行离线索引流程
- 检查索引文件路径配置
- 验证索引文件格式正确

## 重试机制

### retry_with_backoff 装饰器

系统提供了带指数退避的重试装饰器，用于处理临时性错误。

**位置：** `rag/utils/retry.py`

**特性：**
- 指数退避：每次重试的延迟时间呈指数增长
- 可配置的重试次数和延迟参数
- 详细的日志记录
- 自动异常包装

**参数：**
```python
@retry_with_backoff(
    max_retries=3,           # 最大重试次数
    initial_delay=1.0,       # 初始延迟时间（秒）
    backoff_factor=2.0,      # 退避因子
    exceptions=(Exception,), # 需要重试的异常类型
    logger=None             # 日志记录器
)
```

**延迟计算：**
```
第1次重试延迟: initial_delay * (backoff_factor ^ 0) = 1.0秒
第2次重试延迟: initial_delay * (backoff_factor ^ 1) = 2.0秒
第3次重试延迟: initial_delay * (backoff_factor ^ 2) = 4.0秒
```

**使用示例：**
```python
from rag.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, initial_delay=1.0)
def call_external_api():
    # API调用代码
    pass
```

### LLM API调用包装器

所有LLM API调用都通过 `call_llm_with_retry` 函数进行，该函数自动应用重试机制。

**位置：** `rag/utils/llm_wrapper.py`

**特性：**
- 自动重试（默认3次）
- 指数退避延迟
- 详细的错误日志
- 特定异常类型处理（APIError, APIConnectionError, RateLimitError, APITimeoutError）

**使用示例：**
```python
from rag.utils.llm_wrapper import call_llm_with_retry

response = call_llm_with_retry(
    model="gpt-4o-2024-11-20",
    prompt="你的提示词",
    api_key="your-api-key",
    base_url=None,
    temperature=0,
    max_retries=3,
    initial_delay=1.0
)
```

## 日志记录

### 日志级别

系统使用标准的Python logging模块，支持以下日志级别：

- **DEBUG**: 详细的调试信息（API调用参数、响应长度等）
- **INFO**: 一般信息（成功的操作、重试成功等）
- **WARNING**: 警告信息（重试尝试、非致命错误等）
- **ERROR**: 错误信息（失败的操作、异常详情等）

### 日志配置

使用 `setup_logger` 函数配置日志记录器：

```python
from rag.utils.retry import setup_logger

# 创建日志记录器
logger = setup_logger("rag.mymodule", level=logging.INFO)

# 使用日志记录器
logger.info("操作成功")
logger.warning("警告信息")
logger.error("错误信息")
```

### 日志输出示例

```
2025-11-11 18:22:32 - rag.llm - WARNING - 函数 _call_api 执行失败（第 1/3 次尝试）
2025-11-11 18:22:32 - rag.llm - WARNING - 错误: Connection timeout
2025-11-11 18:22:32 - rag.llm - WARNING - 将在 1.00 秒后重试...
2025-11-11 18:22:33 - rag.llm - INFO - 函数 _call_api 在第 2 次尝试后成功执行
```

## 用户友好的错误消息

系统提供 `get_user_friendly_error_message` 函数，将技术错误转换为用户友好的消息。

**位置：** `rag/utils/llm_wrapper.py`

### 错误消息映射

#### 1. API密钥错误
**技术错误：** "Invalid API key", "authentication failed", "unauthorized"

**用户消息：**
```
API密钥验证失败。请检查：
1. 环境变量中的API密钥是否正确设置
2. API密钥是否有效且未过期
3. 如果使用自定义提供者，请确认base_url和api_key配置正确
```

#### 2. 网络连接错误
**技术错误：** "connection error", "network error"

**用户消息：**
```
网络连接失败。请检查：
1. 网络连接是否正常
2. 如果使用自定义提供者，请确认base_url是否正确
3. 防火墙或代理设置是否阻止了连接
```

#### 3. 速率限制错误
**技术错误：** "rate limit", "too many requests"

**用户消息：**
```
API请求速率超限。建议：
1. 等待几分钟后重试
2. 减少并发请求数量
3. 考虑升级API服务计划
```

#### 4. 超时错误
**技术错误：** "timeout"

**用户消息：**
```
API请求超时。建议：
1. 检查网络连接稳定性
2. 稍后重试
3. 如果问题持续，可能是服务端负载过高
```

#### 5. 模型不存在错误
**技术错误：** "model not found", "model does not exist"

**用户消息：**
```
指定的模型不存在或无权访问。请检查：
1. 配置文件中的model_name是否正确
2. 您的API密钥是否有权访问该模型
3. 模型名称拼写是否正确
```

## 主流程错误处理

### 离线索引流程（run_rag_index.py）

```python
try:
    # 执行索引流程
    ...
except ConfigurationError as e:
    # 配置错误处理
    print(f"配置错误: {str(e)}")
except LLMAPIError as e:
    # LLM API错误处理
    print(get_user_friendly_error_message(e))
except RAGException as e:
    # 其他RAG错误
    print(f"错误: {str(e)}")
except Exception as e:
    # 未预期的错误
    print(f"未预期的错误: {str(e)}")
```

### 在线搜索流程（run_rag_qa.py）

```python
try:
    # 执行问答流程
    ...
except IndexLoadError as e:
    # 索引加载错误处理
    print(f"索引加载失败: {str(e)}")
    print("建议: 确认已运行 run_rag_index.py 生成索引")
except LLMAPIError as e:
    # LLM API错误处理
    print(get_user_friendly_error_message(e))
except RAGException as e:
    # 其他RAG错误
    print(f"错误: {str(e)}")
```

## 最佳实践

### 1. 使用适当的重试参数

根据不同的场景调整重试参数：

```python
# 快速失败（用于测试）
call_llm_with_retry(..., max_retries=1, initial_delay=0.5)

# 标准配置（推荐）
call_llm_with_retry(..., max_retries=3, initial_delay=1.0)

# 容错性强（生产环境）
call_llm_with_retry(..., max_retries=5, initial_delay=2.0)
```

### 2. 记录详细日志

在关键操作处添加日志记录：

```python
logger.info(f"开始处理文档: {doc_name}")
try:
    result = process_document(doc_path)
    logger.info(f"文档处理成功: {doc_name}")
except Exception as e:
    logger.error(f"文档处理失败: {doc_name}, 错误: {str(e)}")
    raise
```

### 3. 提供清晰的错误上下文

抛出异常时包含足够的上下文信息：

```python
try:
    tree_index = load_tree_index(doc_id)
except FileNotFoundError:
    raise IndexLoadError(
        f"树形索引文件不存在: {doc_id}_structure.json\n"
        f"请确认已运行离线索引流程"
    )
```

### 4. 优雅降级

在非关键功能失败时，提供降级方案：

```python
try:
    description = generate_description(tree_structure)
except LLMAPIError as e:
    logger.warning(f"描述生成失败，使用默认描述: {e}")
    description = "文档描述生成失败"
```

## 测试

运行测试脚本验证错误处理和重试机制：

```bash
python test_retry_mechanism.py
```

测试覆盖：
- 重试成功场景
- 重试失败场景
- 立即成功场景
- 指数退避延迟验证
- 用户友好错误消息生成

## 故障排查

### 问题：重试次数过多导致响应缓慢

**解决方案：**
- 减少 `max_retries` 参数
- 增加 `initial_delay` 以避免过快重试
- 检查网络连接稳定性

### 问题：日志输出过多

**解决方案：**
- 调整日志级别为 WARNING 或 ERROR
- 使用日志过滤器
- 配置日志输出到文件而非控制台

### 问题：错误消息不够详细

**解决方案：**
- 启用 DEBUG 日志级别
- 查看完整的异常堆栈
- 检查日志文件获取更多上下文

## 相关文件

- `rag/exceptions.py` - 异常类定义
- `rag/utils/retry.py` - 重试机制实现
- `rag/utils/llm_wrapper.py` - LLM调用包装器
- `test_retry_mechanism.py` - 测试脚本
- `run_rag_index.py` - 离线索引主流程
- `run_rag_qa.py` - 在线搜索主流程
