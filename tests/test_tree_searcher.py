"""
测试TreeSearcher类
"""
import json
from rag.config.config_manager import ConfigManager
from rag.online.tree_searcher import TreeSearcher


def test_tree_searcher():
    """测试TreeSearcher的基本功能"""
    print("=" * 60)
    print("测试TreeSearcher类")
    print("=" * 60)
    
    # 初始化配置管理器
    config = ConfigManager("rag_config.yaml")
    
    # 初始化TreeSearcher
    tree_searcher = TreeSearcher(config)
    print("✓ TreeSearcher初始化成功")
    
    # 测试加载树形索引
    doc_id = "775ab06bf0ea11b8"  # 2023-annual-report-truncated.pdf
    try:
        tree_index = tree_searcher.load_tree_index(doc_id)
        print(f"✓ 成功加载树形索引: {tree_index.get('doc_name', 'Unknown')}")
        print(f"  - 节点数量: {len(tree_index['structure'])}")
    except Exception as e:
        print(f"✗ 加载树形索引失败: {e}")
        return
    
    # 测试搜索节点
    query = "What is the Federal Reserve's monetary policy in 2023?"
    print(f"\n测试问题: {query}")
    
    try:
        node_ids = tree_searcher.search_nodes(query, tree_index)
        print(f"✓ 搜索到 {len(node_ids)} 个相关节点")
        print(f"  - 节点ID列表: {node_ids}")
    except Exception as e:
        print(f"✗ 搜索节点失败: {e}")
        return
    
    # 测试提取节点文本
    if node_ids:
        try:
            node_text = tree_searcher.extract_node_text(node_ids, tree_index)
            print(f"\n✓ 成功提取节点文本")
            print(f"  - 文本长度: {len(node_text)} 字符")
            print(f"\n提取的节点内容预览:")
            print("-" * 60)
            # 只显示前500个字符
            preview = node_text[:500] if len(node_text) > 500 else node_text
            print(preview)
            if len(node_text) > 500:
                print("...")
            print("-" * 60)
        except Exception as e:
            print(f"✗ 提取节点文本失败: {e}")
    else:
        print("\n没有找到相关节点，跳过文本提取测试")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_node_map_building():
    """测试节点映射构建功能"""
    print("\n" + "=" * 60)
    print("测试节点映射构建")
    print("=" * 60)
    
    config = ConfigManager("rag_config.yaml")
    tree_searcher = TreeSearcher(config)
    
    # 创建测试树结构
    test_structure = [
        {
            "title": "Section 1",
            "node_id": "0001",
            "nodes": [
                {
                    "title": "Subsection 1.1",
                    "node_id": "0002"
                },
                {
                    "title": "Subsection 1.2",
                    "node_id": "0003"
                }
            ]
        },
        {
            "title": "Section 2",
            "node_id": "0004"
        }
    ]
    
    node_map = tree_searcher._build_node_map(test_structure)
    print(f"✓ 构建节点映射成功")
    print(f"  - 映射包含 {len(node_map)} 个节点")
    print(f"  - 节点ID: {list(node_map.keys())}")
    
    # 验证所有节点都被正确映射
    expected_ids = ["0001", "0002", "0003", "0004"]
    for node_id in expected_ids:
        if node_id in node_map:
            print(f"  ✓ 节点 {node_id} 存在: {node_map[node_id]['title']}")
        else:
            print(f"  ✗ 节点 {node_id} 缺失")
    
    print("=" * 60)


def test_simplify_tree_structure():
    """测试树结构简化功能"""
    print("\n" + "=" * 60)
    print("测试树结构简化")
    print("=" * 60)
    
    config = ConfigManager("rag_config.yaml")
    tree_searcher = TreeSearcher(config)
    
    # 创建包含完整信息的树结构
    full_structure = [
        {
            "title": "Section 1",
            "node_id": "0001",
            "start_index": 1,
            "end_index": 5,
            "summary": "This is a summary",
            "text": "Full text content here...",
            "nodes": [
                {
                    "title": "Subsection 1.1",
                    "node_id": "0002",
                    "start_index": 1,
                    "end_index": 3,
                    "text": "More text..."
                }
            ]
        }
    ]
    
    simplified = tree_searcher._simplify_tree_structure(full_structure)
    print(f"✓ 简化树结构成功")
    print(f"\n简化后的结构:")
    print(json.dumps(simplified, ensure_ascii=False, indent=2))
    
    # 验证简化后的结构不包含text字段
    def check_no_text(nodes):
        for node in nodes:
            if 'text' in node:
                return False
            if 'nodes' in node:
                if not check_no_text(node['nodes']):
                    return False
        return True
    
    if check_no_text(simplified):
        print("\n✓ 确认简化后的结构不包含text字段")
    else:
        print("\n✗ 简化后的结构仍包含text字段")
    
    print("=" * 60)


if __name__ == "__main__":
    # 运行所有测试
    test_node_map_building()
    test_simplify_tree_structure()
    test_tree_searcher()
