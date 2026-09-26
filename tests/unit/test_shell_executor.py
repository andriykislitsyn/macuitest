import logging
import subprocess
from unittest import mock

import pytest

from macuitest.lib.operating_system import shell_executor
from macuitest.lib.operating_system.shell_executor import ShellExecutor

PASSWORD = 'pa"ss $word'


@pytest.fixture
def run():
    with mock.patch.object(shell_executor.subprocess, "run") as run:
        run.return_value = subprocess.CompletedProcess(
            args="", returncode=1, stdout=b"", stderr=b"denied"
        )
        yield run


@pytest.fixture
def executor():
    executor = ShellExecutor()
    with mock.patch.object(executor, "get_admin_password", return_value=PASSWORD):
        yield executor


def test_sudo_sends_the_password_on_stdin_not_the_command_line(run, executor):
    executor.sudo("ls /private")

    run.assert_called_once()
    assert run.call_args.args[0] == 'sudo -S -p "" ls /private'
    assert run.call_args.kwargs["input"] == f"{PASSWORD}\n".encode()


def test_failed_sudo_command_does_not_log_the_password(run, executor, caplog):
    with caplog.at_level(logging.DEBUG):
        executor.sudo("ls /private")

    assert "ls /private" in caplog.text
    assert PASSWORD not in caplog.text


def test_password_validation_keeps_the_password_off_the_command_line(run):
    run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

    assert ShellExecutor._is_sudo_password(PASSWORD)
    assert PASSWORD not in " ".join(run.call_args.args[0])
    assert run.call_args.kwargs["input"] == f"{PASSWORD}\n"
