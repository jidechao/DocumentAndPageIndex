"""
文档搜索模块
负责基于文件目录索引查找相关文档
"""
import json
import os
from typing import List, Dict, Any
from rag.config.config_manager import ConfigManager
from rag.exceptions import LLMAPIError, IndexLoadError
from rag.utils.llm_wrapper import call_llm_with_retry


class DocSearcher:
    """文档搜索器类，基于文件目录索引查找相关文档"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化文档搜索器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.model = config.get_model_name()
        self.api_key = config.config['llm']['api_key']
        self.base_url = config.config['llm'].get('base_url')
        self.temperature = config.get_temperature()
        self.directory_index = None
        
    def load_directory_index(self, index_path: str = None) -> Dict[str, Any]:
        """
        加载文件目录索引
        
        Args:
            index_path: 索引文件路径，默认从配置中获取
            
        Returns:
            目录索引字典
            
        Raises:
            IndexLoadError: 索引文件不存在或格式错误
        """
        if index_path is None:
            index_path = self.config.get_directory_index_path()
        
        if not os.path.exists(index_path):
            raise IndexLoadError(f"文件目录索引不存在: {index_path}")
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                self.directory_index = json.load(f)
            
            # 验证索引格式
            if 'documents' not in self.directory_index:
                raise IndexLoadError("文件目录索引格式错误: 缺少 'documents' 字段")
            
            return self.directory_index
            
        except json.JSONDecodeError as e:
            raise IndexLoadError(f"文件目录索引JSON解析失败: {e}")
        except Exception as e:
            raise IndexLoadError(f"加载文件目录索引失败: {e}")
    
    def search_documents(self, query: str) -> List[str]:
        """
        搜索相关文档
        
        Args:
            query: 用户问题（重写后）
            
        Returns:
            相关文档的doc_id列表
            
        Raises:
            IndexLoadError: 目录索引未加载
            LLMAPIError: LLM API调用失败
        """
        # 确保目录索引已加载
        if self.directory_index is None:
            self.load_directory_index()
        
        # 如果没有文档，直接返回空列表
        if not self.directory_index['documents']:
            return []
        
        # 构建doc-search的prompt模板
        prompt = self._build_search_prompt(query)
        
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
        
        # 解析JSON响应，提取doc_id列表
        doc_ids = self._parse_response(response)
        
        return doc_ids
    
    def _build_search_prompt(self, query: str) -> str:
        """
        构建doc-search的prompt模板
        
        Args:
            query: 用户问题
            
        Returns:
            完整的prompt字符串
        """
        # 准备文档列表
        documents = self.directory_index['documents']
        
        prompt = f"""你将获得一个文档列表，每个文档包含ID、文件名和描述。你的任务是选择可能包含与用户问题相关信息的文档。

用户问题: {query}

文档列表:
{json.dumps(documents, ensure_ascii=False, indent=2)}

请仔细分析用户问题和每个文档的描述，判断哪些文档可能包含回答该问题所需的信息。

返回格式:
{{
    "thinking": "<你选择这些文档的推理过程>",
    "answer": <相关文档的doc_id列表，例如 ["doc_id1", "doc_id2"]。如果没有相关文档则返回 []>
}}

注意事项：
1. 只返回可能相关的文档的doc_id
2. 如果没有任何文档与问题相关，返回空列表 []
3. answer字段必须是一个列表，即使只有一个doc_id也要用列表格式

只返回JSON结构，不要输出其他内容。
"""
        return prompt
    
    def _parse_response(self, response: str) -> List[str]:
        """
        解析LLM响应，提取doc_id列表
        
        Args:
            response: LLM返回的JSON字符串
            
        Returns:
            doc_id列表
            
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
            
            # 提取doc_id列表
            if 'answer' not in result:
                raise LLMAPIError("LLM响应缺少 'answer' 字段")
            
            doc_ids = result['answer']
            
            # 验证返回的是列表
            if not isinstance(doc_ids, list):
                raise LLMAPIError(f"LLM响应的 'answer' 字段应该是列表，实际类型: {type(doc_ids)}")
            
            # 验证列表中的元素都是字符串
            for doc_id in doc_ids:
                if not isinstance(doc_id, str):
                    raise LLMAPIError(f"doc_id应该是字符串，实际类型: {type(doc_id)}")
            
            return doc_ids
            
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"解析LLM响应失败: {e}\n响应内容: {response}")
        except KeyError as e:
            raise LLMAPIError(f"LLM响应缺少必需字段: {e}")
