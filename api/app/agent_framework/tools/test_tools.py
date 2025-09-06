
from typing import Dict, Any
import math

from app.agent_framework.factory.tool_factory import ToolCommand


class ExampleSearchTool(ToolCommand):
    """示例搜索工具"""
    @classmethod
    def get_name(cls) -> str:
        return "example_search"
    
    @classmethod
    def get_description(cls) -> str:
        return "搜索工具，用于获取网络上的信息，适用于需要最新数据或外部知识的问题"
    
    @classmethod
    def get_parameters(cls) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "要搜索的查询字符串，应具体明确"
            }
        }
    
    def execute(self,** kwargs) -> Dict[str, Any]:
        query = kwargs.get("query", "")
        if not query:
            return {"error": "查询参数不能为空"}
        
        # 模拟搜索结果
        return {
            "query": query,
            "results": [
                {"title": f"关于{query}的结果1", "snippet": f"这是关于{query}的搜索结果摘要，包含相关的最新信息和数据..."},
                {"title": f"关于{query}的结果2", "snippet": f"这是另一个关于{query}的搜索结果摘要，提供了不同的视角和补充信息..."}
            ],
            "source": "模拟搜索引擎"
        }

class CalculatorTool(ToolCommand):
    """计算器工具，用于执行数学计算"""
    @classmethod
    def get_name(cls) -> str:
        return "calculator"
    
    @classmethod
    def get_description(cls) -> str:
        return "计算器工具，用于执行数学计算，支持加减乘除、幂运算等基本数学操作"
    
    @classmethod
    def get_parameters(cls) -> Dict[str, Any]:
        return {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式，例如'2 + 3 * 4'或'sqrt(16) + 5'"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        expression = kwargs.get("expression", "")
        if not expression:
            return {"error": "计算表达式不能为空"}
        
        try:
            # 安全计算表达式，限制可用函数
            allowed_globals = {
                "math": math,
                "sqrt": math.sqrt,
                "pow": math.pow,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan
            }
            result = eval(expression, allowed_globals, {})
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
        except Exception as e:
            return {"error": f"计算错误: {str(e)}", "expression": expression}
