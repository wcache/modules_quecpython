import utime
import usys
import _thread
import osTimer
from queue import Queue


Lock = _thread.allocate_lock


class TimeoutError(Exception):
    pass


class FullError(Exception):
    pass


class Singleton(object):
    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance

    def __repr__(self):
        return self.cls.__repr__()


class Waiter(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.__unlock_timer = osTimer()
        self.__is_timeout = False

    def __auto_unlock(self, _):
        self.__is_timeout = True
        self.release()

    def acquire(self, timeout=-1):
        self.__lock.acquire()
        if timeout > 0:
            self.__is_timeout = False
            self.__unlock_timer.start(timeout * 1000, 0, self.__auto_unlock)
        self.__lock.acquire()  # block until timeout or release
        self.__unlock_timer.stop()
        if self.__lock.locked():
            self.__lock.release()
        if self.__is_timeout:
            raise TimeoutError

    def release(self):
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

        try:
            waiter.acquire(timeout)  # block until timeout or notify
        except TimeoutError as exc:
            raise exc
        finally:
            with self.__lock:
                self.__waiters.remove(waiter)

    def notify(self, n=1):
        if n <= 0:
            raise ValueError('invalid param, n should be > 0.')
        with self.__lock:
            for waiter in self.__waiters[:n]:
                waiter.release()

    def notify_all(self):
        with self.__lock:
            for waiter in self.__waiters:
                waiter.release()


class Event(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()
        self.flag = False
        self.cond = Condition()

    def wait(self, timeout=-1):
        """wait until internal flag is True"""
        if not self.is_set():
            self.cond.wait(timeout)
        return self.flag

    def set(self):
        with self.__lock:
            self.flag = True
            self.cond.notify_all()

    def clear(self):
        with self.__lock:
            self.flag = False

    def is_set(self):
        with self.__lock:
            return self.flag


class _Result(object):

    def __init__(self):
        self.__rv = None
        self.__exc = None
        self.__finished = Event()

    def set(self, exc, rv):
        self.__exc = exc
        self.__rv = rv
        self.__finished.set()

    def get(self, timeout=-1):
        self.__finished.wait(timeout=timeout)
        if self.__exc:
            raise self.__exc
        return self.__rv


class Thread(object):

    def __init__(self, target=None, args=(), kwargs=None):
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs or {}
        self.__worker_thread_id = None
        self.__lock = Lock()

    def __repr__(self):
        return '<Thread {}>'.format(self.__worker_thread_id)

    def is_running(self):
        return self.__worker_thread_id and _thread.threadIsRunning(self.__worker_thread_id)

    def start(self, delay=-1):
        if not self.is_running():
            if delay > 0:
                utime.sleep(delay)
            result = _Result()
            self.__worker_thread_id = _thread.start_new_thread(self.run, (result, ))
            return result

    def stop(self):
        if self.is_running():
            _thread.stop_thread(self.__worker_thread_id)
            self.__worker_thread_id = None

    def run(self, result):
        try:
            rv = self.__target(*self.__args, **self.__kwargs)
        except Exception as e:
            result.set(e, None)
        else:
            result.set(None, rv)


class _WorkItem(object):

    def __init__(self, fn, args, kwargs):
        self.__fn = fn
        self.__args = args
        self.__kwargs = kwargs
        self.result = _Result()

    def run(self):
        try:
            rv = self.__fn(*self.__args, **self.__kwargs)
        except Exception as e:
            self.result.set(e, None)
        else:
            self.result.set(rv, None)


class ThreadPoolExecutor(object):

    def __init__(self, max_workers=10):
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
        self.__max_workers = max_workers
        self.__worker_queue = Queue()
        self.__threads = set()
        self.__lock = Lock()

    def submit(self, fn, *args, **kwargs):
        item = _WorkItem(fn, args, kwargs)
        self.__worker_queue.put(item)
        self.__adjust_thread_count()
        return item.result

    def __adjust_thread_count(self):
        with self.__lock:
            if len(self.__threads) < self.__max_workers:
                t = Thread(target=self.__worker, args=(self.__worker_queue, ))
                t.start()
                self.__threads.add(t)

    @staticmethod
    def __worker(worker_queue):
        while True:
            try:
                item = worker_queue.get()
                item.run()
            except Exception as e:
                usys.print_exception(e)

    def shutdown(self):
        with self.__lock:
            for t in self.__threads:
                t.stop()


class PubSub(object):
    TOPIC_MAP = {}
    PUBSUB_LOCK = Lock()

    @classmethod
    def subscribe(cls, topic, callback):
        with cls.PUBSUB_LOCK:
            if topic not in cls.TOPIC_MAP:
                cls.TOPIC_MAP[topic] = [callback]
            else:
                cls.TOPIC_MAP[topic].append(callback)

    @classmethod
    def publish(cls, topic, *args, **kwargs):
        with cls.PUBSUB_LOCK:
            for cb in cls.TOPIC_MAP.get(topic, []):
                Thread(target=cb, args=args, kwargs=kwargs).start()
