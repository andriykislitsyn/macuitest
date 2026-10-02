import textwrap
from unittest import mock

import pytest

from macuitest.lib.elements.locators.accessibility import AXQuery
from macuitest.locators import __main__ as cli


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
            ]
        )

    assert code == 0
    run.assert_called_once_with(
        "Calculator", out, roles=["AXButton"], margin=2.0, force=True, window=None
    )


def test_capture_passes_the_window_to_match(tmp_path):
    out = tmp_path / "f.py"
    with mock.patch.object(cli, "capture", autospec=True, return_value=[out]) as run:
        cli.main(["capture", "Finder", "--out", str(out), "--window-subrole", "AXDialog"])

    assert run.call_args.kwargs["window"] == AXQuery.of(subrole="AXDialog")


@pytest.mark.parametrize(
    "error", [LookupError("no window"), FileExistsError("exists"), PermissionError("not granted")]
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
