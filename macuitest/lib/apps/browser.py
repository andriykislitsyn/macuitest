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
        as_wrapper.tell_app(self.name, f'make new document with properties {{URL:"{url}"}}')
        wait_condition(lambda: self.native_window is not None)

    def close_tabs(self):
        if self.is_running:
            as_wrapper.tell_app(self.name, 'close tabs of every window', ignoring_responses=True)
            assert wait_condition(lambda: as_wrapper.tell_app(self.name, 'return the number of tabs in windows') == 0)

    def did_webpage_load(self, expected_address: str) -> bool:
        assert self.did_launch
        wait_condition(lambda: self.native_window is not None)
        wait_condition(lambda: self.execute_js_command('document.readyState') == 'complete', timeout=15)
        return wait_condition(lambda: expected_address in self.document_url, timeout=5)

    def execute_js_command(self, command: str) -> None:
        command = command.replace('"', '\\"')
        return as_wrapper.tell_app(self.name, f'tell front document to do JavaScript "{command}"')

    def search_web(self, query: str):
        return as_wrapper.tell_app(self.name, f'tell front tab to search the web for "{query}"')

    def confirm_download(self) -> None:
        time.sleep(.5)
        if confirm_download_dialog := self.confirm_download_dialog:
            confirm_download_dialog.find_element(AXRole='AXButton', AXTitle='Allow').AXPress()

    @property
    def document_cookies(self):
        return self.execute_js_command('document.cookie')

    @property
    def document_url(self) -> str: return as_wrapper.tell_app(self.name, f'tell front document to return URL')

    @property
    def document_name(self) -> str: return as_wrapper.tell_app(self.name, f'tell front document to return name')

    @property
    def document_html(self) -> str: return as_wrapper.tell_app(self.name, f'tell front document to return source')

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
        return self.native_window.find_element(AXIdentifier='StopReloadButton', recursive=True)

    @property
    def address_bar(self) -> NativeUIElement:
        return self.native_window.find_element(AXIdentifier='WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD', recursive=True)

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
