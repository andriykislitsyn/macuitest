from unittest import mock

import pytest

from macuitest.lib.applescript_lib import applescript_wrapper
from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper


@pytest.fixture
def ns_applescript():
    applescript_wrapper._script.cache_clear()
    with (
        mock.patch.object(applescript_wrapper, "NSAppleScript") as ns_applescript,
        mock.patch.object(applescript_wrapper.ae_converter, "unpack", side_effect=lambda r: r),
    ):
        script = ns_applescript.alloc.return_value.initWithSource_.return_value
        script.executeAndReturnError_.return_value = ("result", None)
        yield ns_applescript
    applescript_wrapper._script.cache_clear()


def test_repeated_source_reuses_one_compiled_script(ns_applescript):
    as_wrapper.execute("return 1")
    as_wrapper.execute("return 1")
    as_wrapper.execute("return 2")

    assert [
        call.args[0] for call in ns_applescript.alloc.return_value.initWithSource_.call_args_list
    ] == [
        "return 1",
        "return 2",
    ]


def test_execution_errors_still_raise(ns_applescript):
    script = ns_applescript.alloc.return_value.initWithSource_.return_value
    script.executeAndReturnError_.return_value = (None, {"NSAppleScriptErrorNumber": -1728})

    with pytest.raises(AppleScriptError):
        as_wrapper.execute("return missing value of nothing")


def test_unit_tests_cant_run_real_applescript():
    with pytest.raises(RuntimeError, match="must not run AppleScript"):
        as_wrapper.tell_app_process("get name of window 1", app_process="Finder")
