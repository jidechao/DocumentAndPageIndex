# RAG问答系统使用文档

## 📑 目录

- [简介](#简介)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [离线索引阶段](#离线索引阶段)
- [在线搜索阶段](#在线搜索阶段)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [高级用法](#高级用法)

---

## 简介

基于PageIndex的RAG（检索增强生成）问答系统是一个**无向量数据库**、**基于推理**的智能问答系统。该系统通过构建文档的层次化树形索引，模拟人类专家阅读和理解文档的方式，实现精准的文档检索和问题回答。

### 核心特性

- **无向量数据库**: 使用文档结构和LLM推理进行检索，而非向量搜索
- **无分块**: 文档按自然章节组织，而非人工分块
- **类人检索**: 模拟人类专家导航和提取知识的方式
- **透明可解释**: 基于推理的检索过程，可追溯和可解释

### 工作流程

系统分为两个主要阶段：

1. **离线索引阶段**: 预处理文档，构建树形索引和文件目录索引
2. **在线搜索阶段**: 处理用户问题，检索相关内容并生成答案

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG问答系统                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  离线索引阶段:                                                │
│    1. 文档处理 → 生成树形索引                                │
│    2. 描述生成 → 为每个文档生成摘要                          │
│    3. 目录构建 → 聚合所有文档信息                            │
│                                                               │
│  在线搜索阶段:                                                │
│    1. 问题理解 → 重写和规范化用户问题                        │
│    2. Doc-Search → 查找相关文档                              │
│    3. Tree-Search → 定位文档中的相关节点                     │
│    4. 答案生成 → 基于检索内容生成答案                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```


### 2. 配置API密钥

在项目根目录创建`.env`文件，添加您的API密钥：

```bash
CHATGPT_API_KEY=your_openai_key_here
```

如果使用自定义LLM提供者（如阿里云、智谱等），还需要配置`rag_config.yaml`文件中的`base_url`参数。

### 3. 准备文档

将需要索引的PDF或Markdown文档放在一个目录中，例如`./documents/`。

### 4. 运行离线索引

```bash
# 处理单个文档
python run_rag_index.py --file_path ./documents/report.pdf

# 批量处理目录中的所有文档
python run_rag_index.py --dir_path ./documents
```

### 5. 开始问答

```bash
# 交互式问答模式
python run_rag_qa.py

# 单次问答
python run_rag_qa.py --query "公司2023年的营收是多少？"
```

---

## 离线索引阶段

离线索引阶段负责预处理文档并构建索引，这是使用RAG系统的第一步。

### 基本用法

#### 处理单个文档

```bash
python run_rag_index.py --file_path /path/to/document.pdf
```

#### 批量处理文档

```bash
python run_rag_index.py --dir_path /path/to/documents/
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--file_path` | 单个文档的路径（PDF或Markdown） | 无 |
| `--dir_path` | 包含多个文档的目录路径 | 无 |
| `--config` | 配置文件路径 | `rag_config.yaml` |

### 输出文件

离线索引阶段会生成以下文件：

1. **树形索引文件**: `./indexes/trees/{doc_id}_structure.json`
   - 每个文档的层次化树形结构
   - 包含节点ID、标题、摘要、页面索引等信息

2. **文件目录索引**: `./indexes/directory_index.json`
   - 所有文档的聚合索引
   - 包含doc_id、文档名称和文档描述

### 示例输出

**树形索引结构示例**:

```json
{
  "doc_id": "abc123",
  "doc_name": "2023-annual-report.pdf",
  "doc_description": "This document discusses the company's financial performance in 2023...",
  "structure": [
    {
      "title": "Financial Overview",
      "node_id": "0001",
      "start_index": 1,
      "end_index": 10,
      "summary": "Overview of financial performance...",
      "text": "Full text content...",
      "nodes": [
        {
          "title": "Revenue Analysis",
          "node_id": "0002",
          "start_index": 3,
          "end_index": 5,
          "summary": "Detailed revenue breakdown...",
          "text": "Full text content..."
        }
      ]
    }
  ]
}
```


**文件目录索引示例**:

```json
{
  "documents": [
    {
      "doc_id": "abc123",
      "doc_name": "2023-annual-report.pdf",
      "doc_description": "This document discusses the company's financial performance in 2023..."
    },
    {
      "doc_id": "def456",
      "doc_name": "product-manual.pdf",
      "doc_description": "Technical manual for product installation and maintenance..."
    }
  ]
}
```

### 处理流程

1. **文档处理**: 调用PageIndex处理PDF/Markdown文件，生成树形索引
2. **描述生成**: 使用LLM为每个文档生成一句话描述
3. **目录构建**: 聚合所有文档信息，生成文件目录索引

### 注意事项

- 首次处理大量文档可能需要较长时间，请耐心等待
- 确保API密钥配置正确，否则会导致处理失败
- 如果某个文档处理失败，系统会记录错误并继续处理其他文档
- 生成的索引文件会保存在`./indexes/`目录下

---

## 在线搜索阶段

在线搜索阶段负责处理用户问题并生成答案。

### 基本用法

#### 交互式问答模式

```bash
python run_rag_qa.py
```

在交互式模式下，您可以连续提问：

```
欢迎使用RAG问答系统！
输入 'exit' 或 'quit' 退出程序

请输入您的问题: 公司2023年的营收是多少？
[系统处理中...]
答案: 根据2023年年度报告，公司全年营收为...

请输入您的问题: 主要产品有哪些？
[系统处理中...]
答案: 公司的主要产品包括...

请输入您的问题: exit
再见！
```

#### 单次问答模式

```bash
python run_rag_qa.py --query "公司2023年的营收是多少？"
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--query` | 用户问题（单次问答模式） | 无 |
| `--config` | 配置文件路径 | `rag_config.yaml` |

### 处理流程

在线搜索阶段包含以下步骤：

1. **问题理解**: 
   - 分析用户的原始问题
   - 识别口语化表达和模糊表述
   - 重写为更规范的检索查询

2. **Doc-Search（文档搜索）**:
   - 加载文件目录索引
   - 使用LLM判断哪些文档与问题相关
   - 返回相关文档的doc_id列表

3. **Tree-Search（树搜索）**:
   - 对每个相关文档加载树形索引
   - 使用LLM定位文档中的相关节点
   - 提取相关节点的文本内容

4. **答案生成**:
   - 组装检索到的内容和用户问题
   - 调用LLM生成答案
   - 返回答案给用户

### 无法回答的情况

如果系统无法找到相关信息，会返回友好提示：

```
很抱歉，根据我掌握知识库内容，尚无法回答这个问题。
我会尽快学习我所欠缺的知识，以便更好的为您服务。
```

这种情况通常发生在：
- Doc-Search未找到相关文档
- Tree-Search未找到相关节点
- 问题超出知识库范围


---

## 配置说明

系统使用`rag_config.yaml`文件进行配置。以下是详细的配置参数说明。

### 配置文件结构

```yaml
# LLM配置
llm:
  provider: "openai"
  model: "gpt-4o-2024-11-20"
  api_key: "${CHATGPT_API_KEY}"
  base_url: null
  temperature: 0

# 索引路径配置
paths:
  indexes_dir: "./indexes"
  trees_dir: "./indexes/trees"
  directory_index: "./indexes/directory_index.json"

# PageIndex配置
pageindex:
  toc_check_page_num: 20
  max_page_num_each_node: 10
  max_token_num_each_node: 20000
  if_add_node_id: "yes"
  if_add_node_summary: "yes"
  if_add_doc_description: "yes"
  if_add_node_text: "yes"
```

### LLM配置参数

#### `provider`
- **说明**: LLM提供者类型
- **可选值**: `"openai"` 或 `"custom"`
- **默认值**: `"openai"`
- **用途**: 
  - `"openai"`: 使用OpenAI官方API
  - `"custom"`: 使用自定义LLM提供者（如阿里云、智谱等）

#### `model`
- **说明**: 使用的模型名称
- **示例**: 
  - OpenAI: `"gpt-4o-2024-11-20"`, `"gpt-4-turbo"`
  - 阿里云: `"qwen-max"`, `"qwen-plus"`
  - 智谱: `"glm-4"`, `"glm-4-plus"`
- **默认值**: `"gpt-4o-2024-11-20"`

#### `api_key`
- **说明**: API密钥
- **格式**: `"${ENVIRONMENT_VARIABLE}"` 或直接填写密钥
- **推荐**: 使用环境变量，避免密钥泄露
- **示例**: `"${CHATGPT_API_KEY}"`

#### `base_url`
- **说明**: 自定义LLM提供者的API端点
- **默认值**: `null`（使用OpenAI官方端点）
- **示例**:
  - 阿里云: `"https://dashscope.aliyuncs.com/compatible-mode/v1"`
  - 智谱: `"https://open.bigmodel.cn/api/paas/v4"`
  - 本地部署: `"http://localhost:8000/v1"`

#### `temperature`
- **说明**: 生成温度参数，控制输出的随机性
- **范围**: 0-1
- **默认值**: `0`
- **建议**: 
  - 0: 最确定性，适合问答系统
  - 0.7-0.9: 更有创造性，适合内容生成

### 路径配置参数

#### `indexes_dir`
- **说明**: 索引文件的根目录
- **默认值**: `"./indexes"`

#### `trees_dir`
- **说明**: 树形索引文件的存储目录
- **默认值**: `"./indexes/trees"`

#### `directory_index`
- **说明**: 文件目录索引的路径
- **默认值**: `"./indexes/directory_index.json"`

### PageIndex配置参数

#### `toc_check_page_num`
- **说明**: 检查目录的页数
- **默认值**: `20`
- **用途**: 在文档前N页中查找目录

#### `max_page_num_each_node`
- **说明**: 每个节点的最大页数
- **默认值**: `10`
- **用途**: 控制树节点的粒度

#### `max_token_num_each_node`
- **说明**: 每个节点的最大token数
- **默认值**: `20000`
- **用途**: 控制节点内容的长度

#### `if_add_node_id`
- **说明**: 是否添加节点ID
- **可选值**: `"yes"` 或 `"no"`
- **默认值**: `"yes"`

#### `if_add_node_summary`
- **说明**: 是否添加节点摘要
- **可选值**: `"yes"` 或 `"no"`
- **默认值**: `"yes"`

#### `if_add_doc_description`
- **说明**: 是否添加文档描述
- **可选值**: `"yes"` 或 `"no"`
- **默认值**: `"yes"`

#### `if_add_node_text`
- **说明**: 是否添加节点文本内容
- **可选值**: `"yes"` 或 `"no"`
- **默认值**: `"yes"`


### 配置示例

#### 使用OpenAI官方API

```yaml
llm:
  provider: "openai"
  model: "gpt-4o-2024-11-20"
  api_key: "${CHATGPT_API_KEY}"
  base_url: null
  temperature: 0
```

`.env`文件：
```bash
CHATGPT_API_KEY=sk-your-openai-key-here
```

#### 使用阿里云通义千问

```yaml
llm:
  provider: "custom"
  model: "qwen-max"
  api_key: "${DASHSCOPE_API_KEY}"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  temperature: 0
```

`.env`文件：
```bash
DASHSCOPE_API_KEY=sk-your-dashscope-key-here
```

#### 使用智谱AI

```yaml
llm:
  provider: "custom"
  model: "glm-4-plus"
  api_key: "${ZHIPU_API_KEY}"
  base_url: "https://open.bigmodel.cn/api/paas/v4"
  temperature: 0
```

`.env`文件：
```bash
ZHIPU_API_KEY=your-zhipu-key-here
```

#### 使用本地部署的模型

```yaml
llm:
  provider: "custom"
  model: "llama-3-70b"
  api_key: "not-needed"
  base_url: "http://localhost:8000/v1"
  temperature: 0
```

---

## 常见问题

### Q1: 如何选择合适的LLM模型？

**A**: 建议使用以下模型：

- **推荐**: GPT-4o、GPT-4-turbo（OpenAI）
- **国内替代**: 通义千问Max、智谱GLM-4-Plus
- **性价比**: GPT-4o-mini、通义千问Plus

选择标准：
- 推理能力强，能够理解复杂的文档结构
- 支持较长的上下文窗口（至少32K tokens）
- 响应速度快，适合实时问答

### Q2: 处理文档时出现API错误怎么办？

**A**: 常见原因和解决方法：

1. **API密钥无效**
   - 检查`.env`文件中的API密钥是否正确
   - 确认密钥有足够的额度

2. **网络连接问题**
   - 检查网络连接
   - 如果在国内，可能需要配置代理或使用国内LLM提供者

3. **速率限制**
   - 系统已内置重试机制
   - 如果频繁触发限制，考虑升级API套餐或降低并发

4. **模型不存在**
   - 检查配置文件中的`model`参数是否正确
   - 确认该模型在您的API账户中可用

### Q3: 如何提高检索准确性？

**A**: 以下方法可以提高检索准确性：

1. **优化文档质量**
   - 确保文档有清晰的结构和目录
   - 避免扫描版PDF，使用文字版PDF

2. **调整PageIndex参数**
   - 减小`max_page_num_each_node`，增加树的深度
   - 增加`toc_check_page_num`，更好地识别目录

3. **改进问题表述**
   - 使用清晰、具体的问题
   - 包含关键词和上下文信息

4. **使用更强的模型**
   - 升级到GPT-4o或其他高性能模型

### Q4: 系统支持哪些文档格式？

**A**: 目前支持：

- **PDF文档**: 推荐使用文字版PDF，扫描版PDF效果较差
- **Markdown文档**: 需要使用`#`标记标题层级

未来计划支持：
- Word文档（.docx）
- HTML文档
- 纯文本文档

### Q5: 如何处理大量文档？

**A**: 处理大量文档的建议：

1. **批量索引**
   ```bash
   python run_rag_index.py --dir_path ./documents
   ```

2. **分批处理**
   - 将文档分成多个批次
   - 避免一次性处理过多文档

3. **监控进度**
   - 系统会输出处理进度
   - 查看日志文件了解详细信息

4. **增量更新**
   - 新增文档时，只需索引新文档
   - 系统会自动更新文件目录索引

### Q6: 为什么有时候无法回答问题？

**A**: 可能的原因：

1. **问题超出知识库范围**
   - 确认相关文档已被索引
   - 检查文档内容是否包含答案

2. **问题表述不清**
   - 尝试重新表述问题
   - 提供更多上下文信息

3. **检索失败**
   - Doc-Search未找到相关文档
   - Tree-Search未找到相关节点
   - 可以查看日志了解详细原因

4. **文档质量问题**
   - 文档结构混乱
   - 文本提取不完整


### Q7: 如何查看系统运行日志？

**A**: 系统日志包含以下信息：

1. **控制台输出**
   - 实时显示处理进度
   - 显示错误和警告信息

2. **日志文件**
   - 位于`./logs/`目录
   - 包含详细的处理信息和错误堆栈

3. **调试模式**
   - 在代码中设置日志级别为DEBUG
   - 查看更详细的运行信息

### Q8: 系统的性能如何？

**A**: 性能指标参考：

1. **离线索引阶段**
   - 单个文档（100页）: 约2-5分钟
   - 批量处理（10个文档）: 约20-50分钟
   - 主要耗时在LLM API调用

2. **在线搜索阶段**
   - 单次问答: 约5-15秒
   - 包含问题理解、文档搜索、树搜索和答案生成

3. **优化建议**
   - 使用更快的模型（如GPT-4o-mini）
   - 减少节点数量（调整PageIndex参数）
   - 使用本地部署的模型

### Q9: 如何备份和迁移索引？

**A**: 索引文件管理：

1. **备份索引**
   ```bash
   # 备份整个索引目录
   cp -r ./indexes ./indexes_backup
   
   # 或者只备份特定文件
   cp ./indexes/directory_index.json ./backup/
   cp -r ./indexes/trees ./backup/trees
   ```

2. **迁移索引**
   - 将`./indexes`目录复制到新环境
   - 确保配置文件中的路径正确
   - 无需重新索引文档

3. **版本控制**
   - 建议将索引文件加入`.gitignore`
   - 索引文件较大，不适合版本控制
   - 可以版本控制配置文件和代码

### Q10: 系统是否支持多语言？

**A**: 多语言支持情况：

1. **当前支持**
   - 中文文档和问答
   - 英文文档和问答
   - 其他语言取决于LLM模型能力

2. **最佳实践**
   - 使用与文档语言相同的语言提问
   - 混合语言文档可能影响检索效果
   - 选择支持多语言的LLM模型

---

## 高级用法

### 自定义Prompt模板

系统的Prompt模板定义在各个模块中，您可以根据需要自定义：

1. **问题理解模块** (`rag/online/query_understanding.py`)
2. **Doc-Search模块** (`rag/online/doc_searcher.py`)
3. **Tree-Search模块** (`rag/online/tree_searcher.py`)
4. **答案生成模块** (`rag/online/answer_generator.py`)

### 集成到现有系统

#### Python API调用

```python
from rag.config import ConfigManager
from rag.offline import DocumentProcessor, DescriptionGenerator, DirectoryIndexBuilder
from rag.online import QueryUnderstanding, DocSearcher, TreeSearcher, AnswerGenerator

# 初始化配置
config = ConfigManager("rag_config.yaml")

# 离线索引
processor = DocumentProcessor(config)
doc_info = processor.process_single_document("document.pdf")

generator = DescriptionGenerator(config)
description = generator.generate_description(doc_info['tree_structure'])

builder = DirectoryIndexBuilder(config)
builder.build_directory_index({doc_info['doc_id']: doc_info})

# 在线搜索
query_understanding = QueryUnderstanding(config)
rewritten_query = query_understanding.rewrite_query("用户问题")

doc_searcher = DocSearcher(config)
doc_ids = doc_searcher.search_documents(rewritten_query)

tree_searcher = TreeSearcher(config)
all_context = ""
for doc_id in doc_ids:
    tree_structure = tree_searcher.load_tree_index(doc_id)
    node_ids = tree_searcher.search_nodes(rewritten_query, tree_structure)
    context = tree_searcher.extract_node_text(node_ids, tree_structure)
    all_context += context

answer_generator = AnswerGenerator(config)
answer = answer_generator.generate_answer("用户问题", all_context)
print(answer)
```

#### Web API封装

您可以使用Flask或FastAPI将系统封装为Web服务：

```python
from flask import Flask, request, jsonify
from rag.config import ConfigManager
from rag.online import QueryUnderstanding, DocSearcher, TreeSearcher, AnswerGenerator

app = Flask(__name__)
config = ConfigManager("rag_config.yaml")

# 初始化模块
query_understanding = QueryUnderstanding(config)
doc_searcher = DocSearcher(config)
tree_searcher = TreeSearcher(config)
answer_generator = AnswerGenerator(config)

@app.route('/api/qa', methods=['POST'])
def qa():
    data = request.json
    query = data.get('query')
    
    # 处理问题
    rewritten_query = query_understanding.rewrite_query(query)
    doc_ids = doc_searcher.search_documents(rewritten_query)
    
    if not doc_ids:
        return jsonify({
            'answer': answer_generator.get_no_answer_message()
        })
    
    # 检索内容
    all_context = ""
    for doc_id in doc_ids:
        tree_structure = tree_searcher.load_tree_index(doc_id)
        node_ids = tree_searcher.search_nodes(rewritten_query, tree_structure)
        context = tree_searcher.extract_node_text(node_ids, tree_structure)
        all_context += context
    
    if not all_context:
        return jsonify({
            'answer': answer_generator.get_no_answer_message()
        })
    
    # 生成答案
    answer = answer_generator.generate_answer(query, all_context)
    
    return jsonify({
        'answer': answer,
        'doc_ids': doc_ids
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```


### 性能优化

#### 1. 缓存策略

```python
from functools import lru_cache
import json

class CachedDocSearcher(DocSearcher):
    @lru_cache(maxsize=128)
    def load_directory_index(self, index_path=None):
        """缓存文件目录索引"""
        return super().load_directory_index(index_path)

class CachedTreeSearcher(TreeSearcher):
    @lru_cache(maxsize=256)
    def load_tree_index(self, doc_id):
        """缓存树形索引"""
        return super().load_tree_index(doc_id)
```

#### 2. 并发处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_documents_async(file_paths):
    """并发处理多个文档"""
    processor = DocumentProcessor(config)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                executor,
                processor.process_single_document,
                file_path
            )
            for file_path in file_paths
        ]
        results = await asyncio.gather(*tasks)
    
    return results

# 使用
file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = asyncio.run(process_documents_async(file_paths))
```

#### 3. 批量查询优化

```python
def batch_qa(queries, batch_size=10):
    """批量处理多个问题"""
    results = []
    
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i+batch_size]
        batch_results = []
        
        for query in batch:
            # 处理单个问题
            answer = process_query(query)
            batch_results.append({
                'query': query,
                'answer': answer
            })
        
        results.extend(batch_results)
    
    return results
```

### 错误处理和重试

系统已内置错误处理和重试机制，但您也可以自定义：

```python
from rag.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=5, initial_delay=2)
def custom_llm_call(prompt):
    """自定义LLM调用，带重试机制"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### 监控和日志

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/rag_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.info("开始处理文档")
logger.error("处理失败", exc_info=True)
```

---

## 完整使用示例

### 示例1: 财务报告问答

```bash
# 1. 索引财务报告
python run_rag_index.py --dir_path ./financial_reports

# 2. 开始问答
python run_rag_qa.py

# 示例问题：
# - 公司2023年的总营收是多少？
# - 研发费用占营收的比例是多少？
# - 主要的风险因素有哪些？
# - 现金流状况如何？
```

### 示例2: 技术文档查询

```bash
# 1. 索引技术文档
python run_rag_index.py --dir_path ./technical_docs

# 2. 单次查询
python run_rag_qa.py --query "如何配置数据库连接？"

# 更多示例问题：
python run_rag_qa.py --query "系统支持哪些认证方式？"
python run_rag_qa.py --query "如何进行性能优化？"
python run_rag_qa.py --query "API的速率限制是多少？"
```

### 示例3: 学术论文分析

```bash
# 1. 索引学术论文
python run_rag_index.py --file_path ./papers/research_paper.pdf

# 2. 交互式问答
python run_rag_qa.py

# 示例问题：
# - 这篇论文的主要贡献是什么？
# - 使用了哪些实验方法？
# - 实验结果如何？
# - 与其他方法相比有什么优势？
```

---

## 故障排除

### 问题: 导入模块失败

```bash
ModuleNotFoundError: No module named 'rag'
```

**解决方法**:
```bash
# 确保在项目根目录运行
cd /path/to/project

# 重新安装依赖
pip install -r requirements.txt

# 检查Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题: API调用超时

```bash
openai.APITimeoutError: Request timed out
```

**解决方法**:
1. 检查网络连接
2. 增加超时时间（在代码中配置）
3. 使用国内LLM提供者
4. 配置代理

### 问题: 索引文件损坏

```bash
JSONDecodeError: Expecting value
```

**解决方法**:
```bash
# 删除损坏的索引文件
rm -rf ./indexes/trees/*
rm ./indexes/directory_index.json

# 重新索引
python run_rag_index.py --dir_path ./documents
```

### 问题: 内存不足

```bash
MemoryError: Unable to allocate array
```

**解决方法**:
1. 减小`max_token_num_each_node`参数
2. 分批处理文档
3. 增加系统内存
4. 使用更小的模型

---

## 系统要求

### 硬件要求

- **CPU**: 2核心以上
- **内存**: 4GB以上（推荐8GB）
- **存储**: 根据文档数量，建议预留10GB以上空间

### 软件要求

- **Python**: 3.8或更高版本
- **操作系统**: Windows、macOS、Linux
- **网络**: 稳定的互联网连接（用于API调用）

### 依赖包

详见`requirements.txt`文件：

```
openai==1.101.0
pymupdf==1.26.4
PyPDF2==3.0.1
tiktoken==0.11.0
pyyaml==6.0.2
python-dotenv==1.1.0
```

---

## 更新日志

### v1.0.0 (2024-01-15)

- ✅ 实现离线索引阶段
  - 文档处理模块
  - 描述生成模块
  - 目录索引构建模块

- ✅ 实现在线搜索阶段
  - 问题理解模块
  - Doc-Search模块
  - Tree-Search模块
  - 答案生成模块

- ✅ 配置管理
  - 支持YAML配置文件
  - 支持环境变量
  - 支持自定义LLM提供者

- ✅ 错误处理和重试机制
  - LLM API调用重试
  - 详细的错误日志
  - 友好的错误提示

---

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 报告问题

在GitHub Issues中提交问题时，请包含：
- 问题描述
- 复现步骤
- 错误日志
- 系统环境信息

### 提交代码

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

---

## 许可证

本项目基于PageIndex开源项目开发，遵循相同的许可证。

---

## 联系方式

- **项目主页**: [PageIndex GitHub](https://github.com/VectifyAI/PageIndex)
- **文档**: [PageIndex Docs](https://docs.pageindex.ai)
- **Discord**: [加入社区](https://discord.com/invite/VuXuf29EUj)

---

## 致谢

本项目基于[PageIndex](https://github.com/VectifyAI/PageIndex)开发，感谢PageIndex团队的开源贡献。

---

**祝您使用愉快！如有问题，请随时联系我们。** 🚀
