"""
RAG系统异常类层次结构
"""


class RAGException(Exception):
    """RAG系统基础异常类"""
    pass


class DocumentProcessingError(RAGException):
    """文档处理错误"""
    pass


class LLMAPIError(RAGException):
    """LLM API调用错误"""
    pass


class IndexLoadError(RAGException):
    """索引加载错误"""
    pass


class ConfigurationError(RAGException):
    """配置错误"""
    pass
