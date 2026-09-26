import plistlib

import pytest

from macuitest.lib.operating_system.plist_helper import PlistHelper


def test_set_property_keeps_existing_keys(tmp_path):
    path = tmp_path / "prefs.plist"
    path.write_bytes(plistlib.dumps({"kept": 1}))

    PlistHelper(str(path)).set_property("added", "yes")

    assert plistlib.loads(path.read_bytes()) == {"kept": 1, "added": "yes"}


def test_reads_binary_property_lists(tmp_path):
    path = tmp_path / "binary.plist"
    path.write_bytes(plistlib.dumps({"key": "value"}, fmt=plistlib.FMT_BINARY))

    assert PlistHelper(str(path)).read_property("key") == "value"


def test_invalid_property_list_raises_instead_of_being_overwritten(tmp_path):
    path = tmp_path / "broken.plist"
    path.write_bytes(b"not a plist")

    with pytest.raises(plistlib.InvalidFileException):
        PlistHelper(str(path)).set_property("key", "value")
    assert path.read_bytes() == b"not a plist"
