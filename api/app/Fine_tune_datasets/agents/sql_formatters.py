import json
import os
from jinja2 import Environment, FileSystemLoader
from app.Fine_tune_datasets.foundation.data_processor import Formatter
from app.Fine_tune_datasets.services.model_service import ModelService


class SqlAlpacaFormatter(Formatter):
    """数据库结构化数据专用Alpaca格式转换器"""

    def __init__(self):
        # 模板路径设置（与非结构化共用prompt目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'prompt')
        template_path = os.path.abspath(template_path)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板目录不存在: {template_path}")

        # 加载数据库专用转换模板
        self.env = Environment(
            loader=FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.template = self.env.get_template('sql_prompt.jinja')
        self.model_service = None

    def format(self, item, model_api_key=None):
        """将数据库记录转换为Alpaca格式（instruction-input-output）"""
        if not item:
            return None

        # 调用模型服务进行转换
        return self._convert_with_model(item, model_api_key)

    def _convert_with_model(self, item, api_key=None):
        """使用模型将数据库记录转换为Alpaca格式"""
        if self.model_service is None:
            actual_api_key = api_key or os.getenv('QWEN_API_KEY')
            if not actual_api_key:
                raise ValueError("缺少模型API密钥（QWEN_API_KEY）")
            self.model_service = ModelService(api_key=actual_api_key)

        # 渲染提示词（告诉模型如何转换数据库记录）
        prompt = self.template.render(
            data_json=json.dumps(item, ensure_ascii=False, indent=2),
            example="""示例：
            原始数据: {"id":1, "question":"什么是刑法？", "answer":"刑法是规定犯罪和刑罚的法律"}
            转换后: {"instruction":"解释什么是刑法", "input":"", "output":"刑法是规定犯罪和刑罚的法律"}
            """
        )

        # 调用模型转换
        result = self.model_service.call_model_for_conversion(item, prompt)

        # 验证转换结果格式
        if result and isinstance(result, dict) and all(k in result for k in ['instruction', 'input', 'output']):
            return result
        else:
            print(f"转换失败，结果格式不正确: {result}")
            return None
