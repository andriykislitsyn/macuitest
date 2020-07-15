import glob
import logging
import os
import time
from typing import List

from macuitest.lib.applescript_lib.applescript_wrapper import as_wrapper, AppleScriptError
from macuitest.lib.apps.application import Application
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.native.native_ui_element import NativeUIElement
from macuitest.lib.operating_system.env import env
from macuitest.lib.operating_system.macos import macos


class DownloadHasNotStartedException(Exception):
    pass


class DownloadHasNotFinishedException(Exception):
    pass


class MaliciousFileWarning(Exception):
    """Thrown when Chrome shows a warning after downloading a malicious file."""
    pass


class _BaseBrowser(Application):
    def __init__(self, app_name):
        super().__init__(app_name)
        self.browser_name = app_name
        self.document_type = None
        self.download_temp_pattern = None
        self.downloads_count = -1

    def close_tabs(self):
        try:
            as_wrapper.execute(f'tell every window of application "{self.name}" to close tabs')
            wait_condition(lambda: not self._get_tabs_number())
        except AppleScriptError:
            pass

    def _get_tabs_number(self) -> List[List[str]]:
        try:
            return as_wrapper.execute(f'tell application "{self.name}" to get name of every tab of every window')
        except AppleScriptError:
            pass

    def download_file(self, url, file_name='file_pattern*', expected_file_size=2 * 10 ** 5):
        self.launch()
        self.open_link_as_user(url, is_download_confirmation_needed=True)
        self.wait_download_finished(env.downloads)
        self.close_tabs()
        file_ = wait_condition(glob.glob, 30, os.path.join(env.downloads, file_name))
        assert file_, f'File missing. Contents of `Downloads` folder: {os.listdir(env.downloads)}'
        logging.info(f'File: {file_[0]}')
        file_size = os.path.getsize(file_[0])
        logging.info(f'Size: {file_size}')
        assert file_size >= expected_file_size, f'Package size < 200KB. Actual size is: {file_size / 10 ** 3}KB'
        return file_[0]

    @staticmethod
    def open_link_in_a_new_tab(url):
        as_wrapper.send_keystroke('t', 'command')
        time.sleep(1)
        as_wrapper.typewrite(url)
        time.sleep(1)
        as_wrapper.send_keycode(as_wrapper.key_codes['return'])
        time.sleep(.5)

    def open_link_as_user(self, url, is_download_confirmation_needed=False):
        self.open_new_tab()
        self.set_address_bar_value(url)
        as_wrapper.send_keycode(as_wrapper.key_codes['return'])
        if is_download_confirmation_needed:
            self.downloads_count = self.files_in_downloads_dir
            self.confirm_download()

    def open_new_tab(self):
        as_wrapper.tell_app(self.name, f'make new {self.document_type}')
        time.sleep(1)

    def open_urls(self, urls: List[str]):
        for url in urls:
            self.open_link_as_user(url)

    def set_address_bar_value(self, new_value):
        macos.shell_executor.execute(f'printf "{new_value}" |pbcopy')
        as_wrapper.send_keystroke('v', 'command')  # Paste the data
        time.sleep(1)

    def confirm_download(self):
        pass

    def wait_download_finished(self, target_directory, timeout=180):
        """Wait for a temporary file to be removed from the download directory."""
        time.sleep(3)
        if not wait_condition(lambda: self.files_in_downloads_dir > self.downloads_count, 120):
            raise DownloadHasNotStartedException  # Sometimes resolver works slower than we need. So we wait 2m.
        if not wait_condition(lambda: glob.glob(os.path.join(target_directory, self.download_temp_pattern)) == [],
                              timeout):
            raise DownloadHasNotFinishedException

    def webpage_did_load(self, webpage_address):
        assert wait_condition(lambda: isinstance(self.active_tab_url, str), timeout=30)
        return wait_condition(lambda: webpage_address in self.active_tab_url, timeout=30)

    @property
    def active_tab_url(self):
        return wait_condition(lambda: as_wrapper.execute(self._get_url_command), timeout=30)

    @property
    def files_in_downloads_dir(self):
        return len([file_ for file_ in os.listdir(env.downloads) if not file_.startswith('.')])

    @property
    def _get_url_command(self):
        return f'''
            try
                tell application "{self.name}" to set page_address to URL of last tab of window 1
                    if page_address as string = "missing value" then
                        return false
                    end if
                return page_address as string
            end try'''


class _Safari(_BaseBrowser):
    def __init__(self, app_name='Safari'):
        super().__init__(app_name)
        self.document_type = 'document'
        self.download_temp_pattern = '*.download'

    def set_address_bar_value(self, new_value: str):
        self.window.wait_displayed(timeout=10)
        address_bar = NativeUIElement.from_bundle_id('com.apple.Safari').windows()[0].find_element(
            AXIdentifier='WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD', recursive=True)
        address_bar.AXValue = new_value
        time.sleep(1)


safari = _Safari()
