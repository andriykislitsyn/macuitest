from typing import Optional

from macuitest.config.constants import Region
from macuitest.lib.elements.screen_element import ScreenElement

BOX = Region(1, 2, 3, 4)


class RecordingElement(ScreenElement):
    """Find `BOX` anywhere and record each region searched."""

    def __init__(self):
        self.searched: list[Optional[Region]] = []

    def _locate(self, region):
        self.searched.append(region)
        return BOX


def test_an_explicit_region_wins_over_the_scope():
    element = RecordingElement()
    element.scope = lambda: Region(0, 0, 50, 50)

    element.locate(Region(5, 5, 9, 9))

    assert element.searched == [Region(5, 5, 9, 9)]


def test_without_a_region_the_scope_is_searched():
    element = RecordingElement()
    element.scope = lambda: Region(0, 0, 50, 50)

    assert element.locate() == BOX
    assert element.searched == [Region(0, 0, 50, 50)]


def test_a_scope_returning_none_finds_nothing_without_searching():
    element = RecordingElement()
    element.scope = lambda: None

    assert element.locate() is None
    assert element.searched == []


def test_the_scope_is_read_at_every_lookup():
    element = RecordingElement()
    frames = iter([Region(0, 0, 10, 10), Region(20, 0, 30, 10)])
    element.scope = lambda: next(frames)

    element.locate()
    element.locate()

    assert element.searched == [Region(0, 0, 10, 10), Region(20, 0, 30, 10)]


def test_without_a_scope_the_defaults_apply():
    element = RecordingElement()

    element.locate()

    assert element.searched == [None]
