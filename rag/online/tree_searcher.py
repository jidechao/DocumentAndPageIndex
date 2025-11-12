"""
树搜索模块
负责在文档树形索引中定位相关节点
"""
import json
import os
from typing import List, Dict, Any
from rag.config.config_manager import ConfigManager
from rag.exceptions import LLMAPIError, IndexLoadError
from rag.utils.llm_wrapper import call_llm_with_retry


class TreeSearcher:
    """树搜索器类，在文档树形索引中定位相关节点"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化树搜索器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.model = config.get_model_name()
        self.api_key = config.config['llm']['api_key']
        self.base_url = config.config['llm'].get('base_url')
        self.temperature = config.get_temperature()
        
    def load_tree_index(self, doc_id: str) -> Dict[str, Any]:
        """
        加载文档的树形索引
        
        Args:
            doc_id: 文档ID
            
        Returns:
            树形索引字典
            
        Raises:
            IndexLoadError: 索引文件不存在或格式错误
        """
        trees_dir = self.config.get_trees_dir()
        tree_path = os.path.join(trees_dir, f"{doc_id}_structure.json")
        
        if not os.path.exists(tree_path):
            raise IndexLoadError(f"树形索引文件不存在: {tree_path}")
        
        try:
            with open(tree_path, 'r', encoding='utf-8') as f:
                tree_index = json.load(f)
            
            # 验证索引格式
            if 'structure' not in tree_index:
                raise IndexLoadError(f"树形索引格式错误: 缺少 'structure' 字段")
            
            return tree_index
            
        except json.JSONDecodeError as e:
            raise IndexLoadError(f"树形索引JSON解析失败: {e}")
        except Exception as e:
            raise IndexLoadError(f"加载树形索引失败: {e}")
    
    def search_nodes(self, query: str, tree_structure: Dict[str, Any]) -> List[str]:
        """
        搜索相关节点
        
        Args:
            query: 用户问题（重写后）
            tree_structure: 文档树形结构
            
        Returns:
            相关节点的node_id列表
            
        Raises:
            LLMAPIError: LLM API调用失败
        """
        # 如果树结构为空，直接返回空列表
        if not tree_structure.get('structure'):
            return []
        
        # 构建tree-search的prompt模板
        prompt = self._build_search_prompt(query, tree_structure)
        
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
        
        # 解析JSON响应，提取node_id列表
        node_ids = self._parse_response(response)
        
        return node_ids
    
    def extract_node_text(self, node_ids: List[str], tree_structure: Dict[str, Any]) -> str:
        """
        从树结构中提取节点文本内容
        
        Args:
            node_ids: 节点ID列表
            tree_structure: 文档树形结构
            
        Returns:
            聚合的节点文本内容
        """
        if not node_ids:
            return ""
        
        # 构建node_id到节点的映射
        node_map = self._build_node_map(tree_structure['structure'])
        
        # 提取每个节点的信息
        extracted_texts = []
        for node_id in node_ids:
            if node_id in node_map:
                node = node_map[node_id]
                node_info = self._format_node_info(node)
                extracted_texts.append(node_info)
        
        # 聚合所有节点信息
        if extracted_texts:
            return "\n\n---\n\n".join(extracted_texts)
        else:
            return ""
    
    def _build_node_map(self, structure: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        递归构建node_id到节点的映射
        
        Args:
            structure: 树形结构列表
            
        Returns:
            node_id到节点的字典映射
        """
        node_map = {}
        
        def traverse(nodes):
            for node in nodes:
                if 'node_id' in node:
                    node_map[node['node_id']] = node
                # 递归处理子节点
                if 'nodes' in node and node['nodes']:
                    traverse(node['nodes'])
        
        traverse(structure)
        return node_map
    
    def _format_node_info(self, node: Dict[str, Any]) -> str:
        """
        格式化节点信息为文本
        
        Args:
            node: 节点字典
            
        Returns:
            格式化的节点信息文本
        """
        parts = []
        
        # 添加标题
        if 'title' in node:
            parts.append(f"标题: {node['title']}")
        
        # 添加节点ID
        if 'node_id' in node:
            parts.append(f"节点ID: {node['node_id']}")
        
        # 添加页面范围
        if 'start_index' in node and 'end_index' in node:
            parts.append(f"页面范围: {node['start_index']}-{node['end_index']}")
        
        # 添加摘要（如果有）
        if 'summary' in node and node['summary']:
            parts.append(f"摘要: {node['summary']}")
        
        # 添加文本内容（如果有）
        if 'text' in node and node['text']:
            parts.append(f"内容:\n{node['text']}")
        
        return "\n".join(parts)
    
    def _build_search_prompt(self, query: str, tree_structure: Dict[str, Any]) -> str:
        """
        构建tree-search的prompt模板
        
        Args:
            query: 用户问题
            tree_structure: 文档树形结构
            
        Returns:
            完整的prompt字符串
        """
        # 创建简化的树结构用于prompt（只保留关键信息）
        simplified_structure = self._simplify_tree_structure(tree_structure['structure'])
        
        doc_name = tree_structure.get('doc_name', '未知文档')
        
        prompt = f"""你将获得一个问题和文档的树形结构。你需要找到所有可能包含答案的节点。

用户问题: {query}

文档名称: {doc_name}

文档树形结构:
{json.dumps(simplified_structure, ensure_ascii=False, indent=2)}

请仔细分析用户问题和文档的树形结构，判断哪些节点可能包含回答该问题所需的信息。
树形结构中的每个节点包含：
- title: 节点标题
- node_id: 节点唯一标识符
- start_index/end_index: 节点对应的页面范围
- summary: 节点内容摘要（如果有）
- nodes: 子节点列表（如果有）

返回格式:
{{
    "thinking": "<你认为哪些节点相关的推理过程>",
    "node_list": <相关节点的node_id列表，例如 ["0001", "0002"]。如果没有相关节点则返回 []>
}}

注意事项：
1. 只返回可能包含答案的节点的node_id
2. 如果没有任何节点与问题相关，返回空列表 []
3. node_list字段必须是一个列表，即使只有一个node_id也要用列表格式
4. node_id必须是字符串类型

只返回JSON结构，不要输出其他内容。
"""
        return prompt
    
    def _simplify_tree_structure(self, structure: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        简化树结构，只保留用于搜索的关键信息
        
        Args:
            structure: 完整的树形结构
            
        Returns:
            简化后的树形结构
        """
        def simplify_node(node):
            simplified = {
                'title': node.get('title', ''),
                'node_id': node.get('node_id', ''),
                'start_index': node.get('start_index', 0),
                'end_index': node.get('end_index', 0)
            }
            
            # 添加摘要（如果有且不为空）
            if node.get('summary'):
                simplified['summary'] = node['summary']
            
            # 递归处理子节点
            if 'nodes' in node and node['nodes']:
                simplified['nodes'] = [simplify_node(child) for child in node['nodes']]
            
            return simplified
        
        return [simplify_node(node) for node in structure]
    
    def _parse_response(self, response: str) -> List[str]:
        """
        解析LLM响应，提取node_id列表
        
        Args:
            response: LLM返回的JSON字符串
            
        Returns:
            node_id列表
            
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
            
            # 提取node_id列表
            if 'node_list' not in result:
                raise LLMAPIError("LLM响应缺少 'node_list' 字段")
            
            node_ids = result['node_list']
            
            # 验证返回的是列表
            if not isinstance(node_ids, list):
                raise LLMAPIError(f"LLM响应的 'node_list' 字段应该是列表，实际类型: {type(node_ids)}")
            
            # 验证列表中的元素都是字符串
            for node_id in node_ids:
                if not isinstance(node_id, str):
                    raise LLMAPIError(f"node_id应该是字符串，实际类型: {type(node_id)}")
            
            return node_ids
            
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"解析LLM响应失败: {e}\n响应内容: {response}")
        except KeyError as e:
            raise LLMAPIError(f"LLM响应缺少必需字段: {e}")
