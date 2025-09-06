import uuid
from datetime import datetime

from app.agent_framework.observer.observer import Observable, Observer
from app.agent_framework.memory.memory import MemorySystem
from app.agent_framework.factory.tool_factory import ToolFactory
from app.agent_framework.perceive.perception import PerceptionSystem
from app.agent_framework.action.action import ActionSystem, Action, ActionType
from app.agent_framework.thinkings.thinking_strategy import ThinkingStrategy, LLMBasedThinkingStrategy
from app.agent_framework.llm.llm_client import LLMClientFactory
from app.agent_framework.config import Config
from typing import Any


class AgentController(Observable, Observer):
    """智能体控制器，协调各个组件工作 - 外观模式"""
    def __init__(self):
        super().__init__()
        
        # 验证配置
        Config.validate()
        
        # 创建核心组件
        self._memory = MemorySystem(Config.MAX_SHORT_TERM_MEMORY)
        self._tool_factory = ToolFactory()
        self._perception = PerceptionSystem(self._memory)
        self._llm_client = LLMClientFactory.create_client()
        self._thinking_strategy = LLMBasedThinkingStrategy(self._llm_client)
        self._action_system = ActionSystem(self._memory, self._tool_factory)
        
        # 注册观察者
        self._perception.add_observer(self)
        self._action_system.add_observer(self)
        self._memory.add_observer(self)
        
        # 状态管理
        self._state = "idle"
    
    def set_thinking_strategy(self, strategy: ThinkingStrategy):
        """设置思考策略 - 策略模式应用"""
        self._thinking_strategy = strategy
        self.notify_observers("strategy_changed", {"strategy": type(strategy).__name__})
    
    def register_tool(self, tool_name: str, tool_class):
        """注册工具"""
        self._tool_factory.register_tool(tool_name, tool_class)
        self.notify_observers("tool_registered", {"tool_name": tool_name})
    
    def process_query(self, query: str) -> Action:
        """处理用户查询的主流程"""
        self._state = "processing"
        self.notify_observers("state_changed", {"state": self._state})
        
        try:
            # 1. 感知处理输入
            processed_input = self._perception.process_input(query)
            
            # 2. 思考过程
            thought = self._thinking_strategy.think(query, self._memory)
            self._memory.add_short_term_memory(
                content=f"思考过程: {thought.content}",
                metadata={"thought_id": thought.id, "thought_type": thought.thought_type.value}
            )
            self.notify_observers("thought_generated", thought)
            
            # 3. 获取可用工具元数据并决定是否使用工具
            tools_metadata = [
                self._tool_factory.get_tool_metadata(tool_name)
                for tool_name in self._tool_factory.get_available_tools()
            ]
            
            tool_decision = self._llm_client.decide_tool_use(
                prompt=query,
                thought=thought.content,
                tools_metadata=tools_metadata
            )
            
            if tool_decision.get("need_tool", False):
                # 3.1 需要调用工具
                tool_name = tool_decision.get("tool_name")
                parameters = tool_decision.get("parameters", {})
                
                if not tool_name:
                    response_content = "无法确定需要使用的工具，请尝试更明确的问题。"
                    final_action = self._action_system.generate_response(response_content, thought.id)
                else:
                    try:
                        action = self._action_system.call_tool(tool_name, parameters, thought.id)
                        
                        # 4. 评估工具结果是否足够回答问题
                        evaluation = self._llm_client.evaluate_result(
                            query=query,
                            tool_result=action.result,
                            thought=thought.content
                        )
                        
                        if evaluation.get("sufficient", False):
                            # 结果足够，生成最终回答
                            memory_context = "\n".join([
                                mem.content for mem in 
                                self._memory.retrieve_relevant_memories(query)
                            ])
                            
                            response_content = self._llm_client.generate_response(
                                query=query,
                                thought=thought.content,
                                memory_context=memory_context,
                                tool_result=action.result
                            )
                            final_action = self._action_system.generate_response(response_content, thought.id)
                        else:
                            # 结果不足够，根据评估建议下一步
                            response_content = f"{evaluation.get('reason', '工具返回结果不足')} " \
                                               f"{evaluation.get('next_step', '请提供更多信息以便进一步查询')}"
                            final_action = self._action_system.generate_response(response_content, thought.id)
                    except Exception as e:
                        response_content = f"调用工具时出错: {str(e)}"
                        final_action = self._action_system.generate_response(response_content, thought.id)
            else:
                # 3.2 不需要调用工具，直接生成回答
                memory_context = "\n".join([
                    mem.content for mem in 
                    self._memory.retrieve_relevant_memories(query)
                ])
                
                response_content = self._llm_client.generate_response(
                    query=query,
                    thought=thought.content,
                    memory_context=memory_context
                )
                final_action = self._action_system.generate_response(response_content, thought.id)
                
                # 将重要信息存入长期记忆
                if self._should_store_in_long_term(final_action.content):
                    self._action_system.store_in_long_term_memory(final_action.content, thought.id)
            
            self._state = "idle"
            self.notify_observers("state_changed", {"state": self._state})
            return final_action
            
        except Exception as e:
            self._state = "error"
            self.notify_observers("state_changed", {"state": self._state})
            error_action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.RESPONSE,
                content=f"处理查询时出错: {str(e)}",
                timestamp=datetime.now()
            )
            self.notify_observers("error_occurred", error_action)
            return error_action
    
    def _should_store_in_long_term(self, content: str) -> bool:
        """判断是否应该将内容存入长期记忆"""
        # 简化实现：长度超过一定阈值的内容存入长期记忆
        return len(content) > 50
    
    def get_memory_system(self) -> MemorySystem:
        """获取记忆系统实例（主要用于测试）"""
        return self._memory
    
    def update(self, event: str, data: Any):
        """处理来自其他组件的事件"""
        self.notify_observers(event, data)
