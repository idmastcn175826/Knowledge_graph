import json
import os
from jinja2 import Environment, FileSystemLoader

from app.Fine_tune_datasets.foundation.data_processor import Formatter
from app.Fine_tune_datasets.services.model_service import ModelService




class AlpacaFormatter(Formatter):
    """Alpaca格式转换器"""

    def __init__(self):
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建模板路径：core/prompt/
        template_path = os.path.join(current_dir, '..', 'prompt')

        # 转换为绝对路径
        template_path = os.path.abspath(template_path)

        # 确保模板目录存在
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板目录不存在: {template_path}")

        # 检查模板文件是否存在
        template_file = os.path.join(template_path, 'alpaca_conversion.jinja2')
        if not os.path.exists(template_file):
            raise FileNotFoundError(f"模板文件不存在: {template_file}")

        print(f"加载模板路径: {template_path}")
        print(f"模板文件: {template_file}")

        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.template = self.env.get_template('alpaca_conversion.jinja2')
        self.model_service = None

    def format(self, item, model_api_key=None):
        """
        将数据项转换为Alpaca格式
        """
        # 尝试直接映射已知字段
        formatted = self._direct_map(item)

        # 如果直接映射成功，返回结果
        if formatted:
            return formatted

        # 如果直接映射失败，尝试使用模型进行转换
        return self._convert_with_model(item, model_api_key)

    def _direct_map(self, item):
        """尝试直接映射常见字段组合到Alpaca格式"""
        # 原有的直接映射逻辑
        field_mappings = [
            {
                'instruction': 'instruction',
                'input': 'input',
                'output': 'output'
            },
            {
                'instruction': 'question',
                'input': '',
                'output': 'answer'
            },
            {
                'instruction': 'command',
                'input': '',
                'output': 'response'
            },
            {
                'instruction': 'question',
                'input': 'context',
                'output': 'answer'
            }
        ]

        for mapping in field_mappings:
            try:
                result = {
                    key: item[field] if field else ''
                    for key, field in mapping.items()
                }

                if result['instruction'] and result['output']:
                    return result
            except (KeyError, TypeError):
                continue

        return None

    def _convert_with_model(self, item, api_key=None):
        """使用模型服务将原始数据转换为Alpaca格式"""
        # 初始化模型服务（如果尚未初始化）
        if self.model_service is None:
            # 使用传入的API密钥或环境变量中的密钥
            actual_api_key = api_key or os.getenv('QWEN_API_KEY')
            if not actual_api_key:
                print("警告: 未提供API密钥且环境变量中未设置QWEN_API_KEY")
                return None

            self.model_service = ModelService(api_key=actual_api_key)

        # 使用Jinja2模板渲染提示词
        prompt = self.template.render(
            data_json=json.dumps(item, ensure_ascii=False)
        )

        # 调用模型服务进行转换
        return self.model_service.call_model_for_conversion(item, prompt)