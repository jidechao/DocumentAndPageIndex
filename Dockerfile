# PageIndex RAG MCP服务器 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements_mcp.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_mcp.txt

# 复制应用代码
COPY mcp_server.py ./
COPY rag_config.yaml ./
COPY rag/ ./rag/
COPY pageindex/ ./pageindex/

# 创建索引目录（将通过volume挂载）
RUN mkdir -p /app/indexes/trees

# 暴露HTTP端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/mcp', headers={'Accept': 'text/event-stream'})" || exit 1

# 启动命令（默认使用HTTP模式）
CMD ["python", "mcp_server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
