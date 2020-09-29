import glob
import os
import time
from typing import ClassVar, List

from macuitest.config.constants import MINUTE
from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper
from macuitest.lib.apps.application import Application
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.native.native_ui_element import NativeUIElement
from macuitest.lib.operating_system.env import env


class Safari(Application):
    def __init__(self, app_name='Safari'):
        super().__init__(app_name)
        self.bundle_id: ClassVar[str] = 'com.apple.Safari'

    def download_file(self, url: str, file_name: str = '*pattern*', timeout: int = MINUTE):
        _before_ = self.downloads
        self.request_webpage(url)
        self.confirm_download()
        assert wait_condition(lambda: self.downloads > _before_, timeout=MINUTE)
        assert wait_condition(lambda: glob.glob(os.path.join(env.downloads, '*.download')) == [], timeout=timeout)
        return wait_condition(glob.glob, 30, os.path.join(env.downloads, file_name))

    def request_webpage(self, url: str):
        as_wrapper.tell_app(self.name, 'make new document with properties {URL:"%s"}' % url)

    def close_tabs(self):
        if self.native_window:
            as_wrapper.tell_app(self.name, 'close tabs of front window')
            wait_condition(lambda: not self.tabs)

    def did_webpage_load(self, webpage_address: str) -> bool:
        wait_condition(lambda: self.stop_reload_button is not None)
        wait_condition(lambda: self.stop_reload_button.AXTitle == 'Reload this page')
        wait_condition(lambda: self.execute_js_command('document.readyState') == 'complete')
        return webpage_address in self.address_bar_value

    def execute_js_command(self, command: str) -> None:
        return as_wrapper.tell_app(self.name, f'''tell front document to do JavaScript "{command}"''')

    def confirm_download(self) -> None:
        if confirm_download_dialog := self.confirm_download_dialog:
            confirm_download_dialog.find_element(AXRole='AXButton', AXTitle='Allow').AXPress()

    def __get_address_bar_value(self) -> str:
        return self.address_bar.AXValue

    def __set_address_bar_value(self, new_value: str) -> None:
        address_bar = self.address_bar
        address_bar.AXFocused = True
        time.sleep(.5)
        address_bar.AXValue = new_value

    address_bar_value = property(__get_address_bar_value, __set_address_bar_value)

    @property
    def stop_reload_button(self) -> NativeUIElement:
        return self.address_bar.AXParent.find_element(AXIdentifier='StopReloadButton')

    @property
    def address_bar(self) -> NativeUIElement:
        return self.tool_bar.find_element(AXIdentifier='WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD', recursive=True)

    @property
    def tool_bar(self) -> NativeUIElement:
        return self.native_window.find_element(AXRole='AXToolbar')

    @property
    def tabs(self) -> List[NativeUIElement]:
        try:
            result = self.native_window.find_element(AXIdentifier='TabBar').AXChildren
        except AttributeError:
            result = []
        return result

    @property
    def confirm_download_dialog(self) -> NativeUIElement:
        return self.native_window.find_element(AXIdentifier='AXSafariModalDialog', recursive=True)

    @property
    def native_window(self) -> NativeUIElement:
        return NativeUIElement.from_bundle_id(self.bundle_id).find_element(AXRole='AXWindow', AXMain=True)

    @property
    def downloads(self) -> List[str]:
        return [f for f in os.listdir(env.downloads) if not f.startswith('.')]


safari = Safari()
