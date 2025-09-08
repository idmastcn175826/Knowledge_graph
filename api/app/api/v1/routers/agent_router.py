from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.agent_framework.agent.agent import AgentController
from app.agent_framework.tools.test_tools  import ExampleSearchTool, CalculatorTool
from app.utils.auth import get_current_user  # 假设你有用户认证工具

# 初始化日志
logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter()


# 初始化智能体控制器（可以考虑使用单例模式或依赖注入）
class AgentManager:
    """智能体管理器，确保全局只有一个智能体实例"""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AgentController()
            # 注册工具
            cls._instance.register_tool(ExampleSearchTool.get_name(), ExampleSearchTool)
            cls._instance.register_tool(CalculatorTool.get_name(), CalculatorTool)
            logger.info("智能体控制器初始化完成并注册了默认工具")
        return cls._instance


# 请求和响应模型
class AgentQueryRequest(BaseModel):
    """智能体查询请求模型"""
    query: str = Field(..., description="用户的查询内容")
    session_id: Optional[str] = Field(None, description="会话ID，用于维持上下文")
    history: Optional[List[Dict[str, str]]] = Field(None, description="历史对话记录")


class AgentResponse(BaseModel):
    """智能体响应模型"""
    response: str = Field(..., description="智能体的回答内容")
    session_id: Optional[str] = Field(None, description="会话ID")
    thought_process: Optional[str] = Field(None, description="智能体的思考过程，调试用")
    tool_used: Optional[Dict[str, Any]] = Field(None, description="使用的工具信息")


# 依赖项：获取智能体实例
def get_agent():
    return AgentManager.get_instance()


@router.post("/query", response_model=AgentResponse, summary="向智能体发送查询")
async def agent_query(
        request: AgentQueryRequest,
        agent: AgentController = Depends(get_agent),
        current_user: dict = Depends(get_current_user)  # 可选：添加用户认证
):
    """
    向智能体发送查询并获取回答

    - 支持上下文会话（通过session_id）
    - 可传入历史对话记录
    - 自动处理工具调用逻辑
    """
    try:
        logger.info(f"用户 {current_user.get('id') if current_user else '匿名'} 发送查询: {request.query}")

        # 如果有历史记录，先将其添加到智能体记忆中
        if request.history:
            for msg in request.history:
                if "user" in msg and "content" in msg:
                    agent.get_memory_system().add_short_term_memory(f"用户: {msg['content']}")
                elif "agent" in msg and "content" in msg:
                    agent.get_memory_system().add_short_term_memory(f"智能体: {msg['content']}")

        # 处理查询
        action_result = agent.process_query(request.query)

        # 构建响应
        response = AgentResponse(
            response=action_result.content,
            session_id=request.session_id,
            # 这里可以根据实际需要添加思考过程和工具使用信息
            thought_process=getattr(action_result, 'thought_id', None),
            tool_used=getattr(action_result, 'tool_info', None)
        )

        logger.info(f"智能体处理完成，会话ID: {request.session_id}")
        return response

    except Exception as e:
        logger.error(f"智能体处理查询时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"智能体处理查询失败: {str(e)}")


@router.get("/tools", summary="获取智能体现有的工具列表")
async def get_available_tools(
        agent: AgentController = Depends(get_agent)
):
    """获取智能体已注册的所有工具信息"""
    try:
        tools = [
            agent._tool_factory.get_tool_metadata(tool_name)
            for tool_name in agent._tool_factory.get_available_tools()
        ]
        return {"tools": tools}
    except Exception as e:
        logger.error(f"获取工具列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@router.post("/clear-memory", summary="清除智能体的记忆")
async def clear_agent_memory(
        session_id: Optional[str] = Query(None, description="特定会话ID的记忆，为空则清除所有"),
        agent: AgentController = Depends(get_agent),
        current_user: dict = Depends(get_current_user)
):
    """清除智能体的短期记忆，可选清除特定会话的记忆"""
    try:
        # 这里简化处理，实际可能需要根据session_id清除特定记忆
        agent.get_memory_system().clear_short_term_memory()
        return {"message": "智能体记忆已清除"}
    except Exception as e:
        logger.error(f"清除智能体记忆失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清除智能体记忆失败: {str(e)}")
