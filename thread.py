import _thread
import osTimer


class Waiter(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.__lock.acquire()
        self.__unlock_timer = osTimer()

    def __auto_unlock(self, _):
        self.notify()

    def wait(self, timeout=-1):
        if timeout > 0:
            self.__unlock_timer.start(timeout * 1000, 0, self.__auto_unlock)
        self.__lock.acquire()  # block until timeout or notify
        self.__lock.release()
        self.__unlock_timer.stop()

    def notify(self):
        if self.__lock.locked():
            self.__lock.release()


class Condition(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.__waiters = []

    def wait(self, timeout=-1):
        waiter = Waiter()
        with self.__lock:
            self.__waiters.append(waiter)
        waiter.wait(timeout)  # block until timeout or notify
        with self.__lock:
            self.__waiters.remove(waiter)

    def notify(self, n=1):
        if n <= 0:
            raise ValueError('invalid param, n should be > 0.')
        with self.__lock:
            for waiter in self.__waiters[:n]:
                waiter.notify()

    def notify_all(self):
        with self.__lock:
            for waiter in self.__waiters:
                waiter.notify()


class Event(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.flag = False
        self.cond = Condition()

    def wait(self):
        """wait until internal flag is True"""
        if not self.flag:
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


class Thread(object):

    def __init__(self, target=None, args=(), kwargs=None):
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs or {}
        self.__worker_thread_id = None

    def is_running(self):
        return self.__worker_thread_id and _thread.threadIsRunning(self.__worker_thread_id)

    def start(self):
        if not self.is_running():
            self.__worker_thread_id = _thread.start_new_thread(self.run, ())

    def stop(self):
        if self.is_running():
            _thread.stop_thread(self.__worker_thread_id)
            self.__worker_thread_id = None

    def run(self):
        self.__target(*self.__args, **self.__kwargs)


class TimeoutError(Exception):
    pass


class Future(object):

    def __init__(self):
        self.__rv = None
        self.__exc = None
        self.__finished = False
        self.__cond = Condition()

    def set(self, exc, rv):
        self.__exc = exc
        self.__rv = rv
        self.__finished = True
        self.__cond.notify_all()

    def get_result(self, timeout=-1):
        self.__cond.wait(timeout=timeout)
        if not self.__finished:
            raise TimeoutError
        if self.__exc:
            raise self.__exc
        return self.__rv


class _Async(object):

    def __init__(self, target=None, args=(), kwargs=None):
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs or {}

    def delay(self):
        f = Future()
        _thread.start_new_thread(self.run, (f, ))
        return f

    def run(self, future):
        try:
            rv = self.__target(*self.__args, **self.__kwargs)
        except Exception as e:
            future.set(e, None)
        else:
            future.set(None, rv)


class Async(object):

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return _Async(target=self.fn, args=args, kwargs=kwargs).delay()
