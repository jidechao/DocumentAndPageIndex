"""
运行所有测试的主脚本
包括单元测试和集成测试
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()


def check_prerequisites():
    """检查测试前提条件"""
    print("检查测试前提条件...")
    
    # 检查API密钥
    if not os.getenv('CHATGPT_API_KEY'):
        print("✗ 错误: 未设置CHATGPT_API_KEY环境变量")
        return False
    
    print("✓ API密钥已配置")
    
    # 检查配置文件
    if not os.path.exists('rag_config.yaml'):
        print("✗ 错误: 未找到rag_config.yaml配置文件")
        return False
    
    print("✓ 配置文件存在")
    
    # 检查测试文档
    if not os.path.exists('tests/pdfs'):
        print("✗ 错误: 未找到tests/pdfs目录")
        return False
    
    pdf_files = [f for f in os.listdir('tests/pdfs') if f.endswith('.pdf')]
    if not pdf_files:
        print("✗ 错误: tests/pdfs目录中没有PDF文件")
        return False
    
    print(f"✓ 找到 {len(pdf_files)} 个测试PDF文件")
    
    return True


def run_unit_tests():
    """运行单元测试"""
    print("\n" + "=" * 80)
    print("运行单元测试")
    print("=" * 80)
    
    unit_tests = [
        ('test_document_processor.py', 'DocumentProcessor'),
        ('test_description_generator.py', 'DescriptionGenerator'),
        ('test_query_understanding.py', 'QueryUnderstanding'),
        ('test_doc_searcher.py', 'DocSearcher'),
        ('test_tree_searcher.py', 'TreeSearcher'),
        ('test_answer_generator.py', 'AnswerGenerator'),
    ]
    
    results = []
    
    for test_file, test_name in unit_tests:
        print(f"\n{'=' * 80}")
        print(f"运行 {test_name} 测试")
        print('=' * 80)
        
        if not os.path.exists(test_file):
            print(f"✗ 测试文件不存在: {test_file}")
            results.append((test_name, False))
            continue
        
        try:
            # 运行测试
            exit_code = os.system(f'python {test_file}')
            
            if exit_code == 0:
                print(f"\n✓ {test_name} 测试通过")
                results.append((test_name, True))
            else:
                print(f"\n✗ {test_name} 测试失败")
                results.append((test_name, False))
        
        except Exception as e:
            print(f"\n✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    return results


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "=" * 80)
    print("运行集成测试")
    print("=" * 80)
    
    integration_tests = [
        ('tests/test_offline_integration.py', '离线索引集成测试'),
        ('tests/test_online_integration.py', '在线搜索集成测试'),
    ]
    
    results = []
    
    for test_file, test_name in integration_tests:
        print(f"\n{'=' * 80}")
        print(f"运行 {test_name}")
        print('=' * 80)
        
        if not os.path.exists(test_file):
            print(f"✗ 测试文件不存在: {test_file}")
            results.append((test_name, False))
            continue
        
        try:
            # 运行测试
            exit_code = os.system(f'python {test_file}')
            
            if exit_code == 0:
                print(f"\n✓ {test_name} 通过")
                results.append((test_name, True))
            else:
                print(f"\n✗ {test_name} 失败")
                results.append((test_name, False))
        
        except Exception as e:
            print(f"\n✗ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    return results


def print_summary(unit_results, integration_results):
    """打印测试摘要"""
    print("\n" + "=" * 80)
    print("测试摘要")
    print("=" * 80)
    
    print("\n单元测试结果:")
    for test_name, passed in unit_results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status} - {test_name}")
    
    print("\n集成测试结果:")
    for test_name, passed in integration_results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status} - {test_name}")
    
    # 统计
    total_unit = len(unit_results)
    passed_unit = sum(1 for _, passed in unit_results if passed)
    
    total_integration = len(integration_results)
    passed_integration = sum(1 for _, passed in integration_results if passed)
    
    total = total_unit + total_integration
    passed = passed_unit + passed_integration
    
    print(f"\n总计:")
    print(f"  单元测试: {passed_unit}/{total_unit} 通过")
    print(f"  集成测试: {passed_integration}/{total_integration} 通过")
    print(f"  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n" + "=" * 80)
        print("✓ 所有测试通过!")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print(f"✗ {total - passed} 个测试失败")
        print("=" * 80)
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("RAG问答系统 - 测试套件")
    print("=" * 80)
    
    # 检查前提条件
    if not check_prerequisites():
        print("\n前提条件检查失败，退出测试")
        sys.exit(1)
    
    # 运行单元测试
    unit_results = run_unit_tests()
    
    # 运行集成测试
    integration_results = run_integration_tests()
    
    # 打印摘要
    all_passed = print_summary(unit_results, integration_results)
    
    # 返回退出码
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
