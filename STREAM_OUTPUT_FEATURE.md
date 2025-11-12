# 流式输出功能说明

## 概述

为了改善用户体验，RAG问答系统现在支持流式输出功能。在等待答案生成时，系统会：
1. 显示处理进度提示
2. 实时流式输出答案内容

## 新增功能

### 1. 等待提示

在非详细模式（`--verbose`未启用）下，系统会显示简洁的处理进度：

```
正在理解问题... ✓
正在搜索相关文档... ✓ (找到 2 个)
正在搜索相关内容... ✓
正在生成答案...

答案:
[流式输出答案内容...]
```

### 2. 流式输出

答案会实时逐字输出，而不是等待完整答案生成后一次性显示。这样用户可以：
- 更快看到答案开始
- 实时了解生成进度
- 获得更好的交互体验

## 技术实现

### 异步API

使用OpenAI的异步API实现流式输出：

```python
from openai import AsyncOpenAI

async def call_llm_with_retry_stream(...):
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True  # 启用流式输出
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
```

### 答案生成器

`AnswerGenerator`类新增了流式生成方法：

```python
async def generate_answer_stream(self, query: str, context: str):
    """流式生成答案"""
    prompt = self._build_answer_prompt(query, context)
    
    async for chunk in call_llm_with_retry_stream(
        model=self.model,
        prompt=prompt,
        api_key=self.api_key,
        base_url=self.base_url,
        temperature=self.temperature
    ):
        yield chunk
```

### RAG问答系统

`RAGQASystem`类新增了异步流式问答方法：

```python
async def answer_question_stream(self, original_query: str):
    """流式回答用户问题"""
    # 步骤1-3: 问题理解、文档搜索、节点搜索
    # 显示进度提示
    
    # 步骤4: 流式生成答案
    async for chunk in self.answer_generator.generate_answer_stream(query, context):
        yield chunk
```

## 使用方法

### 交互式模式

```bash
python run_rag_qa.py
```

系统会自动使用流式输出，答案会实时显示。

### 单次问答模式

```bash
python run_rag_qa.py --query "你的问题"
```

答案会流式输出到终端。

### 详细模式

```bash
python run_rag_qa.py --verbose
```

在详细模式下，会显示完整的处理步骤信息，同时保持流式输出答案。

## 兼容性

### 保留的非流式方法

为了向后兼容，保留了原有的非流式方法：

```python
def answer_question(self, original_query: str) -> str:
    """非流式回答（返回完整答案）"""
    # 原有实现保持不变
```

这个方法仍然可以在需要完整答案字符串的场景中使用（如测试、批处理等）。

### 异步包装

对于同步调用场景，使用`asyncio.run()`包装异步函数：

```python
def interactive_mode(qa_system: RAGQASystem):
    """交互式问答模式（包装异步函数）"""
    asyncio.run(interactive_mode_async(qa_system))
```

## 测试

运行流式输出测试：

```bash
python test_stream_output.py
```

这会测试基本的流式答案生成功能。

## 优势

1. **更好的用户体验**
   - 减少等待焦虑
   - 实时反馈
   - 更自然的交互

2. **更快的首字节时间**
   - 用户更快看到答案开始
   - 感知性能提升

3. **进度可见性**
   - 清晰的处理步骤提示
   - 了解系统正在做什么

4. **保持响应性**
   - 即使生成长答案也不会卡顿
   - 可以随时中断（Ctrl+C）

## 注意事项

1. **网络要求**
   - 流式输出需要稳定的网络连接
   - 网络中断会导致输出不完整

2. **错误处理**
   - 流式输出中的错误会立即显示
   - 不会等待完整响应

3. **日志记录**
   - 流式输出的内容不会自动记录到日志
   - 如需记录，需要在应用层实现

## 未来改进

1. **进度条**
   - 添加可视化进度条
   - 显示预估剩余时间

2. **取消功能**
   - 支持优雅地取消正在进行的生成
   - 保存部分结果

3. **重试机制**
   - 为流式输出添加重试支持
   - 处理网络中断恢复

4. **缓存**
   - 缓存流式输出结果
   - 支持重放和回顾
