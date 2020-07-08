import threading

from macuitest.config.config_parser import config
from macuitest.lib.elements.ui_element import UIElement
from macuitest.lib.elements.uie.screenshot_path_builder import ScreenshotPathBuilder
from macuitest.lib.operating_system.env import env


class WrongApplicationSignature(Exception):
    pass


class SecurityManager:
    """Wrapper around the Command line interface to keychains and Security framework."""
    _cli: str = 'security'
    _screenshot = ScreenshotPathBuilder('common')
    _btn_always_allow = UIElement(_screenshot.btn_always_allow, sim=0.82)

    def __init__(self, executor):
        self.executor = executor

    def enable_gatekeeper(self):
        """Allow opening apps from identified developers only."""
        self.executor.sudo('spctl --master-enable')

    def disable_gatekeeper(self):
        """Allow opening apps from unidentified developers."""
        self.executor.sudo('spctl --master-disable')

    def check_package_signature(self, package_path: str) -> int:
        return self.executor.execute(f'pkgutil --check-signature "{package_path}"').returncode

    def check_application_signature(self, application_path):
        output = self.executor.sudo_get_output(f'codesign -v --deep {application_path}')
        if output:
            error_message = f'{application_path} is not sign correctly: {output}'
            raise WrongApplicationSignature(error_message)

    def remove_keychain_entry(self, service_name: str) -> None:
        """Remove a keychain by a service name."""
        while self.find_generic_password(service_name) == 0:
            self.delete_generic_password(service_name)

    def get_keychain_item_password(self, account_name: str) -> str:
        threading.Thread(target=self._allow_access).start()
        return self.executor.get_output(f'{self._cli} find-generic-password -a "{account_name}" -w')

    def _allow_access(self):
        if self._btn_always_allow.is_visible:
            if env.version > (10, 10):
                self._btn_always_allow.paste(x_off=100, y_off=-40, phrase=config.password)
            self._btn_always_allow.click()
            self._btn_always_allow.wait_vanish()

    def find_generic_password(self, service_name: str) -> int:
        """Find a password in login keychain by a service name."""
        return self.executor.execute(f'{self._cli} find-generic-password -s {service_name} > /dev/null 2>&1').returncode

    def delete_generic_password(self, service_name: str) -> int:
        """Delete a password in login keychain by a service name."""
        return self.executor.execute(f'{self._cli} delete-generic-password -s {service_name} > /dev/null 2>&1')

    def reset_authorization_database(self, search_pattern: str = 'Auth') -> int:
        """Clear the system.login.console authorization rights."""
        result = -9001
        database_content = self.read_authorizationdb()
        if search_pattern in database_content:
            _updated = '\n'.join((ln for ln in database_content.splitlines() if search_pattern not in ln))
            result = self.update_authorizationdb(_updated)
        return result

    def reset_access_to_service(self, service: str, client: str = '') -> int:
        """Reset all decisions for the specified service.
        The `tccutil` manages the privacy database, which stores decisions the user has made
        about whether apps may access personal data. Reset will cause apps to prompt again
        the next time they access the service.

        If a bundle identifier is specified, the service will be reset for that bundle only.
        """
        return self.executor.execute(f'tccutil reset {service} {client}'.rstrip())

    def read_authorizationdb(self, right: str = 'system.login.console') -> str:
        """Read a login authorization database that controls macOS login progress."""
        return self.executor.get_output(f'{self._cli} -q authorizationdb read {right}')

    def update_authorizationdb(self, payload: str) -> int:
        """Update contents of the login authorization database."""
        return self.executor.sudo(f"-v;sudo {self._cli} -q authorizationdb write system.login.console <<< '{payload}'")
