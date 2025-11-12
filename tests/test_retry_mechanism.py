"""
测试重试机制和错误处理
"""
import time
from rag.utils.retry import retry_with_backoff, setup_logger
from rag.exceptions import LLMAPIError


# 设置日志
logger = setup_logger("test", level=20)  # INFO level


def test_retry_success_after_failures():
    """测试在几次失败后成功的情况"""
    print("\n" + "=" * 70)
    print("测试1: 重试机制 - 第3次尝试成功")
    print("=" * 70)
    
    attempt_count = [0]  # 使用列表来在闭包中修改
    
    @retry_with_backoff(max_retries=5, initial_delay=0.5, logger=logger)
    def flaky_function():
        attempt_count[0] += 1
        print(f"  尝试 #{attempt_count[0]}")
        if attempt_count[0] < 3:
            raise Exception(f"模拟失败 (尝试 {attempt_count[0]})")
        return "成功!"
    
    try:
        result = flaky_function()
        print(f"\n✓ 结果: {result}")
        print(f"✓ 总共尝试了 {attempt_count[0]} 次")
    except Exception as e:
        print(f"\n✗ 失败: {e}")


def test_retry_all_failures():
    """测试所有尝试都失败的情况"""
    print("\n" + "=" * 70)
    print("测试2: 重试机制 - 所有尝试都失败")
    print("=" * 70)
    
    attempt_count = [0]
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5, logger=logger)
    def always_fail():
        attempt_count[0] += 1
        print(f"  尝试 #{attempt_count[0]}")
        raise Exception("总是失败")
    
    try:
        result = always_fail()
        print(f"\n✗ 不应该成功: {result}")
    except LLMAPIError as e:
        print(f"\n✓ 正确抛出 LLMAPIError")
        print(f"✓ 错误消息: {str(e)}")
        print(f"✓ 总共尝试了 {attempt_count[0]} 次")


def test_retry_immediate_success():
    """测试第一次就成功的情况"""
    print("\n" + "=" * 70)
    print("测试3: 重试机制 - 第一次就成功")
    print("=" * 70)
    
    attempt_count = [0]
    
    @retry_with_backoff(max_retries=3, initial_delay=0.5, logger=logger)
    def immediate_success():
        attempt_count[0] += 1
        print(f"  尝试 #{attempt_count[0]}")
        return "立即成功!"
    
    try:
        result = immediate_success()
        print(f"\n✓ 结果: {result}")
        print(f"✓ 只尝试了 {attempt_count[0]} 次（无需重试）")
    except Exception as e:
        print(f"\n✗ 失败: {e}")


def test_exponential_backoff():
    """测试指数退避延迟"""
    print("\n" + "=" * 70)
    print("测试4: 指数退避延迟")
    print("=" * 70)
    
    attempt_times = []
    
    @retry_with_backoff(max_retries=4, initial_delay=0.5, backoff_factor=2.0, logger=logger)
    def test_backoff():
        attempt_times.append(time.time())
        if len(attempt_times) < 4:
            raise Exception(f"失败 (尝试 {len(attempt_times)})")
        return "成功"
    
    try:
        result = test_backoff()
        print(f"\n✓ 结果: {result}")
        
        # 计算延迟时间
        if len(attempt_times) > 1:
            print("\n延迟时间:")
            for i in range(1, len(attempt_times)):
                delay = attempt_times[i] - attempt_times[i-1]
                expected = 0.5 * (2.0 ** (i-1))
                print(f"  尝试 {i} -> {i+1}: {delay:.2f}秒 (预期: ~{expected:.2f}秒)")
    except Exception as e:
        print(f"\n✗ 失败: {e}")


def test_user_friendly_error_messages():
    """测试用户友好的错误消息"""
    print("\n" + "=" * 70)
    print("测试5: 用户友好的错误消息")
    print("=" * 70)
    
    from rag.utils.llm_wrapper import get_user_friendly_error_message
    
    test_errors = [
        Exception("Invalid API key provided"),
        Exception("Connection timeout"),
        Exception("Rate limit exceeded"),
        Exception("Model gpt-5 does not exist"),
        Exception("Some unknown error"),
    ]
    
    for i, error in enumerate(test_errors, 1):
        print(f"\n测试错误 {i}: {str(error)}")
        print("-" * 70)
        message = get_user_friendly_error_message(error)
        print(message)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RAG系统 - 重试机制和错误处理测试")
    print("=" * 70)
    
    test_retry_success_after_failures()
    test_retry_all_failures()
    test_retry_immediate_success()
    test_exponential_backoff()
    test_user_friendly_error_messages()
    
    print("\n" + "=" * 70)
    print("所有测试完成!")
    print("=" * 70)
