from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict
from typing import Tuple
from typing import Union

KB: int = 10 ** 3
MB: int = 10 ** 6
GB: int = 10 ** 9

SECOND: int = 1
MINUTE: int = 60 * SECOND
HOUR: int = 60 * MINUTE


class DNSMapping(str):
    pass


@dataclass(frozen=True)
class Point:
    x: Union[int, float]
    y: Union[int, float]


@dataclass(frozen=True)
class Frame:
    x1: Union[int, float]
    y1: Union[int, float]
    x2: Union[int, float]
    y2: Union[int, float]
    center: Point
    width: Union[int, float]
    height: Union[int, float]


@dataclass
class Region:
    x1: Union[int, float]
    y1: Union[int, float]
    x2: Union[int, float]
    y2: Union[int, float]


@dataclass(frozen=True)
class ScreenSize:
    width: Union[int, float]
    height: Union[int, float]


@dataclass(frozen=True)
class CheckboxState:
    states: MappingProxyType = MappingProxyType(
        {"unchecked": 0, 0: 0, "checked": 1, 1: 1, "indeterminate": 2, 2: 2}
    )
    checked: int = 1
    unchecked: int = 0
    indeterminate: int = 2


@dataclass(frozen=True)
class Colors:
    red: Tuple[str, ...] = (
        "lightcoral",
        "lightsalmon",
        "salmon",
        "tomato",
    )
    green: Tuple[str, ...] = (
        "lightgreen",
        "limegreen",
        "mediumaquamarine",
        "mediumseagreen",
        "darkseagreen",
    )
    blue: Tuple[str, ...] = (
        "deepskyblue",
        "dodgerblue",
        "cornflowerblue",
        "royalblue",
        "lavender",
        "lightskyblue",
        "mediumturquoise",
    )
    orange: Tuple[str, ...] = (
        "coral",
        "lightsalmon",
        "sandybrown",
        "darkorange",
        "goldenrod",
    )
    grey: Tuple[str, ...] = (
        "darkgray",
        "darkslategray",
        "dimgray",
        "lightgray",
        "slategray",
        "darkgrey",
        "darkslategrey",
        "dimgrey",
        "lightgrey",
        "slategrey",
        "silver",
    )


@dataclass(frozen=True)
class DisclosureTriangleState:
    closed: int = 0
    opened: int = 1


@dataclass
class URLDetails:
    url: str
    schema: str
    domain: str
    path: str
    query: Dict[str, str]
