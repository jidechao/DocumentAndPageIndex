"""
答案生成模块
负责基于检索内容生成答案
"""
from typing import AsyncGenerator
from rag.config.config_manager import ConfigManager
from rag.exceptions import LLMAPIError
from rag.utils.llm_wrapper import call_llm_with_retry, call_llm_with_retry_stream


class AnswerGenerator:
    """答案生成器类，基于检索内容生成答案"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化答案生成器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.model = config.get_model_name()
        self.api_key = config.config['llm']['api_key']
        self.base_url = config.config['llm'].get('base_url')
        self.temperature = config.get_temperature()
        
    def generate_answer(self, query: str, context: str) -> str:
        """
        生成答案
        
        Args:
            query: 用户问题（原始问题）
            context: 检索到的上下文内容
            
        Returns:
            生成的答案
            
        Raises:
            LLMAPIError: LLM API调用失败
        """
        # 构建答案生成的prompt模板
        prompt = self._build_answer_prompt(query, context)
        
        # 使用带重试机制的LLM调用
        response = call_llm_with_retry(
            model=self.model,
            prompt=prompt,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_retries=3,
            initial_delay=1.0
        )
        
        return response.strip()
    
    async def generate_answer_stream(self, query: str, context: str) -> AsyncGenerator[str, None]:
        """
        流式生成答案
        
        Args:
            query: 用户问题（原始问题）
            context: 检索到的上下文内容
            
        Yields:
            答案的文本片段
            
        Raises:
            LLMAPIError: LLM API调用失败
        """
        # 构建答案生成的prompt模板
        prompt = self._build_answer_prompt(query, context)
        
        # 使用异步流式LLM调用
        async for chunk in call_llm_with_retry_stream(
            model=self.model,
            prompt=prompt,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature
        ):
            yield chunk
    
    def get_no_answer_message(self) -> str:
        """
        获取无法回答的消息
        
        Returns:
            无法回答的友好提示消息
        """
        return "很抱歉，根据我掌握知识库内容，尚无法回答这个问题。我会尽快学习我所欠缺的知识，以便更好的为您服务。"
    
    def _build_answer_prompt(self, query: str, context: str) -> str:
        """
        构建答案生成的prompt模板
        
        Args:
            query: 用户问题
            context: 检索到的上下文内容
            
        Returns:
            完整的prompt字符串
        """
        prompt = f"""你是一个专业的问答助手。请根据提供的上下文内容回答用户的问题。

用户问题: {query}

上下文内容:
{context}

请基于上述上下文内容回答用户的问题。如果上下文中没有足够的信息来回答问题，请明确说明。

直接返回答案，不要输出其他内容。
"""
        return prompt
