from macuitest.lib.operating_system.crash_reporter import CrashReporter
from macuitest.lib.operating_system.defaults import Defaults
from macuitest.lib.operating_system.disk_util import DiskUtil
from macuitest.lib.operating_system.file_manager import FileManager
from macuitest.lib.operating_system.hosts import Hosts
from macuitest.lib.operating_system.login_window import LoginWindow
from macuitest.lib.operating_system.memory_manager import MemoryManager
from macuitest.lib.operating_system.networking import Networking
from macuitest.lib.operating_system.security_manager import SecurityManager
from macuitest.lib.operating_system.service_manager import ServiceManager
from macuitest.lib.operating_system.shell_executor import ShellExecutor
from macuitest.lib.operating_system.system_information import SystemInformation
from macuitest.lib.operating_system.time_manager import TimeManager

__all__ = ["macos"]


class MacOS:
    def __init__(self, shell_executor: ShellExecutor):
        self.shell_executor = shell_executor
        self.crash_reporter = CrashReporter(self.shell_executor)
        self.disk_util = DiskUtil(self.shell_executor)
        self.file_manager = FileManager(self.shell_executor)
        self.login_window = LoginWindow(self.shell_executor)
        self.memory_manager = MemoryManager(self.shell_executor)
        self.networking = Networking(self.shell_executor)
        self.security_manager = SecurityManager(self.shell_executor)
        self.service_manager = ServiceManager(self.shell_executor)
        self.sys_info = SystemInformation(self.shell_executor)
        self.time_manager = TimeManager(self.shell_executor)
        self.defaults = Defaults(self.shell_executor, self.service_manager)
        self.hosts = Hosts(self.shell_executor, self.file_manager)


macos = MacOS(shell_executor=ShellExecutor())
