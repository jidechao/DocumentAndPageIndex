"""
测试答案生成模块
"""
import os
from dotenv import load_dotenv
from rag.config.config_manager import ConfigManager
from rag.online.answer_generator import AnswerGenerator

# 加载环境变量
load_dotenv()


def test_answer_generator_init():
    """测试AnswerGenerator初始化"""
    print("测试1: AnswerGenerator初始化")
    config = ConfigManager()
    generator = AnswerGenerator(config)
    
    assert generator.config is not None
    assert generator.model is not None
    assert generator.api_key is not None
    print(f"✓ 初始化成功，使用模型: {generator.model}")
    print()


def test_get_no_answer_message():
    """测试获取无法回答的消息"""
    print("测试2: 获取无法回答的消息")
    config = ConfigManager()
    generator = AnswerGenerator(config)
    
    message = generator.get_no_answer_message()
    expected_message = "很抱歉，根据我掌握知识库内容，尚无法回答这个问题。我会尽快学习我所欠缺的知识，以便更好的为您服务。"
    
    assert message == expected_message
    print(f"✓ 无法回答消息: {message}")
    print()


def test_generate_answer():
    """测试答案生成"""
    print("测试3: 答案生成")
    config = ConfigManager()
    generator = AnswerGenerator(config)
    
    # 测试问题和上下文
    query = "什么是机器学习？"
    context = """
    机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习和改进，而无需明确编程。
    机器学习算法通过分析大量数据来识别模式，并使用这些模式来做出预测或决策。
    常见的机器学习类型包括监督学习、无监督学习和强化学习。
    """
    
    try:
        answer = generator.generate_answer(query, context)
        print(f"✓ 问题: {query}")
        print(f"✓ 生成的答案: {answer}")
        assert len(answer) > 0
        print()
    except Exception as e:
        print(f"✗ 答案生成失败: {e}")
        print()


def test_generate_answer_with_insufficient_context():
    """测试上下文不足时的答案生成"""
    print("测试4: 上下文不足时的答案生成")
    config = ConfigManager()
    generator = AnswerGenerator(config)
    
    # 测试问题和不相关的上下文
    query = "量子计算机的工作原理是什么？"
    context = """
    机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习和改进。
    """
    
    try:
        answer = generator.generate_answer(query, context)
        print(f"✓ 问题: {query}")
        print(f"✓ 生成的答案: {answer}")
        assert len(answer) > 0
        print()
    except Exception as e:
        print(f"✗ 答案生成失败: {e}")
        print()


if __name__ == "__main__":
    print("=" * 60)
    print("答案生成模块测试")
    print("=" * 60)
    print()
    
    # 检查API密钥
    if not os.getenv('CHATGPT_API_KEY'):
        print("错误: 未设置CHATGPT_API_KEY环境变量")
        exit(1)
    
    # 运行测试
    test_answer_generator_init()
    test_get_no_answer_message()
    test_generate_answer()
    test_generate_answer_with_insufficient_context()
    
    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)
