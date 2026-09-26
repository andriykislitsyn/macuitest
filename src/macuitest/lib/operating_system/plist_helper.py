import os
import plistlib
from typing import Any
from typing import Dict

from macuitest.lib.core import wait_condition


class PropertyListMissing(Exception):
    pass


class PlistHelper:
    def __init__(self, property_list):
        self.plist = property_list

    def read_property(self, key) -> Any:
        return self.read_plist().get(key)

    def delete_property(self, key):
        _content = self.read_plist()
        try:
            _content.pop(key)
        except KeyError:
            return
        self.write_plist(_content)

    def set_property(self, key, value):
        _content = self.read_plist()
        _content[key] = value
        self.write_plist(_content)

    def write_plist(self, content):
        with open(self.plist, "wb") as f:
            plistlib.dump(content, f)

    def read_plist(self) -> Dict[str, Any]:
        """Read the property list, XML or binary.

        Raises:
            PropertyListMissing: The file didn't appear within 15 seconds.
            plistlib.InvalidFileException: The file isn't a valid property list.
        """
        if not wait_condition(lambda: os.path.exists(self.plist), timeout=15):
            raise PropertyListMissing
        with open(self.plist, "rb") as f:
            return plistlib.load(f)
