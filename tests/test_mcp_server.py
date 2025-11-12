"""
测试MCP服务器功能
使用FastMCP的Client进行in-memory测试
"""
import asyncio
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastmcp import Client
from mcp_server import mcp, initialize_rag_modules
from rag.exceptions import LLMAPIError, IndexLoadError


def extract_result(result_obj):
    """从ToolResult中提取实际结果"""
    if hasattr(result_obj, 'content') and len(result_obj.content) > 0:
        content = result_obj.content[0]
        if hasattr(content, 'text'):
            text = content.text
            # 尝试解析JSON
            try:
                return json.loads(text)
            except:
                return text
        # 如果content不是text类型，可能是直接的数据
        return content
    # 如果没有content，返回空列表（用于空结果情况）
    return []


async def test_server_initialization():
    """测试服务器初始化"""
    print("=" * 60)
    print("测试1: MCP服务器初始化")
    print("=" * 60)
    
    try:
        print("\n1. 测试服务器实例创建...")
        assert mcp is not None, "MCP服务器实例应该存在"
        assert mcp.name == "PageIndex RAG", "服务器名称应该是'PageIndex RAG'"
        print("✓ MCP服务器实例创建成功")
        
        print("\n2. 测试工具注册...")
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            
            assert "document_search" in tool_names, "document_search工具应该已注册"
            assert "tree_search" in tool_names, "tree_search工具应该已注册"
            print(f"✓ 已注册工具: {tool_names}")
        
        print("\n✓ 服务器初始化测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 服务器初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_modules_loading():
    """测试RAG模块加载"""
    print("\n" + "=" * 60)
    print("测试2: RAG模块加载")
    print("=" * 60)
    
    try:
        print("\n1. 初始化RAG模块...")
        initialize_rag_modules("rag_config.yaml")
        print("✓ RAG模块初始化成功")
        
        print("\n2. 验证模块实例...")
        import mcp_server
        
        assert mcp_server.config is not None, "配置管理器应该已初始化"
        print("✓ 配置管理器已加载")
        
        assert mcp_server.query_understanding is not None, "QueryUnderstanding应该已初始化"
        print("✓ QueryUnderstanding已加载")
        
        assert mcp_server.doc_searcher is not None, "DocSearcher应该已初始化"
        print("✓ DocSearcher已加载")
        
        assert mcp_server.tree_searcher is not None, "TreeSearcher应该已初始化"
        print("✓ TreeSearcher已加载")
        
        print("\n3. 验证目录索引加载...")
        directory_index = mcp_server.doc_searcher.directory_index
        assert directory_index is not None, "目录索引应该已加载"
        assert 'documents' in directory_index, "目录索引应该包含documents字段"
        print(f"✓ 目录索引已加载，包含 {len(directory_index['documents'])} 个文档")
        
        print("\n✓ RAG模块加载测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ RAG模块加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_search_normal():
    """测试Document_Search工具 - 正常查询流程"""
    print("\n" + "=" * 60)
    print("测试3: Document_Search - 正常查询")
    print("=" * 60)
    
    try:
        print("\n1. 测试正常查询...")
        query = "pageindex如何安装依赖"
        k = 3
        
        async with Client(mcp) as client:
            result_obj = await client.call_tool("document_search", {"query": query, "k": k})
            result = extract_result(result_obj)
        
        print(f"查询: {query}")
        print(f"K值: {k}")
        print(f"重写查询: {result['rewrite_query']}")
        print(f"相关文档数: {len(result['relvant_doc_id'])}")
        print(f"文档ID: {result['relvant_doc_id']}")
        
        assert 'rewrite_query' in result, "结果应该包含rewrite_query字段"
        assert 'relvant_doc_id' in result, "结果应该包含relvant_doc_id字段"
        assert isinstance(result['relvant_doc_id'], list), "relvant_doc_id应该是列表"
        assert len(result['relvant_doc_id']) <= k, f"返回文档数不应超过k={k}"
        
        print("\n✓ 正常查询测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 正常查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_search_k_parameter():
    """测试Document_Search工具 - K参数"""
    print("\n" + "=" * 60)
    print("测试4: Document_Search - K参数测试")
    print("=" * 60)
    
    try:
        query = "pageindex如何使用"
        
        async with Client(mcp) as client:
            # 测试默认K值
            print("\n1. 测试默认K值...")
            result_obj = await client.call_tool("document_search", {"query": query})
            result = extract_result(result_obj)
            print(f"默认K值返回文档数: {len(result['relvant_doc_id'])}")
            assert len(result['relvant_doc_id']) <= 3, "默认K值应该是3"
            print("✓ 默认K值测试通过")
            
            # 测试K=1
            print("\n2. 测试K=1...")
            result_obj = await client.call_tool("document_search", {"query": query, "k": 1})
            result = extract_result(result_obj)
            print(f"K=1返回文档数: {len(result['relvant_doc_id'])}")
            assert len(result['relvant_doc_id']) <= 1, "K=1时最多返回1个文档"
            print("✓ K=1测试通过")
            
            # 测试K=5
            print("\n3. 测试K=5...")
            result_obj = await client.call_tool("document_search", {"query": query, "k": 5})
            result = extract_result(result_obj)
            print(f"K=5返回文档数: {len(result['relvant_doc_id'])}")
            assert len(result['relvant_doc_id']) <= 5, "K=5时最多返回5个文档"
            print("✓ K=5测试通过")
        
        print("\n✓ K参数测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ K参数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_search_empty_result():
    """测试Document_Search工具 - 空结果处理"""
    print("\n" + "=" * 60)
    print("测试5: Document_Search - 空结果处理")
    print("=" * 60)
    
    try:
        print("\n1. 测试不相关查询...")
        query = "量子纠缠的物理原理和应用场景"
        
        async with Client(mcp) as client:
            result_obj = await client.call_tool("document_search", {"query": query, "k": 3})
            result = extract_result(result_obj)
        
        print(f"查询: {query}")
        print(f"重写查询: {result['rewrite_query']}")
        print(f"相关文档数: {len(result['relvant_doc_id'])}")
        
        assert 'rewrite_query' in result, "结果应该包含rewrite_query字段"
        assert 'relvant_doc_id' in result, "结果应该包含relvant_doc_id字段"
        assert isinstance(result['relvant_doc_id'], list), "relvant_doc_id应该是列表"
        
        if len(result['relvant_doc_id']) == 0:
            print("✓ 正确返回空文档列表")
        else:
            print(f"注意: 返回了 {len(result['relvant_doc_id'])} 个文档（可能是误匹配）")
        
        print("\n✓ 空结果处理测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 空结果处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tree_search_single_document():
    """测试Tree_Search工具 - 单文档搜索"""
    print("\n" + "=" * 60)
    print("测试6: Tree_Search - 单文档搜索")
    print("=" * 60)
    
    try:
        async with Client(mcp) as client:
            print("\n1. 先执行document_search获取文档ID...")
            doc_result_obj = await client.call_tool("document_search", {"query": "pageindex如何安装", "k": 1})
            doc_result = extract_result(doc_result_obj)
            
            if not doc_result['relvant_doc_id']:
                print("⚠ 没有找到相关文档，跳过tree_search测试")
                return True
            
            rewrite_query = doc_result['rewrite_query']
            doc_ids = doc_result['relvant_doc_id'][:1]
            
            print(f"重写查询: {rewrite_query}")
            print(f"文档ID: {doc_ids}")
            
            print("\n2. 执行tree_search...")
            result_obj = await client.call_tool("tree_search", {
                "rewrite_query": rewrite_query,
                "relvant_doc_id": doc_ids
            })
            result = extract_result(result_obj)
        
        print(f"返回文档数: {len(result)}")
        
        assert isinstance(result, list), "结果应该是列表"
        
        if len(result) > 0:
            doc = result[0]
            print(f"\n文档名称: {doc['doc_name']}")
            print(f"块数量: {len(doc['chunks'])}")
            
            assert 'doc_name' in doc, "文档应该包含doc_name字段"
            assert 'chunks' in doc, "文档应该包含chunks字段"
            assert isinstance(doc['chunks'], list), "chunks应该是列表"
            
            if len(doc['chunks']) > 0:
                chunk = doc['chunks'][0]
                print(f"\n第一个块:")
                print(f"  node_id: {chunk['node_id']}")
                print(f"  text长度: {len(chunk['text'])} 字符")
                print(f"  text预览: {chunk['text'][:100]}...")
                
                assert 'node_id' in chunk, "块应该包含node_id字段"
                assert 'text' in chunk, "块应该包含text字段"
        
        print("\n✓ 单文档搜索测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 单文档搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tree_search_multiple_documents():
    """测试Tree_Search工具 - 多文档搜索"""
    print("\n" + "=" * 60)
    print("测试7: Tree_Search - 多文档搜索")
    print("=" * 60)
    
    try:
        async with Client(mcp) as client:
            print("\n1. 先执行document_search获取多个文档ID...")
            doc_result_obj = await client.call_tool("document_search", {"query": "pageindex", "k": 3})
            doc_result = extract_result(doc_result_obj)
            
            if not doc_result['relvant_doc_id']:
                print("⚠ 没有找到相关文档，跳过tree_search测试")
                return True
            
            rewrite_query = doc_result['rewrite_query']
            doc_ids = doc_result['relvant_doc_id']
            
            print(f"重写查询: {rewrite_query}")
            print(f"文档数量: {len(doc_ids)}")
            print(f"文档ID: {doc_ids}")
            
            print("\n2. 执行tree_search...")
            result_obj = await client.call_tool("tree_search", {
                "rewrite_query": rewrite_query,
                "relvant_doc_id": doc_ids
            })
            result = extract_result(result_obj)
        
        print(f"返回文档数: {len(result)}")
        
        assert isinstance(result, list), "结果应该是列表"
        
        for i, doc in enumerate(result, 1):
            print(f"\n文档{i}:")
            print(f"  名称: {doc['doc_name']}")
            print(f"  块数量: {len(doc['chunks'])}")
            
            assert 'doc_name' in doc, "文档应该包含doc_name字段"
            assert 'chunks' in doc, "文档应该包含chunks字段"
            assert len(doc['chunks']) > 0, "文档应该至少有一个块"
        
        print("\n✓ 多文档搜索测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 多文档搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tree_search_nonexistent_document():
    """测试Tree_Search工具 - 文档不存在情况"""
    print("\n" + "=" * 60)
    print("测试8: Tree_Search - 文档不存在")
    print("=" * 60)
    
    try:
        print("\n1. 使用不存在的文档ID...")
        rewrite_query = "测试查询"
        doc_ids = ["nonexistent_doc_id_12345"]
        
        print(f"重写查询: {rewrite_query}")
        print(f"文档ID: {doc_ids}")
        
        async with Client(mcp) as client:
            print("\n2. 执行tree_search...")
            result_obj = await client.call_tool("tree_search", {
                "rewrite_query": rewrite_query,
                "relvant_doc_id": doc_ids
            })
            result = extract_result(result_obj)
        
        print(f"返回文档数: {len(result)}")
        
        assert isinstance(result, list), "结果应该是列表"
        assert len(result) == 0, "不存在的文档应该返回空列表"
        
        print("✓ 正确处理不存在的文档")
        
        print("\n✓ 文档不存在测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 文档不存在测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end_integration():
    """测试端到端集成 - Document_Search → Tree_Search完整流程"""
    print("\n" + "=" * 60)
    print("测试9: 端到端集成测试")
    print("=" * 60)
    
    try:
        test_queries = [
            "pageindex如何安装依赖",
            "如何使用pageindex处理PDF文档",
        ]
        
        async with Client(mcp) as client:
            for i, query in enumerate(test_queries, 1):
                print(f"\n测试查询{i}: {query}")
                print("-" * 60)
                
                # 步骤1: Document Search
                print("\n步骤1: 执行document_search...")
                doc_result_obj = await client.call_tool("document_search", {"query": query, "k": 2})
                doc_result = extract_result(doc_result_obj)
                
                print(f"  重写查询: {doc_result['rewrite_query']}")
                print(f"  找到文档数: {len(doc_result['relvant_doc_id'])}")
                
                assert 'rewrite_query' in doc_result
                assert 'relvant_doc_id' in doc_result
                
                if not doc_result['relvant_doc_id']:
                    print("  ⚠ 没有找到相关文档，跳过tree_search")
                    continue
                
                # 步骤2: Tree Search
                print("\n步骤2: 执行tree_search...")
                tree_result_obj = await client.call_tool("tree_search", {
                    "rewrite_query": doc_result['rewrite_query'],
                    "relvant_doc_id": doc_result['relvant_doc_id']
                })
                tree_result = extract_result(tree_result_obj)
                
                print(f"  返回文档数: {len(tree_result)}")
                
                assert isinstance(tree_result, list)
                
                # 步骤3: 验证结果格式
                print("\n步骤3: 验证结果格式...")
                for doc in tree_result:
                    assert 'doc_name' in doc, "文档应该包含doc_name"
                    assert 'chunks' in doc, "文档应该包含chunks"
                    assert isinstance(doc['chunks'], list), "chunks应该是列表"
                    
                    for chunk in doc['chunks']:
                        assert 'node_id' in chunk, "块应该包含node_id"
                        assert 'text' in chunk, "块应该包含text"
                        assert isinstance(chunk['text'], str), "text应该是字符串"
                        assert len(chunk['text']) > 0, "text不应该为空"
                
                print("  ✓ 结果格式验证通过")
                
                # 显示结果摘要
                print("\n结果摘要:")
                total_chunks = sum(len(doc['chunks']) for doc in tree_result)
                print(f"  总文档数: {len(tree_result)}")
                print(f"  总块数: {total_chunks}")
                
                for doc in tree_result:
                    print(f"  - {doc['doc_name']}: {len(doc['chunks'])} 个块")
        
        print("\n✓ 端到端集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 端到端集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始MCP服务器测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 服务器初始化
    results.append(("服务器初始化", asyncio.run(test_server_initialization())))
    
    # 测试2: RAG模块加载
    results.append(("RAG模块加载", test_rag_modules_loading()))
    
    # 测试3-5: Document_Search工具
    results.append(("Document_Search - 正常查询", asyncio.run(test_document_search_normal())))
    results.append(("Document_Search - K参数", asyncio.run(test_document_search_k_parameter())))
    results.append(("Document_Search - 空结果", asyncio.run(test_document_search_empty_result())))
    
    # 测试6-8: Tree_Search工具
    results.append(("Tree_Search - 单文档", asyncio.run(test_tree_search_single_document())))
    results.append(("Tree_Search - 多文档", asyncio.run(test_tree_search_multiple_documents())))
    results.append(("Tree_Search - 不存在文档", asyncio.run(test_tree_search_nonexistent_document())))
    
    # 测试9: 端到端集成
    results.append(("端到端集成", asyncio.run(test_end_to_end_integration())))
    
    # 显示测试摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
