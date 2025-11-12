# Docker部署指南

本文档提供PageIndex RAG MCP服务的Docker部署详细说明。

## 文件说明

- `Dockerfile`: Docker镜像构建文件
- `docker-compose.yml`: Docker Compose配置文件
- `.dockerignore`: Docker构建时忽略的文件列表

## 快速开始

### 使用Docker Compose（推荐）

1. 确保已安装Docker和Docker Compose
2. 创建`.env`文件并设置API密钥：
   ```bash
   CHATGPT_API_KEY=your_api_key_here
   ```
3. 启动服务：
   ```bash
   docker-compose up -d
   ```
4. 查看日志：
   ```bash
   docker-compose logs -f
   ```

### 使用Docker命令

1. 构建镜像：
   ```bash
   docker build -t pageindex-rag-mcp .
   ```

2. 运行容器：
   ```bash
   docker run -d \
     --name pageindex-rag-mcp \
     -p 8000:8000 \
     -e CHATGPT_API_KEY=your_api_key \
     -v $(pwd)/indexes:/app/indexes \
     pageindex-rag-mcp
   ```

## 配置说明

### 环境变量

- `CHATGPT_API_KEY`: LLM API密钥（必需）
- `PYTHONUNBUFFERED`: Python输出缓冲设置（已在Dockerfile中设置）

### 卷挂载

- `./indexes:/app/indexes`: 索引文件目录（必需）
- `./rag_config.yaml:/app/rag_config.yaml`: 配置文件（可选）
- `./logs:/app/logs`: 日志目录（可选）

### 端口映射

- `8000:8000`: HTTP服务端口

## 验证部署

1. 检查容器状态：
   ```bash
   docker ps | grep pageindex-rag-mcp
   ```

2. 测试HTTP端点：
   ```bash
   curl -H "Accept: text/event-stream" http://localhost:8000/mcp
   ```

3. 查看健康检查状态：
   ```bash
   docker inspect pageindex-rag-mcp | grep -A 10 Health
   ```

## 与Claude Desktop集成

在Claude Desktop配置文件中添加：

```json
{
  "mcpServers": {
    "pageindex-rag": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## 故障排除

### 容器无法启动

1. 查看日志：
   ```bash
   docker logs pageindex-rag-mcp
   ```

2. 检查配置：
   ```bash
   docker exec pageindex-rag-mcp cat /app/rag_config.yaml
   ```

### 索引文件找不到

1. 检查卷挂载：
   ```bash
   docker inspect pageindex-rag-mcp | grep -A 10 Mounts
   ```

2. 验证索引文件：
   ```bash
   docker exec pageindex-rag-mcp ls -la /app/indexes
   ```

### 网络连接问题

1. 检查端口映射：
   ```bash
   docker port pageindex-rag-mcp
   ```

2. 测试容器内部连接：
   ```bash
   docker exec pageindex-rag-mcp curl http://localhost:8000/mcp
   ```

## 生产环境建议

1. **使用环境变量管理敏感信息**
   - 不要在配置文件中硬编码API密钥
   - 使用Docker secrets或环境变量

2. **配置资源限制**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

3. **启用日志轮转**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

4. **使用反向代理**
   - 配置Nginx或Traefik作为反向代理
   - 启用HTTPS
   - 添加访问控制

5. **监控和告警**
   - 使用Prometheus监控容器指标
   - 配置健康检查告警
   - 集成日志聚合系统

## 更新部署

1. 拉取最新代码
2. 重新构建镜像：
   ```bash
   docker-compose build
   ```
3. 重启服务：
   ```bash
   docker-compose up -d
   ```

## 清理

停止并删除容器：
```bash
docker-compose down

# 或使用Docker命令
docker stop pageindex-rag-mcp
docker rm pageindex-rag-mcp
```

删除镜像：
```bash
docker rmi pageindex-rag-mcp
```

## 参考资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [README_MCP.md](./README_MCP.md) - MCP服务完整文档
