import AppKit
import pytest
import Quartz

from macuitest.config import DEFAULT_FILE
from macuitest.config.settings import settings
from macuitest.lib.elements.ui import monitor as monitor_module
from macuitest.lib.operating_system import permissions


@pytest.fixture(autouse=True)
def default_settings():
    """Run every test on the shipped defaults, so a valid local config can't change results."""
    settings.load(DEFAULT_FILE)


@pytest.fixture(autouse=True)
def permissions_granted(monkeypatch):
    """Treat every permission as granted, since CI runners can't grant them."""
    monkeypatch.setattr(permissions, "_granted", set(permissions.PERMISSIONS))


@pytest.fixture(autouse=True)
def no_screen_capture(monkeypatch):
    """Fail any test that reaches a real screen capture, which reads nothing useful in CI."""

    def capture(*args):
        raise RuntimeError(
            "Unit tests must not capture the screen. Patch monitor.capture or use text_image."
        )

    monkeypatch.setattr(monitor_module.CoreGraphics, "CGWindowListCreateImage", capture)


def render_text(labels, width, height, scale=2, size=16):
    """Return a CGImage of black `labels` on white, each a (text, x, y) with x, y in points."""
    context = Quartz.CGBitmapContextCreate(
        None,
        width * scale,
        height * scale,
        8,
        0,
        Quartz.CGColorSpaceCreateDeviceRGB(),
        Quartz.kCGImageAlphaPremultipliedLast,
    )
    Quartz.CGContextSetRGBFillColor(context, 1, 1, 1, 1)
    Quartz.CGContextFillRect(context, Quartz.CGRectMake(0, 0, width * scale, height * scale))
    Quartz.CGContextScaleCTM(context, scale, scale)
    AppKit.NSGraphicsContext.saveGraphicsState()
    AppKit.NSGraphicsContext.setCurrentContext_(
        AppKit.NSGraphicsContext.graphicsContextWithCGContext_flipped_(context, False)
    )
    attributes = {
        AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(size),
        AppKit.NSForegroundColorAttributeName: AppKit.NSColor.blackColor(),
    }
    for text, x, y in labels:
        string = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, attributes)
        # AppKit's origin is bottom left.
        string.drawAtPoint_((x, height - y - string.size().height))
    AppKit.NSGraphicsContext.restoreGraphicsState()
    return Quartz.CGBitmapContextCreateImage(context)


@pytest.fixture
def text_image():
    return render_text
