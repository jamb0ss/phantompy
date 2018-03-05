import os
import socket
from itertools import islice
from inspect import ismethod, isfunction
from functools import wraps
from json import dumps
from contextlib import contextmanager
from random import uniform
from threading import Lock
from time import sleep


__all__ = [
    'sliding_window',
    'weighted_choice',
    'iter_chunks',
    'is_range',
    'get_nested_item',
    'silent',
    'custom_value',
    'thread_safe',
    'ThreadSafeIterator',
    'ThreadSafeCounter',
]


def sliding_window(seq, n=2):
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def iter_chunks(data, chunk_size):
    for i in xrange(0, len(data), chunk_size):
        yield data[i:i+chunk_size]


def weighted_choice(choices):
    population = sum(
        weight for value, weight in choices
    )
    winner = uniform(0, population)
    cum_probability = 0
    for value, weight in choices:
        if cum_probability + weight > winner:
            return value
        cum_probability += weight


def is_range(range):
    return (
        isinstance(range, (list, tuple)) and
        len(range) == 2 and
        all([isinstance(_, int) for _ in range]) and
        range[0] <= range[1]
    )


def get_nested_item(dict_obj, *keys, **kwargs):
    try:
        return reduce(dict.__getitem__, keys, dict_obj)
    except (KeyError, TypeError):
        for kw in ('d', 'default'):
            if kw in kwargs:
                return kwargs[kw]
        else:
            raise KeyError(str(keys))


@contextmanager
def custom_value(obj, attr, value=None):
    if value is None:
        yield
    else:
        if isinstance(obj, dict):
            old_value = obj[attr]
            obj[attr] = value
        else:
            old_value = getattr(obj, attr)
            setattr(obj, attr, value)
        try:
            yield
        except Exception:
            raise
        finally:
            if isinstance(obj, dict):
                obj[attr] = old_value
            else:
                setattr(obj, attr, old_value)


# TODO: fix args signature, patch __doc__
def silent(*args, **kwargs):

    default = kwargs.pop('default', None)

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            silent = kwargs.pop('silent', default)
            if silent:
                try:
                    return func(*args, **kwargs)
                except err:
                    return
            else:
                return func(*args, **kwargs)

        return wrapper

    if (
        len(args) == 1 and
        (ismethod(args[0]) or isfunction(args[0]))
    ):
        err = Exception
        return decorator(args[0])

    else:
        if args and isinstance(args[0], (list, tuple, set)):
            args = tuple(args[0])
        err = args or Exception
        return decorator


# RLock?
@contextmanager
def thread_safe(obj, _cache={}, _selflock=Lock()):
    with _selflock:
        obj_lock = _cache.setdefault(id(obj), Lock())
    with obj_lock:
        yield obj


class ThreadSafeCounter(object):
    """misc::ThreadSafeCounter"""

    def __init__(self, value=0):
        self._lock = Lock()
        self.value = value

    def inc(self, value=1):
        with self._lock:
            self.value += value

    def dec(self, value=1):
        with self._lock:
            self.value -= value

    def __repr__(self):
        return str(self.value)


class ThreadSafeIterator(object):
    """misc::ThreadSafeIterator"""

    def __init__(self, obj):
        self._lock = Lock()
        self.iterator = iter(obj)

    def __iter__(self):
        return self

    def next(self):
        with self._lock:
            return self.iterator.next()


class ScriptLock(object):
    """misc::ScriptLock

    This class is used to prevent a Python script from running in parallel.
    * only one instance of the script can be started at the same time

    >>> script_lock = ScriptLock()
    >>> work...

    """
    def __init__(self, name=None, attempts_num=1, attempts_timeout=10):
        if name is None:
            name = os.path.realpath(os.path.dirname(__file__))
        elif not isinstance(name, basestring):
            raise TypeError(':name must be string')
        if not isinstance(attempts_num, int):
            raise TypeError(':attempts_num must be int')
        if not isinstance(attempts_timeout, int):
            raise TypeError(':attempts_timeout must be int')

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while attempts_num:
            attempts_num -= 1
            try:
                self.socket.bind('\0' + '::script_lock::' + name)
                break
            except socket.error:
                if attempts_num:
                    sleep(attempts_timeout)
                    continue
                raise SystemExit



