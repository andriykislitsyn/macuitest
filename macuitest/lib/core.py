import time
from typing import Any, Callable, Union, Tuple


def wait_condition(predicate: Callable, timeout: Union[int, float] = 10, *args, **kwargs) -> Any:
    """Call `predicate` and return its result."""
    end = time.time() + timeout
    while time.time() < end:
        result = predicate(*args, **kwargs)
        if result:
            return result
        time.sleep(0.05)
    return False


def convert_version_from_tuple_to_str(string: Tuple[int, ...]) -> str:
    return '.'.join(str(i) for i in string)


def convert_version_from_str_to_tuple(string: str) -> Tuple[int, ...]:
    return tuple([int(item) for item in string.split('.')])


def convert_file_size_to_bytes(string: str) -> int:
    _size, _unit = string.strip().lower().replace('zero', '0').replace(',', '').split()
    dots = len([i for i in _size if i == '.'])
    return int(float(_size.replace('.', '', dots - 1)) * 1000 ** ('bytes', 'kb', 'mb', 'gb', 'tb').index(_unit))
