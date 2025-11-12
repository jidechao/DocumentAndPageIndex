"""
测试DescriptionGenerator类的功能
"""
import os
from rag.config.config_manager import ConfigManager
from rag.offline.description_generator import DescriptionGenerator


def test_description_generator_init():
    """测试DescriptionGenerator初始化"""
    print("=" * 60)
    print("测试1: DescriptionGenerator初始化")
    print("=" * 60)
    
    config = ConfigManager("rag_config.yaml")
    generator = DescriptionGenerator(config)
    
    assert generator.config is not None
    assert generator.model is not None
    assert generator.api_key is not None
    print(f"✓ 初始化成功")
    print(f"  - 使用模型: {generator.model}")
    print(f"  - 温度参数: {generator.temperature}")
    print()


def test_generate_description():
    """测试文档描述生成"""
    print("=" * 60)
    print("测试2: 文档描述生成")
    print("=" * 60)
    
    config = ConfigManager("rag_config.yaml")
    generator = DescriptionGenerator(config)
    
    # 创建测试树结构
    test_tree_structure = {
        "doc_id": "test_doc_001",
        "doc_name": "test_document.pdf",
        "structure": [
            {
                "title": "Introduction to Machine Learning",
                "node_id": "0001",
                "start_index": 1,
                "end_index": 5,
                "summary": "This section introduces the basic concepts of machine learning",
                "text": "Machine learning is a branch of artificial intelligence...",
                "nodes": [
                    {
                        "title": "Supervised Learning",
                        "node_id": "0002",
                        "start_index": 2,
                        "end_index": 3,
                        "summary": "Explains supervised learning algorithms",
                        "text": "Supervised learning uses labeled data..."
                    }
                ]
            },
            {
                "title": "Deep Learning",
                "node_id": "0003",
                "start_index": 6,
                "end_index": 10,
                "summary": "Covers neural networks and deep learning",
                "text": "Deep learning is a subset of machine learning..."
            }
        ]
    }
    
    try:
        description = generator.generate_description(test_tree_structure)
        print(f"✓ 描述生成成功")
        print(f"  - 生成的描述: {description}")
        assert len(description) > 0
        assert isinstance(description, str)
        print()
    except Exception as e:
        print(f"✗ 描述生成失败: {e}")
        raise


def test_generate_description_with_real_tree():
    """使用真实的树形索引测试描述生成"""
    print("=" * 60)
    print("测试3: 使用真实树形索引生成描述")
    print("=" * 60)
    
    import json
    
    config = ConfigManager("rag_config.yaml")
    generator = DescriptionGenerator(config)
    
    # 尝试加载一个真实的树形索引文件
    trees_dir = config.config['paths']['trees_dir']
    
    if os.path.exists(trees_dir):
        tree_files = [f for f in os.listdir(trees_dir) if f.endswith('_structure.json')]
        
        if tree_files:
            # 使用第一个树形索引文件
            tree_file = tree_files[0]
            tree_path = os.path.join(trees_dir, tree_file)
            
            print(f"  - 加载树形索引: {tree_file}")
            
            with open(tree_path, 'r', encoding='utf-8') as f:
                tree_structure = json.load(f)
            
            try:
                description = generator.generate_description(tree_structure)
                print(f"✓ 描述生成成功")
                print(f"  - 文档名称: {tree_structure.get('doc_name', 'Unknown')}")
                print(f"  - 生成的描述: {description}")
                assert len(description) > 0
                print()
            except Exception as e:
                print(f"✗ 描述生成失败: {e}")
                raise
        else:
            print("  - 未找到树形索引文件，跳过此测试")
            print()
    else:
        print(f"  - 树形索引目录不存在: {trees_dir}")
        print("  - 跳过此测试")
        print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DescriptionGenerator 测试套件")
    print("=" * 60)
    print()
    
    # 检查API密钥
    if not os.getenv('CHATGPT_API_KEY'):
        print("错误: 未设置CHATGPT_API_KEY环境变量")
        exit(1)
    
    # 运行测试
    test_description_generator_init()
    test_generate_description()
    test_generate_description_with_real_tree()
    
    print("=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)
