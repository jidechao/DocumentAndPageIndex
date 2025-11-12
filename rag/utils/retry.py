"""
重试机制和日志工具模块
"""
import time
import logging
import functools
from typing import Callable, Any, Tuple, Type
from rag.exceptions import LLMAPIError


def setup_logger(name: str = "rag", level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: logging.Logger = None
) -> Callable:
    """
    带指数退避的重试装饰器
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        backoff_factor: 退避因子，每次重试延迟时间乘以此因子
        exceptions: 需要重试的异常类型元组
        logger: 日志记录器，如果为None则创建默认记录器
        
    Returns:
        装饰器函数
        
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def call_api():
            # API调用代码
            pass
    """
    if logger is None:
        logger = setup_logger()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # 尝试执行函数
                    result = func(*args, **kwargs)
                    
                    # 如果之前有重试，记录成功信息
                    if attempt > 0:
                        logger.info(
                            f"函数 {func.__name__} 在第 {attempt + 1} 次尝试后成功执行"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # 如果是最后一次尝试，不再重试
                    if attempt == max_retries - 1:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_retries} 次尝试后仍然失败"
                        )
                        logger.error(f"最后的错误: {str(e)}")
                        
                        # 如果是一般异常，包装为LLMAPIError
                        if not isinstance(e, LLMAPIError):
                            raise LLMAPIError(
                                f"LLM API调用失败（已重试{max_retries}次）: {str(e)}"
                            ) from e
                        else:
                            raise
                    
                    # 计算延迟时间（指数退避）
                    delay = initial_delay * (backoff_factor ** attempt)
                    
                    # 记录重试信息
                    logger.warning(
                        f"函数 {func.__name__} 执行失败（第 {attempt + 1}/{max_retries} 次尝试）"
                    )
                    logger.warning(f"错误: {str(e)}")
                    logger.warning(f"将在 {delay:.2f} 秒后重试...")
                    
                    # 等待后重试
                    time.sleep(delay)
            
            # 理论上不会到达这里，但为了安全起见
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator
