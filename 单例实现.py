"""
单例模式（装饰器实现）
author: 韦伟（dustin.wei@quectel.com)
date: 2023-05-22
"""

from threading import Lock


class Singleton(object):
    """单例装饰"""
    __lock = Lock()

    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        with self.__lock:
            if self.instance is None:
                self.instance = self.cls(*args, **kwargs)
            return self.instance

    def __str__(self):
        return str(self.cls)

    def __repr__(self):
        return self.__str__()
