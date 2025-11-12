"""
配置管理器模块
"""
import os
import yaml
from typing import Any, Dict, Optional
from openai import OpenAI
from rag.exceptions import ConfigurationError


class ConfigManager:
    """配置管理器类，支持从YAML文件和环境变量加载配置"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 rag_config.yaml
        """
        self.config_path = config_path or "rag_config.yaml"
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
            
        Raises:
            ConfigurationError: 配置文件不存在或格式错误
        """
        if not os.path.exists(self.config_path):
            raise ConfigurationError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"读取配置文件失败: {e}")
        
        # 处理环境变量替换
        config = self._resolve_env_variables(config)
        
        # 验证必需的配置项
        self._validate_config(config)
        
        return config
    
    def _resolve_env_variables(self, config: Any) -> Any:
        """
        递归解析配置中的环境变量
        
        Args:
            config: 配置对象（可能是字典、列表或字符串）
            
        Returns:
            解析后的配置对象
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_variables(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_variables(item) for item in config]
        elif isinstance(config, str):
            # 处理 ${ENV_VAR} 格式的环境变量
            if config.startswith("${") and config.endswith("}"):
                env_var = config[2:-1]
                value = os.getenv(env_var)
                if value is None:
                    raise ConfigurationError(f"环境变量未设置: {env_var}")
                return value
            return config
        else:
            return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        验证配置的必需项
        
        Args:
            config: 配置字典
            
        Raises:
            ConfigurationError: 缺少必需的配置项
        """
        # 验证LLM配置
        if 'llm' not in config:
            raise ConfigurationError("配置文件缺少 'llm' 部分")
        
        llm_config = config['llm']
        required_llm_fields = ['provider', 'model', 'api_key']
        for field in required_llm_fields:
            if field not in llm_config:
                raise ConfigurationError(f"LLM配置缺少必需字段: {field}")
        
        # 验证路径配置
        if 'paths' not in config:
            raise ConfigurationError("配置文件缺少 'paths' 部分")
        
        # 验证PageIndex配置
        if 'pageindex' not in config:
            raise ConfigurationError("配置文件缺少 'pageindex' 部分")
    
    def get_llm_client(self) -> OpenAI:
        """
        获取LLM客户端
        
        Returns:
            OpenAI客户端实例
            
        Raises:
            ConfigurationError: LLM配置错误
        """
        llm_config = self.config['llm']
        
        try:
            # 构建客户端参数
            client_kwargs = {
                'api_key': llm_config['api_key']
            }
            
            # 如果配置了自定义base_url，则使用自定义提供者
            if llm_config.get('base_url'):
                client_kwargs['base_url'] = llm_config['base_url']
            
            client = OpenAI(**client_kwargs)
            return client
        except Exception as e:
            raise ConfigurationError(f"创建LLM客户端失败: {e}")
    
    def get_model_name(self) -> str:
        """
        获取模型名称
        
        Returns:
            模型名称字符串
        """
        return self.config['llm']['model']
    
    def get_temperature(self) -> float:
        """
        获取温度参数
        
        Returns:
            温度值
        """
        return self.config['llm'].get('temperature', 0)
    
    def get_indexes_dir(self) -> str:
        """
        获取索引目录路径
        
        Returns:
            索引目录路径
        """
        return self.config['paths']['indexes_dir']
    
    def get_trees_dir(self) -> str:
        """
        获取树形索引目录路径
        
        Returns:
            树形索引目录路径
        """
        return self.config['paths']['trees_dir']
    
    def get_directory_index_path(self) -> str:
        """
        获取文件目录索引路径
        
        Returns:
            文件目录索引路径
        """
        return self.config['paths']['directory_index']
    
    def get_pageindex_config(self) -> Dict[str, Any]:
        """
        获取PageIndex配置
        
        Returns:
            PageIndex配置字典
        """
        return self.config['pageindex']
