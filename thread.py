import _thread

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