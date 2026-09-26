"""Locate a template image inside a screenshot."""

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import cv2
import numpy

_BANDS = os.cpu_count() or 1
_executor = ThreadPoolExecutor(max_workers=_BANDS, thread_name_prefix="macuitest-match")


def find_template(
    screen: numpy.ndarray, template: numpy.ndarray, threshold: float
) -> Optional[tuple[int, int]]:
    """Return the top-left pixel of the best match of `template` in `screen`, if good enough.

    Both images are single-channel. A match counts when its normalized correlation coefficient,
    rounded to three decimals, reaches `threshold`. The screen is split into horizontal bands
    matched in parallel, and every position is still scored at full resolution.
    """
    bands = _bands(screen.shape[0], template.shape[0])
    score, position = max(
        _executor.map(lambda band: _match_band(screen, template, band), bands),
        key=lambda result: result[0],
    )
    return position if round(score, 3) >= threshold else None


def _bands(screen_height: int, template_height: int) -> list[tuple[int, int]]:
    """Split the rows where a match can start into bands of whole template heights or more."""
    positions = screen_height - template_height + 1
    if positions < 1:
        return [(0, 1)]  # Leave it to matchTemplate to reject a template taller than the screen.
    count = max(1, min(_BANDS, positions // template_height))
    step = -(-positions // count)
    return [(start, min(start + step, positions)) for start in range(0, positions, step)]


def _match_band(
    screen: numpy.ndarray, template: numpy.ndarray, band: tuple[int, int]
) -> tuple[float, tuple[int, int]]:
    first_row, end_row = band
    area = screen[first_row : end_row + template.shape[0] - 1]
    _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED))
    return score, (x, y + first_row)
