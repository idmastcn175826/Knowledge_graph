import unittest

from app.agent_framework.agent.agent import AgentController
from app.agent_framework.tools.test_tools import ExampleSearchTool, CalculatorTool
from app.agent_framework.memory.memory import MemorySystem
from app.agent_framework.factory.tool_factory import ToolFactory


class TestMemorySystem(unittest.TestCase):
    """测试记忆系统功能"""
    
    def setUp(self):
        self.memory = MemorySystem(max_short_term_entries=10)
    
    def test_add_short_term_memory(self):
        """测试添加短期记忆"""
        initial_count = self.memory.get_short_term_memory_count()
        memory_id = self.memory.add_short_term_memory("测试短期记忆")
        self.assertEqual(self.memory.get_short_term_memory_count(), initial_count + 1)
        self.assertIsNotNone(self.memory.get_memory_by_id(memory_id))
    
    def test_add_long_term_memory(self):
        """测试添加长期记忆"""
        initial_count = self.memory.get_long_term_memory_count()
        memory_id = self.memory.add_long_term_memory("测试长期记忆")
        self.assertEqual(self.memory.get_long_term_memory_count(), initial_count + 1)
        self.assertIsNotNone(self.memory.get_memory_by_id(memory_id))
    
    def test_retrieve_relevant_memories(self):
        """测试检索相关记忆"""
        self.memory.add_short_term_memory("Python是一种编程语言")
        self.memory.add_long_term_memory("Java是另一种编程语言")
        self.memory.add_short_term_memory("猫是一种动物")
        
        # 检索与"编程语言"相关的记忆
        results = self.memory.retrieve_relevant_memories("编程语言")
        self.assertEqual(len(results), 2)
        
        # 检索与"动物"相关的记忆
        results = self.memory.retrieve_relevant_memories("动物")
        self.assertEqual(len(results), 1)
        self.assertIn("猫是一种动物", results[0].content)
    
    def test_clear_short_term_memory(self):
        """测试清除短期记忆"""
        self.memory.add_short_term_memory("测试短期记忆1")
        self.memory.add_short_term_memory("测试短期记忆2")
        self.assertGreater(self.memory.get_short_term_memory_count(), 0)
        
        self.memory.clear_short_term_memory()
        self.assertEqual(self.memory.get_short_term_memory_count(), 0)

class TestToolSystem(unittest.TestCase):
    """测试工具系统功能"""
    
    def setUp(self):
        self.tool_factory = ToolFactory()
        self.tool_factory.register_tool(ExampleSearchTool.get_name(), ExampleSearchTool)
        self.tool_factory.register_tool(CalculatorTool.get_name(), CalculatorTool)
    
    def test_tool_registration(self):
        """测试工具注册"""
        tools = self.tool_factory.get_available_tools()
        self.assertIn("example_search", tools)
        self.assertIn("calculator", tools)
    
    def test_create_tool(self):
        """测试创建工具实例"""
        search_tool = self.tool_factory.create_tool("example_search")
        self.assertIsInstance(search_tool, ExampleSearchTool)
        
        calculator_tool = self.tool_factory.create_tool("calculator")
        self.assertIsInstance(calculator_tool, CalculatorTool)
    
    def test_tool_execution(self):
        """测试工具执行"""
        # 测试搜索工具
        search_tool = self.tool_factory.create_tool("example_search")
        result = search_tool.execute(query="人工智能")
        self.assertIn("results", result)
        self.assertEqual(result["query"], "人工智能")
        
        # 测试计算器工具
        calculator_tool = self.tool_factory.create_tool("calculator")
        result = calculator_tool.execute(expression="2 + 3 * 4")
        self.assertEqual(result["result"], 14)
        
        # 测试错误情况
        result = calculator_tool.execute(expression="invalid expression")
        self.assertIn("error", result)

class TestAgentController(unittest.TestCase):
    """测试智能体控制器功能"""
    
    def setUp(self):
        self.agent = AgentController()
        self.agent.register_tool(ExampleSearchTool.get_name(), ExampleSearchTool)
        self.agent.register_tool(CalculatorTool.get_name(), CalculatorTool)
    
    def test_process_query_with_tool(self):
        """测试需要调用工具的查询处理"""
        # 测试搜索工具调用
        response = self.agent.process_query("查询机器学习最新趋势")
        self.assertEqual(response.action_type.name, "RESPONSE")
        self.assertIsNotNone(response.content)
        
        # 测试计算器工具调用
        response = self.agent.process_query("计算 10 + 20 * 5")
        self.assertIsNotNone(response.content)
    
    def test_process_query_without_tool(self):
        """测试不需要调用工具的查询处理"""
        response = self.agent.process_query("你好，今天天气怎么样？")
        self.assertEqual(response.action_type.name, "RESPONSE")
        self.assertIsNotNone(response.content)
        
        # 检查是否存储到记忆
        memory_system = self.agent.get_memory_system()
        memories = memory_system.retrieve_relevant_memories("你好，今天天气怎么样？")
        self.assertGreater(len(memories), 0)
    
    def test_memory_usage(self):
        """测试智能体记忆使用情况"""
        memory_system = self.agent.get_memory_system()
        initial_short_term_count = memory_system.get_short_term_memory_count()
        
        # 处理查询，应该增加短期记忆
        self.agent.process_query("这是一个测试查询，用于测试记忆功能")
        self.assertGreater(memory_system.get_short_term_memory_count(), initial_short_term_count)

if __name__ == "__main__":
    unittest.main()
