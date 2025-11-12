# PageIndex RAG MCP服务

## 概述

PageIndex RAG MCP服务是一个基于Model Context Protocol (MCP)的服务，它将PageIndex RAG系统的文档搜索和树搜索功能暴露为MCP工具，使其能够与Claude Desktop、Cline等AI助手工具无缝集成。

### 主要功能

- **Document_Search**: 根据用户查询搜索相关文档，返回文档ID列表
- **Tree_Search**: 在指定文档中搜索相关内容块，返回详细的文本片段

### 技术特点

- 基于FastMCP框架构建
- 支持STDIO、HTTP、SSE三种传输协议
- 复用现有RAG模块（QueryUnderstanding、DocSearcher、TreeSearcher）
- 完整的错误处理和日志记录
- 支持流式响应

## 安装

### 前置要求

- Python 3.8+
- 已安装并配置好PageIndex RAG系统
- 已创建文档索引（directory_index.json和树索引文件）

### 安装依赖

```bash
# 安装基础RAG依赖
pip install -r requirements.txt

# 安装MCP服务依赖
pip install -r requirements_mcp.txt
```

### 配置

1. 确保`.env`文件中配置了LLM API密钥：

```bash
CHATGPT_API_KEY=your_api_key_here
```

2. （可选）在`rag_config.yaml`中配置MCP服务参数：

```yaml
mcp:
  transport: "stdio"  # 或 "http", "sse"
  host: "0.0.0.0"
  port: 8000
  log_level: "INFO"
```


## 启动服务

### STDIO模式（推荐用于本地工具集成）

```bash
python mcp_server.py
```

### HTTP模式（推荐用于Web部署）

```bash
python mcp_server.py --transport http --port 8000
```

### SSE模式（兼容旧版MCP客户端）

```bash
python mcp_server.py --transport sse --port 8000
```

### 命令行参数

```bash
python mcp_server.py --help
```

可用参数：
- `--config`: 配置文件路径（默认：rag_config.yaml）
- `--transport`: 传输协议（stdio/http/sse，默认：stdio）
- `--host`: HTTP/SSE服务器主机（默认：0.0.0.0）
- `--port`: HTTP/SSE服务器端口（默认：8000）


## Claude Desktop集成

### 配置文件位置

Claude Desktop的配置文件位置因操作系统而异：

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### STDIO模式配置（推荐）

STDIO模式适合本地开发和使用，配置简单且稳定。

**配置步骤**：

1. 找到或创建Claude Desktop配置文件（见上方路径）

2. 添加以下配置（参考 `claude_desktop_config_stdio.json`）：

```json
{
  "mcpServers": {
    "pageindex-rag": {
      "command": "python",
      "args": [
        "C:/path/to/your/project/mcp_server.py"
      ],
      "env": {
        "CHATGPT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. 修改配置：
   - 将 `C:/path/to/your/project/mcp_server.py` 替换为实际的绝对路径
   - 将 `your_api_key_here` 替换为你的API密钥
   - 如果使用虚拟环境，可以将 `python` 替换为虚拟环境中的Python路径

**Windows路径示例**：
```json
"args": ["D:/projects/pageindex-rag/mcp_server.py"]
```

**使用虚拟环境示例**：
```json
{
  "mcpServers": {
    "pageindex-rag": {
      "command": "D:/projects/pageindex-rag/.venv/Scripts/python.exe",
      "args": [
        "D:/projects/pageindex-rag/mcp_server.py"
      ],
      "env": {
        "CHATGPT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**注意事项**：
- 必须使用绝对路径
- Windows路径使用正斜杠 `/` 或双反斜杠 `\\`
- 确保Python可执行文件和mcp_server.py都可访问
- API密钥也可以通过系统环境变量设置，然后在配置中引用

### HTTP模式配置

HTTP模式适合远程部署或多客户端共享同一个服务实例。

**配置步骤**：

1. 先启动HTTP模式的MCP服务器：
```bash
python mcp_server.py --transport http --port 8000
```

2. 在Claude Desktop配置文件中添加（参考 `claude_desktop_config_http.json`）：

```json
{
  "mcpServers": {
    "pageindex-rag": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**远程服务器示例**：
```json
{
  "mcpServers": {
    "pageindex-rag": {
      "url": "http://your-server-ip:8000/mcp"
    }
  }
}
```

**注意事项**：
- 确保服务器在Claude Desktop启动前已经运行
- 如果使用远程服务器，确保网络可达且防火墙已开放端口
- HTTP模式需要服务器持续运行

### 验证集成

1. **保存配置文件**后，完全退出并重启Claude Desktop

2. 在Claude Desktop中开始新对话，询问：
   ```
   你有哪些可用的工具？
   ```

3. Claude应该能够看到以下工具：
   - `document_search`: 搜索相关文档
   - `tree_search`: 在文档树中搜索相关节点

4. 测试工具功能：
   ```
   请帮我搜索关于PageIndex安装的文档
   ```

### 故障排除

**问题1：Claude Desktop看不到工具**

解决方案：
- 检查配置文件路径是否正确
- 检查JSON格式是否正确（使用JSON验证器）
- 确保完全重启了Claude Desktop
- 查看Claude Desktop的日志文件（通常在配置文件同目录下）

**问题2：工具调用失败**

解决方案：
- STDIO模式：检查Python路径和mcp_server.py路径是否正确
- HTTP模式：确认服务器正在运行（访问 http://localhost:8000/mcp）
- 检查API密钥是否正确设置
- 查看mcp_server.py的日志输出

**问题3：找不到索引文件**

解决方案：
- 确保已运行索引生成脚本
- 检查 `indexes/directory_index.json` 文件是否存在
- 检查 `indexes/trees/` 目录下是否有树索引文件
- 在STDIO模式下，工作目录应该是项目根目录

### 配置文件示例

项目中提供了两个配置示例文件：

- `claude_desktop_config_stdio.json`: STDIO模式配置示例
- `claude_desktop_config_http.json`: HTTP模式配置示例

可以参考这些文件进行配置。


## 工具使用示例

### Document_Search工具

**功能**: 搜索与查询相关的文档

**参数**:
- `query` (string, 必需): 用户查询问题
- `k` (integer, 可选): 返回的最大文档数量，默认为3

**返回值**:
```json
{
  "rewrite_query": "重写后的查询",
  "relvant_doc_id": ["doc_id_1", "doc_id_2", "doc_id_3"]
}
```

**使用示例**:

在Claude Desktop中：
```
请帮我搜索关于PageIndex安装的文档
```

Claude会调用：
```json
{
  "tool": "document_search",
  "parameters": {
    "query": "PageIndex安装",
    "k": 3
  }
}
```

### Tree_Search工具

**功能**: 在指定文档中搜索相关内容块

**参数**:
- `rewrite_query` (string, 必需): 重写后的查询
- `relvant_doc_id` (array, 必需): 相关文档ID列表

**返回值**:
```json
[
  {
    "doc_name": "demo.pdf",
    "chunks": [
      {
        "node_id": "0010",
        "text": "文档内容片段..."
      }
    ]
  }
]
```

**使用示例**:

通常在Document_Search之后自动调用：
```json
{
  "tool": "tree_search",
  "parameters": {
    "rewrite_query": "PageIndex安装步骤",
    "relvant_doc_id": ["08ff78e753db0442", "d98d29785cdd803e"]
  }
}
```


## 完整工作流程示例

用户在Claude Desktop中提问：
```
PageIndex如何安装依赖？
```

Claude的处理流程：

1. **调用Document_Search**:
   ```json
   {
     "query": "PageIndex如何安装依赖",
     "k": 3
   }
   ```
   
   返回：
   ```json
   {
     "rewrite_query": "PageIndex如何安装依赖",
     "relvant_doc_id": ["08ff78e753db0442", "d98d29785cdd803e"]
   }
   ```

2. **调用Tree_Search**:
   ```json
   {
     "rewrite_query": "PageIndex如何安装依赖",
     "relvant_doc_id": ["08ff78e753db0442", "d98d29785cdd803e"]
   }
   ```
   
   返回：
   ```json
   [
     {
       "doc_name": "README.md",
       "chunks": [
         {
           "node_id": "0010",
           "text": "## 安装\n\n```bash\npip install -r requirements.txt\n```"
         }
       ]
     }
   ]
   ```

3. **Claude生成回答**:
   基于检索到的内容，Claude会生成一个完整的回答。


## 测试

### 使用FastMCP CLI测试

```bash
# 安装fastmcp CLI（如果还没安装）
pip install fastmcp

# 测试服务
fastmcp dev mcp_server.py
```

### 手动测试工具

```python
from fastmcp import FastMCP

# 创建测试客户端
client = FastMCP.create_client("mcp_server:mcp")

# 测试Document_Search
result = await client.call_tool(
    "document_search",
    {"query": "PageIndex安装", "k": 3}
)
print(result)

# 测试Tree_Search
result = await client.call_tool(
    "tree_search",
    {
        "rewrite_query": "PageIndex安装",
        "relvant_doc_id": ["08ff78e753db0442"]
    }
)
print(result)
```


## 故障排除

### 常见问题

**1. 服务启动失败**

检查：
- Python版本是否>=3.8
- 所有依赖是否已安装
- rag_config.yaml配置是否正确
- API密钥是否已设置

**2. Claude Desktop无法识别工具**

检查：
- claude_desktop_config.json配置是否正确
- 路径是否使用绝对路径
- 是否重启了Claude Desktop
- 查看Claude Desktop的日志文件

**3. 工具调用失败**

检查：
- 索引文件是否存在（directory_index.json和树索引）
- LLM API是否可访问
- 查看mcp_server.py的日志输出

**4. 找不到文档**

检查：
- 是否已运行索引生成脚本
- directory_index.json是否包含文档
- 树索引文件是否存在于indexes/trees/目录

### 日志查看

服务运行时会输出详细日志：

```
2024-01-01 10:00:00 - __main__ - INFO - Loading configuration from rag_config.yaml
2024-01-01 10:00:01 - __main__ - INFO - Initializing RAG modules
2024-01-01 10:00:02 - __main__ - INFO - Loading directory index
2024-01-01 10:00:03 - __main__ - INFO - RAG modules initialized successfully
2024-01-01 10:00:04 - __main__ - INFO - Starting MCP server with stdio transport
```


## Docker部署

Docker部署适合生产环境或需要隔离环境的场景。

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (可选)

### 方式1：使用Docker Compose（推荐）

**步骤1：准备环境变量**

创建 `.env` 文件（如果还没有）：
```bash
CHATGPT_API_KEY=your_api_key_here
```

**步骤2：启动服务**

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f mcp-server

# 停止服务
docker-compose down
```

**步骤3：验证服务**

```bash
# 检查容器状态
docker-compose ps

# 测试HTTP端点
curl -H "Accept: text/event-stream" http://localhost:8000/mcp
```

### 方式2：使用Docker命令

**步骤1：构建镜像**

```bash
docker build -t pageindex-rag-mcp .
```

**步骤2：运行容器**

```bash
# Windows PowerShell
docker run -d `
  --name pageindex-rag-mcp `
  -p 8000:8000 `
  -e CHATGPT_API_KEY=your_api_key `
  -v ${PWD}/indexes:/app/indexes `
  -v ${PWD}/rag_config.yaml:/app/rag_config.yaml `
  pageindex-rag-mcp

# Linux/macOS
docker run -d \
  --name pageindex-rag-mcp \
  -p 8000:8000 \
  -e CHATGPT_API_KEY=your_api_key \
  -v $(pwd)/indexes:/app/indexes \
  -v $(pwd)/rag_config.yaml:/app/rag_config.yaml \
  pageindex-rag-mcp
```

**步骤3：管理容器**

```bash
# 查看日志
docker logs -f pageindex-rag-mcp

# 停止容器
docker stop pageindex-rag-mcp

# 启动容器
docker start pageindex-rag-mcp

# 删除容器
docker rm pageindex-rag-mcp
```

### Docker配置说明

**docker-compose.yml配置项**：

```yaml
version: '3.8'
services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pageindex-rag-mcp
    ports:
      - "8000:8000"              # 映射HTTP端口
    environment:
      - CHATGPT_API_KEY=${CHATGPT_API_KEY}  # 从.env文件读取
    volumes:
      - ./indexes:/app/indexes              # 挂载索引目录（必需）
      - ./rag_config.yaml:/app/rag_config.yaml  # 挂载配置文件
      - ./logs:/app/logs                    # 挂载日志目录（可选）
    restart: unless-stopped                 # 自动重启策略
    healthcheck:                            # 健康检查
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/mcp', headers={'Accept': 'text/event-stream'})"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**重要说明**：

1. **索引目录挂载**：必须挂载 `indexes` 目录，否则服务无法访问文档索引
2. **配置文件**：可以挂载自定义的 `rag_config.yaml`
3. **环境变量**：API密钥通过环境变量传递，不要硬编码在镜像中
4. **端口映射**：默认映射8000端口，可以修改为其他端口

### 与Claude Desktop集成

Docker部署的服务使用HTTP模式，配置方式：

```json
{
  "mcpServers": {
    "pageindex-rag": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

如果Docker运行在远程服务器：

```json
{
  "mcpServers": {
    "pageindex-rag": {
      "url": "http://your-server-ip:8000/mcp"
    }
  }
}
```

### 生产环境建议

1. **使用环境变量管理敏感信息**
   ```bash
   # 不要在docker-compose.yml中硬编码API密钥
   # 使用.env文件或系统环境变量
   ```

2. **配置反向代理**
   ```nginx
   # Nginx配置示例
   location /mcp {
       proxy_pass http://localhost:8000/mcp;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
   }
   ```

3. **启用HTTPS**
   ```bash
   # 使用Let's Encrypt或其他SSL证书
   # 在反向代理层配置HTTPS
   ```

4. **监控和日志**
   ```bash
   # 挂载日志目录
   -v ./logs:/app/logs
   
   # 使用日志聚合工具（如ELK、Loki等）
   ```

5. **资源限制**
   ```yaml
   # 在docker-compose.yml中添加资源限制
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
       reservations:
         cpus: '1'
         memory: 2G
   ```

### 故障排除

**问题1：容器启动失败**

```bash
# 查看详细日志
docker logs pageindex-rag-mcp

# 检查配置文件
docker exec pageindex-rag-mcp cat /app/rag_config.yaml

# 检查索引文件
docker exec pageindex-rag-mcp ls -la /app/indexes
```

**问题2：无法访问HTTP端点**

```bash
# 检查容器是否运行
docker ps | grep pageindex-rag-mcp

# 检查端口映射
docker port pageindex-rag-mcp

# 测试容器内部连接
docker exec pageindex-rag-mcp curl http://localhost:8000/mcp
```

**问题3：索引文件找不到**

```bash
# 确保索引目录已挂载
docker inspect pageindex-rag-mcp | grep -A 10 Mounts

# 检查索引文件权限
ls -la indexes/
```

## 性能优化

### 缓存策略

- 目录索引在服务启动时加载并缓存在内存中
- 树索引使用LRU缓存，最多缓存100个文档
- 建议为频繁访问的文档预热缓存

### 并发处理

- 服务支持异步处理多个请求
- HTTP模式下可以处理并发请求
- 建议根据硬件资源调整并发数

## 安全建议

1. **API密钥保护**
   - 使用环境变量存储API密钥
   - 不要在配置文件中硬编码密钥
   - 定期轮换API密钥

2. **访问控制**
   - HTTP模式下建议配置防火墙规则
   - 仅允许可信IP访问
   - 考虑添加身份验证

3. **输入验证**
   - 服务会自动验证所有输入参数
   - 限制查询长度防止滥用
   - 监控异常请求模式

## 更多资源

- [FastMCP文档](https://github.com/jlowin/fastmcp)
- [Model Context Protocol规范](https://modelcontextprotocol.io/)
- [Claude Desktop文档](https://claude.ai/desktop)
- [PageIndex RAG项目](./README.md)

## 许可证

本项目遵循与PageIndex RAG相同的许可证。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。
