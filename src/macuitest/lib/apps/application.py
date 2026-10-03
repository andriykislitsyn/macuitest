import os
import time
from typing import Union

from macuitest.lib.applescript_lib.applescript_wrapper import AppleScriptError
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.applescript_element import Window
from macuitest.lib.operating_system.env import env
from macuitest.lib.operating_system.macos import macos
from macuitest.lib.operating_system.plist_helper import PlistHelper


class Application:
    def __init__(self, app_name: str, location: str = env.applications):
        self.name: str = app_name
        self.application_property_list: str = f"{location}/{self.name}.app/Contents/Info.plist"
        self.contents_reader: PlistHelper = PlistHelper(self.application_property_list)
        # Not "window 1": it can resolve to an overlay, such as Chrome's 66x20 phantom window.
        # Keep the parentheses. Without them, `attribute "AXPosition" of first window whose ...`
        # applies `whose` to the attribute, not the window.
        self.window = Window(
            '(first window whose subrole is "AXStandardWindow")', process=self.name
        )

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
        """Move `window` to an AppleScript point such as "{1210, 670}".

        Raises:
            AppleScriptError: The app has no standard window, or System Events rejected the move.
        """
        as_wrapper.tell_app_process(
            f"set position of {self.window.locator} to {position}", self.name
        )

    def set_window_size(self, size: str = "{700, 400}"):
        """Resize `window` to an AppleScript size such as "{700, 400}".

        Raises:
            AppleScriptError: The app has no standard window, or System Events rejected the resize.
        """
        as_wrapper.tell_app_process(f"set size of {self.window.locator} to {size}", self.name)

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

    def set_hidden(self, value: bool = True):
        converted = {True: "true", False: "false"}.get(value)
        self._set_attribute("AXHidden", converted)

    @property
    def is_frontmost(self) -> bool:
        return wait_condition(lambda: self._read_attribute("AXFrontmost"), timeout=5)

    @property
    def is_hidden(self) -> bool:
        return wait_condition(lambda: self._read_attribute("AXHidden"), timeout=3)

    @property
    def frontmost(self) -> bool:
        return self.is_frontmost

    @frontmost.setter
    def frontmost(self, value: bool) -> None:
        self.set_frontmost(value)

    @property
    def hidden(self) -> bool:
        return self.is_hidden

    @hidden.setter
    def hidden(self, value: bool) -> None:
        self.set_hidden(value)

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


finder = Finder()
installer = Installer()
