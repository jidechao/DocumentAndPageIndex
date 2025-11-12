"""
LLM API调用包装器
提供带重试机制和错误处理的LLM调用功能
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from openai import OpenAI, AsyncOpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from rag.exceptions import LLMAPIError
from rag.utils.retry import retry_with_backoff, setup_logger


# 设置日志记录器
logger = setup_logger("rag.llm")


async def call_llm_with_retry_stream(
    model: str,
    prompt: str,
    api_key: str,
    base_url: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0,
) -> AsyncGenerator[str, None]:
    """
    带流式输出的异步LLM API调用
    
    Args:
        model: 模型名称
        prompt: 提示词
        api_key: API密钥
        base_url: 自定义API基础URL（可选）
        chat_history: 聊天历史（可选）
        temperature: 温度参数
        
    Yields:
        LLM响应的文本片段
        
    Raises:
        LLMAPIError: API调用失败
    """
    try:
        # 构建客户端参数
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        # 创建异步OpenAI客户端
        client = AsyncOpenAI(**client_kwargs)
        
        # 构建消息列表
        if chat_history:
            messages = chat_history.copy()
            messages.append({"role": "user", "content": prompt})
        else:
            messages = [{"role": "user", "content": prompt}]
        
        # 记录API调用信息
        logger.debug(f"调用LLM API (异步流式) - 模型: {model}, 消息数: {len(messages)}")
        
        # 调用API（异步流式）
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        # 逐块返回响应
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
        
        logger.debug(f"LLM API异步流式调用完成")
        
    except APIError as e:
        logger.error(f"OpenAI API错误: {e}")
        raise LLMAPIError(f"OpenAI API错误: {e}") from e
        
    except APIConnectionError as e:
        logger.error(f"API连接错误: {e}")
        raise LLMAPIError(f"无法连接到API服务: {e}") from e
        
    except RateLimitError as e:
        logger.error(f"API速率限制: {e}")
        raise LLMAPIError(f"API请求速率超限，请稍后重试: {e}") from e
        
    except APITimeoutError as e:
        logger.error(f"API超时: {e}")
        raise LLMAPIError(f"API请求超时: {e}") from e
        
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise LLMAPIError(f"LLM API调用失败: {e}") from e


def call_llm_with_retry(
    model: str,
    prompt: str,
    api_key: str,
    base_url: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> str:
    """
    带重试机制的LLM API调用
    
    Args:
        model: 模型名称
        prompt: 提示词
        api_key: API密钥
        base_url: 自定义API基础URL（可选）
        chat_history: 聊天历史（可选）
        temperature: 温度参数
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        
    Returns:
        LLM响应文本
        
    Raises:
        LLMAPIError: API调用失败
    """
    # 使用retry装饰器包装实际的API调用
    @retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=2.0,
        exceptions=(
            APIError,
            APIConnectionError,
            RateLimitError,
            APITimeoutError,
            Exception
        ),
        logger=logger
    )
    def _call_api():
        """实际的API调用函数"""
        try:
            # 构建客户端参数
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            
            # 创建OpenAI客户端
            client = OpenAI(**client_kwargs)
            
            # 构建消息列表
            if chat_history:
                messages = chat_history.copy()
                messages.append({"role": "user", "content": prompt})
            else:
                messages = [{"role": "user", "content": prompt}]
            
            # 记录API调用信息
            logger.debug(f"调用LLM API - 模型: {model}, 消息数: {len(messages)}")
            
            # 调用API
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            
            # 记录成功信息
            logger.debug(f"LLM API调用成功 - 响应长度: {len(content)} 字符")
            
            return content
            
        except APIError as e:
            logger.error(f"OpenAI API错误: {e}")
            raise LLMAPIError(f"OpenAI API错误: {e}") from e
            
        except APIConnectionError as e:
            logger.error(f"API连接错误: {e}")
            raise LLMAPIError(f"无法连接到API服务: {e}") from e
            
        except RateLimitError as e:
            logger.error(f"API速率限制: {e}")
            raise LLMAPIError(f"API请求速率超限，请稍后重试: {e}") from e
            
        except APITimeoutError as e:
            logger.error(f"API超时: {e}")
            raise LLMAPIError(f"API请求超时: {e}") from e
            
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise LLMAPIError(f"LLM API调用失败: {e}") from e
    
    # 执行带重试的API调用
    try:
        return _call_api()
    except LLMAPIError:
        # 直接抛出LLMAPIError
        raise
    except Exception as e:
        # 包装其他异常
        logger.error(f"LLM调用失败: {e}")
        raise LLMAPIError(f"LLM调用失败: {e}") from e


def get_user_friendly_error_message(error: Exception) -> str:
    """
    将技术错误转换为用户友好的错误消息
    
    Args:
        error: 异常对象
        
    Returns:
        用户友好的错误消息
    """
    error_str = str(error).lower()
    
    # API密钥相关错误
    if "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
        return (
            "API密钥验证失败。请检查：\n"
            "1. 环境变量中的API密钥是否正确设置\n"
            "2. API密钥是否有效且未过期\n"
            "3. 如果使用自定义提供者，请确认base_url和api_key配置正确"
        )
    
    # 网络连接错误
    if "connection" in error_str or "network" in error_str:
        return (
            "网络连接失败。请检查：\n"
            "1. 网络连接是否正常\n"
            "2. 如果使用自定义提供者，请确认base_url是否正确\n"
            "3. 防火墙或代理设置是否阻止了连接"
        )
    
    # 速率限制错误
    if "rate limit" in error_str or "too many requests" in error_str:
        return (
            "API请求速率超限。建议：\n"
            "1. 等待几分钟后重试\n"
            "2. 减少并发请求数量\n"
            "3. 考虑升级API服务计划"
        )
    
    # 超时错误
    if "timeout" in error_str:
        return (
            "API请求超时。建议：\n"
            "1. 检查网络连接稳定性\n"
            "2. 稍后重试\n"
            "3. 如果问题持续，可能是服务端负载过高"
        )
    
    # 模型不存在错误
    if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
        return (
            "指定的模型不存在或无权访问。请检查：\n"
            "1. 配置文件中的model_name是否正确\n"
            "2. 您的API密钥是否有权访问该模型\n"
            "3. 模型名称拼写是否正确"
        )
    
    # 通用错误
    return (
        f"发生错误: {str(error)}\n"
        "建议：\n"
        "1. 检查配置文件是否正确\n"
        "2. 查看日志获取详细错误信息\n"
        "3. 如果问题持续，请联系技术支持"
    )
