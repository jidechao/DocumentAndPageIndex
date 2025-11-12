#!/usr/bin/env python3
"""
RAG系统离线索引主流程脚本
支持单文件和目录批量处理
"""
import os
import sys
import argparse
import glob
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from rag.config.config_manager import ConfigManager
from rag.offline.document_processor import DocumentProcessor
from rag.offline.description_generator import DescriptionGenerator
from rag.offline.directory_index_builder import DirectoryIndexBuilder
from rag.exceptions import RAGException, LLMAPIError, ConfigurationError
from rag.utils.llm_wrapper import get_user_friendly_error_message
from rag.utils.retry import setup_logger

# 设置日志记录器
logger = setup_logger("rag.index")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='RAG系统离线索引 - 处理文档并构建索引',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理单个文档
  python run_rag_index.py --file_path document.pdf
  
  # 批量处理目录下的所有文档
  python run_rag_index.py --dir_path ./documents
  
  # 指定配置文件
  python run_rag_index.py --dir_path ./documents --config custom_config.yaml
        """
    )
    
    # 文件输入参数（互斥）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--file_path',
        type=str,
        help='单个文档文件路径 (PDF或Markdown)'
    )
    input_group.add_argument(
        '--dir_path',
        type=str,
        help='文档目录路径，将处理目录下所有PDF和Markdown文件'
    )
    
    # 配置文件参数
    parser.add_argument(
        '--config',
        type=str,
        default='rag_config.yaml',
        help='配置文件路径 (默认: rag_config.yaml)'
    )
    
    # 递归搜索参数
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='递归搜索子目录中的文档'
    )
    
    return parser.parse_args()


def collect_document_files(dir_path: str, recursive: bool = False) -> List[str]:
    """
    收集目录下的所有文档文件
    
    Args:
        dir_path: 目录路径
        recursive: 是否递归搜索子目录
        
    Returns:
        文档文件路径列表
    """
    supported_extensions = ['.pdf', '.md', '.markdown']
    file_paths = []
    
    if recursive:
        # 递归搜索
        for ext in supported_extensions:
            pattern = os.path.join(dir_path, '**', f'*{ext}')
            file_paths.extend(glob.glob(pattern, recursive=True))
    else:
        # 只搜索当前目录
        for ext in supported_extensions:
            pattern = os.path.join(dir_path, f'*{ext}')
            file_paths.extend(glob.glob(pattern))
    
    return sorted(file_paths)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    print("=" * 70)
    print("RAG系统 - 离线索引阶段")
    print("=" * 70)
    print()
    
    try:
        # 1. 加载配置
        print(f"[1/4] 加载配置文件: {args.config}")
        config = ConfigManager(args.config)
        print(f"✓ 配置加载成功")
        print(f"  - 模型: {config.get_model_name()}")
        print(f"  - 索引目录: {config.get_indexes_dir()}")
        print()
        
        # 2. 收集要处理的文档
        print("[2/4] 收集文档文件")
        if args.file_path:
            # 单文件模式
            if not os.path.exists(args.file_path):
                print(f"✗ 错误: 文件不存在: {args.file_path}")
                sys.exit(1)
            file_paths = [args.file_path]
            print(f"✓ 找到 1 个文档")
        else:
            # 目录模式
            if not os.path.isdir(args.dir_path):
                print(f"✗ 错误: 目录不存在: {args.dir_path}")
                sys.exit(1)
            file_paths = collect_document_files(args.dir_path, args.recursive)
            if not file_paths:
                print(f"✗ 错误: 目录中没有找到支持的文档文件 (PDF, Markdown)")
                sys.exit(1)
            print(f"✓ 找到 {len(file_paths)} 个文档")
        
        # 显示文档列表
        for i, fp in enumerate(file_paths, 1):
            print(f"  {i}. {fp}")
        print()
        
        # 3. 处理文档并生成描述
        print("[3/4] 处理文档并生成树形索引")
        print("-" * 70)
        
        # 初始化处理器
        doc_processor = DocumentProcessor(config)
        desc_generator = DescriptionGenerator(config)
        
        # 批量处理文档
        documents_info = doc_processor.process_documents(file_paths)
        
        if not documents_info:
            print("\n✗ 错误: 没有成功处理任何文档")
            sys.exit(1)
        
        print("-" * 70)
        print()
        
        # 为每个文档生成描述
        print("生成文档描述...")
        for doc_id, doc_info in documents_info.items():
            try:
                print(f"  正在生成描述: {doc_info['doc_name']}")
                description = desc_generator.generate_description(
                    doc_info['tree_structure']
                )
                doc_info['doc_description'] = description
                print(f"  ✓ 描述: {description[:100]}...")
            except Exception as e:
                print(f"  ✗ 生成描述失败: {str(e)}")
                doc_info['doc_description'] = ""
        print()
        
        # 4. 构建文件目录索引
        print("[4/4] 构建文件目录索引")
        index_builder = DirectoryIndexBuilder(config)
        directory_index_path = index_builder.build_directory_index(documents_info)
        print()
        
        # 显示完成信息
        print("=" * 70)
        print("✓ 离线索引完成!")
        print("=" * 70)
        print(f"成功处理: {len(documents_info)} 个文档")
        print(f"文件目录索引: {directory_index_path}")
        print(f"树形索引目录: {config.get_trees_dir()}")
        print()
        print("现在可以使用 run_rag_qa.py 进行在线问答")
        print("=" * 70)
        
    except ConfigurationError as e:
        print(f"\n✗ 配置错误: {str(e)}")
        logger.error(f"配置错误: {str(e)}")
        sys.exit(1)
    except LLMAPIError as e:
        print(f"\n✗ LLM API调用失败:")
        print(get_user_friendly_error_message(e))
        logger.error(f"LLM API错误: {str(e)}")
        sys.exit(1)
    except RAGException as e:
        print(f"\n✗ 错误: {str(e)}")
        logger.error(f"RAG错误: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断操作")
        logger.info("用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 未预期的错误: {str(e)}")
        print("\n建议:")
        print("1. 检查配置文件是否正确")
        print("2. 确认所有依赖包已正确安装")
        print("3. 查看日志获取详细错误信息")
        logger.error(f"未预期的错误: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
