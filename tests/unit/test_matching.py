import cv2
import numpy
import pytest

from macuitest.lib.elements.ui import matching
from macuitest.lib.elements.ui.matching import find_template


@pytest.fixture
def screen():
    return numpy.random.default_rng(seed=11).integers(0, 256, size=(900, 700), dtype=numpy.uint8)


@pytest.fixture(autouse=True)
def four_bands(monkeypatch):
    monkeypatch.setattr(matching, "_BANDS", 4)


def test_finds_the_template_where_it_was_cut(screen):
    assert find_template(screen, screen[500:540, 300:380], 0.925) == (300, 500)


def test_finds_a_template_straddling_a_band_boundary(screen):
    height = 60
    boundary = matching._bands(screen.shape[0], height)[1][0]
    top = boundary - height // 2

    assert find_template(screen, screen[top : top + height, 100:200], 0.925) == (100, top)


def test_returns_none_below_the_threshold(screen):
    unrelated = numpy.random.default_rng(seed=12).integers(0, 256, size=(40, 80), dtype=numpy.uint8)

    assert find_template(screen, unrelated, 0.925) is None


@pytest.mark.parametrize(
    "screen_height, template_height", [(900, 40), (900, 899), (900, 900), (1000, 7), (61, 30)]
)
def test_bands_cover_every_start_row_exactly_once(screen_height, template_height):
    rows = [
        row
        for start, end in matching._bands(screen_height, template_height)
        for row in range(start, end)
    ]

    assert rows == list(range(screen_height - template_height + 1))


def test_template_taller_than_the_screen_raises(screen):
    with pytest.raises(cv2.error):
        find_template(screen, numpy.zeros((901, 10), dtype=numpy.uint8), 0.925)
