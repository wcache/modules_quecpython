import ujson as json
from common import Lock, Queue, Thread, Waiter, TimeoutError


class FormatError(Exception):
    pass


class ValidateError(Exception):
    pass


class SerialNumber(object):
    max_number = 0xFFFF
    lock = Lock()
    iterator = iter(range(max_number+1))

    @classmethod
    def get(cls):
        with cls.lock:
            try:
                return next(cls.iterator)
            except StopIteration:
                cls.iterator = iter(range(cls.max_number+1))
                return next(cls.iterator)


class Head(object):
    LENGTH = 3

    def __init__(self, ack=False, serial_number=None):
        self.ack = ack
        self.serial_number = serial_number

    def dump(self):
        flag = 0x00
        if self.ack:
            flag |= 0x80
        else:
            flag &= 0x7F
        return bytearray([flag]) + self.serial_number.to_bytes(2, 'big')

    @classmethod
    def load(cls, raw):
        flag = raw[0]
        serial_number = int.from_bytes(raw[1:3], 'big')
        self = cls(
            ack=bool(flag & 0x80),
            serial_number=serial_number
        )
        return self

    def is_ack(self):
        return self.ack


class Body(object):

    def __init__(self, payload=None):
        self.payload = payload or {}

    def dump(self):
        return json.dumps(self.payload).encode()

    @classmethod
    def load(cls, raw):
        self = cls(payload=json.loads(raw.decode()))
        return self


class Message(object):
    IDENTIFIER = 0x7E

    def __init__(self, payload=None, ack=False, serial_number=None):
        if ack and serial_number is None:
            raise ValidateError('ack message must explicitly give a serial number.')
        self.payload = payload or {}
        self.ack = ack
        self.serial_number = SerialNumber.get() if serial_number is None else serial_number

    def __repr__(self):
        s = ''
        s += 'ack: {}\n'.format(self.ack)
        s += 'serial number: {}\n'.format(self.serial_number)
        s += 'payload: {}\n'.format(self.payload)
        return s

    def dump(self):
        head = Head(ack=self.ack, serial_number=self.serial_number)
        body = Body(payload=self.payload)
        data = head.dump() + body.dump()
        crc = self.gen_crc(data)
        raw = b''
        raw += self.IDENTIFIER.to_bytes(1, 'big')
        raw += self.escape(data + bytearray([crc]))
        raw += self.IDENTIFIER.to_bytes(1, 'big')
        return raw

    @staticmethod
    def escape(data):
        origin = b''
        for one in data:
            if one == 0x7E:
                origin += b'\x25\x02'
            elif one == 0x25:
                origin += b'\x25\x01'
            else:
                origin += one.to_bytes(1, 'big')
        return origin

    @staticmethod
    def revert(data):
        origin = b''
        index = 0
        while index <= len(data) - 1:
            one = data[index]
            if one == 0x25:
                if data[index + 1] == 0x01:
                    origin += b'\x25'
                elif data[index + 1] == 0x02:
                    origin += b'\x7E'
                else:
                    raise FormatError('revert error at {} bytes, 0x01 or 0x02 should be followed.'.format(index))
                index += 2
            else:
                origin += one.to_bytes(1, 'big')
                index += 1
        return origin

    @classmethod
    def load(cls, raw):
        if len(raw) < 8:
            raise FormatError('message less than 8 bytes.')
        if raw[0] != cls.IDENTIFIER or raw[-1] != cls.IDENTIFIER:
            raise FormatError('identifier error, not a valid message.')
        data = cls.revert(raw[1:-1])
        crc = data[-1]
        if crc != cls.gen_crc(data[:-1]):
            raise ValidateError('CRC validate FAILED.')
        head = Head.load(data[:Head.LENGTH])
        body = Body.load(data[Head.LENGTH:-1])
        self = cls(
            payload=body.payload,
            ack=head.ack,
            serial_number=head.serial_number
        )
        return self

    @staticmethod
    def gen_crc(data):
        crc = data[0]
        for one in data[1:]:
            crc ^= one
        return crc


class Parser(object):

    def __init__(self, load=True):
        self.buffer = b''
        self.message_list = []
        self.__load = load

    def parse(self, data):
        self.buffer += data

        while True:
            header_index = self.buffer.find(b'\x7E')
            if header_index == -1:
                self.clear()
                break

            tail_index = self.buffer.find(b'\x7E', header_index+1)
            if tail_index == -1:
                break  # waiting for more bytes

            if tail_index - header_index == 1:
                self.buffer = self.buffer[tail_index:]
                continue

            try:
                if self.__load:
                    msg = Message.load(self.buffer[header_index:tail_index+1])
                else:
                    msg = self.buffer[header_index:tail_index+1]
                self.message_list.append(msg)
            except Exception as e:
                print('message parse error: {}'.format(e))

            self.buffer = self.buffer[tail_index+1:]

    @property
    def messages(self):
        rv, self.message_list = self.message_list, []
        return rv

    def clear(self):
        self.buffer = b''


class MessageService(object):

    def __init__(self):
        self.stream = None
        self.queue = Queue()
        self.read_thread = Thread(target=self.__read_thread_worker)
        self.ack_lock = Lock()
        self.ack_dict = {}

    def init(self, stream):
        self.stream = stream
        self.read_thread.start()

    def deinit(self):
        self.read_thread.stop()
        self.stream = None

    def get_ack(self, request, timeout=-1):
        waiter = Waiter()
        with self.ack_lock:
            self.ack_dict[request] = [None, waiter]

        try:
            waiter.acquire(timeout)
        except TimeoutError as e:
            with self.ack_lock:
                del self.ack_dict[request]
            return
        else:
            with self.ack_lock:
                response = self.ack_dict[request][0]
                del self.ack_dict[request]
            return response

    def put_ack(self, response):
        with self.ack_lock:
            for request, temp in self.ack_dict.items():
                if request.serial_number == response.serial_number:
                    temp[0] = response
                    temp[1].release()
                    break

    def __read_thread_worker(self):
        parser = Parser()
        while True:
            try:
                data = self.stream.read(1024, timeout=10)
                parser.parse(data)
                for msg in parser.messages:
                    if msg.ack:
                        self.put_ack(msg)
                    else:
                        self.queue.put(msg)
            except TimeoutError:
                parser.clear()
                continue
            except Exception as e:
                print(e)
                continue

    def send(self, msg, timeout=-1):
        self.stream.write(msg.dump())
        if timeout != 0:
            return self.get_ack(msg, timeout)

    def recv(self):
        return self.queue.get()
