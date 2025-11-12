"""
测试流式输出功能
"""
import asyncio
from dotenv import load_dotenv
from rag.config.config_manager import ConfigManager
from rag.online.answer_generator import AnswerGenerator

# 加载环境变量
load_dotenv()


async def test_stream_answer():
    """测试流式答案生成"""
    print("=" * 60)
    print("测试流式答案生成")
    print("=" * 60)
    
    config = ConfigManager("rag_config.yaml")
    generator = AnswerGenerator(config)
    
    query = "什么是机器学习？"
    context = """
    机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习和改进，而无需明确编程。
    机器学习算法通过分析大量数据来识别模式，并使用这些模式来做出预测或决策。
    常见的机器学习类型包括监督学习、无监督学习和强化学习。
    """
    
    print(f"\n问题: {query}")
    print("\n答案:")
    print("-" * 60)
    
    try:
        async for chunk in generator.generate_answer_stream(query, context):
            print(chunk, end="", flush=True)
        
        print()
        print("-" * 60)
        print("\n✓ 流式输出测试成功")
        
    except Exception as e:
        print(f"\n✗ 流式输出测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_stream_answer())
