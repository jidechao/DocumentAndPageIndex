#!/usr/bin/env python3
"""
PageIndex RAG MCP服务器

这是一个基于Model Context Protocol (MCP)的服务器，将PageIndex RAG系统的
文档搜索和树搜索功能暴露为MCP工具，使其能够与Claude Desktop、Cline等
AI助手工具无缝集成。

主要功能：
- Document_Search: 根据用户查询搜索相关文档，返回文档ID列表
- Tree_Search: 在指定文档中搜索相关内容块，返回详细的文本片段

支持的传输协议：
- STDIO: 适合本地工具集成（默认）
- HTTP: 适合Web部署和远程访问
- SSE: 兼容旧版MCP客户端

使用示例：
    # STDIO模式（默认）
    python mcp_server.py
    
    # HTTP模式
    python mcp_server.py --transport http --port 8000
    
    # 自定义配置文件
    python mcp_server.py --config custom_config.yaml

作者: PageIndex Team
版本: 1.0.0
"""
import argparse
import logging
from typing import Annotated, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量（从.env文件读取API密钥等配置）
load_dotenv()

from fastmcp import FastMCP
from rag.config.config_manager import ConfigManager
from rag.online.query_understanding import QueryUnderstanding
from rag.online.doc_searcher import DocSearcher
from rag.online.tree_searcher import TreeSearcher
from rag.exceptions import LLMAPIError, IndexLoadError, ConfigurationError

# 配置日志系统，输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 降低 Uvicorn 的日志级别，避免显示关闭时的超时警告
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)

# 创建FastMCP服务器实例
# 服务器名称将显示在MCP客户端中
mcp = FastMCP("PageIndex RAG")

# 全局变量存储RAG模块实例
# 这些模块在服务器启动时初始化，并在整个生命周期中复用
config = None  # 配置管理器
query_understanding = None  # 查询理解模块
doc_searcher = None  # 文档搜索模块
tree_searcher = None  # 树搜索模块


def initialize_rag_modules(config_path: str = "rag_config.yaml"):
    """
    初始化RAG模块
    
    这个函数负责加载配置文件并初始化所有必需的RAG模块。
    它会在服务器启动时被调用一次，初始化后的模块实例会被
    存储在全局变量中供工具函数使用。
    
    初始化步骤：
    1. 加载配置文件（rag_config.yaml）
    2. 创建QueryUnderstanding实例（用于查询重写）
    3. 创建DocSearcher实例（用于文档搜索）
    4. 创建TreeSearcher实例（用于树搜索）
    5. 预加载目录索引到内存（提高搜索性能）
    
    Args:
        config_path: 配置文件路径，默认为"rag_config.yaml"
        
    Raises:
        ConfigurationError: 配置文件不存在或格式错误
        IndexLoadError: 目录索引文件加载失败
        
    Note:
        这个函数会修改全局变量，因此不是线程安全的。
        但由于它只在服务器启动时调用一次，这不会造成问题。
    """
    global config, query_understanding, doc_searcher, tree_searcher
    
    logger.info(f"Loading configuration from {config_path}")
    # 加载配置文件，包含LLM设置、路径配置等
    config = ConfigManager(config_path)
    
    logger.info("Initializing RAG modules")
    # 初始化查询理解模块，用于将用户查询重写为优化的搜索查询
    query_understanding = QueryUnderstanding(config)
    # 初始化文档搜索模块，用于在目录索引中搜索相关文档
    doc_searcher = DocSearcher(config)
    # 初始化树搜索模块，用于在文档树中搜索相关节点
    tree_searcher = TreeSearcher(config)
    
    logger.info("Loading directory index")
    # 预加载目录索引到内存，避免每次搜索时重复读取文件
    # 这会显著提高搜索性能，特别是在处理大量请求时
    doc_searcher.load_directory_index()
    
    logger.info("RAG modules initialized successfully")


# Pydantic模型定义
# 这些模型用于定义Tree_Search工具的返回值结构
# FastMCP会自动将这些模型转换为JSON Schema供客户端使用

class Chunk(BaseModel):
    """
    文档块模型
    
    表示从文档树中提取的一个内容块。每个块对应树结构中的一个节点，
    包含节点ID和该节点的文本内容。
    
    Attributes:
        node_id: 节点的唯一标识符（如"0010"），用于在树结构中定位节点
        text: 节点的文本内容，可能包含标题、段落、列表等
        
    Example:
        {
            "node_id": "0010",
            "text": "## 安装\n\n```bash\npip install -r requirements.txt\n```"
        }
    """
    node_id: str
    text: str


class DocumentChunks(BaseModel):
    """
    文档及其块的模型
    
    表示一个文档及其相关内容块的集合。Tree_Search工具会为每个
    相关文档返回一个DocumentChunks实例。
    
    Attributes:
        doc_name: 文档名称（如"README.md"），从树索引中提取
        chunks: 该文档中相关的内容块列表，按相关性排序
        
    Example:
        {
            "doc_name": "README.md",
            "chunks": [
                {
                    "node_id": "0010",
                    "text": "## 安装\n\n..."
                },
                {
                    "node_id": "0011",
                    "text": "## 使用\n\n..."
                }
            ]
        }
    """
    doc_name: str
    chunks: List[Chunk]


@mcp.tool
async def document_search(
    query: Annotated[str, Field(description="用户查询问题")],
    k: Annotated[int, Field(default=3, ge=1, description="返回的最大文档数量")]
) -> dict:
    """
    搜索相关文档
    
    根据用户查询，首先进行查询理解和重写，然后在目录索引中搜索相关文档。
    返回重写后的查询和相关文档ID列表。
    
    Args:
        query: 用户查询问题
        k: 返回的最大文档数量，默认为3
        
    Returns:
        包含rewrite_query和relvant_doc_id的字典
    """
    try:
        logger.info(f"Document search: query='{query}', k={k}")
        
        # 步骤1: 查询重写
        # 使用LLM将用户的自然语言查询转换为优化的搜索查询
        # 这可以提高搜索的准确性和相关性
        rewritten_query = query_understanding.rewrite_query(query)
        logger.info(f"Rewritten query: '{rewritten_query}'")
        
        # 步骤2: 搜索文档
        # 在目录索引中搜索与重写查询相关的文档
        # 返回的doc_ids按相关性分数排序（最相关的在前）
        doc_ids = doc_searcher.search_documents(rewritten_query)
        logger.info(f"Found {len(doc_ids)} documents: {doc_ids}")
        
        # 步骤3: 限制返回数量
        # 只返回前K个最相关的文档，避免返回过多结果
        doc_ids = doc_ids[:k]
        
        # 步骤4: 构造并返回结果
        # 返回重写后的查询和相关文档ID列表
        # 重写后的查询可以用于后续的Tree_Search
        result = {
            "rewrite_query": rewritten_query,
            "relvant_doc_id": doc_ids
        }
        logger.info(f"Document search completed: {len(doc_ids)} documents returned")
        return result
        
    except LLMAPIError as e:
        # LLM API调用失败（如网络错误、API密钥无效、速率限制等）
        logger.error(f"LLM API error in document_search: {str(e)}")
        raise Exception(f"查询理解失败: {str(e)}")
    except IndexLoadError as e:
        # 索引文件加载失败（如文件不存在、格式错误等）
        logger.error(f"Index load error in document_search: {str(e)}")
        raise Exception(f"索引加载失败: {str(e)}")
    except Exception as e:
        # 其他未预期的错误
        logger.error(f"Unexpected error in document_search: {str(e)}", exc_info=True)
        raise Exception(f"文档搜索失败: {str(e)}")


@mcp.tool
async def tree_search(
    rewrite_query: Annotated[str, Field(description="重写后的查询")],
    relvant_doc_id: Annotated[List[str], Field(description="相关文档ID列表")]
) -> List[DocumentChunks]:
    """
    在文档树中搜索相关节点
    
    根据重写后的查询和文档ID列表，在每个文档的树索引中搜索相关节点，
    并提取节点的文本内容。
    
    Args:
        rewrite_query: 重写后的查询
        relvant_doc_id: 相关文档ID列表
        
    Returns:
        包含文档名称和相关块的列表
    """
    try:
        logger.info(f"Tree search: query='{rewrite_query}', docs={relvant_doc_id}")
        
        # 存储所有文档的搜索结果
        results = []
        
        # 遍历每个文档ID，在其树索引中搜索相关节点
        for doc_id in relvant_doc_id:
            try:
                # 步骤1: 加载树索引
                # 每个文档都有一个对应的树索引文件（doc_id_structure.json）
                # 树索引包含文档的层次结构和每个节点的内容
                tree_index = tree_searcher.load_tree_index(doc_id)
                doc_name = tree_index.get('doc_name', doc_id)
                logger.info(f"Processing document: {doc_name}")
                
                # 步骤2: 搜索相关节点
                # 使用LLM在树结构中搜索与查询相关的节点
                # 返回的node_ids按相关性排序
                node_ids = tree_searcher.search_nodes(rewrite_query, tree_index)
                logger.info(f"Found {len(node_ids)} nodes in {doc_name}: {node_ids}")
                
                # 步骤3: 提取节点文本
                if node_ids:
                    chunks = []
                    # 构建node_id到节点对象的映射，方便快速查找
                    node_map = tree_searcher._build_node_map(tree_index['structure'])
                    
                    # 遍历每个相关节点，提取其文本内容
                    for node_id in node_ids:
                        if node_id in node_map:
                            node = node_map[node_id]
                            # 提取text字段（节点的实际内容）
                            text = node.get('text', '')
                            if text:
                                # 创建Chunk对象，包含节点ID和文本
                                chunks.append(Chunk(node_id=node_id, text=text))
                    
                    # 步骤4: 添加到结果列表
                    # 只有当找到有效的chunks时才添加该文档
                    if chunks:
                        results.append(DocumentChunks(
                            doc_name=doc_name,
                            chunks=chunks
                        ))
                        logger.info(f"Added {len(chunks)} chunks from {doc_name}")
                        
            except IndexLoadError as e:
                # 树索引文件加载失败（如文件不存在）
                # 记录警告但继续处理其他文档
                logger.warning(f"Failed to load tree index for {doc_id}: {str(e)}")
                continue
            except Exception as e:
                # 处理单个文档时发生错误
                # 记录错误但继续处理其他文档
                logger.error(f"Error processing doc {doc_id}: {str(e)}")
                continue
        
        logger.info(f"Tree search completed: {len(results)} documents with chunks")
        return results
        
    except Exception as e:
        # 整个树搜索过程中发生未预期的错误
        logger.error(f"Unexpected error in tree_search: {str(e)}", exc_info=True)
        raise Exception(f"树搜索失败: {str(e)}")


def parse_arguments():
    """
    解析命令行参数
    
    支持的参数：
    - --config: 配置文件路径
    - --transport: 传输协议（stdio/http/sse）
    - --host: HTTP/SSE服务器主机地址
    - --port: HTTP/SSE服务器端口
    
    Returns:
        argparse.Namespace: 解析后的参数对象
        
    Example:
        # STDIO模式（默认）
        python mcp_server.py
        
        # HTTP模式
        python mcp_server.py --transport http --port 8000
        
        # 自定义配置文件
        python mcp_server.py --config custom_config.yaml
    """
    parser = argparse.ArgumentParser(
        description='PageIndex RAG MCP服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='rag_config.yaml',
        help='配置文件路径 (默认: rag_config.yaml)'
    )
    
    parser.add_argument(
        '--transport',
        type=str,
        choices=['stdio', 'http', 'sse'],
        default='stdio',
        help='传输协议 (默认: stdio)\n'
             'stdio: 标准输入输出，适合本地工具集成\n'
             'http: HTTP协议，适合Web部署\n'
             'sse: Server-Sent Events，兼容旧版MCP客户端'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='HTTP/SSE服务器主机 (默认: 0.0.0.0)\n'
             '0.0.0.0表示监听所有网络接口'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='HTTP/SSE服务器端口 (默认: 8000)'
    )
    
    return parser.parse_args()


def main():
    """
    主函数
    
    服务器启动流程：
    1. 解析命令行参数
    2. 初始化RAG模块（加载配置、创建模块实例、预加载索引）
    3. 根据指定的传输协议启动MCP服务器
    
    支持的传输协议：
    - stdio: 通过标准输入输出通信，适合本地工具集成（如Claude Desktop）
    - http: 通过HTTP协议通信，适合Web部署和远程访问
    - sse: 通过Server-Sent Events通信，兼容旧版MCP客户端
    
    错误处理：
    - ConfigurationError: 配置文件错误，服务器无法启动
    - 其他异常: 记录详细错误信息并退出
    
    Note:
        服务器启动后会一直运行，直到收到中断信号（Ctrl+C）或发生致命错误。
    """
    args = parse_arguments()
    
    try:
        # 步骤1: 初始化RAG模块
        # 这会加载配置文件、创建所有必需的模块实例、预加载索引
        initialize_rag_modules(args.config)
        
        # 步骤2: 启动MCP服务器
        logger.info(f"Starting MCP server with {args.transport} transport")
        
        # 根据指定的传输协议启动服务器
        if args.transport == 'stdio':
            # STDIO模式：通过标准输入输出通信
            # 适合作为子进程运行，由父进程（如Claude Desktop）管理
            mcp.run(transport='stdio')
        elif args.transport == 'http':
            # HTTP模式：启动HTTP服务器
            # 客户端通过HTTP请求调用工具
            mcp.run(transport='http', host=args.host, port=args.port)
        elif args.transport == 'sse':
            # SSE模式：启动SSE服务器
            # 支持服务器推送事件，兼容旧版MCP客户端
            mcp.run(transport='sse', host=args.host, port=args.port)
            
    except KeyboardInterrupt:
        # 用户按Ctrl+C退出，这是正常的退出方式
        logger.info("MCP server stopped by user")
    except ConfigurationError as e:
        # 配置错误：配置文件不存在、格式错误、必需字段缺失等
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        # 其他未预期的错误
        logger.error(f"Failed to start MCP server: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
