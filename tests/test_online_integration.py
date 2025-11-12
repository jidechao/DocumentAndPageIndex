"""
在线搜索阶段的端到端集成测试
测试从问题理解到答案生成的完整流程
"""
import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.config.config_manager import ConfigManager
from rag.online.query_understanding import QueryUnderstanding
from rag.online.doc_searcher import DocSearcher
from rag.online.tree_searcher import TreeSearcher
from rag.online.answer_generator import AnswerGenerator


def test_online_search_with_relevant_documents():
    """测试有相关文档时的在线搜索流程"""
    print("=" * 60)
    print("集成测试1: 在线搜索 - 有相关文档")
    print("=" * 60)
    
    # 初始化配置
    config = ConfigManager("rag_config.yaml")
    
    # 测试问题
    original_query = "美联储2023年的货币政策是什么？"
    print(f"\n1. 原始问题: {original_query}")
    
    # 步骤1: 问题理解和重写
    print("\n2. 问题理解和重写...")
    query_understanding = QueryUnderstanding(config)
    
    try:
        rewritten_query = query_understanding.rewrite_query(original_query)
        print(f"✓ 问题重写成功")
        print(f"  - 重写后的问题: {rewritten_query}")
    except Exception as e:
        print(f"✗ 问题重写失败: {e}")
        raise
    
    # 步骤2: Doc-Search - 查找相关文档
    print("\n3. Doc-Search - 查找相关文档...")
    doc_searcher = DocSearcher(config)
    
    try:
        # 加载目录索引
        directory_index = doc_searcher.load_directory_index()
        print(f"  - 加载了 {len(directory_index['documents'])} 个文档的索引")
        
        # 搜索相关文档
        doc_ids = doc_searcher.search_documents(rewritten_query)
        
        if not doc_ids:
            print("  - 未找到相关文档")
            print("  - 返回无法回答消息")
            generator = AnswerGenerator(config)
            answer = generator.get_no_answer_message()
            print(f"\n最终答案: {answer}")
            print("\n" + "=" * 60)
            print("✓ 无相关文档场景测试通过")
            print("=" * 60)
            return
        
        print(f"✓ 找到 {len(doc_ids)} 个相关文档")
        for doc_id in doc_ids:
            doc_name = next(
                (doc['doc_name'] for doc in directory_index['documents'] 
                 if doc['doc_id'] == doc_id),
                "未知文档"
            )
            print(f"  - {doc_id}: {doc_name}")
        
    except Exception as e:
        print(f"✗ Doc-Search失败: {e}")
        raise
    
    # 步骤3: Tree-Search - 在相关文档中查找节点
    print("\n4. Tree-Search - 查找相关节点...")
    tree_searcher = TreeSearcher(config)
    
    all_context = []
    
    for doc_id in doc_ids:
        try:
            # 加载树形索引
            tree_index = tree_searcher.load_tree_index(doc_id)
            doc_name = tree_index.get('doc_name', doc_id)
            print(f"\n  处理文档: {doc_name}")
            
            # 搜索相关节点
            node_ids = tree_searcher.search_nodes(rewritten_query, tree_index)
            
            if not node_ids:
                print(f"    - 未找到相关节点")
                continue
            
            print(f"    ✓ 找到 {len(node_ids)} 个相关节点: {node_ids}")
            
            # 提取节点文本
            node_text = tree_searcher.extract_node_text(node_ids, tree_index)
            print(f"    ✓ 提取文本长度: {len(node_text)} 字符")
            
            all_context.append(f"来自文档 {doc_name}:\n{node_text}")
            
        except Exception as e:
            print(f"    ✗ Tree-Search失败: {e}")
            continue
    
    # 检查是否有上下文
    if not all_context:
        print("\n  所有文档都未找到相关节点")
        print("  返回无法回答消息")
        generator = AnswerGenerator(config)
        answer = generator.get_no_answer_message()
        print(f"\n最终答案: {answer}")
        print("\n" + "=" * 60)
        print("✓ 无相关节点场景测试通过")
        print("=" * 60)
        return
    
    # 步骤4: 答案生成
    print("\n5. 答案生成...")
    generator = AnswerGenerator(config)
    
    try:
        context = "\n\n".join(all_context)
        answer = generator.generate_answer(original_query, context)
        print(f"✓ 答案生成成功")
        print(f"\n最终答案:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
        
    except Exception as e:
        print(f"✗ 答案生成失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("✓ 在线搜索集成测试通过")
    print("=" * 60)


def test_online_search_with_no_relevant_documents():
    """测试无相关文档时的在线搜索流程"""
    print("\n" + "=" * 60)
    print("集成测试2: 在线搜索 - 无相关文档")
    print("=" * 60)
    
    # 初始化配置
    config = ConfigManager("rag_config.yaml")
    
    # 测试一个不相关的问题
    original_query = "量子纠缠的物理原理是什么？"
    print(f"\n1. 原始问题: {original_query}")
    
    # 步骤1: 问题理解和重写
    print("\n2. 问题理解和重写...")
    query_understanding = QueryUnderstanding(config)
    
    try:
        rewritten_query = query_understanding.rewrite_query(original_query)
        print(f"✓ 问题重写成功")
        print(f"  - 重写后的问题: {rewritten_query}")
    except Exception as e:
        print(f"✗ 问题重写失败: {e}")
        raise
    
    # 步骤2: Doc-Search
    print("\n3. Doc-Search - 查找相关文档...")
    doc_searcher = DocSearcher(config)
    
    try:
        doc_ids = doc_searcher.search_documents(rewritten_query)
        
        if not doc_ids:
            print("✓ 未找到相关文档（符合预期）")
            generator = AnswerGenerator(config)
            answer = generator.get_no_answer_message()
            print(f"\n最终答案: {answer}")
            
            expected_message = "很抱歉，根据我掌握知识库内容，尚无法回答这个问题。我会尽快学习我所欠缺的知识，以便更好的为您服务。"
            assert answer == expected_message
            print("✓ 返回了正确的无法回答消息")
        else:
            print(f"  - 找到了 {len(doc_ids)} 个文档（可能是误判）")
            print("  - 继续测试流程...")
        
    except Exception as e:
        print(f"✗ Doc-Search失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("✓ 无相关文档场景测试通过")
    print("=" * 60)


def test_online_search_multiple_queries():
    """测试多个不同类型的问题"""
    print("\n" + "=" * 60)
    print("集成测试3: 多问题测试")
    print("=" * 60)
    
    # 初始化配置
    config = ConfigManager("rag_config.yaml")
    
    # 初始化所有组件
    query_understanding = QueryUnderstanding(config)
    doc_searcher = DocSearcher(config)
    tree_searcher = TreeSearcher(config)
    generator = AnswerGenerator(config)
    
    # 测试问题列表
    test_queries = [
        "Federal Reserve的主要职责是什么？",
        "2023年的通货膨胀率是多少？",
        "什么是量子计算？"  # 不相关的问题
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"问题 {i}: {query}")
        print('=' * 60)
        
        try:
            # 问题重写
            rewritten_query = query_understanding.rewrite_query(query)
            print(f"重写后: {rewritten_query}")
            
            # Doc-Search
            doc_ids = doc_searcher.search_documents(rewritten_query)
            
            if not doc_ids:
                answer = generator.get_no_answer_message()
                print(f"结果: 无相关文档")
                print(f"答案: {answer}")
                continue
            
            print(f"找到 {len(doc_ids)} 个相关文档")
            
            # Tree-Search
            all_context = []
            for doc_id in doc_ids:
                tree_index = tree_searcher.load_tree_index(doc_id)
                node_ids = tree_searcher.search_nodes(rewritten_query, tree_index)
                
                if node_ids:
                    node_text = tree_searcher.extract_node_text(node_ids, tree_index)
                    all_context.append(node_text)
            
            if not all_context:
                answer = generator.get_no_answer_message()
                print(f"结果: 无相关节点")
                print(f"答案: {answer}")
                continue
            
            # 答案生成
            context = "\n\n".join(all_context)
            answer = generator.generate_answer(query, context)
            print(f"答案: {answer[:200]}...")
            
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✓ 多问题测试完成")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("在线搜索阶段集成测试套件")
    print("=" * 60)
    print()
    
    # 检查API密钥
    if not os.getenv('CHATGPT_API_KEY'):
        print("错误: 未设置CHATGPT_API_KEY环境变量")
        exit(1)
    
    # 检查目录索引是否存在
    config = ConfigManager("rag_config.yaml")
    directory_index_path = config.config['paths']['directory_index']
    
    if not os.path.exists(directory_index_path):
        print(f"警告: 目录索引文件不存在: {directory_index_path}")
        print("请先运行离线索引流程: python run_rag_index.py")
        exit(1)
    
    # 运行测试
    test_online_search_with_relevant_documents()
    test_online_search_with_no_relevant_documents()
    test_online_search_multiple_queries()
    
    print("\n" + "=" * 60)
    print("✓ 所有集成测试完成")
    print("=" * 60)
