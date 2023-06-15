import _thread
import ujson as json


class MutexMethod(object):
    default_lock = _thread.allocate_lock()

    def __init__(self, lock=None):
        self.lock = lock or self.default_lock

    def __call__(self, method):
        def wrapper(*args, **kwargs):
            with self.lock:
                return method(*args, **kwargs)
        return wrapper


class JsonConfigureClass(object):

    def __init__(self, path, encoding='utf8'):
        self.config_path = path
        self.encoding = encoding
        self.settings = None
        self.load()  # first load setting from json file.

    def __str__(self):
        return str(self.settings)

    def __repr__(self):
        return self.__str__()

    @MutexMethod()
    def load(self, reload=False):
        if (self.settings is None) or reload:
            with open(self.config_path, 'r', encoding=self.encoding) as f:
                self.settings = json.load(f)

    def reload(self):
        self.load(reload=True)

    @MutexMethod()
    def save(self):
        with open(self.config_path, 'w+', encoding=self.encoding) as f:
            json.dump(self.settings, f)

    @MutexMethod()
    def get(self, key):
        return self.recurse_execute(
            self.settings,
            key.split('.'),
            operate='get'
        )

    def __getitem__(self, item):
        return self.get(item)

    @MutexMethod()
    def set(self, key, value):
        return self.recurse_execute(
            self.settings,
            key.split('.'),
            value=value,
            operate='set'
        )

    def __setitem__(self, key, value):
        return self.set(key, value)

    @MutexMethod()
    def delete(self, key):
        keys = key.split('.')
        return self.recurse_execute(
            self.settings,
            keys,
            operate='delete'
        )

    def __delitem__(self, key):
        return self.delete(key)

    def recurse_execute(self, settings, keys, value=None, operate=''):
        if len(keys) == 0:
            return

        if not isinstance(settings, dict):
            raise TypeError('config item \"{}\" is not valid(DictLike).'.format(settings))

        key = keys.pop(0)

        if len(keys) == 0:
            if operate == 'get':
                return settings[key]
            elif operate == 'set':
                settings[key] = value
            elif operate == 'delete':
                del settings[key]
            return

        if key not in settings:
            if operate == 'set':
                settings[key] = {}  # auto create sub items recursively.
            else:
                return

        return self.recurse_execute(settings[key], keys, value=value, operate=operate)


def ConfigureHandler(path):
    if path.endswith('.json'):
        return JsonConfigureClass(path)
    else:
        raise TypeError('file format not supported!')


config = ConfigureHandler('/usr/config.json')
