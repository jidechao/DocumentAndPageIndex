"""
扩展测试QueryUnderstanding类的时间处理功能
"""
from rag.config.config_manager import ConfigManager
from rag.online.query_understanding import QueryUnderstanding


def test_multiple_queries():
    """测试多个不同类型的问题重写"""
    
    # 初始化配置管理器
    config = ConfigManager("rag_config.yaml")
    
    # 初始化问题理解器
    query_understanding = QueryUnderstanding(config)
    
    # 测试用例
    test_cases = [
        "这个公司去年赚了多少钱？",
        "今年的营收目标是什么？",
        "上个季度的销售额怎么样？",
        "公司的主要业务是啥？",
        "CEO是谁呀？"
    ]
    
    print("=" * 60)
    for i, original_query in enumerate(test_cases, 1):
        print(f"\n测试 {i}:")
        print(f"原始问题: {original_query}")
        
        try:
            rewritten_query = query_understanding.rewrite_query(original_query)
            print(f"重写后的问题: {rewritten_query}")
            print("✓ 成功")
            
        except Exception as e:
            print(f"✗ 失败: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_multiple_queries()
