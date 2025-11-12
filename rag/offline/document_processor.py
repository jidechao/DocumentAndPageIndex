"""
文档处理器模块
负责处理PDF和Markdown文档，生成树形索引
"""
import os
import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from pageindex import page_index_main, md_to_tree
from pageindex.utils import ConfigLoader
from rag.exceptions import DocumentProcessingError
from rag.config.config_manager import ConfigManager


class DocumentProcessor:
    """文档处理器类，支持批量处理PDF和Markdown文档"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化文档处理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.trees_dir = config.get_trees_dir()
        self.pageindex_config = config.get_pageindex_config()
        
        # 确保索引目录存在
        os.makedirs(self.trees_dir, exist_ok=True)
        
    def _generate_doc_id(self, file_path: str) -> str:
        """
        生成文档唯一标识符
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            文档ID (使用文件路径的hash值)
        """
        # 使用文件路径的hash值作为doc_id
        file_path_normalized = os.path.normpath(file_path)
        hash_object = hashlib.md5(file_path_normalized.encode())
        doc_id = hash_object.hexdigest()[:16]  # 使用前16位
        return doc_id
    
    def _get_tree_index_path(self, doc_id: str) -> str:
        """
        获取树形索引文件路径
        
        Args:
            doc_id: 文档ID
            
        Returns:
            树形索引文件路径
        """
        return os.path.join(self.trees_dir, f"{doc_id}_structure.json")
    
    def process_single_document(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个文档
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            包含文档信息的字典:
            {
                'doc_id': str,
                'doc_name': str,
                'file_path': str,
                'tree_index_path': str,
                'tree_structure': dict
            }
            
        Raises:
            DocumentProcessingError: 文档处理失败
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"文件不存在: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # 生成doc_id
            doc_id = self._generate_doc_id(file_path)
            tree_index_path = self._get_tree_index_path(doc_id)
            
            # 根据文件类型调用不同的处理函数
            if file_ext == '.pdf':
                tree_structure = self._process_pdf(file_path)
            elif file_ext in ['.md', '.markdown']:
                tree_structure = self._process_markdown(file_path)
            else:
                raise DocumentProcessingError(
                    f"不支持的文件格式: {file_ext}。仅支持 PDF 和 Markdown 文件"
                )
            
            # 添加doc_id到树形结构
            tree_structure['doc_id'] = doc_id
            
            # 确保doc_name包含完整的文件名（包括扩展名）
            # 如果tree_structure中的doc_name不包含扩展名，则使用完整的文件名
            original_doc_name = tree_structure.get('doc_name', '')
            file_basename = os.path.basename(file_path)
            
            # 检查doc_name是否已经包含扩展名
            if original_doc_name and not original_doc_name.endswith(file_ext):
                # 如果不包含扩展名，使用完整的文件名
                doc_name = file_basename
            else:
                # 如果已经包含扩展名或为空，使用原值或文件名
                doc_name = original_doc_name if original_doc_name else file_basename
            
            # 更新tree_structure中的doc_name
            tree_structure['doc_name'] = doc_name
            
            # 保存树形索引到文件
            with open(tree_index_path, 'w', encoding='utf-8') as f:
                json.dump(tree_structure, f, indent=2, ensure_ascii=False)
            
            return {
                'doc_id': doc_id,
                'doc_name': doc_name,
                'file_path': file_path,
                'tree_index_path': tree_index_path,
                'tree_structure': tree_structure
            }
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            raise DocumentProcessingError(
                f"处理文档 {file_path} 时发生错误: {str(e)}"
            ) from e
    
    def _process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        处理PDF文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            树形索引结构
        """
        # 构建PageIndex配置
        pageindex_config_with_model = self.pageindex_config.copy()
        pageindex_config_with_model['model'] = self.config.get_model_name()
        
        opt = ConfigLoader().load(pageindex_config_with_model)
        
        # 设置环境变量以支持自定义 base_url
        # 注意：PageIndex 内部使用 openai 库，需要通过环境变量传递 base_url
        import os
        original_base_url = os.environ.get('OPENAI_BASE_URL')
        base_url = self.config.config['llm'].get('base_url')
        
        if base_url:
            os.environ['OPENAI_BASE_URL'] = base_url
        
        try:
            # 调用PageIndex的page_index_main函数
            tree_structure = page_index_main(pdf_path, opt=opt)
        finally:
            # 恢复原始环境变量
            if original_base_url is not None:
                os.environ['OPENAI_BASE_URL'] = original_base_url
            elif 'OPENAI_BASE_URL' in os.environ:
                del os.environ['OPENAI_BASE_URL']
        
        return tree_structure
    
    def _process_markdown(self, md_path: str) -> Dict[str, Any]:
        """
        处理Markdown文档
        
        Args:
            md_path: Markdown文件路径
            
        Returns:
            树形索引结构
        """
        # 从配置中获取参数
        if_thinning = False  # 默认不进行树形精简
        min_token_threshold = self.pageindex_config.get('max_token_num_each_node', 20000)
        if_add_node_summary = self.pageindex_config.get('if_add_node_summary', 'yes')
        if_add_doc_description = self.pageindex_config.get('if_add_doc_description', 'yes')
        if_add_node_text = self.pageindex_config.get('if_add_node_text', 'yes')
        if_add_node_id = self.pageindex_config.get('if_add_node_id', 'yes')
        summary_token_threshold = 200  # 摘要token阈值
        model = self.config.get_model_name()
        
        # 设置环境变量以支持自定义 base_url
        # 注意：PageIndex 内部使用 openai 库，需要通过环境变量传递 base_url
        original_base_url = os.environ.get('OPENAI_BASE_URL')
        base_url = self.config.config['llm'].get('base_url')
        
        if base_url:
            os.environ['OPENAI_BASE_URL'] = base_url
        
        try:
            # 调用PageIndex的md_to_tree函数
            tree_structure = asyncio.run(md_to_tree(
                md_path=md_path,
                if_thinning=if_thinning,
                min_token_threshold=min_token_threshold,
                if_add_node_summary=if_add_node_summary,
                summary_token_threshold=summary_token_threshold,
                model=model,
                if_add_doc_description=if_add_doc_description,
                if_add_node_text=if_add_node_text,
                if_add_node_id=if_add_node_id
            ))
        finally:
            # 恢复原始环境变量
            if original_base_url is not None:
                os.environ['OPENAI_BASE_URL'] = original_base_url
            elif 'OPENAI_BASE_URL' in os.environ:
                del os.environ['OPENAI_BASE_URL']
        
        return tree_structure
    
    def process_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        批量处理文档
        
        Args:
            file_paths: 文档文件路径列表
            
        Returns:
            包含所有文档信息的字典:
            {
                'doc_id1': {
                    'doc_name': str,
                    'file_path': str,
                    'tree_index_path': str,
                    'tree_structure': dict
                },
                ...
            }
        """
        results = {}
        errors = []
        
        for file_path in file_paths:
            try:
                print(f"正在处理文档: {file_path}")
                doc_info = self.process_single_document(file_path)
                results[doc_info['doc_id']] = doc_info
                print(f"✓ 成功处理: {file_path}")
            except Exception as e:
                error_msg = f"处理文档 {file_path} 失败: {str(e)}"
                print(f"✗ {error_msg}")
                errors.append({
                    'file_path': file_path,
                    'error': str(e)
                })
        
        # 记录处理结果
        print(f"\n处理完成:")
        print(f"  成功: {len(results)} 个文档")
        print(f"  失败: {len(errors)} 个文档")
        
        if errors:
            print("\n失败的文档:")
            for error in errors:
                print(f"  - {error['file_path']}: {error['error']}")
        
        return results
