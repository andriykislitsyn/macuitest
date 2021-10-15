import os
from typing import Optional
from typing import Tuple

from macuitest.lib.operating_system.shell_executor import ShellExecutor


class Env:
    """macOS environment variables container."""

    _home: Optional[str] = None
    _version: Optional[str] = None

    def __init__(self):
        self.executor = ShellExecutor()

    @property
    def version_str(self) -> str:
        return ".".join(str(i) for i in env.version).strip()

    @property
    def version_major_str(self) -> str:
        return ".".join(str(i) for i in self.version_major).strip()

    @property
    def version_major(self) -> Tuple[int, ...]:
        return self.version[:2]

    @property
    def version(self) -> Tuple[int, ...]:
        """Get macOS version."""
        return tuple((int(item) for item in self.__version.split(".")))

    @property
    def __version(self) -> str:
        if self._version is None:
            self._version = self.executor.get_output("sw_vers -productVersion")
        return self._version

    @property
    def applications(self) -> str:
        return "/Applications"

    @property
    def system_applications(self) -> str:
        return f"{self.system}{self.applications}"

    @property
    def temp_dir(self) -> str:
        return os.getenv("TMPDIR")

    @property
    def system(self) -> str:
        return "/System"

    @property
    def system_library(self) -> str:
        return "/Library"

    @property
    def system_app_support(self) -> str:
        return os.path.join(self.system_library, "Application Support")

    @property
    def system_caches(self) -> str:
        return os.path.join(self.system_library, "Caches")

    @property
    def system_diag_reports(self) -> str:
        return os.path.join(self.system_logs, "DiagnosticReports")

    @property
    def system_extensions(self) -> str:
        return os.path.join(self.system_library, "Extensions")

    @property
    def system_internet_plugins(self) -> str:
        return os.path.join(self.system_library, "Internet Plug-Ins")

    @property
    def system_launch_daemons(self) -> str:
        return os.path.join(self.system_library, "LaunchDaemons")

    @property
    def system_logs(self) -> str:
        return os.path.join(self.system_library, "Logs")

    @property
    def system_preferences(self) -> str:
        return os.path.join(self.system_library, "Preferences")

    @property
    def system_preference_panes(self) -> str:
        return os.path.join(self.system_library, "PreferencePanes")

    @property
    def system_privileged_helper_tools(self) -> str:
        return os.path.join(self.system_library, "PrivilegedHelperTools")

    @property
    def system_security(self) -> str:
        return os.path.join(self.system_library, "Security")

    @property
    def system_widgets(self) -> str:
        return os.path.join(self.system_library, "Widgets")

    @property
    def user(self) -> str:
        return os.environ.get("USER")

    @property
    def home(self) -> str:
        return self.__home

    @property
    def trash(self) -> str:
        return os.path.join(self.__home, ".Trash")

    @property
    def desktop(self) -> str:
        return os.path.join(self.__home, "Desktop")

    @property
    def documents(self) -> str:
        return os.path.join(self.__home, "Documents")

    @property
    def downloads(self) -> str:
        return os.path.join(self.__home, "Downloads")

    @property
    def movies(self) -> str:
        return os.path.join(self.__home, "Movies")

    @property
    def music(self) -> str:
        return os.path.join(self.__home, "Music")

    @property
    def pictures(self) -> str:
        return os.path.join(self.__home, "Pictures")

    @property
    def user_caches(self) -> str:
        return os.path.join(self.user_lib, "Caches")

    @property
    def user_diag_reports(self) -> str:
        return os.path.join(self.user_lib, "Logs", "DiagnosticReports")

    @property
    def user_logs(self) -> str:
        return os.path.join(self.user_lib, "Logs")

    @property
    def user_launch_agents(self) -> str:
        return os.path.join(self.user_lib, "LaunchAgents")

    @property
    def user_app_support(self) -> str:
        return os.path.join(self.user_lib, "Application Support")

    @property
    def user_app_script(self) -> str:
        return os.path.join(self.user_lib, "Application Scripts")

    @property
    def user_saved_app_state(self) -> str:
        return os.path.join(self.user_lib, "Saved Application State")

    @property
    def user_cookies(self) -> str:
        return os.path.join(self.user_lib, "Cookies")

    @property
    def user_containers(self) -> str:
        return os.path.join(self.user_lib, "Containers")

    @property
    def user_group_containers(self) -> str:
        return os.path.join(self.user_lib, "Group Containers")

    @property
    def user_preferences(self) -> str:
        return os.path.join(self.user_lib, "Preferences")

    @property
    def user_lib(self) -> str:
        return os.path.join(self.__home, "Library")

    @property
    def __home(self) -> str:
        """Get path to the user HOME folder."""
        if self._home is None:
            self._home = os.getenv("HOME")
        return self._home


env = Env()
