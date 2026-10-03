from unittest import mock

from macuitest.lib.operating_system.service_manager import ServiceManager


def test_launch_application_by_name_quotes_the_name_for_the_shell():
    executor = mock.Mock()
    manager = ServiceManager(executor)

    with mock.patch.object(ServiceManager, "wait_process_appeared", return_value=True):
        manager.launch_application_by_name("Text Edit'; rm -rf ~; '")

    executor.execute.assert_called_once_with("open -a 'Text Edit'\"'\"'; rm -rf ~; '\"'\"''")
