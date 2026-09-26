import logging
import os
import subprocess
from typing import Optional
from typing import Union


class ShellExecutor:
    execution_timeout_code: int = -1001
    pipe: int = -1
    stdout: int = -2
    devnull: int = -3

    def __init__(self):
        self.__password: Optional[str] = None

    def sudo_get_output(self, cmd: str, timeout: Optional[int] = None) -> Optional[str]:
        """Execute shell instruction with elevated privileges and return execution output."""
        response = self.sudo(cmd, timeout=timeout)
        if isinstance(response, subprocess.CompletedProcess):
            return response.stdout.decode(encoding="utf-8").strip()

    def get_output(self, cmd: str, timeout: Optional[int] = None) -> Optional[str]:
        """Execute shell instruction and return execution output."""
        response = self.__execute(cmd=cmd, timeout=timeout)
        if isinstance(response, subprocess.CompletedProcess):
            return response.stdout.decode(encoding="utf-8").strip()

    def sudo(
        self, cmd: str, timeout: Optional[int] = None
    ) -> Union[subprocess.CompletedProcess, int]:
        """Execute shell instruction with elevated privileges and return execution code."""
        return self.__execute(
            cmd=f'sudo -S -p "" {cmd}', timeout=timeout, stdin=f"{self.get_admin_password()}\n"
        )

    def execute(
        self, cmd: str, timeout: Optional[int] = None
    ) -> Union[subprocess.CompletedProcess, int]:
        """Execute a shell instruction and return a `CompletedProcess` object."""
        return self.__execute(cmd=cmd, timeout=timeout)

    def get_admin_password(self, auto_keychain: str = "com.macuitest.automation"):
        if self.__password is None:
            subprocess.call("sudo -k", shell=True)
            _password = subprocess.getoutput(
                f"security find-generic-password -a {auto_keychain} -w 2>/dev/null"
            )
            if self._is_sudo_password(_password):
                self.__password = _password
            else:  # Fallback. Reading environment variables.
                _password = os.environ.get("MACUITEST_PASSWORD")
                if _password is not None and self._is_sudo_password(_password):
                    self.__password = _password
                else:
                    raise SystemExit(
                        f"\nCANNOT USE SPECIFIED ADMIN PASSWORD:\n"
                        f"a) Add your actual password to environment variables\n"
                        f"b) Create a login keychain item with account name "
                        f'"{auto_keychain}" in Keychain Access.app\n'
                        f"https://support.apple.com/en-gb/guide/keychain-access/kyca1120/mac\n"
                    )
        return self.__password

    @staticmethod
    def _is_sudo_password(password: str) -> bool:
        validation = subprocess.run(
            ["sudo", "-S", "-p", "", "-v", "--"],
            input=f"{password}\n",
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return validation.returncode == 0

    def __execute(
        self, cmd: str, timeout: Optional[int] = None, stdin: Optional[str] = None
    ) -> Union[subprocess.CompletedProcess, int]:
        """Run `cmd` in a shell, writing `stdin` to its standard input when given."""
        try:
            response = subprocess.run(
                cmd,
                shell=True,
                input=stdin.encode() if stdin is not None else None,
                stderr=self.pipe,
                stdout=self.pipe,
                timeout=timeout,
            )
            if response.returncode:
                warning_message = (
                    f'Command "{cmd}" failed with exit code {response.returncode}\n\t'
                    f'{response.stderr.decode(encoding="utf-8").strip()}'
                )
                logging.debug(warning_message)
            return response
        except subprocess.TimeoutExpired as e:
            logging.error(e)
            return self.execution_timeout_code
