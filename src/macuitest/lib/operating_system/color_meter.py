"""Name the colors on screen after the closest CSS3 color."""

from typing import Optional
from typing import Tuple

import cv2
import numpy

from macuitest.config.colors import CSS3_COLORS
from macuitest.config.constants import Point
from macuitest.config.constants import Region
from macuitest.lib.elements.ui.monitor import monitor

_NAMES = [name for name, *_ in CSS3_COLORS]
_NAME_INDEX = {name: index for index, name in enumerate(_NAMES)}
_RGB_PACKING = numpy.array([1 << 16, 1 << 8, 1], dtype=numpy.uint32)
# Colors per distance matrix, so photos and gradients with many unique colors stay in memory.
_CHUNK = 8192


def _to_lab(rgb: numpy.ndarray) -> numpy.ndarray:
    """Convert an (N, 3) array of 8-bit RGB colors to CIELAB."""
    as_image = (rgb.reshape(1, -1, 3) / 255).astype(numpy.float32)
    return cv2.cvtColor(as_image, cv2.COLOR_RGB2Lab).reshape(-1, 3)


_PALETTE_LAB = _to_lab(numpy.array([rgb for _, *rgb in CSS3_COLORS], dtype=numpy.uint8))


def get_most_common_color(
    x1: int, y1: int, x2: int, y2: int, ignore_colors: Optional[Tuple[str, ...]] = None
) -> str:
    """Return the closest CSS3 color name covering the most pixels, skipping `ignore_colors`.

    `x1`, `y1`, `x2`, `y2` are global display points, with `x2` and `y2` exclusive.

    Raises:
        LookupError: Every pixel in the region is one of `ignore_colors`.
    """
    pixels = _capture_rgb(Region(x1, y1, x2, y2))
    # unique() over packed integers is far faster than over RGB rows.
    _, first_seen, counts = numpy.unique(
        pixels.astype(numpy.uint32) @ _RGB_PACKING, return_index=True, return_counts=True
    )
    totals = numpy.bincount(_closest(pixels[first_seen]), weights=counts, minlength=len(_NAMES))
    for name in ignore_colors or ():
        if name in _NAME_INDEX:
            totals[_NAME_INDEX[name]] = 0
    if not totals.any():
        raise LookupError(f"Every pixel in the region is one of {ignore_colors}")
    return _NAMES[int(totals.argmax())]


def get_color(point: Point) -> str:
    """Return the closest CSS3 color name at `point`, in global display points."""
    return get_closest_color(_capture_rgb(Region(point.x, point.y, point.x + 1, point.y + 1))[0])


def get_closest_color(pixel) -> str:
    """Return the name of the CSS3 color perceptually closest to the (r, g, b) `pixel`."""
    return _NAMES[int(_closest(numpy.array([pixel], dtype=numpy.uint8))[0])]


def _capture_rgb(region: Region) -> numpy.ndarray:
    """Return the pixels of `region` as an (N, 3) RGB array, top-left pixel first."""
    return cv2.cvtColor(monitor.make_snapshot(region), cv2.COLOR_BGRA2RGB).reshape(-1, 3)


def _closest(rgb: numpy.ndarray) -> numpy.ndarray:
    """Return, for each RGB color, the index of the perceptually closest palette color."""
    lab = _to_lab(rgb)
    return numpy.concatenate(
        [
            numpy.linalg.norm(chunk[:, None] - _PALETTE_LAB[None], axis=2).argmin(axis=1)
            for chunk in (lab[start : start + _CHUNK] for start in range(0, len(lab), _CHUNK))
        ]
    )
