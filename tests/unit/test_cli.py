import subprocess
import sys
import textwrap
from unittest import mock

import pytest

from macuitest import cli
from macuitest.config.constants import Region
from macuitest.lib import actions
from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.lib.elements.locators.target import Target
from macuitest.lib.elements.native.calls import AXErrorUnsupported
from macuitest.lib.elements.screen_element import UIElementNotFoundOnScreen

LOCATOR = 'ax(identifier="OK", kind=Button)'


def test_check_exits_zero_for_a_clean_module(tmp_path, capsys):
    module = tmp_path / "screens.py"
    module.write_text("from macuitest.lib.elements.locators import Screen\n")

    assert cli.main(["check", str(module)]) == 0
    assert capsys.readouterr().out == ""


def test_check_lists_missing_images_and_exits_one(tmp_path, capsys):
    module = tmp_path / "screens.py"
    module.write_text(
        textwrap.dedent(
            """
            from macuitest.lib.elements.locators import Screen, image

            class Main(Screen):
                ok = image()
            """
        )
    )

    assert cli.main(["check", str(module)]) == 1
    assert f"Missing: {tmp_path / 'screens' / 'main' / 'ok.png'}" in capsys.readouterr().out


def test_capture_passes_its_options(tmp_path):
    out = tmp_path / "c.py"
    with mock.patch.object(cli, "capture", autospec=True, return_value=[out]) as run:
        code = cli.main(
            [
                "capture",
                "Calculator",
                "--out",
                str(out),
                "--role",
                "AXButton",
                "--margin",
                "2",
                "--force",
                "--append",
            ]
        )

    assert code == 0
    run.assert_called_once_with(
        "Calculator", out, roles=["AXButton"], margin=2.0, force=True, window=None, append=True
    )


def test_capture_passes_the_window_to_match(tmp_path):
    out = tmp_path / "f.py"
    with mock.patch.object(cli, "capture", autospec=True, return_value=[out]) as run:
        cli.main(["capture", "Finder", "--out", str(out), "--window-subrole", "AXDialog"])

    assert run.call_args.kwargs["window"] == AXQuery.of(subrole="AXDialog")


@pytest.mark.parametrize(
    "error",
    [
        LookupError("no window"),
        FileExistsError("exists"),
        PermissionError("not granted"),
        OSError("Can't write c/png.png"),
    ],
)
def test_capture_errors_exit_one_with_the_message(tmp_path, capsys, error):
    with mock.patch.object(cli, "capture", autospec=True, side_effect=error):
        code = cli.main(["capture", "Calculator", "--out", str(tmp_path / "c.py")])

    assert code == 1
    assert str(error) in capsys.readouterr().err


def test_a_negative_margin_is_a_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["capture", "Calculator", "--out", str(tmp_path / "c.py"), "--margin", "-1"])

    assert exit_info.value.code == 2


def test_tree_passes_its_options_and_prints_the_tree(capsys):
    with mock.patch.object(cli, "tree", autospec=True, return_value="AXWindow\n") as run:
        code = cli.main(
            ["tree", "TextEdit", "--window-title", "Fonts", "--role", "AXButton", "--activate"]
        )

    assert code == 0
    run.assert_called_once_with(
        "TextEdit", window=AXQuery.of(title="Fonts"), roles=["AXButton"], activate=True
    )
    assert capsys.readouterr().out == "AXWindow\n"


@pytest.mark.parametrize("error", [LookupError("no windows"), PermissionError("not granted")])
def test_tree_errors_exit_one_with_the_message(capsys, error):
    with mock.patch.object(cli, "tree", autospec=True, side_effect=error):
        code = cli.main(["tree", "Calculator"])

    assert code == 1
    assert str(error) in capsys.readouterr().err


@pytest.mark.parametrize("name", ["missing.py", "notes.txt"])
def test_check_of_a_module_it_cant_load_exits_one_with_the_message(tmp_path, capsys, name):
    (tmp_path / "notes.txt").write_text("notes")

    code = cli.main(["check", str(tmp_path / name)])

    assert code == 1
    assert name in capsys.readouterr().err


def test_python_m_macuitest_runs_the_command_line():
    result = subprocess.run(
        [sys.executable, "-m", "macuitest", "--help"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    assert "usage: macuitest" in result.stdout


def test_the_old_locators_command_is_gone():
    result = subprocess.run(
        [sys.executable, "-m", "macuitest.locators", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0


@pytest.fixture
def target(monkeypatch):
    """Resolve every target to one fake element of TextEdit."""
    element = mock.Mock()
    resolved = Target(element, "TextEdit", LOCATOR)
    resolve = mock.Mock(return_value=resolved)
    monkeypatch.setattr(cli, "resolve", resolve)
    return resolved


def test_find_prints_the_element(target, capsys):
    snapshot = actions.Snapshot("AXButton", "Search", None, Region(412, 88, 436, 112))
    with mock.patch.object(cli.actions, "find", autospec=True, return_value=snapshot):
        code = cli.main(["find", "TextEdit", LOCATOR])

    assert code == 0
    assert capsys.readouterr().out == 'AXButton "Search" at 412,88 24x24 value=None\n'


def test_find_prints_only_the_box_of_a_screen_element(target, capsys):
    snapshot = actions.Snapshot(box=Region(1, 2, 11, 22))
    with mock.patch.object(cli.actions, "find", autospec=True, return_value=snapshot):
        cli.main(["find", "TextEdit", LOCATOR])

    assert capsys.readouterr().out == "at 1,2 10x20\n"


def test_find_exits_one_when_the_element_is_missing(target, capsys):
    with mock.patch.object(cli.actions, "find", autospec=True, return_value=None):
        code = cli.main(["find", "TextEdit", LOCATOR])

    assert code == 1
    assert capsys.readouterr().err == (
        f"Not found: {LOCATOR}. List elements with: macuitest tree TextEdit\n"
    )


def test_find_exits_one_when_the_app_isnt_running(capsys):
    with mock.patch("macuitest.lib.elements.locators.factories.windows", return_value=[]):
        code = cli.main(["find", "NoSuchApp", LOCATOR])

    assert code == 1
    assert "Not found" in capsys.readouterr().err


def test_read_prints_the_value(target, capsys):
    with mock.patch.object(cli.actions, "read", autospec=True, return_value="Untitled"):
        assert cli.main(["read", "TextEdit", LOCATOR]) == 0

    assert capsys.readouterr().out == "Untitled\n"


def test_read_prints_nothing_for_no_value(target, capsys):
    with mock.patch.object(cli.actions, "read", autospec=True, return_value=None):
        cli.main(["read", "TextEdit", LOCATOR])

    assert capsys.readouterr().out == "\n"


@pytest.mark.parametrize(
    "arguments, vanish, timeout", [([], False, None), (["--vanish", "--timeout", "2"], True, 2.0)]
)
def test_wait_passes_its_options(target, arguments, vanish, timeout):
    with mock.patch.object(cli.actions, "wait", autospec=True, return_value=True) as wait:
        assert cli.main(["wait", "TextEdit", LOCATOR, *arguments]) == 0

    wait.assert_called_once_with(target.element, vanish=vanish, timeout=timeout)


def test_wait_exits_one_on_timeout(target, capsys):
    with mock.patch.object(cli.actions, "wait", autospec=True, return_value=False):
        assert cli.main(["wait", "TextEdit", LOCATOR]) == 1

    assert "Timed out" in capsys.readouterr().err


def test_press_passes_the_pause(target):
    with mock.patch.object(cli.actions, "press", autospec=True) as press:
        assert cli.main(["press", "TextEdit", LOCATOR, "--pause", "0.5"]) == 0

    press.assert_called_once_with(target.element, pause=0.5)


def test_set_passes_the_value_after_the_target(target):
    with mock.patch.object(cli.actions, "set_value", autospec=True) as set_value:
        assert cli.main(["set", "TextEdit", LOCATOR, "hello"]) == 0

    set_value.assert_called_once_with(target.element, "hello")


def test_set_needs_exactly_one_value(target, capsys):
    with pytest.raises(SystemExit) as exit_:
        cli.main(["set", "TextEdit", LOCATOR])

    assert exit_.value.code == 2


def test_extra_arguments_after_the_target_exit_two(target):
    with pytest.raises(SystemExit) as exit_:
        cli.main(["press", "TextEdit", LOCATOR, "extra"])

    assert exit_.value.code == 2


def test_click_passes_the_app_and_options(target):
    with mock.patch.object(cli.actions, "click", autospec=True) as click:
        assert cli.main(["click", "TextEdit", LOCATOR, "--double"]) == 0

    click.assert_called_once_with(target.element, "TextEdit", double=True, right=False)


@pytest.mark.parametrize(
    "error, code",
    [
        (actions.UsageError("press needs an ax() element"), 2),
        (ValueError("could not convert"), 2),
        (actions.FocusError("TextEdit didn't come to the front"), 1),
        (AXErrorUnsupported('Attribute "AXValue" is not settable'), 1),
        (PermissionError("Grant Accessibility"), 1),
    ],
)
def test_action_errors_map_to_exit_codes(target, capsys, error, code):
    with mock.patch.object(cli.actions, "press", autospec=True, side_effect=error):
        assert cli.main(["press", "TextEdit", LOCATOR]) == code

    assert str(error) in capsys.readouterr().err


def test_click_exits_one_when_a_screen_element_isnt_on_screen(target, capsys):
    with mock.patch.object(
        cli.actions, "click", autospec=True, side_effect=UIElementNotFoundOnScreen("x")
    ):
        assert cli.main(["click", "TextEdit", LOCATOR]) == 1

    assert "Not found" in capsys.readouterr().err


def test_an_invalid_locator_exits_two(capsys):
    assert cli.main(["find", "TextEdit", "eval('1')"]) == 2
    assert "Expected a call" in capsys.readouterr().err


def test_window_flags_with_a_module_reference_exit_two(tmp_path, capsys):
    module = tmp_path / "screens.py"
    module.write_text("from macuitest.lib.elements.locators import Screen\n")

    assert cli.main(["find", f"{module}:Main.ok", "--window-title", "Fonts"]) == 2
    assert "--window" in capsys.readouterr().err


def test_find_prints_the_value_of_an_element_without_a_role(target, capsys):
    with mock.patch.object(
        cli.actions, "find", autospec=True, return_value=actions.Snapshot(value="OK")
    ):
        cli.main(["find", "TextEdit", LOCATOR])

    assert capsys.readouterr().out == "value='OK'\n"
