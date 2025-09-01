import json
from abc import ABC, abstractmethod

class DataLoader(ABC):
    """数据加载器抽象基类，定义数据加载接口"""
    
    @abstractmethod
    def load(self, source_info):
        """
        加载数据
        
        Args:
            source_info: 数据源信息，根据加载器类型不同而不同
            
        Returns:
            原始数据列表
        """

        pass

class Formatter(ABC):
    """格式化器抽象基类，定义数据格式化接口"""
    
    @abstractmethod
    def format(self, item, model_api_key=None):
        """
        格式化单条数据
        
        Args:
            item: 原始数据项
            model_api_key: 模型API密钥（如需调用大模型辅助格式化）
            
        Returns:
            格式化后的数据项
        """
        pass

class DataProcessor:
    """数据处理器，协调数据加载和格式化过程"""
    
    def __init__(self, loader: DataLoader, formatter: Formatter, model_api_key=None):
        """
        初始化数据处理器
        
        Args:
            loader: 数据加载器实例
            formatter: 格式化器实例
            model_api_key: 模型API密钥
        """
        self.loader = loader
        self.formatter = formatter
        self.model_api_key = model_api_key

    def load_data(self, source_info):
        """加载数据"""
        return self.loader.load(source_info)
    
    def convert(self, data):
        """
        转换数据格式
        
        Args:
            data: 原始数据列表
            
        Returns:
            转换后的数据集
        """
        converted = []
        for item in data:
            try:
                formatted_item = self.formatter.format(item, self.model_api_key)
                if formatted_item:
                    converted.append(formatted_item)
            except Exception as e:
                print(f"处理数据项时出错: {str(e)}, 数据项: {item}")
        return converted
    
    @staticmethod
    def save_data(data, output_path):
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class DataProcessorFactory:
    """数据处理器工厂，用于创建数据处理器实例"""
    
    def __init__(self):
        self.loaders = {}
        self.formatters = {}
    
    def register_loader(self, loader_type, loader_class):
        """注册数据加载器"""
        if not issubclass(loader_class, DataLoader):
            raise ValueError("加载器类必须继承自DataLoader")
        self.loaders[loader_type] = loader_class
    
    def register_formatter(self, formatter_type, formatter_class):
        """注册数据格式化器"""
        if not issubclass(formatter_class, Formatter):
            raise ValueError("格式化器类必须继承自Formatter")
        self.formatters[formatter_type] = formatter_class
    
    def create_processor(self, source_type, formatter_type, **kwargs):
        """
        创建数据处理器
        
        Args:
            source_type: 数据源类型
            formatter_type: 格式化器类型
           ** kwargs: 其他参数，包括source_info和模型API密钥等
            
        Returns:
            DataProcessor实例
        """
        if source_type not in self.loaders:
            raise ValueError(f"不支持的数据源类型: {source_type}")
        
        if formatter_type not in self.formatters:
            raise ValueError(f"不支持的格式化器类型: {formatter_type}")
        
        # 创建加载器和格式化器实例
        loader = self.loaders[source_type]()
        formatter = self.formatters[formatter_type]()
        
        # 提取模型API密钥
        model_api_key = kwargs.get('qwen_api_key')
        
        # 创建并返回数据处理器
        return DataProcessor(
            loader=loader,
            formatter=formatter,
            model_api_key=model_api_key
        )
