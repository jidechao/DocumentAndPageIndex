#!/usr/bin/env python3
"""
RAG系统在线搜索主流程脚本
支持交互式和单次问答模式
"""
import sys
import argparse
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from rag.config.config_manager import ConfigManager
from rag.online.query_understanding import QueryUnderstanding
from rag.online.doc_searcher import DocSearcher
from rag.online.tree_searcher import TreeSearcher
from rag.online.answer_generator import AnswerGenerator
from rag.exceptions import RAGException, LLMAPIError, ConfigurationError, IndexLoadError
from rag.utils.llm_wrapper import get_user_friendly_error_message
from rag.utils.retry import setup_logger

# 设置日志记录器
logger = setup_logger("rag.qa")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='RAG系统在线搜索 - 智能问答',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式问答模式
  python run_rag_qa.py
  
  # 单次问答模式
  python run_rag_qa.py --query "用户问题"
  
  # 指定配置文件
  python run_rag_qa.py --config custom_config.yaml
  
  # 跳过问题重写
  python run_rag_qa.py --no-rewrite
        """
    )
    
    # 问题参数
    parser.add_argument(
        '--query',
        type=str,
        help='用户问题（单次问答模式）'
    )
    
    # 配置文件参数
    parser.add_argument(
        '--config',
        type=str,
        default='rag_config.yaml',
        help='配置文件路径 (默认: rag_config.yaml)'
    )
    
    # 问题重写开关
    parser.add_argument(
        '--no-rewrite',
        action='store_true',
        help='跳过问题重写步骤'
    )
    
    # 详细输出
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细的处理过程'
    )
    
    return parser.parse_args()


class RAGQASystem:
    """RAG问答系统主类"""
    
    def __init__(self, config: ConfigManager, verbose: bool = False, enable_rewrite: bool = True):
        """
        初始化RAG问答系统
        
        Args:
            config: 配置管理器实例
            verbose: 是否显示详细输出
            enable_rewrite: 是否启用问题重写
        """
        self.config = config
        self.verbose = verbose
        self.enable_rewrite = enable_rewrite
        
        # 初始化各个模块
        self.query_understanding = QueryUnderstanding(config) if enable_rewrite else None
        self.doc_searcher = DocSearcher(config)
        self.tree_searcher = TreeSearcher(config)
        self.answer_generator = AnswerGenerator(config)
        
        # 加载文件目录索引
        if self.verbose:
            print("正在加载文件目录索引...")
        self.doc_searcher.load_directory_index()
        if self.verbose:
            num_docs = len(self.doc_searcher.directory_index['documents'])
            print(f"✓ 已加载 {num_docs} 个文档的索引\n")
    
    async def answer_question_stream(self, original_query: str):
        """
        流式回答用户问题
        
        Args:
            original_query: 用户原始问题
            
        Yields:
            答案的文本片段或状态消息
        """
        try:
            # 步骤1: 问题理解和重写
            if self.enable_rewrite:
                if self.verbose:
                    print("[1/4] 问题理解和重写")
                    print(f"原始问题: {original_query}")
                else:
                    print("正在理解问题...", end="", flush=True)
                
                rewritten_query = self.query_understanding.rewrite_query(original_query)
                
                if self.verbose:
                    print(f"重写问题: {rewritten_query}")
                    print()
                else:
                    print(" ✓")
            else:
                rewritten_query = original_query
                if self.verbose:
                    print("[1/4] 跳过问题重写")
                    print(f"问题: {original_query}")
                    print()
            
            # 步骤2: Doc-Search - 查找相关文档
            if self.verbose:
                print("[2/4] 搜索相关文档 (Doc-Search)")
            else:
                print("正在搜索相关文档...", end="", flush=True)
            
            doc_ids = self.doc_searcher.search_documents(rewritten_query)
            
            if self.verbose:
                if doc_ids:
                    print(f"✓ 找到 {len(doc_ids)} 个相关文档: {doc_ids}")
                else:
                    print("✗ 未找到相关文档")
                print()
            else:
                if doc_ids:
                    print(f" ✓ (找到 {len(doc_ids)} 个)")
                else:
                    print(" ✗")
            
            # 判断: doc_id列表是否为空
            if not doc_ids:
                yield self.answer_generator.get_no_answer_message()
                return
            
            # 步骤3: Tree-Search - 在每个相关文档中查找相关节点
            if self.verbose:
                print("[3/4] 在文档中搜索相关节点 (Tree-Search)")
            else:
                print("正在搜索相关内容...", end="", flush=True)
            
            all_contexts = []
            has_any_nodes = False
            
            for doc_id in doc_ids:
                try:
                    # 加载树形索引
                    tree_index = self.tree_searcher.load_tree_index(doc_id)
                    doc_name = tree_index.get('doc_name', doc_id)
                    
                    if self.verbose:
                        print(f"  正在搜索文档: {doc_name}")
                    
                    # 搜索相关节点
                    node_ids = self.tree_searcher.search_nodes(rewritten_query, tree_index)
                    
                    if node_ids:
                        has_any_nodes = True
                        if self.verbose:
                            print(f"  ✓ 找到 {len(node_ids)} 个相关节点: {node_ids}")
                        
                        # 提取节点文本
                        context = self.tree_searcher.extract_node_text(node_ids, tree_index)
                        
                        # 添加文档来源信息
                        context_with_source = f"[来源文档: {doc_name}]\n\n{context}"
                        all_contexts.append(context_with_source)
                    else:
                        if self.verbose:
                            print(f"  ✗ 未找到相关节点")
                
                except Exception as e:
                    if self.verbose:
                        print(f"  ✗ 处理文档 {doc_id} 时出错: {str(e)}")
                    continue
            
            if self.verbose:
                print()
            else:
                if has_any_nodes:
                    print(" ✓")
                else:
                    print(" ✗")
            
            # 判断: 所有文档的node_id列表是否都为空
            if not has_any_nodes:
                yield self.answer_generator.get_no_answer_message()
                return
            
            # 步骤4: 答案生成
            if self.verbose:
                print("[4/4] 生成答案")
            else:
                print("正在生成答案...\n")
            
            # 聚合所有上下文
            combined_context = "\n\n==========\n\n".join(all_contexts)
            
            # 流式生成答案
            async for chunk in self.answer_generator.generate_answer_stream(original_query, combined_context):
                yield chunk
            
            if self.verbose:
                print("\n✓ 答案生成完成")
                print()
            
        except LLMAPIError as e:
            logger.error(f"LLM API错误: {str(e)}")
            error_msg = get_user_friendly_error_message(e)
            yield f"\nLLM API调用失败:\n{error_msg}"
        except RAGException as e:
            logger.error(f"RAG错误: {str(e)}")
            yield f"\n错误: {str(e)}"
        except Exception as e:
            logger.error(f"未预期的错误: {str(e)}", exc_info=True)
            yield f"\n未预期的错误: {str(e)}"
    
    def answer_question(self, original_query: str) -> str:
        """
        回答用户问题
        
        Args:
            original_query: 用户原始问题
            
        Returns:
            答案字符串
        """
        try:
            # 步骤1: 问题理解和重写
            if self.enable_rewrite:
                if self.verbose:
                    print("[1/4] 问题理解和重写")
                    print(f"原始问题: {original_query}")
                
                rewritten_query = self.query_understanding.rewrite_query(original_query)
                
                if self.verbose:
                    print(f"重写问题: {rewritten_query}")
                    print()
            else:
                rewritten_query = original_query
                if self.verbose:
                    print("[1/4] 跳过问题重写")
                    print(f"问题: {original_query}")
                    print()
            
            # 步骤2: Doc-Search - 查找相关文档
            if self.verbose:
                print("[2/4] 搜索相关文档 (Doc-Search)")
            
            doc_ids = self.doc_searcher.search_documents(rewritten_query)
            
            if self.verbose:
                if doc_ids:
                    print(f"✓ 找到 {len(doc_ids)} 个相关文档: {doc_ids}")
                else:
                    print("✗ 未找到相关文档")
                print()
            
            # 判断: doc_id列表是否为空
            if not doc_ids:
                return self.answer_generator.get_no_answer_message()
            
            # 步骤3: Tree-Search - 在每个相关文档中查找相关节点
            if self.verbose:
                print("[3/4] 在文档中搜索相关节点 (Tree-Search)")
            
            all_contexts = []
            has_any_nodes = False
            
            for doc_id in doc_ids:
                try:
                    # 加载树形索引
                    tree_index = self.tree_searcher.load_tree_index(doc_id)
                    doc_name = tree_index.get('doc_name', doc_id)
                    
                    if self.verbose:
                        print(f"  正在搜索文档: {doc_name}")
                    
                    # 搜索相关节点
                    node_ids = self.tree_searcher.search_nodes(rewritten_query, tree_index)
                    
                    if node_ids:
                        has_any_nodes = True
                        if self.verbose:
                            print(f"  ✓ 找到 {len(node_ids)} 个相关节点: {node_ids}")
                        
                        # 提取节点文本
                        context = self.tree_searcher.extract_node_text(node_ids, tree_index)
                        
                        # 添加文档来源信息
                        context_with_source = f"[来源文档: {doc_name}]\n\n{context}"
                        all_contexts.append(context_with_source)
                    else:
                        if self.verbose:
                            print(f"  ✗ 未找到相关节点")
                
                except Exception as e:
                    if self.verbose:
                        print(f"  ✗ 处理文档 {doc_id} 时出错: {str(e)}")
                    continue
            
            if self.verbose:
                print()
            
            # 判断: 所有文档的node_id列表是否都为空
            if not has_any_nodes:
                return self.answer_generator.get_no_answer_message()
            
            # 步骤4: 答案生成
            if self.verbose:
                print("[4/4] 生成答案")
            
            # 聚合所有上下文
            combined_context = "\n\n==========\n\n".join(all_contexts)
            
            # 生成答案
            answer = self.answer_generator.generate_answer(original_query, combined_context)
            
            if self.verbose:
                print("✓ 答案生成完成")
                print()
            
            return answer
            
        except LLMAPIError as e:
            logger.error(f"LLM API错误: {str(e)}")
            error_msg = get_user_friendly_error_message(e)
            return f"LLM API调用失败:\n{error_msg}"
        except RAGException as e:
            logger.error(f"RAG错误: {str(e)}")
            return f"错误: {str(e)}"
        except Exception as e:
            logger.error(f"未预期的错误: {str(e)}", exc_info=True)
            return f"未预期的错误: {str(e)}"


async def interactive_mode_async(qa_system: RAGQASystem):
    """
    异步交互式问答模式（支持流式输出）
    
    Args:
        qa_system: RAG问答系统实例
    """
    print("=" * 70)
    print("RAG系统 - 交互式问答模式")
    print("=" * 70)
    print("输入问题开始问答，输入 'quit' 或 'exit' 退出")
    print("=" * 70)
    print()
    
    while True:
        try:
            # 获取用户输入
            query = input("问题: ").strip()
            
            # 检查退出命令
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n再见!")
                break
            
            # 跳过空输入
            if not query:
                continue
            
            print()
            
            # 流式回答问题
            print("-" * 70)
            print("答案:")
            
            async for chunk in qa_system.answer_question_stream(query):
                print(chunk, end="", flush=True)
            
            print()
            print("-" * 70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except EOFError:
            print("\n\n再见!")
            break


def interactive_mode(qa_system: RAGQASystem):
    """
    交互式问答模式（包装异步函数）
    
    Args:
        qa_system: RAG问答系统实例
    """
    asyncio.run(interactive_mode_async(qa_system))


async def single_query_mode_async(qa_system: RAGQASystem, query: str):
    """
    异步单次问答模式（支持流式输出）
    
    Args:
        qa_system: RAG问答系统实例
        query: 用户问题
    """
    print("=" * 70)
    print("RAG系统 - 单次问答模式")
    print("=" * 70)
    print(f"问题: {query}")
    print("=" * 70)
    print()
    
    # 流式回答问题
    print("-" * 70)
    print("答案:")
    
    async for chunk in qa_system.answer_question_stream(query):
        print(chunk, end="", flush=True)
    
    print()
    print("-" * 70)


def single_query_mode(qa_system: RAGQASystem, query: str):
    """
    单次问答模式（包装异步函数）
    
    Args:
        qa_system: RAG问答系统实例
        query: 用户问题
    """
    asyncio.run(single_query_mode_async(qa_system, query))


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    try:
        # 加载配置
        if args.verbose:
            print(f"加载配置文件: {args.config}")
        config = ConfigManager(args.config)
        if args.verbose:
            print(f"✓ 配置加载成功")
            print(f"  - 模型: {config.get_model_name()}")
            print()
        
        # 初始化RAG问答系统
        qa_system = RAGQASystem(
            config=config,
            verbose=args.verbose,
            enable_rewrite=not args.no_rewrite
        )
        
        # 根据模式运行
        if args.query:
            # 单次问答模式
            single_query_mode(qa_system, args.query)
        else:
            # 交互式问答模式
            interactive_mode(qa_system)
        
    except ConfigurationError as e:
        print(f"\n✗ 配置错误: {str(e)}")
        logger.error(f"配置错误: {str(e)}")
        sys.exit(1)
    except IndexLoadError as e:
        print(f"\n✗ 索引加载失败: {str(e)}")
        print("\n建议:")
        print("1. 确认已运行 run_rag_index.py 生成索引")
        print("2. 检查索引文件路径是否正确")
        print("3. 确认索引文件格式是否正确")
        logger.error(f"索引加载错误: {str(e)}")
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
