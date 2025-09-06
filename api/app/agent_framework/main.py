from typing import Any

from app.agent_framework.agent.agent import AgentController
from app.agent_framework.tools.test_tools import ExampleSearchTool, CalculatorTool
from app.agent_framework.observer.observer import Observer

def main():
    # 创建智能体
    print("初始化智能体...")
    agent = AgentController()
    
    # 注册工具
    print("注册工具...")
    agent.register_tool(ExampleSearchTool.get_name(), ExampleSearchTool)
    agent.register_tool(CalculatorTool.get_name(), CalculatorTool)
    
    # 添加观察者监控智能体行为
    class AgentMonitor(Observer):
        def update(self, event: str, data: Any):
            if event in ["thought_generated", "action_executed"]:
                print(f"\n[事件] {event}")
                # 简化输出，只显示关键信息
                if event == "thought_generated":
                    print(f"[思考] {data.content[:100]}...")
                elif event == "action_executed":
                    if data.action_type.name == "TOOL_CALL":
                        print(f"[工具调用] {data.content['tool_name']} -> {str(data.result)[:100]}...")
    
    agent.add_observer(AgentMonitor())
    
    # 调用查询
    print("\n===== 处理第一个查询 =====")
    query1 = "当前工具注册了那些工具包"
    print(f"用户查询: {query1}")
    response = agent.process_query(query1)
    print(f"\n智能体回答: {response.content}")
    


if __name__ == "__main__":
    main()
