import functools
import time
from typing import Any, Callable, Union, Tuple


class WaitConditionException(Exception):
    """A `placeholder` exception for `wait_condition`."""


def wait_condition(predicate: Callable, timeout: Union[int, float] = 10,
                   exceptions: tuple = (WaitConditionException, ), *args, **kwargs) -> Any:
    """Call `predicate` and return its result."""
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(.005)
        try:
            if result := predicate(*args, **kwargs):
                return result
        except exceptions:
            continue
    return False


def _parametrized(decorator):
    @functools.wraps(decorator)
    def wrapper(*args, **kwargs):
        def result(func):
            return decorator(func, *args, **kwargs)
        return result
    return wrapper


@_parametrized
def slow_down(func, seconds: float):
    """Slow down `func` by adding timeouts before and after its execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep(seconds)
        result = func(*args, **kwargs)
        time.sleep(seconds)
        return result
    return wrapper


def convert_version_from_tuple_to_str(string: Tuple[int, ...]) -> str:
    return '.'.join(str(i) for i in string)


def convert_version_from_str_to_tuple(string: str) -> Tuple[int, ...]:
    return tuple([int(item) for item in string.split('.')])


def convert_file_size_to_bytes(string: str) -> int:
    _size, _unit = string.strip().lower().replace('zero', '0').replace(',', '').split()
    dots = len([i for i in _size if i == '.'])
    return int(float(_size.replace('.', '', dots - 1)) * 1000 ** ('bytes', 'kb', 'mb', 'gb', 'tb').index(_unit))
