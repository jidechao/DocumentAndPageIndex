"""
测试DocSearcher类的功能
"""
from rag.config.config_manager import ConfigManager
from rag.online.doc_searcher import DocSearcher


def test_doc_searcher():
    """测试文档搜索功能"""
    print("=" * 60)
    print("测试DocSearcher类")
    print("=" * 60)
    
    # 初始化配置管理器
    print("\n1. 初始化配置管理器...")
    config = ConfigManager("rag_config.yaml")
    print("✓ 配置管理器初始化成功")
    
    # 初始化DocSearcher
    print("\n2. 初始化DocSearcher...")
    doc_searcher = DocSearcher(config)
    print("✓ DocSearcher初始化成功")
    
    # 加载文件目录索引
    print("\n3. 加载文件目录索引...")
    directory_index = doc_searcher.load_directory_index()
    print(f"✓ 成功加载文件目录索引，包含 {len(directory_index['documents'])} 个文档")
    
    # 显示文档列表
    print("\n文档列表:")
    for doc in directory_index['documents']:
        print(f"  - doc_id: {doc['doc_id']}")
        print(f"    doc_name: {doc['doc_name']}")
        print(f"    doc_description: {doc['doc_description'][:100]}...")
        print()
    
    # 测试搜索相关文档
    test_queries = [
        "美联储2023年的货币政策是什么？",
        "Federal Reserve的年度报告中提到了什么？",
        "关于量子计算的最新进展"  # 不相关的问题
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i + 3}. 测试查询: {query}")
        try:
            doc_ids = doc_searcher.search_documents(query)
            if doc_ids:
                print(f"✓ 找到 {len(doc_ids)} 个相关文档:")
                for doc_id in doc_ids:
                    # 查找文档名称
                    doc_name = next(
                        (doc['doc_name'] for doc in directory_index['documents'] 
                         if doc['doc_id'] == doc_id),
                        "未知文档"
                    )
                    print(f"  - {doc_id} ({doc_name})")
            else:
                print("✓ 没有找到相关文档")
        except Exception as e:
            print(f"✗ 搜索失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_doc_searcher()
