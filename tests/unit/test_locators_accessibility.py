import pytest

from macuitest.config.constants import Region
from macuitest.lib.elements.locators import accessibility as ax
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.native.calls import AXErrorCannotComplete
from macuitest.lib.elements.native.calls import AXErrorInvalidUIElement
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


def test_a_window_query_picks_the_first_matching_window(running):
    running(window(), window(subrole="AXDialog", frame=(50, 60, 300, 120)))

    frame = ax.standard_window_frame("Calculator", AXQuery.of(subrole="AXDialog"))

    assert frame == Region(50, 60, 350, 180)


def test_a_window_query_without_a_match_has_no_frame(running):
    running(window())

    assert ax.standard_window_frame("Calculator", AXQuery.of(title="Settings")) is None


def test_a_window_query_skips_minimized_windows(running):
    running(window(subrole="AXDialog", minimized=True))

    assert ax.standard_window_frame("Calculator", AXQuery.of(subrole="AXDialog")) is None


def test_a_minimized_window_has_no_frame(running):
    running(window(minimized=True))

    assert ax.standard_window_frame("Calculator") is None


class WindowServer:
    """Serve window list entries and count how often the list is read."""

    def __init__(self, monkeypatch, *owners):
        self.reads = 0
        self.owners = list(owners)
        self.alive = {pid for _, pid in owners}
        monkeypatch.setattr(ax, "_pids", {})
        monkeypatch.setattr(ax.Quartz, "CGWindowListCopyWindowInfo", self.window_list)
        monkeypatch.setattr(ax, "_alive", lambda pid: pid in self.alive)
        monkeypatch.setattr(ax.NativeUIElement, "from_pid", lambda pid: FakeAX(pid=pid))

    def window_list(self, *args):
        self.reads += 1
        return [
            {"kCGWindowOwnerName": name, "kCGWindowOwnerPID": pid, "kCGWindowLayer": 0}
            for name, pid in self.owners
        ]


def test_app_root_finds_the_app_by_its_window_owner(monkeypatch):
    WindowServer(monkeypatch, ("Finder", 10), ("Calculator", 42))

    root = ax.app_root("Calculator")

    assert root is not None
    assert root.get_ax_attribute("pid") == 42


def test_app_root_reuses_the_pid_while_the_process_lives(monkeypatch):
    server = WindowServer(monkeypatch, ("Calculator", 42))

    ax.app_root("Calculator")
    ax.app_root("Calculator")

    assert server.reads == 1


def test_app_root_looks_up_a_relaunched_app_again(monkeypatch):
    server = WindowServer(monkeypatch, ("Calculator", 42))
    ax.app_root("Calculator")
    server.alive.clear()
    server.owners = [("Calculator", 43)]
    server.alive.add(43)

    root = ax.app_root("Calculator")

    assert root is not None
    assert root.get_ax_attribute("pid") == 43


def test_an_app_without_windows_reads_as_not_running(monkeypatch):
    WindowServer(monkeypatch, ("Finder", 10))

    assert ax.app_root("Calculator") is None
    assert ax.windows("Calculator") == []
    assert ax.standard_window_frame("Calculator") is None


def test_a_hidden_app_has_no_window_frame(monkeypatch):
    app = FakeAX(AXRole="AXApplication", AXHidden=True, AXWindows=[window()])
    monkeypatch.setattr(ax, "app_root", lambda name: app)

    assert ax.standard_window_frame("Calculator") is None


class Vanishing(FakeAX):
    """An element that raises `error` for every attribute, like one whose app is going away."""

    def __init__(self, error):
        super().__init__()
        self.error = error

    def get_ax_attribute(self, name):
        raise self.error("gone")


@pytest.mark.parametrize("error", [AXErrorCannotComplete, AXErrorInvalidUIElement])
def test_an_app_that_stops_answering_has_no_windows(monkeypatch, error):
    monkeypatch.setattr(ax, "app_root", lambda name: Vanishing(error))

    assert ax.windows("Calculator") == []
    assert ax.standard_window_frame("Calculator") is None


def test_a_window_that_closes_during_the_lookup_has_no_frame(running):
    running(Vanishing(AXErrorInvalidUIElement))

    assert ax.standard_window_frame("Calculator") is None


def test_find_first_skips_an_element_that_vanished():
    seven = FakeAX(AXDescription="7")
    root = FakeAX(Vanishing(AXErrorInvalidUIElement), seven)

    assert ax.find_first([root], AXQuery.of(description="7")) is seven


def test_lookups_need_accessibility(monkeypatch):
    monkeypatch.setattr(permissions, "_granted", set())
    monkeypatch.setattr(permissions.ApplicationServices, "AXIsProcessTrusted", lambda: False)

    with pytest.raises(PermissionError):
        ax.windows("Calculator")


@pytest.mark.parametrize("size", [(0, 50), (50, 0), None])
def test_an_element_without_area_has_no_frame(size):
    element = FakeAX(AXPosition=(5, 5), AXSize=size)

    assert ax.frame_of(element) is None
