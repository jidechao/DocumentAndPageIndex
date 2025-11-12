"""
测试DocumentProcessor处理实际文档
"""
import os
import json
from rag.config.config_manager import ConfigManager
from rag.offline.document_processor import DocumentProcessor


def test_process_single_document():
    """测试处理单个文档"""
    
    print("=" * 60)
    print("测试处理单个PDF文档")
    print("=" * 60)
    
    # 初始化
    config = ConfigManager("rag_config.yaml")
    processor = DocumentProcessor(config)
    
    # 选择一个较小的测试文件
    test_file = "tests/pdfs/earthmover.pdf"
    
    if not os.path.exists(test_file):
        print(f"✗ 测试文件不存在: {test_file}")
        return
    
    print(f"\n正在处理文档: {test_file}")
    print("-" * 60)
    
    try:
        # 处理文档
        result = processor.process_single_document(test_file)
        
        print("\n✓ 文档处理成功!")
        print(f"\n文档信息:")
        print(f"  - doc_id: {result['doc_id']}")
        print(f"  - doc_name: {result['doc_name']}")
        print(f"  - file_path: {result['file_path']}")
        print(f"  - tree_index_path: {result['tree_index_path']}")
        
        # 检查树形索引文件是否创建
        if os.path.exists(result['tree_index_path']):
            print(f"\n✓ 树形索引文件已创建: {result['tree_index_path']}")
            
            # 读取并显示部分内容
            with open(result['tree_index_path'], 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
            
            print(f"\n树形索引结构预览:")
            print(f"  - doc_id: {tree_data.get('doc_id')}")
            print(f"  - doc_name: {tree_data.get('doc_name')}")
            if 'doc_description' in tree_data:
                print(f"  - doc_description: {tree_data.get('doc_description')[:100]}...")
            
            if 'structure' in tree_data and tree_data['structure']:
                print(f"  - 顶层节点数: {len(tree_data['structure'])}")
                print(f"\n  前3个顶层节点:")
                for i, node in enumerate(tree_data['structure'][:3]):
                    print(f"    {i+1}. {node.get('title', 'N/A')} (node_id: {node.get('node_id', 'N/A')})")
        
        print("\n" + "=" * 60)
        print("✓ 单文档处理测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()


def test_process_multiple_documents():
    """测试批量处理文档"""
    
    print("\n\n" + "=" * 60)
    print("测试批量处理文档")
    print("=" * 60)
    
    # 初始化
    config = ConfigManager("rag_config.yaml")
    processor = DocumentProcessor(config)
    
    # 选择多个测试文件（选择较小的文件）
    test_files = [
        "tests/pdfs/earthmover.pdf",
        "tests/pdfs/2023-annual-report-truncated.pdf"
    ]
    
    # 过滤存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if not existing_files:
        print("✗ 没有找到测试文件")
        return
    
    print(f"\n准备处理 {len(existing_files)} 个文档:")
    for f in existing_files:
        print(f"  - {f}")
    
    print("\n" + "-" * 60)
    
    try:
        # 批量处理
        results = processor.process_documents(existing_files)
        
        print("\n" + "=" * 60)
        print(f"✓ 批量处理完成! 成功处理 {len(results)} 个文档")
        print("=" * 60)
        
        print("\n处理结果:")
        for doc_id, info in results.items():
            print(f"\n  文档: {info['doc_name']}")
            print(f"    - doc_id: {doc_id}")
            print(f"    - 索引文件: {info['tree_index_path']}")
        
    except Exception as e:
        print(f"\n✗ 批量处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 测试单文档处理
    test_process_single_document()
    
    # 测试批量处理（注释掉）
    # test_process_multiple_documents()
