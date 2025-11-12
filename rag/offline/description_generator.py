"""
描述生成器模块
负责基于树形索引生成文档描述
"""
import os
from typing import Dict, Any
from pageindex.utils import create_clean_structure_for_description
from rag.config.config_manager import ConfigManager
from rag.utils.llm_wrapper import call_llm_with_retry
from rag.exceptions import LLMAPIError


class DescriptionGenerator:
    """描述生成器类，基于树形索引生成文档描述"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化描述生成器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.model = config.get_model_name()
        self.api_key = config.config['llm']['api_key']
        self.base_url = config.config['llm'].get('base_url')
        self.temperature = config.get_temperature()
        
    def generate_description(self, tree_structure: Dict[str, Any]) -> str:
        """
        生成文档描述
        
        Args:
            tree_structure: 文档的树形索引结构
            
        Returns:
            文档的一句话描述
            
        Raises:
            LLMAPIError: LLM API调用失败
        """
        # 使用PageIndex的create_clean_structure_for_description清理树结构
        # 移除不必要的字段如'text'，只保留用于描述生成的关键信息
        clean_structure = create_clean_structure_for_description(
            tree_structure.get('structure', tree_structure)
        )
        
        # 构建提示词
        prompt = f"""Your are an expert in generating descriptions for a document.
    You are given a structure of a document. Your task is to generate a one-sentence description for the document, which makes it easy to distinguish the document from other documents.
        
    Document Structure: {clean_structure}
    
    Directly return the description, do not include any other text.
    """
        
        # 使用带重试机制的LLM调用
        description = call_llm_with_retry(
            model=self.model,
            prompt=prompt,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_retries=3,
            initial_delay=1.0
        )
        
        return description
