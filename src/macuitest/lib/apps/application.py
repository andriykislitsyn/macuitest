import logging
import os
import time
from typing import Dict
from typing import List
from typing import Union

from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.applescript_element import ASElement
from macuitest.lib.operating_system.env import env
from macuitest.lib.operating_system.macos import macos
from macuitest.lib.operating_system.plist_helper import PlistHelper


class Application:
    def __init__(self, app_name: str, location: str = env.applications):
        self.name: str = app_name
        self.application_property_list: str = f"{location}/{self.name}.app/Contents/Info.plist"
        self.contents_reader: PlistHelper = PlistHelper(self.application_property_list)
        self.window = ASElement("window 1", process=self.name)

    def close_windows(self):
        try:
            return as_wrapper.tell_app(self.name, "close every window")
        except AppleScriptError:
            pass

    def relaunch(self) -> None:
        self.quit()
        time.sleep(3)
        self.launch()

    def quit(self, pause: Union[int, float] = 2) -> None:
        time.sleep(pause)
        as_wrapper.tell_app(self.name, "quit", ignoring_responses=True)
        if not macos.service_manager.wait_process_disappeared(self.name):
            macos.service_manager.kill_process(self.name)
        if not self.did_quit:
            raise EnvironmentError(f'{self.name} has not quit.')

    @property
    def did_quit(self) -> bool:
        return macos.service_manager.wait_process_disappeared(self.name)

    def launch(self) -> bool:
        macos.service_manager.launch_application_by_name(self.name)
        return self.window.wait_displayed(timeout=15)

    def activate(self):
        as_wrapper.tell_app(app=self.name, command="activate")
        if not self.frontmost:
            raise EnvironmentError(f'{self.name} has not activated')

    def set_window_position(self, position: str = "{1210, 670}"):
        if self.frontmost:
            try:
                return as_wrapper.tell_app_process(
                    f"set position of the front window to {position}", self.name
                )
            except AppleScriptError:
                pass

    def set_window_size(self, size: str = "{700, 400}"):
        if self.frontmost:
            try:
                return as_wrapper.tell_app_process(
                    f"set size of the front window to {size}", self.name
                )
            except AppleScriptError:
                pass

    @property
    def version(self) -> int:
        return self.contents_reader.read_property("CFBundleShortVersionString")

    @property
    def build(self) -> int:
        return self.contents_reader.read_property("CFBundleVersion")

    @property
    def is_running(self) -> bool:
        return macos.service_manager.wait_process_appeared(self.name, timeout=2)

    @property
    def did_launch(self) -> bool:
        return macos.service_manager.wait_process_appeared(self.name, timeout=20)

    def set_frontmost(self, value: bool = True):
        converted = {True: "true", False: "false"}.get(value)
        self._set_attribute("AXFrontmost", converted)

    def is_frontmost(self) -> bool:
        return wait_condition(lambda: self._read_attribute("AXFrontmost"), timeout=5)

    def set_hidden(self, value: bool = True):
        converted = {True: "true", False: "false"}.get(value)
        self._set_attribute("AXHidden", converted)

    def is_hidden(self) -> bool:
        return wait_condition(lambda: self._read_attribute("AXHidden"), timeout=3)

    def _set_attribute(self, attribute, value):
        return self.__execute(f'set value of attribute "{attribute}"', params=f"to {value}")

    def _read_attribute(self, attribute):
        try:
            return self.__execute(f'get value of attribute "{attribute}"')
        except AppleScriptError:
            return None

    def __execute(self, command, params=""):
        """Execute a command.
        :param str command: The name of the command to _execute as a string.
        :param str params: Command parameters.
        :return str: Execution output."""
        _command = f"{command} {params}" if params else f"{command}"
        return as_wrapper.tell_app_process(command=_command, app_process=self.name)

    hidden = property(is_hidden, set_hidden)
    frontmost = property(is_frontmost, set_frontmost)


class Finder(Application):
    def __init__(self):
        super().__init__("Finder")

    @property
    def window_path(self) -> str:
        return as_wrapper.tell_app(
            self.name, "return POSIX path of (target of first window as alias)"
        )

    def eject_mounted_disks(self) -> None:
        return as_wrapper.tell_app(self.name, "eject (every disk whose ejectable is true)")

    def move_file_to_trash(self, target: str) -> None:
        as_wrapper.tell_app(self.name, f'move POSIX file "{target}" to trash')

    def show_destination(self, destination: str) -> None:
        if not os.path.exists(destination):
            raise FileNotFoundError(destination)
        as_wrapper.tell_app(self.name, f'reveal POSIX file "{destination}"')
        self.window.wait_displayed()
        self.activate()

    def open_destination(self, destination: str) -> None:
        if not os.path.exists(destination):
            raise FileNotFoundError(destination)
        as_wrapper.tell_app(self.name, f'open POSIX file "{destination}"')


class Installer(Application):
    def __init__(self):
        super().__init__("Installer")

    def open_destination(self, destination: str) -> None:
        destination = destination.strip()
        if not os.path.exists(destination):
            raise FileNotFoundError(destination)
        macos.shell_executor.execute(f'open "{destination}" -a Installer')
        self.window.wait_displayed(timeout=10)
        self.activate()


class SystemPreferences(Application):
    anchors: Dict[str, str] = {
        "full_disk_access": "Privacy_AllFiles",
        "camera_access": "Privacy_Camera",
    }

    def __init__(self):
        super().__init__("System Preferences")

    def authorize(self):
        return as_wrapper.tell_app(self.name, "tell current pane to authorize")

    def show_anchor(self, anchor: str, pane_id="com.apple.preference.security"):
        return as_wrapper.tell_app(self.name, f'reveal anchor "{anchor}" of pane "{pane_id}"')

    def reveal_pane(self, pane_id="com.apple.preference.security"):
        return as_wrapper.tell_app(self.name, f'reveal pane "{pane_id}"')

    def get_pane_anchors(self, pane_id: str) -> List[str]:
        return as_wrapper.tell_app(self.name, f'return name of every anchor of pane "{pane_id}"')

    @property
    def current_pane_anchors(self) -> List[str]:
        try:
            return as_wrapper.tell_app(self.name, "return name of every anchor of current pane")
        except AppleScriptError:
            logging.warning("You must launch System Preferences first.")
            return list()

    @property
    def current_pane_id(self):
        return as_wrapper.tell_app(self.name, "return id of current pane")

    @property
    def pane_ids(self) -> List[str]:
        return as_wrapper.tell_app(self.name, "return id of every pane")


finder = Finder()
installer = Installer()
system_preferences_app = SystemPreferences()
