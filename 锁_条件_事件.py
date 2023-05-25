import _thread
from queue import Queue


class AutoLock(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()

    def __enter__(self):
        self.__lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__lock.release()


class Event(object):

    def __init__(self):
        self.__lock = AutoLock()
        self.flag = False

    def set(self):
        with self.__lock:
            self.flag = True

    def clear(self):
        with self.__lock:
            self.flag = False

    def isSet(self):
        return self.flag


class Condition1(object):

    def __init__(self, queue=Queue(maxsize=1)):
        self.__block_queue = queue

    def wait(self):
        # return a *notify party*(`identity`), see .notify() method
        return self.__block_queue.get()

    def notify(self, identity=None):
        # `identity` is a param defined by customer, means *notify party*
        self.__block_queue.put(identity)



# 定时器上下文
from machine import Timer
class TimerContext(object):
    __timer = Timer(Timer.Timer1)

    def __init__(self, timeout, callback):
        self.timeout = timeout  # ms; >0 will start a one shot timer, <=0 do nothing.
        self.timer_cb = callback  # callback after timeout.

    def __enter__(self):
        if self.timeout > 0:
            self.__timer.start(period=self.timeout, mode=Timer.ONE_SHOT, callback=self.timer_cb)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timeout > 0:
            self.__timer.stop()