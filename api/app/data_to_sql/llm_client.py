import requests

from app.config.config import settings

import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """大模型客户端，用于生成SQL语句"""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = settings.QWEN_API_BASE_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.api_key = settings.QWEN_DEFAULT_API_KEY

    def generate_sql(self, question, db_type, table_name=None):
        """
        根据自然语言问题生成SQL语句
        """
        # 构建提示词
        table_info = f"表名为: {table_name}" if table_name else "请根据问题推断合适的表"
        prompt = f"""
        请将以下问题转换为{db_type.value}数据库的SQL查询语句。
        {table_info}。
        只返回SQL语句，不要包含任何解释或额外内容。

        问题: {question}
        SQL: 
        """

        try:
            # DashScope API 使用不同的请求格式
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # DashScope API 使用 messages 格式
            data = {
                "model": "qwen-turbo",  # 或其他支持的模型
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个SQL专家，能够将自然语言问题转换为准确的SQL查询语句。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }

            logger.info(f"调用LLM API: {self.api_url}")
            response = requests.post(self.api_url, json=data, headers=headers)
            response.raise_for_status()

            # 解析 DashScope API 响应
            result = response.json()
            logger.info(f"LLM API响应: {result}")

            # DashScope API 返回格式不同
            if "choices" in result and len(result["choices"]) > 0:
                sql = result["choices"][0]["message"]["content"].strip()
                # 清理SQL，移除可能的多余字符
                sql = sql.replace("```sql", "").replace("```", "").strip()
                return sql
            else:
                raise Exception(f"无效的API响应格式: {result}")

        except Exception as e:
            logger.error(f"生成SQL时发生错误: {str(e)}", exc_info=True)
            raise Exception(f"生成SQL时发生错误: {str(e)}")


# 创建全局实例
llm_client = LLMClient()


def generate_sql(question, db_type, table_name=None):
    """便捷函数，用于生成SQL语句"""
    return llm_client.generate_sql(question, db_type, table_name)
