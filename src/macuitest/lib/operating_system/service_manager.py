import time
from collections import namedtuple
from pathlib import Path
from typing import List
from typing import Union

from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper
from macuitest.lib.core import wait_condition
from macuitest.lib.operating_system.shell_executor import ShellExecutor


class ServiceManager:
    Service = namedtuple("Service", ["id", "is_system_service"])

    def __init__(self, executor: ShellExecutor):
        self.executor = executor

    def launch_application_by_bundle_id(self, bundle_id: str, process_name: str) -> bool:
        self.executor.execute(f'open -b "{bundle_id}"')
        return self.wait_process_appeared(process_name)

    def launch_application_by_name(self, app_name: str) -> bool:
        self.executor.execute(f'open -a "{app_name}"')
        return self.wait_process_appeared(app_name)

    def launch_application_by_path(self, path: str) -> bool:
        self.executor.execute(f'open "{path}"')
        return self.wait_process_appeared(Path(path).stem)

    def force_kill_process(self, process: str, sudo: bool = False):
        _execute = self.executor.sudo if sudo else self.executor.execute
        return _execute(f"pkill -9 {process}")

    def kill_process(self, process, sudo=False, pause: Union[int, float] = 1):
        time.sleep(pause)
        _execute = self.executor.sudo if sudo else self.executor.execute
        _execute(f'killall -9 "{process}"')
        return self.wait_process_disappeared(process)

    def wait_process_appeared(self, process_name, timeout=10):
        return wait_condition(lambda: process_name in self.processes_list, timeout=timeout)

    def wait_process_disappeared(self, process_name, timeout=10):
        return wait_condition(lambda: process_name not in self.processes_list, timeout=timeout)

    @property
    def processes_list(self) -> List[str]:
        """Return list of system processes."""
        return as_wrapper.tell_sys_events("return name of every process")

    @staticmethod
    def add_login_item(app_name, is_hidden=False):
        app_path = (
            "/System/Applications"
            if Path(f"/System/Applications/{app_name}.app").exists()
            else "/Applications"
        )
        _cmd = 'make login item at end with properties {path:"%s/%s.app", hidden:%s}' % (
            app_path,
            app_name,
            is_hidden,
        )
        return as_wrapper.tell_sys_events(_cmd)

    @staticmethod
    def add_login_item_by_path(path_):
        return as_wrapper.tell_sys_events(
            'make login item at end with properties {path:"%s"}' % path_
        )

    def clear_login_items(self):
        return [self.remove_login_item(login_item) for login_item in self.login_items]

    @staticmethod
    def remove_login_item(login_item: str):
        return as_wrapper.tell_sys_events(f'delete login item "{login_item}"')

    @property
    def login_items(self, hidden=False):
        _cmd = "get the name of every login item"
        if hidden:
            _cmd += " whose hidden is true"
        return as_wrapper.tell_sys_events(_cmd)

    @property
    def cron_jobs(self) -> str:
        return self.executor.get_output("crontab -l")

    def remove_cron_jobs(self) -> int:
        return self.executor.execute("crontab -r")

    def load_service(self, service: Service) -> int:
        return self._manipulate_service("load", service)

    def unload_service(self, service: Service) -> int:
        return self._manipulate_service("unload", service)

    def remove_service(self, service: Service) -> int:
        return self._manipulate_service("remove", service)

    def _manipulate_service(self, action: str, service: Service) -> int:
        _execute = self.executor.sudo if service.is_system_service else self.executor.execute
        flag = " " if action == "remove" else " -wF "
        return _execute(f"launchctl {action}{flag}{service.id}")

    def did_user_service_quit(self, service: str) -> bool:
        return wait_condition(lambda: service not in self.user_services)

    def did_user_service_launch(self, service: str) -> bool:
        return wait_condition(lambda: service in self.user_services)

    def did_system_service_launch(self, service: str) -> bool:
        return wait_condition(lambda: service in self.system_services)

    @property
    def user_services(self) -> List[str]:
        return self.__get_services(domain="user")

    @property
    def system_services(self) -> List[str]:
        return self.__get_services(domain="system")

    def __get_services(self, domain: str = "user") -> List[str]:
        _execute = self.executor.get_output if domain == "user" else self.executor.sudo_get_output
        return [item.split("\t")[-1] for item in _execute("launchctl list").splitlines()]

    def unload_kext(self, kext_id) -> int:
        return self.executor.sudo(f"kextunload -b {kext_id}")

    def get_process_cpu_usage(self, process_name: str) -> float:
        pid = wait_condition(lambda: self.executor.get_output(f"pgrep {process_name}$"), timeout=3)
        if pid:
            return float(
                self.executor.get_output(f"ps -p {pid} -o %cpu").split("%CPU")[1].strip()
            ).__round__(2)
        raise LookupError(f'Process "{process_name}" not found')
