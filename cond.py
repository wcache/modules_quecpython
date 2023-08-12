
class Singleton(object):
    """单例装饰"""

    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance

    def __repr__(self):
        return repr(self.cls)


@Singleton
class A():

    def __str__(self):
        return 'strxxx'

    def __repr__(self):
        return'repr xxx'



a = A()
print(a)
print(repr(a))
b = A()
print(b)
print(id(a) == id(b))