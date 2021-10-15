"""Some basic functions to be used throughout the project."""
import functools
import time
from typing import Any
from typing import Callable
from typing import Tuple
from typing import Union


class WaitConditionException(Exception):
    """A `placeholder` exception for `wait_condition`."""


def wait_condition(
    predicate: Callable,
    timeout: Union[int, float] = 10,
    exceptions: tuple = (WaitConditionException,),
    *args,
    **kwargs,
) -> Any:
    """Execute `predicate` and return the result."""
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(0.005)
        try:
            result = predicate(*args, **kwargs)
            if result:
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


def is_close(
    actual: Union[int, float], expected: Union[int, float], threshold: Union[int, float]
) -> bool:
    """Compare the difference between two input numbers with specified threshold."""
    return abs(round(actual, 2) - round(expected, 2)) <= threshold


def convert_version_from_tuple_to_str(string: Tuple[int, ...]) -> str:
    """Convert program version from tuple to string."""
    return ".".join(str(i) for i in string)


def convert_version_from_str_to_tuple(string: str) -> Tuple[int, ...]:
    """Convert program version from string to tuple."""
    return tuple([int(item) for item in string.split(".")])


def convert_file_size_to_bytes(string: str) -> int:
    """Convert human readable file size to integer."""
    _size, _unit = string.strip().lower().replace("zero", "0").replace(",", "").split()
    dots = len([i for i in _size if i == "."])
    return int(
        float(_size.replace(".", "", dots - 1))
        * 1000 ** ("bytes", "kb", "mb", "gb", "tb").index(_unit)
    )
