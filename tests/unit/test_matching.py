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


def test_finds_a_template_at_the_last_start_row_of_a_band(screen):
    height = 60
    top = matching._bands(screen.shape[0], height)[1][0] - 1

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


@pytest.mark.parametrize("shape", [(901, 10), (10, 701)])
def test_template_larger_than_the_screen_is_not_found(screen, shape):
    assert find_template(screen, numpy.zeros(shape, dtype=numpy.uint8), 0.925) is None


@pytest.mark.parametrize("bands", [1, 3, 4, 8])
def test_identical_copies_resolve_to_the_topmost_then_leftmost(screen, bands, monkeypatch):
    monkeypatch.setattr(matching, "_BANDS", bands)
    template = screen[0:30, 0:40].copy()
    for y, x in [(700, 500), (300, 400), (300, 100), (600, 20)]:
        screen[y : y + 30, x : x + 40] = template
    screen[0:30, 0:40] = numpy.flipud(template)

    assert find_template(screen, template, 0.925) == (100, 300)
