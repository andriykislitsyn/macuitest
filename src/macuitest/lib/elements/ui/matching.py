"""Locate a template image inside a screenshot."""

import math
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import cv2
import numpy

_BANDS = os.cpu_count() or 1
_executor = ThreadPoolExecutor(max_workers=_BANDS, thread_name_prefix="macuitest-match")
# Identical copies score about 1e-6 apart depending on their surroundings, so treat closer scores
# as ties.
_TIE = 1e-5


def find_template(
    screen: numpy.ndarray, template: numpy.ndarray, threshold: float
) -> Optional[tuple[int, int]]:
    """Return the (x, y) pixel of the best match's top-left corner, or None below `threshold`.

    Both images are single-channel. The score is the normalized correlation coefficient, rounded to
    three decimals. Ties resolve to the topmost, then leftmost match. Bands of rows are matched in
    parallel on a shared thread pool.
    """
    if template.shape[0] > screen.shape[0] or template.shape[1] > screen.shape[1]:
        return None
    bands = _bands(screen.shape[0], template.shape[0])
    results = list(_executor.map(lambda band: _match_band(screen, template, band), bands))
    best = max(score for score, _ in results)
    score, position = next(result for result in results if result[0] >= best - _TIE)
    return position if round(score, 3) >= threshold else None


def _bands(screen_height: int, template_height: int) -> list[tuple[int, int]]:
    """Split the rows where a match can start into at most `_BANDS` half-open ranges, top first.

    Every range except the last spans at least one template height.
    """
    positions = screen_height - template_height + 1
    count = max(1, min(_BANDS, positions // template_height))
    step = math.ceil(positions / count)
    return [(start, min(start + step, positions)) for start in range(0, positions, step)]


def _match_band(
    screen: numpy.ndarray, template: numpy.ndarray, band: tuple[int, int]
) -> tuple[float, tuple[int, int]]:
    """Match `template` at the start rows in `band`.

    Returns:
        The best score and the topmost, then leftmost (x, y) in `screen` scoring within `_TIE`
        of it.
    """
    first_row, end_row = band
    area = screen[first_row : end_row + template.shape[0] - 1]
    scores = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
    best = float(scores.max())
    y, x = divmod(int(numpy.argmax(scores >= best - _TIE)), scores.shape[1])
    return best, (x, y + first_row)
