import re
from collections import namedtuple

from ApplicationServices import AXUIElementGetTypeID
from ApplicationServices import AXValueGetType
from ApplicationServices import NSPointFromString
from ApplicationServices import NSRangeFromString
from ApplicationServices import NSSizeFromString
from ApplicationServices import kAXValueCFRangeType
from ApplicationServices import kAXValueCGPointType
from ApplicationServices import kAXValueCGSizeType
from CoreFoundation import CFArrayGetTypeID
from CoreFoundation import CFGetTypeID
from CoreFoundation import CFStringGetTypeID


class Converter:
    def __init__(self, ax_ui_element_class=None):
        self.app_ref_class = ax_ui_element_class

    def convert_value(self, value):
        if CFGetTypeID(value) == CFStringGetTypeID():
            try:
                return str(value)
            except UnicodeEncodeError:
                return str(value.encode("utf-8"))
        if CFGetTypeID(value) == AXUIElementGetTypeID():
            return self.convert_app_ref(value)
        if CFGetTypeID(value) == CFArrayGetTypeID():
            return self.convert_list(value)
        if AXValueGetType(value) == kAXValueCGSizeType:
            return self.convert_size(value)
        if AXValueGetType(value) == kAXValueCGPointType:
            return self.convert_point(value)
        if AXValueGetType(value) == kAXValueCFRangeType:
            return self.convert_range(value)
        else:
            return value

    def convert_list(self, value):
        return [self.convert_value(item) for item in value]

    def convert_app_ref(self, value):
        return self.app_ref_class(ref=value)

    @staticmethod
    def convert_size(value):
        repr_searched = re.search("{.*}", str(value)).group()
        CGSize = namedtuple("CGSize", ["width", "height"])
        size = NSSizeFromString(repr_searched)
        return CGSize(size.width, size.height)

    @staticmethod
    def convert_point(value):
        repr_searched = re.search("{.*}", str(value)).group()
        CGPoint = namedtuple("CGPoint", ["x", "y"])
        point = NSPointFromString(repr_searched)
        return CGPoint(point.x, point.y)

    @staticmethod
    def convert_range(value):
        repr_searched = re.search("{.*}", str(value)).group()
        CFRange = namedtuple("CFRange", ["location", "length"])
        _range_ = NSRangeFromString(repr_searched)
        return CFRange(_range_.location, _range_.length)
