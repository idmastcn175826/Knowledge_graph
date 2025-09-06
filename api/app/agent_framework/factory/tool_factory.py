from abc import ABC, abstractmethod
from typing import Dict, Any, List

# 命令模式 - 工具接口
class ToolCommand(ABC):
    """工具命令接口"""
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行命令"""
        pass
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """获取命令名称"""
        pass
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """获取命令描述"""
        pass
    
    @classmethod
    @abstractmethod
    def get_parameters(cls) -> Dict[str, Any]:
        """获取命令参数描述"""
        pass

# 工厂模式 - 工具工厂
class ToolFactory:
    """工具工厂类，用于创建工具实例"""
    _tool_registry = {}
    
    @classmethod
    def register_tool(cls, tool_name: str, tool_class):
        """注册工具类"""
        if tool_name not in cls._tool_registry:
            cls._tool_registry[tool_name] = tool_class
    
    @classmethod
    def create_tool(cls, tool_name: str,** kwargs) -> ToolCommand:
        """创建工具实例"""
        if tool_name not in cls._tool_registry:
            raise ValueError(f"工具 {tool_name} 未注册")
        return cls._tool_registry[tool_name](**kwargs)
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """获取所有可用工具名称"""
        return list(cls._tool_registry.keys())
    
    @classmethod
    def get_tool_metadata(cls, tool_name: str) -> Dict[str, Any]:
        """获取工具元数据"""
        if tool_name not in cls._tool_registry:
            raise ValueError(f"工具 {tool_name} 未注册")
        tool_class = cls._tool_registry[tool_name]
        return {
            "name": tool_class.get_name(),
            "description": tool_class.get_description(),
            "parameters": tool_class.get_parameters()
        }
