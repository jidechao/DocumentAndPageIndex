"""
问题理解模块
负责分析和重写用户问题
"""
import json
from datetime import datetime
from typing import Dict, Any
from rag.config.config_manager import ConfigManager
from rag.exceptions import LLMAPIError
from rag.utils.llm_wrapper import call_llm_with_retry


class QueryUnderstanding:
    """问题理解器类，分析和重写用户问题"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化问题理解器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.model = config.get_model_name()
        self.api_key = config.config['llm']['api_key']
        self.base_url = config.config['llm'].get('base_url')
        self.temperature = config.get_temperature()
        
    def rewrite_query(self, original_query: str) -> str:
        """
        重写用户问题
        
        Args:
            original_query: 用户原始问题
            
        Returns:
            重写后的规范查询
            
        Raises:
            LLMAPIError: LLM API调用失败
        """
        # 构建问题重写的prompt模板
        prompt = self._build_rewrite_prompt(original_query)
        
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
        
        # 解析JSON响应
        rewritten_query = self._parse_response(response)
        
        return rewritten_query
    
    def _build_rewrite_prompt(self, original_query: str) -> str:
        """
        构建问题重写的prompt模板
        
        Args:
            original_query: 用户原始问题
            
        Returns:
            完整的prompt字符串
        """
        # 获取当前时间
        current_time = datetime.now()
        current_date = current_time.strftime("%Y年%m月%d日")
        current_year = current_time.year
        
        prompt = f"""你是一个专业的问题理解助手。你的任务是将用户的口语化问题转换为更适合文档检索的规范查询。

当前时间: {current_date}
当前年份: {current_year}年

用户原始问题: {original_query}

请分析这个问题，识别其中的口语化表达、模糊表述和不规范用词，然后将其重写为更清晰、更规范的检索查询。
重写时要保留问题的核心意图和关键信息。

注意事项：
1. 如果问题中包含相对时间表达（如"去年"、"今年"、"上个月"等），请根据当前时间将其转换为具体的年份或日期
2. 保持问题的核心意图不变
3. 使用更规范、更适合检索的表达方式

返回格式:
{{
    "analysis": "<对原始问题的分析，包括时间转换的说明>",
    "rewritten_query": "<重写后的规范查询>"
}}

只返回JSON结构，不要输出其他内容。
"""
        return prompt
    
    def _parse_response(self, response: str) -> str:
        """
        解析LLM响应，提取重写后的查询
        
        Args:
            response: LLM返回的JSON字符串
            
        Returns:
            重写后的查询字符串
            
        Raises:
            LLMAPIError: JSON解析失败或缺少必需字段
        """
        try:
            # 清理响应文本，移除可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # 解析JSON
            result = json.loads(response)
            
            # 提取重写后的查询
            if 'rewritten_query' not in result:
                raise LLMAPIError("LLM响应缺少 'rewritten_query' 字段")
            
            return result['rewritten_query']
            
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"解析LLM响应失败: {e}\n响应内容: {response}")
        except KeyError as e:
            raise LLMAPIError(f"LLM响应缺少必需字段: {e}")
