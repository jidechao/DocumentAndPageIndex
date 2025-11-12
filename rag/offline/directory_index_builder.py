"""
目录索引构建器模块
负责聚合所有文档信息并构建文件目录索引
"""
import os
import json
from typing import Dict, Any
from rag.config.config_manager import ConfigManager
from rag.exceptions import IndexLoadError


class DirectoryIndexBuilder:
    """目录索引构建器类，聚合所有文档信息并生成文件目录索引"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化目录索引构建器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.directory_index_path = config.get_directory_index_path()
        
        # 确保索引目录存在
        index_dir = os.path.dirname(self.directory_index_path)
        if index_dir:
            os.makedirs(index_dir, exist_ok=True)
        
    def build_directory_index(self, documents_info: Dict[str, Any]) -> str:
        """
        构建文件目录索引
        
        Args:
            documents_info: 文档信息字典，格式为:
                {
                    'doc_id1': {
                        'doc_name': str,
                        'file_path': str,
                        'tree_index_path': str,
                        'tree_structure': dict,
                        'doc_description': str  # 可选，如果已生成
                    },
                    ...
                }
            
        Returns:
            目录索引文件路径
            
        Raises:
            IndexLoadError: 构建索引失败
        """
        try:
            # 构建文档列表
            documents = []
            for doc_id, doc_info in documents_info.items():
                document_entry = {
                    'doc_id': doc_id,
                    'doc_name': doc_info.get('doc_name', 'Unknown'),
                    'doc_description': doc_info.get('doc_description', '')
                }
                documents.append(document_entry)
            
            # 构建目录索引结构
            directory_index = {
                'documents': documents
            }
            
            # 保存到JSON文件
            with open(self.directory_index_path, 'w', encoding='utf-8') as f:
                json.dump(directory_index, f, indent=2, ensure_ascii=False)
            
            print(f"✓ 文件目录索引已保存到: {self.directory_index_path}")
            print(f"  包含 {len(documents)} 个文档")
            
            return self.directory_index_path
            
        except Exception as e:
            raise IndexLoadError(
                f"构建文件目录索引失败: {str(e)}"
            ) from e
