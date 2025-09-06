
from typing import Dict, Any


class WeatherTool():
    """天气查询工具，用于获取指定城市的天气信息"""

    # 工具元数据：供大模型识别工具功能和参数
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        return {
            "name": "weather_query",  # 工具唯一标识（小写、下划线）
            "description": "查询指定城市的天气信息，支持获取当前天气或未来几天预报",
            "parameters": {
                "city": {"type": "string", "description": "城市名称，如'北京'、'上海'"},
                "days": {"type": "int", "optional": True, "description": "查询天数，默认1天（当前天气），最多7天"}
            }
        }

    # 工具执行逻辑：实现具体功能
    @staticmethod
    def execute(city: str, days: int = 1) -> Dict[str, Any]:
        """
        查询天气信息
        :param city: 城市名称
        :param days: 查询天数（1-7）
        :return: 天气结果字典
        """
        try:
            # 实际场景中这里会调用第三方天气API（如高德、百度天气API）
            # 此处用模拟数据示例
            return {
                "success": True,
                "city": city,
                "days": days,
                "weather": [
                    {"date": "2025-09-06", "temperature": "25-32℃", "condition": "晴"}
                    for _ in range(days)
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"查询失败：{str(e)}"
            }