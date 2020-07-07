import glob
import logging
import os
import time
from typing import Union, List

import atomacos

from lib.applescript_lib.applescript_wrapper import as_wrapper, AppleScriptError
from lib.application import Application
from lib.core import wait_condition
from lib.elements.applescript_element import ASElement
from lib.elements.ui_element import UIElement
from lib.operating_system.env import env
from lib.operating_system.macos import macos
from lib.ui_element.screenshot_path_builder import ScreenshotPathBuilder


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
        self.close_tabs()
        self.activate()
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
        time.sleep(0.6)
        as_wrapper.typewrite(url)
        time.sleep(0.6)
        as_wrapper.send_keycode(as_wrapper.key_codes['return'])
        time.sleep(0.3)

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
        if not wait_condition(lambda: glob.glob(os.path.join(target_directory,
                                                             self.download_temp_pattern)) == [], timeout):
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
        address_bar = atomacos.getAppRefByBundleId('com.apple.Safari').windows()[0] \
            .findFirstR(AXIdentifier='WEB_BROWSER_ADDRESS_AND_SEARCH_FIELD')
        address_bar.AXValue = new_value
        time.sleep(1)


class _Chrome(_BaseBrowser):
    def __init__(self, app_name='Google Chrome'):
        super(_Chrome, self).__init__(app_name)
        self._screenshot = ScreenshotPathBuilder('system')
        self.document_type = 'window'
        self.download_temp_pattern = '*.crdownload'
        self.button_keep = ASElement('button "Keep" of group 1 of tool bar 1 of window 1', self.name)
        self.btn_download = ASElement(f'button 1 of group 1 of group "Downloads bar" of group 1 of window 1', self.name)
        self.btn_discard = ASElement(f'button 3 of group 1 of group "Downloads bar" of group 1 of window 1', self.name)
        self.btn_discard_ui = UIElement(self._screenshot.btn_discard__chrome)
        self.icon_warning_ui = UIElement(self._screenshot.icon_warning__chrome)

    def open_link_as_user(self, url, is_download_confirmation_needed=False):
        super(_Chrome, self).open_link_as_user(url, is_download_confirmation_needed)

    def wait_download_finished(self, target_directory, timeout=180):
        """Wait for a temporary file to be removed from the download directory."""
        time.sleep(3)
        if not wait_condition(lambda: self.files_in_downloads_dir > self.downloads_count, 120):
            raise DownloadHasNotStartedException  # Sometimes resolver works slower than we need. So we wait 2m.
        if self.btn_download.wait_displayed(timeout=30):
            if self.icon_warning_ui.wait_displayed(region=self.btn_download.region()) \
                    or self.btn_discard_ui.wait_displayed(region=self.btn_download.region()):
                raise MaliciousFileWarning
        if not wait_condition(
                lambda: glob.glob(os.path.join(target_directory, self.download_temp_pattern)) == [], timeout):
            raise DownloadHasNotFinishedException


class _Firefox(_BaseBrowser):
    count_windows_command = 'tell application "System Events" to tell application process "firefox" to count windows'

    def __init__(self, app_name='firefox'):
        super().__init__(app_name)
        self._screenshot = ScreenshotPathBuilder('common')
        self.download_temp_pattern = '*.part'
        self.btn_cancel = UIElement(self._screenshot.btn_sys_cancel)
        self.btn_save_file = UIElement(self._screenshot.btn_save_file)

    def quit(self, pause: Union[int, float] = 2) -> None:
        _name_tmp = str(self.name)
        self.name = self.name.lower()
        super().quit(pause=pause)
        self.name = _name_tmp

    def close_tabs(self):
        self.close_windows()

    def open_new_tab(self):
        self.launch()
        time.sleep(0.5)
        as_wrapper.send_keystroke('t', 'command')  # Firefox does not support a "make new ..." AppleScript command.
        time.sleep(0.5)

    def confirm_download(self):
        if not wait_condition(lambda: self.windows_count > 1, timeout=120):
            raise DownloadHasNotStartedException
        if self.btn_save_file.is_visible:
            self.btn_save_file.double_click()
            if self.btn_cancel.wait_displayed(timeout=2):
                self.btn_cancel.click(x_off=90)

    @property
    def windows_count(self):
        return as_wrapper.execute(self.count_windows_command)

    @property
    def active_tab_url(self):
        url = as_wrapper.execute(self._get_url_command)
        macos.shell_executor.execute('pbcopy </dev/null')
        return url

    @property
    def _get_url_command(self):
        return '''
            tell application "firefox" to activate
            tell application "System Events"
                keystroke "l" using command down
                keystroke "c" using command down
            end tell
            delay 0.5
            return the clipboard'''


class _FirefoxMavericks(_Firefox):
    def __init__(self):
        super().__init__()
        self.btn_cancel = UIElement(self._screenshot.btn_cancel_firefox)

    def confirm_download(self):
        wait_condition(lambda: self.windows_count == 2)
        if self.btn_save_file.wait_displayed():
            self.btn_save_file.double_click()
            if self.btn_cancel.wait_displayed(timeout=2):
                self.btn_cancel.click(x_off=90)


chrome, firefox, safari = _Chrome(), _Firefox(), _Safari()
