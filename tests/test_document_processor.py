"""
测试DocumentProcessor的简单脚本
"""
import os
from rag.config.config_manager import ConfigManager
from rag.offline.document_processor import DocumentProcessor


def test_document_processor():
    """测试DocumentProcessor基本功能"""
    
    print("=" * 60)
    print("测试 DocumentProcessor")
    print("=" * 60)
    
    # 初始化配置管理器
    print("\n1. 初始化配置管理器...")
    config = ConfigManager("rag_config.yaml")
    print("   ✓ 配置管理器初始化成功")
    
    # 初始化文档处理器
    print("\n2. 初始化文档处理器...")
    processor = DocumentProcessor(config)
    print("   ✓ DocumentProcessor 初始化成功!")
    print(f"   - 树形索引目录: {processor.trees_dir}")
    print(f"   - PageIndex配置: {processor.pageindex_config}")
    
    # 测试doc_id生成
    print("\n3. 测试文档ID生成...")
    test_path = "test_document.pdf"
    doc_id = processor._generate_doc_id(test_path)
    print(f"   - 文件路径: {test_path}")
    print(f"   - 生成的doc_id: {doc_id}")
    
    # 测试树形索引路径生成
    tree_path = processor._get_tree_index_path(doc_id)
    print(f"   - 树形索引路径: {tree_path}")
    
    # 检查是否有测试PDF文件
    print("\n4. 检查测试文件...")
    test_pdf_dir = "tests/pdfs"
    if os.path.exists(test_pdf_dir):
        pdf_files = [f for f in os.listdir(test_pdf_dir) if f.endswith('.pdf')]
        if pdf_files:
            print(f"   找到 {len(pdf_files)} 个测试PDF文件:")
            for pdf in pdf_files[:3]:  # 只显示前3个
                print(f"   - {pdf}")
        else:
            print("   未找到测试PDF文件")
    else:
        print(f"   测试目录不存在: {test_pdf_dir}")
    
    print("\n" + "=" * 60)
    print("✓ DocumentProcessor 基本功能测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    test_document_processor()
