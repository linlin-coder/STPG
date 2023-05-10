from typing import Any


# 单例模式
class Singleton:
    def __init__(self, oneObject) -> None:
        self.oneObject = oneObject
        self._instance = {}

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.oneObject not in self._instance:
            self._instance[self.oneObject] = self.oneObject(*args, **kwds)
        return self._instance[self.oneObject]


# 多线程下的单例模式
import threading


class MultiThreadSingleton(object):
    _instance_lock = threading.Lock()  # 线程锁

    def __init__(self, *args, **kwargs):
        import time
        time.sleep(1)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        with Singleton._instance_lock:
            # hasattr() 函数用于判断对象是否包含对应的属性 , 这里是看看这个类有没有 _instance 属性
            if not hasattr(Singleton, '_instance'):
                Singleton._instance = Singleton(*args, **kwargs)

            return Singleton._instance