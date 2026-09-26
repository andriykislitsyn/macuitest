from macuitest.lib.operating_system.env import env
from macuitest.lib.operating_system.macos import macos


def test_macos_version():
    assert isinstance(env.version, tuple)
    assert 2 <= len(env.version) <= 3
    assert env.version[0] >= 10


def test_major_macos_version():
    assert env.version_major == env.version[:2]


def test_printable_macos_version():
    assert env.version_major_str == f"{env.version[0]}.{env.version[1]}"


def test_paths():
    assert env.home.startswith("/Users")
    assert ".Trash" in env.trash
    assert "Desktop" in env.desktop
    assert "Documents" in env.documents
    assert "/Library" in env.user_lib and "/Users" in env.user_lib


def test_mac_model():
    assert macos.sys_info.uuid is not None
    assert macos.sys_info.hw_uuid is not None
    assert macos.sys_info.mac_model is not None
    assert macos.sys_info.computer_name is not None
    assert "Mac" in macos.sys_info.model_name or "Apple device" in macos.sys_info.model_name
