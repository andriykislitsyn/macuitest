import os
from typing import Any
from typing import Dict

import biplist

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
        return biplist.writePlist(content, self.plist, binary=False)

    def read_plist(self) -> Dict[str, Any]:
        payload = dict()
        if not wait_condition(lambda: os.path.exists(self.plist), timeout=15):
            raise PropertyListMissing
        try:
            payload = biplist.readPlist(self.plist)
        except (biplist.NotBinaryPlistException, biplist.InvalidPlistException):
            raise
        finally:
            return payload
