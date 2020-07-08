import logging
import subprocess
from typing import Optional, Union

from macuitest.config.config_parser import config


class ShellExecutor:
    execution_timeout_code: int = -1001
    pipe: int = -1
    stdout: int = -2
    devnull: int = -3

    def sudo_get_output(self, cmd: str, timeout: Optional[int] = None) -> Optional[str]:
        """Execute shell instruction with elevated privileges and return execution output."""
        response = self.__execute(cmd=f'echo "{config.password}" | sudo -S -p "" {cmd}', timeout=timeout)
        if isinstance(response, subprocess.CompletedProcess):
            return response.stdout.decode(encoding='utf-8').strip()

    def get_output(self, cmd: str, timeout: Optional[int] = None) -> Optional[str]:
        """Execute shell instruction and return execution output."""
        response = self.__execute(cmd=cmd, timeout=timeout)
        if isinstance(response, subprocess.CompletedProcess):
            return response.stdout.decode(encoding='utf-8').strip()

    def sudo(self, cmd: str, timeout: Optional[int] = None) -> Union[subprocess.CompletedProcess, int]:
        """Execute shell instruction with elevated privileges and return execution code."""
        return self.__execute(cmd=f'echo "{config.password}" | sudo -S -p "" {cmd}', timeout=timeout)

    def execute(self, cmd: str, timeout: Optional[int] = None) -> Union[subprocess.CompletedProcess, int]:
        """Execute a shell instruction and return a `CompletedProcess` object."""
        return self.__execute(cmd=cmd, timeout=timeout)

    def __execute(self, cmd: str, timeout: Optional[int] = None) -> Union[subprocess.CompletedProcess, int]:
        """Send instruction to shell."""
        try:
            response = subprocess.run(cmd, shell=True, stderr=self.pipe, stdout=self.pipe, timeout=timeout)
            if response.returncode:
                warning_message = f'Command "{cmd}" failed with exit code {response.returncode}\n\t' \
                                  f'{response.stderr.decode(encoding="utf-8").strip()}'
                logging.debug(warning_message)
            return response
        except subprocess.TimeoutExpired as e:
            logging.error(e)
            return self.execution_timeout_code
