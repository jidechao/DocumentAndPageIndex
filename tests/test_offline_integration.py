"""
离线索引阶段的端到端集成测试
测试从文档处理到目录索引构建的完整流程
"""
import os
import sys
import json
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.config.config_manager import ConfigManager
from rag.offline.document_processor import DocumentProcessor
from rag.offline.description_generator import DescriptionGenerator
from rag.offline.directory_index_builder import DirectoryIndexBuilder


def test_offline_indexing_single_document():
    """测试单个文档的离线索引流程"""
    print("=" * 60)
    print("集成测试1: 单个文档离线索引")
    print("=" * 60)
    
    # 初始化配置
    config = ConfigManager("rag_config.yaml")
    
    # 选择测试文档
    test_pdf = "tests/pdfs/earthmover.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"✗ 测试文档不存在: {test_pdf}")
        return
    
    print(f"\n1. 测试文档: {test_pdf}")
    
    # 步骤1: 文档处理
    print("\n2. 处理文档并生成树形索引...")
    processor = DocumentProcessor(config)
    
    try:
        doc_info = processor.process_single_document(test_pdf)
        print(f"✓ 文档处理成功")
        print(f"  - doc_id: {doc_info['doc_id']}")
        print(f"  - doc_name: {doc_info['doc_name']}")
        print(f"  - 树形索引路径: {doc_info['tree_index_path']}")
        
        # 验证树形索引文件已创建
        assert os.path.exists(doc_info['tree_index_path'])
        print(f"  ✓ 树形索引文件已创建")
        
    except Exception as e:
        print(f"✗ 文档处理失败: {e}")
        raise
    
    # 步骤2: 生成文档描述
    print("\n3. 生成文档描述...")
    generator = DescriptionGenerator(config)
    
    try:
        description = generator.generate_description(doc_info['tree_structure'])
        print(f"✓ 描述生成成功")
        print(f"  - 描述: {description}")
        
        # 更新doc_info
        doc_info['doc_description'] = description
        
    except Exception as e:
        print(f"✗ 描述生成失败: {e}")
        raise
    
    # 步骤3: 构建目录索引
    print("\n4. 构建文件目录索引...")
    builder = DirectoryIndexBuilder(config)
    
    try:
        documents_info = {doc_info['doc_id']: doc_info}
        index_path = builder.build_directory_index(documents_info)
        print(f"✓ 目录索引构建成功")
        print(f"  - 索引路径: {index_path}")
        
        # 验证目录索引文件
        assert os.path.exists(index_path)
        
        with open(index_path, 'r', encoding='utf-8') as f:
            directory_index = json.load(f)
        
        assert 'documents' in directory_index
        assert len(directory_index['documents']) == 1
        assert directory_index['documents'][0]['doc_id'] == doc_info['doc_id']
        print(f"  ✓ 目录索引验证通过")
        
    except Exception as e:
        print(f"✗ 目录索引构建失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("✓ 单个文档离线索引集成测试通过")
    print("=" * 60)


def test_offline_indexing_multiple_documents():
    """测试多个文档的离线索引流程"""
    print("\n" + "=" * 60)
    print("集成测试2: 多文档离线索引")
    print("=" * 60)
    
    # 初始化配置
    config = ConfigManager("rag_config.yaml")
    
    # 选择多个测试文档
    test_pdfs = [
        "tests/pdfs/earthmover.pdf",
        "tests/pdfs/2023-annual-report-truncated.pdf"
    ]
    
    # 过滤存在的文档
    existing_pdfs = [pdf for pdf in test_pdfs if os.path.exists(pdf)]
    
    if len(existing_pdfs) < 2:
        print(f"✗ 需要至少2个测试文档，只找到 {len(existing_pdfs)} 个")
        print("  跳过多文档测试")
        return
    
    print(f"\n1. 测试文档数量: {len(existing_pdfs)}")
    for pdf in existing_pdfs:
        print(f"  - {pdf}")
    
    # 步骤1: 批量处理文档
    print("\n2. 批量处理文档...")
    processor = DocumentProcessor(config)
    
    try:
        documents_info = processor.process_documents(existing_pdfs)
        print(f"✓ 批量处理成功，处理了 {len(documents_info)} 个文档")
        
        for doc_id, doc_info in documents_info.items():
            print(f"  - {doc_info['doc_name']}: {doc_id}")
            assert os.path.exists(doc_info['tree_index_path'])
        
    except Exception as e:
        print(f"✗ 批量处理失败: {e}")
        raise
    
    # 步骤2: 为每个文档生成描述
    print("\n3. 为每个文档生成描述...")
    generator = DescriptionGenerator(config)
    
    for doc_id, doc_info in documents_info.items():
        try:
            description = generator.generate_description(doc_info['tree_structure'])
            doc_info['doc_description'] = description
            print(f"  ✓ {doc_info['doc_name']}: {description[:80]}...")
        except Exception as e:
            print(f"  ✗ {doc_info['doc_name']} 描述生成失败: {e}")
            raise
    
    # 步骤3: 构建聚合的目录索引
    print("\n4. 构建聚合的文件目录索引...")
    builder = DirectoryIndexBuilder(config)
    
    try:
        index_path = builder.build_directory_index(documents_info)
        print(f"✓ 目录索引构建成功")
        print(f"  - 索引路径: {index_path}")
        
        # 验证目录索引
        with open(index_path, 'r', encoding='utf-8') as f:
            directory_index = json.load(f)
        
        assert 'documents' in directory_index
        assert len(directory_index['documents']) == len(documents_info)
        print(f"  ✓ 目录索引包含 {len(directory_index['documents'])} 个文档")
        
        # 验证每个文档的信息
        for doc in directory_index['documents']:
            assert 'doc_id' in doc
            assert 'doc_name' in doc
            assert 'doc_description' in doc
            print(f"  ✓ {doc['doc_name']}: 验证通过")
        
    except Exception as e:
        print(f"✗ 目录索引构建失败: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("✓ 多文档离线索引集成测试通过")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("离线索引阶段集成测试套件")
    print("=" * 60)
    print()
    
    # 检查API密钥
    if not os.getenv('CHATGPT_API_KEY'):
        print("错误: 未设置CHATGPT_API_KEY环境变量")
        exit(1)
    
    # 运行测试
    test_offline_indexing_single_document()
    test_offline_indexing_multiple_documents()
    
    print("\n" + "=" * 60)
    print("✓ 所有集成测试完成")
    print("=" * 60)
