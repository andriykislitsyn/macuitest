import AppKit
import pytest
import Quartz


def render_text(labels, width, height, scale=2, size=16):
    """Return a CGImage of black `labels` on white, each an (text, x, y) top-left in points."""
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
