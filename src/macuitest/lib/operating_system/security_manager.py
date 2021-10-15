class WrongApplicationSignature(Exception):
    pass


class SecurityManager:
    """Wrapper around the Command line interface to keychains and Security framework."""

    _cli: str = "security"

    def __init__(self, executor):
        self.executor = executor

    def enable_gatekeeper(self):
        """Allow opening apps from identified developers only."""
        self.executor.sudo("spctl --master-enable")

    def disable_gatekeeper(self):
        """Allow opening apps from unidentified developers."""
        self.executor.sudo("spctl --master-disable")

    def check_package_signature(self, package_path: str) -> int:
        return self.executor.execute(f'pkgutil --check-signature "{package_path}"').returncode

    def check_application_signature(self, application_path):
        output = self.executor.sudo_get_output(f"codesign -v --deep {application_path}")
        if output:
            error_message = f"{application_path} is not sign correctly: {output}"
            raise WrongApplicationSignature(error_message)

    def remove_keychain_entry(self, service_name: str, flag: str = "s") -> None:
        """Remove a keychain by a service name."""
        while self.find_generic_password(service_name, flag) == 0:
            self.delete_generic_password(service_name, flag)

    def find_generic_password(self, service_name: str, flag: str = "s") -> int:
        """Find a password in login keychain by a service name."""
        return self.executor.execute(
            f"{self._cli} find-generic-password -{flag} {service_name} > /dev/null 2>&1"
        ).returncode

    def delete_generic_password(self, service_name: str, flag: str = "s") -> int:
        """Delete a password in login keychain by a service name."""
        return self.executor.execute(
            f"{self._cli} delete-generic-password -{flag} {service_name} > /dev/null 2>&1"
        ).returncode

    def reset_authorization_database(self, search_pattern: str = "Auth") -> int:
        """Clear the system.login.console authorization rights."""
        result = -9001
        database_content = self.read_authorizationdb()
        if search_pattern in database_content:
            _updated = "\n".join(
                (ln for ln in database_content.splitlines() if search_pattern not in ln)
            )
            result = self.update_authorizationdb(_updated)
        return result

    def reset_access_to_service(self, service: str, client: str = "") -> int:
        """Reset all decisions for the specified service.
        The `tccutil` manages the privacy database, which stores decisions the user has made
        about whether apps may access personal data. Reset will cause apps to prompt again
        the next time they access the service.

        If a bundle identifier is specified, the service will be reset for that bundle only.
        """
        return self.executor.execute(f"tccutil reset {service} {client}".rstrip())

    def read_authorizationdb(self, right: str = "system.login.console") -> str:
        """Read a login authorization database that controls macOS login progress."""
        return self.executor.get_output(f"{self._cli} -q authorizationdb read {right}")

    def update_authorizationdb(self, payload: str) -> int:
        """Update contents of the login authorization database."""
        return self.executor.sudo(
            f"-v;sudo {self._cli} -q authorizationdb write system.login.console <<< '{payload}'"
        )
