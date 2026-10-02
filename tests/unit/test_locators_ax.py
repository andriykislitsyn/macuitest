import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.locators import ax
from macuitest.lib.elements.locators.ax import AXQuery
from macuitest.lib.operating_system import permissions


class FakeAX:
    """An accessibility element with fixed attributes."""

    def __init__(self, *children, **attributes):
        self.attributes = {"AXChildren": list(children), **attributes}

    def get_ax_attribute(self, name):
        return self.attributes.get(name)


def window(*children, subrole="AXStandardWindow", minimized=False, frame=(10, 20, 200, 100)):
    x, y, width, height = frame
    return FakeAX(
        *children,
        AXRole="AXWindow",
        AXSubrole=subrole,
        AXMinimized=minimized,
        AXPosition=(x, y),
        AXSize=(width, height),
    )


@pytest.fixture
def running(monkeypatch):
    """Serve the given windows as a running app's AXWindows."""

    def serve(*app_windows):
        app = FakeAX(AXRole="AXApplication", AXWindows=list(app_windows))
        monkeypatch.setattr(ax, "app_root", lambda name: app)

    return serve


def test_query_matches_every_given_attribute():
    seven = FakeAX(AXIdentifier="Seven", AXRole="AXButton")

    assert AXQuery.of(identifier="Seven", role="AXButton").matches(seven)
    assert not AXQuery.of(identifier="Seven", role="AXStaticText").matches(seven)


def test_query_needs_an_attribute():
    with pytest.raises(TypeError, match="at least one"):
        AXQuery.of()


def test_query_reads_as_its_attributes():
    query = AXQuery.of(description="7", role="AXButton")

    assert str(query) == "AXDescription='7', AXRole='AXButton'"


def test_find_first_returns_the_first_match_depth_first():
    deep = FakeAX(AXDescription="7")
    shallow = FakeAX(AXDescription="7")
    root = FakeAX(FakeAX(deep), shallow)

    assert ax.find_first([root], AXQuery.of(description="7")) is deep


def test_find_first_skips_the_roots_themselves():
    root = FakeAX(AXDescription="7")

    assert ax.find_first([root], AXQuery.of(description="7")) is None


def test_standard_window_frame_reads_the_first_standard_window(running):
    running(window(subrole="AXFloatingWindow", frame=(0, 0, 66, 20)), window())

    assert ax.standard_window_frame("Calculator") == Region(10, 20, 210, 120)


def test_a_minimized_window_has_no_frame(running):
    running(window(minimized=True))

    assert ax.standard_window_frame("Calculator") is None


def test_an_app_that_isnt_running_has_no_windows(monkeypatch):
    def not_running(name):
        raise ValueError(f'"{name}" not found among running applications.')

    monkeypatch.setattr(ax.NativeUIElement, "from_localized_name", not_running)

    assert ax.windows("Calculator") == []
    assert ax.standard_window_frame("Calculator") is None


def test_lookups_need_accessibility(monkeypatch):
    monkeypatch.setattr(permissions, "_granted", set())
    monkeypatch.setattr(permissions.ApplicationServices, "AXIsProcessTrusted", lambda: False)

    with pytest.raises(PermissionError):
        ax.windows("Calculator")


@pytest.mark.parametrize("size", [(0, 50), (50, 0), None])
def test_an_element_without_area_has_no_frame(size):
    element = FakeAX(AXPosition=(5, 5), AXSize=size)

    assert ax.frame_of(element) is None
