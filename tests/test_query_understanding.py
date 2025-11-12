"""
测试QueryUnderstanding类的基本功能
"""
import os
from rag.config.config_manager import ConfigManager
from rag.online.query_understanding import QueryUnderstanding


def test_query_understanding():
    """测试问题理解和重写功能"""
    
    # 初始化配置管理器
    config = ConfigManager("rag_config.yaml")
    
    # 初始化问题理解器
    query_understanding = QueryUnderstanding(config)
    
    # 测试问题重写
    original_query = "这个公司去年赚了多少钱？"
    print(f"原始问题: {original_query}")
    
    try:
        rewritten_query = query_understanding.rewrite_query(original_query)
        print(f"重写后的问题: {rewritten_query}")
        print("\n✓ 问题重写成功!")
        
    except Exception as e:
        print(f"\n✗ 问题重写失败: {e}")
        raise


if __name__ == "__main__":
    test_query_understanding()
