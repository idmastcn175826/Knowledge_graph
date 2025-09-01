# # MCP 相关API端点
# @app.post("/api/v1/mcp/models")
# async def create_model_config(model_config: ModelConfig):
#     """创建或更新模型配置"""
#     pass
#
# @app.get("/api/v1/mcp/models")
# async def list_model_configs():
#     """获取用户的模型配置列表"""
#     pass
#
# @app.get("/api/v1/mcp/models/{model_id}")
# async def get_model_config(model_id: str):
#     """获取特定模型配置"""
#     pass
#
# @app.delete("/api/v1/mcp/models/{model_id}")
# async def delete_model_config(model_id: str):
#     """删除模型配置"""
#     pass
#
# @app.post("/api/v1/mcp/models/{model_id}/test")
# async def test_model_connection(model_id: str, test_prompt: str = "Hello"):
#     """测试模型连接"""
#     pass