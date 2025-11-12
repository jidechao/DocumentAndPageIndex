# RAG问答系统测试文档

本目录包含RAG问答系统的所有测试代码，包括单元测试和集成测试。

## 测试结构

```
tests/
├── pdfs/                           # 测试用的PDF文档
├── results/                        # 测试结果输出
├── test_offline_integration.py     # 离线索引集成测试
├── test_online_integration.py      # 在线搜索集成测试
├── run_all_tests.py               # 运行所有测试的主脚本
└── README.md                       # 本文档
```

根目录下的单元测试文件：
- `test_document_processor.py` - DocumentProcessor单元测试
- `test_description_generator.py` - DescriptionGenerator单元测试
- `test_query_understanding.py` - QueryUnderstanding单元测试
- `test_doc_searcher.py` - DocSearcher单元测试
- `test_tree_searcher.py` - TreeSearcher单元测试
- `test_answer_generator.py` - AnswerGenerator单元测试
- `test_mcp_server.py` - MCP服务器单元测试和集成测试

## 前提条件

1. **环境变量配置**
   ```bash
   # 在.env文件中设置
   CHATGPT_API_KEY=your_api_key_here
   ```

2. **配置文件**
   - 确保根目录下存在`rag_config.yaml`配置文件

3. **测试数据**
   - `tests/pdfs/`目录下需要有测试用的PDF文档
   - 对于在线搜索测试，需要先运行离线索引生成目录索引文件

## 运行测试

### 运行所有测试

```bash
python tests/run_all_tests.py
```

这将依次运行所有单元测试和集成测试，并在最后显示测试摘要。

### 运行单个单元测试

```bash
# DocumentProcessor测试
python test_document_processor.py

# DescriptionGenerator测试
python test_description_generator.py

# QueryUnderstanding测试
python test_query_understanding.py

# DocSearcher测试
python test_doc_searcher.py

# TreeSearcher测试
python test_tree_searcher.py

# AnswerGenerator测试
python test_answer_generator.py

# MCP服务器测试
python tests/test_mcp_server.py
```

### 运行集成测试

```bash
# 离线索引集成测试
python tests/test_offline_integration.py

# 在线搜索集成测试（需要先运行离线索引）
python tests/test_online_integration.py
```

## 测试说明

### 单元测试

单元测试专注于测试各个模块的核心功能：

1. **DocumentProcessor测试**
   - 测试初始化
   - 测试doc_id生成
   - 测试树形索引路径生成
   - 测试文档处理基本功能

2. **DescriptionGenerator测试**
   - 测试初始化
   - 测试文档描述生成
   - 测试使用真实树形索引生成描述

3. **QueryUnderstanding测试**
   - 测试问题理解和重写功能
   - 验证重写后的问题质量

4. **DocSearcher测试**
   - 测试目录索引加载
   - 测试文档搜索功能
   - 测试不同类型的查询

5. **TreeSearcher测试**
   - 测试树形索引加载
   - 测试节点搜索
   - 测试节点文本提取
   - 测试节点映射构建
   - 测试树结构简化

6. **AnswerGenerator测试**
   - 测试初始化
   - 测试答案生成
   - 测试无法回答消息
   - 测试上下文不足时的处理

7. **MCP服务器测试**
   - 测试服务器初始化和工具注册
   - 测试RAG模块加载
   - 测试Document_Search工具（正常查询、K参数、空结果）
   - 测试Tree_Search工具（单文档、多文档、不存在文档）
   - 测试端到端集成流程

### 集成测试

集成测试验证端到端的工作流程：

1. **离线索引集成测试**
   - 单个文档的完整索引流程
   - 多个文档的批量索引流程
   - 验证生成的索引文件

2. **在线搜索集成测试**
   - 有相关文档时的完整搜索流程
   - 无相关文档时的处理
   - 多个不同类型问题的测试

## 测试数据

### PDF文档

`tests/pdfs/`目录包含以下测试文档：
- `2023-annual-report-truncated.pdf` - 美联储年度报告（截断版）
- `earthmover.pdf` - 工程机械文档
- 其他测试PDF文档

### 预期结果

测试会验证以下内容：
- 树形索引文件正确生成
- 文档描述准确且有意义
- 目录索引包含所有文档信息
- 问题重写保留核心意图
- 文档搜索返回相关文档
- 节点搜索定位正确内容
- 答案生成基于检索内容

## 故障排除

### API调用失败

如果遇到API调用失败：
1. 检查`CHATGPT_API_KEY`是否正确设置
2. 检查网络连接
3. 检查API配额是否充足

### 测试文件不存在

如果提示测试文件不存在：
1. 确保在项目根目录运行测试
2. 检查`tests/pdfs/`目录是否包含PDF文件

### 目录索引不存在

如果在线搜索测试提示目录索引不存在：
1. 先运行离线索引流程：`python run_rag_index.py --dir_path tests/pdfs`
2. 或者先运行离线索引集成测试

## 测试覆盖

当前测试覆盖以下需求：

- ✓ 需求1: 离线索引阶段 - 文档处理
- ✓ 需求2: 离线索引阶段 - 文件目录索引构建
- ✓ 需求3: 在线搜索阶段 - 问题理解和重写
- ✓ 需求4: 在线搜索阶段 - Doc-Search文档检索
- ✓ 需求5: 在线搜索阶段 - Tree-Search节点检索
- ✓ 需求6: 在线搜索阶段 - 答案生成
- ✓ 需求7: 系统配置和依赖管理
- ✓ 需求8: 自定义模型提供者支持
- ✓ MCP服务需求: MCP服务器初始化、工具注册、Document_Search和Tree_Search工具功能

## 贡献指南

添加新测试时：
1. 单元测试放在根目录，命名为`test_<module_name>.py`
2. 集成测试放在`tests/`目录
3. 更新`tests/run_all_tests.py`以包含新测试
4. 更新本README文档

## 注意事项

1. 测试会调用真实的LLM API，会产生API费用
2. 集成测试可能需要较长时间运行
3. 某些测试依赖于之前测试生成的文件
4. 建议按顺序运行测试：单元测试 → 离线索引集成测试 → 在线搜索集成测试
