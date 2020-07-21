"""This module implements a basic color meter. It finds the value of a colour on given coordinates."""
import os
from collections import Counter
from multiprocessing import Pool
from typing import Optional, Tuple

import webcolors
from PIL import Image

from macuitest.config.constants import Point
from macuitest.lib.ui.monitor import monitor


class ColorMeter:
    def __init__(self):
        self.__pixels = None

    def get_most_common_color(self, x1: int, x2: int, y1: int, y2: int,
                              ignore_colors: Optional[Tuple[str, ...]] = None):
        pool = Pool(os.cpu_count())
        pixels = [self._pixels[x, y] for x in range(x1, x2) for y in range(y1, y2)]
        colors = pool.map(self.get_closest_color, pixels)
        if ignore_colors:
            colors = (c for c in colors if c not in ignore_colors)
        return Counter(colors).most_common()[0][0]

    def get_color(self, point: Point) -> str:
        return self.get_closest_color(self._pixels[point.x, point.y]).replace('gray', 'grey')

    @staticmethod
    def get_closest_color(pixel) -> str:
        min_colours = {}
        for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            min_colours[((r_c - pixel[0]) ** 2 + (g_c - pixel[1]) ** 2 + (b_c - pixel[2]) ** 2)] = name
        return min_colours[min(min_colours.keys())]

    @property
    def _pixels(self):
        if self.__pixels is None:
            size = (monitor.size.width, monitor.size.height)
            self.__pixels = Image.frombytes('RGB', size, monitor.bytes, 'raw', 'BGRX').load()
            return self.__pixels
        return self.__pixels
