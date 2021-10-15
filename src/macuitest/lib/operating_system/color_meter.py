"""Implements a basic color meter. It finds the value of a colour on given coordinates."""
import multiprocessing
from collections import Counter
from typing import Optional
from typing import Tuple

import cv2

from macuitest.config.colors import CSS3_COLORS
from macuitest.config.constants import Point
from macuitest.lib.elements.ui.monitor import monitor


def get_most_common_color(
    x1: int, y1: int, x2: int, y2: int, ignore_colors: Optional[Tuple[str, ...]] = None
) -> str:
    """Get a color name that is the most common to a specific screen area."""
    pixels = cv2.cvtColor(monitor.make_snapshot(), cv2.COLOR_BGR2RGB)
    with multiprocessing.Pool() as pool:
        colors = pool.map(
            get_closest_color, list(pixels[y, x] for x in range(x1, x2) for y in range(y1, y2))
        )
    if ignore_colors:
        colors = (c for c in colors if c not in ignore_colors)
    return Counter(colors).most_common()[0][0]


def get_color(point: Point) -> str:
    """Get a color name of the given pixel."""
    return get_closest_color(
        cv2.cvtColor(monitor.make_snapshot(), cv2.COLOR_BGR2RGB)[point.y, point.x]
    )


def get_closest_color(pixel) -> str:
    """Calculate RGB difference between `pixel` and every CSS3_COLOR
    and return name of the color with the minimal difference."""
    min_colours = dict()
    pr, pg, pb = pixel
    for name, cr, cg, cb in CSS3_COLORS:
        min_colours[abs(cr - pr) + abs(cg - pg) + abs(cb - pb)] = name
    return min_colours[min(min_colours)]
