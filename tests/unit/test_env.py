from macuitest.lib.operating_system.macos import macos
from macuitest.lib.operating_system.env import env


def test_macos_version():
    assert isinstance(env.version, tuple)
    assert 2 <= len(env.version) <= 3
    assert env.version[0] == 10
    assert 9 <= env.version[1] <= 15


def test_major_macos_version():
    assert isinstance(env.version_major, tuple)
    assert len(env.version_major) == 2
    assert env.version_major[0] == 10
    assert 9 <= env.version_major[1] <= 15


def test_printable_macos_version():
    assert isinstance(env.version_major_str, str)
    assert env.version_major_str.startswith('10.')


def test_paths():
    assert env.home.startswith('/Users')
    assert '.Trash' in env.trash
    assert 'Desktop' in env.desktop
    assert 'Documents' in env.documents
    assert '/Library' in env.user_lib and '/Users' in env.user_lib


def test_mac_model():
    assert macos.sys_info.uuid is not None
    assert macos.sys_info.hw_uuid is not None
    assert macos.sys_info.mac_model is not None
    assert macos.sys_info.computer_name is not None
    assert 'Mac' in macos.sys_info.model_name
