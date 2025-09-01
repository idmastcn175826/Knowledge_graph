import json
import os
from jinja2 import Environment, FileSystemLoader
from app.Fine_tune_datasets.foundation.data_processor import Formatter
from app.Fine_tune_datasets.services.model_service import ModelService


class UnstructuredAlpacaFormatter(Formatter):
    """非结构化数据Alpaca格式转换器"""

    def __init__(self):
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'prompt')
        template_path = os.path.abspath(template_path)

        # 确保模板目录存在
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板目录不存在: {template_path}")

        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 使用不同的模板
        self.template = self.env.get_template('unstructured_alpaca_conversion.jinja2')
        self.model_service = None

    def format(self, item, model_api_key=None):
        """
        将非结构化数据转换为Alpaca格式
        """
        # 对于非结构化数据，直接使用模型进行转换
        return self._convert_with_model(item, model_api_key)

    def _convert_with_model(self, item, api_key=None):
        """使用模型服务将非结构化数据转换为Alpaca格式"""
        # 初始化模型服务
        if self.model_service is None:
            actual_api_key = api_key or os.getenv('QWEN_API_KEY')
            if not actual_api_key:
                print("警告: 未提供API密钥")
                return None
            self.model_service = ModelService(api_key=actual_api_key)

        # 使用Jinja2模板渲染提示词
        prompt = self.template.render(
            data_json=json.dumps(item, ensure_ascii=False, indent=2)
        )

        # 调用模型服务进行转换
        result = self.model_service.call_model_for_conversion(item, prompt)

        # 如果是列表形式的结果，展开它
        if result and isinstance(result, list):
            return result
        elif result:
            return [result]

        return None