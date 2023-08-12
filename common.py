import _thread
import osTimer


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


class Waiter(object):

    def __init__(self):
        self.__info = None  # usr information for notifier

        self.__lock = _thread.allocate_lock()
        self.__lock.acquire()  # acquire immediately for holding the lock.

        self.acquire = self.__lock.acquire
        self.release = self.__lock.release

    @property
    def info(self):
        return self.__info

    @info.setter
    def info(self, info):
        self.__info = info


class Condition(object):
    """条件变量(使用互斥锁实现)"""

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.__waiters = []

    def __create_waiter(self):
        waiter = Waiter()
        with self.__lock:
            self.__waiters.append(waiter)
        return waiter

    def wait(self):
        waiter = self.__create_waiter()
        waiter.acquire()  # block here, waiting for release in the future.
        return waiter.info

    def notify(self, n=1, info=None):
        with self.__lock:
            for waiter in self.__waiters[:n]:
                waiter.info = info
                waiter.release()  # release here, some `wait` method will be unblocked.
                self.__waiters.remove(waiter)

    def notify_all(self, info=None):
        self.notify(n=len(self.__waiters), info=info)


class Event(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.flag = False
        self.cond = Condition()

    def wait(self):
        if self.flag is not True:
            self.cond.wait()
        return self.flag

    def set(self):
        with self.__lock:
            self.flag = True
            self.cond.notify_all()

    def clear(self):
        with self.__lock:
            self.flag = False

    def is_set(self):
        return self.flag

            

# 单次定时器（自动关闭）
class OneShotTimer(object):

    def __init__(self, callback=None):
        self.timer = osTimer()

        def do_nothing(args):
            pass

        self.user_callback = callback or do_nothing

    def start(self, period):
        self.timer.start(period, 0, self.cb)

    def interrupt(self, do=True):
        self.timer.stop()
        if do:
            self.user_callback(None)

    def cb(self, args):
        self.user_callback(args)
        self.timer.stop()  # 必须关闭，否则下一次定时器无法触发回调
        

# 实例方法锁
class MutexMethod(object):
    default_lock = _thread.allocate_lock()

    def __init__(self, lock=None):
        self.lock = lock or self.default_lock

    def __call__(self, method):
        def wrapper(*args, **kwargs):
            with self.lock:
                return method(*args, **kwargs)
        return wrapper
        

class Mutex(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.__unlock_timer = osTimer()

    def __auto_unlock(self, args):
        self.release()

    def acquire(self, timeout=-1):
        if timeout > 0:
            self.__unlock_timer.start(timeout*1000, 0, self.__auto_unlock)
        self.__lock.acquire()

    def release(self):
        if self.__lock.locked():
            self.__lock.release()