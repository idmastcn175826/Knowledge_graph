from abc import ABC, abstractmethod
from typing import Any

class Observable:
    """可观察对象基类，实现观察者模式"""
    def __init__(self):
        self._observers = []
    
    def add_observer(self, observer):
        """添加观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, event: str, data: Any):
        """通知所有观察者"""
        for observer in self._observers:
            observer.update(event, data)

class Observer(ABC):
    """观察者接口"""
    @abstractmethod
    def update(self, event: str, data: Any):
        """处理接收到的事件"""
        pass
