import json
import os
from typing import Dict, Optional, Union, List

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ModelService:
    """模型服务类，负责与阿里云DashScope API的交互（使用OpenAI兼容模式）"""

    def __init__(self, api_key: str = None, model_name: str = None, api_endpoint: str = None):
        """
        初始化模型服务

        Args:
            api_key: DashScope API密钥，如果为None则从环境变量获取
            model_name: 模型名称，如果为None则从环境变量获取
            api_endpoint: API端点，如果为None则使用默认值
        """
        # 从环境变量或参数获取配置
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.model_name = model_name or os.getenv('DASHSCOPE_MODEL_NAME', 'qwen-plus')

        # 使用与成功示例相同的兼容OpenAI的API端点
        self.api_endpoint = api_endpoint or os.getenv(
            'DASHSCOPE_API_ENDPOINT',
            'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
        )

        # 其他可选配置
        self.default_temperature = float(os.getenv('MODEL_TEMPERATURE', '0.3'))
        self.timeout = int(os.getenv('TIMEOUT', '60'))  # 延长超时时间

        # 验证必要配置
        self._validate_config()

    def _validate_config(self):
        """验证配置是否完整"""
        if not self.api_key:
            raise ValueError("API密钥未配置，请设置DASHSCOPE_API_KEY环境变量或传入api_key参数")

        if not self.model_name:
            raise ValueError("模型名称未配置，请设置DASHSCOPE_MODEL_NAME环境变量或传入model_name参数")

    def call_model(self, prompt: str, system_prompt: str = None, temperature: float = None) -> Optional[str]:
        """
        调用DashScope模型（使用OpenAI兼容格式）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词，默认为None
            temperature: 温度参数，控制生成随机性，默认为环境变量配置的值

        Returns:
            模型返回的内容，如果调用失败则返回None
        """
        # 使用默认温度或指定温度
        temp = temperature if temperature is not None else self.default_temperature

        # 构建消息（OpenAI格式）
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 构建请求（OpenAI兼容格式）
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # OpenAI兼容格式的请求数据
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp
        }

        try:
            # 发送请求
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 解析响应（OpenAI格式）
            result = response.json()

            # 检查是否有错误信息
            if "error" in result:
                print(f"模型调用失败: {result['error'].get('message', '未知错误')}")
                return None

            content = result['choices'][0]['message']['content']
            return content

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {str(e)}")
            return None
        except KeyError as e:
            print(f"解析响应失败，缺少关键字段: {str(e)}")
            return None
        except Exception as e:
            print(f"模型调用失败: {str(e)}")
            return None


    def call_model_for_conversion(self, item: Dict, template: str, temperature: float = None) -> Optional[
        Union[Dict, List[Dict]]]:
        """专门用于数据格式转换的模型调用方法，支持返回单条或多条数据"""
        system_prompt = "你是一个数据格式转换专家，擅长将各种数据转换为Alpaca格式。请仅返回JSON格式的结果（单条字典或多条列表），不要添加任何额外解释、代码块标记或说明文字。"

        content = self.call_model(
            prompt=template,
            system_prompt=system_prompt,
            temperature=temperature
        )

        if content:
            try:
                # 关键修复1：彻底清理代码块标记（包括```json、```及可能的其他标记）
                content = content.strip()
                # 移除开头的代码块标记（如```json、```python等）
                if content.startswith('```'):
                    content = content.split('```', 2)[-2].strip()
                # 移除结尾可能残留的标记
                if content.endswith('```'):
                    content = content.rsplit('```', 1)[0].strip()

                # 关键修复2：解析为JSON（支持字典或列表）
                alpaca_result = json.loads(content)

                # 关键修复3：校验格式（支持单条字典或多条列表）
                if isinstance(alpaca_result, dict):
                    # 单条数据：必须包含instruction和output
                    if all(k in alpaca_result for k in ['instruction', 'output']):
                        alpaca_result.setdefault('input', '')
                        return alpaca_result
                    else:
                        print(f"单条数据缺少必要字段: {alpaca_result.keys()}")
                        return None
                elif isinstance(alpaca_result, list):
                    # 多条数据：每个元素必须是符合格式的字典
                    valid_items = []
                    for item in alpaca_result:
                        if isinstance(item, dict) and all(k in item for k in ['instruction', 'output']):
                            item.setdefault('input', '')
                            valid_items.append(item)
                        else:
                            print(f"列表中存在无效项: {item}")
                    return valid_items if valid_items else None  # 返回过滤后的有效列表
                else:
                    print(f"模型返回格式错误（非字典/列表）: {type(alpaca_result)}")
                    return None

            except json.JSONDecodeError:
                print(f"模型返回的不是有效JSON: {content}")
                return None
            except Exception as e:
                print(f"解析模型响应失败: {str(e)}")
                return None

        return None

    def _try_fix_json(self, content: str) -> Optional[Dict]:
        """尝试修复可能的JSON格式错误"""
        try:
            # 尝试去除可能的代码块标记
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()

            # 再次尝试解析
            return json.loads(content)
        except:
            return None
