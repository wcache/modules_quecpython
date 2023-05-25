# /usr/bin/env python

"""
author: dustin.wei
email: dustin.wei@quectel.com
date: 2023-2-14
"""

import _thread
from machine import UART, Timer


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


class Serial(object):

    def __init__(self, port=UART.UART2, baudrate=115200, bytesize=8, parity=0, stopbits=1, flowctl=0):
        self.__uart = UART(port, baudrate, bytesize, parity, stopbits, flowctl)
        self.__uart.set_callback(self.__uart_cb)
        self.__cond = Condition()

    def __uart_cb(self, args):
        self.__cond.notify(info=False)

    def __timer_cb(self, args):
        self.__cond.notify(info=True)

    def write(self, data):
        self.__uart.write(data)

    def read(self, size, timeout=0):
        """
        read from uart port with block or noblock mode.
        :param size: int, N bytes you want to read. if read enough bytes, return immediately.
        :param timeout: int(ms). =0 for no blocking, <0 for block forever, >0 for block until timeout.
        :return: bytes actually read.
        """
        if timeout == 0:
            return self.__uart.read(size)

        r_data = b''
        with TimerContext(timeout, self.__timer_cb):
            while len(r_data) < size:
                raw = self.__uart.read(1)
                if not raw:
                    if self.__cond.wait():
                        break
                else:
                    r_data += raw
        return r_data
