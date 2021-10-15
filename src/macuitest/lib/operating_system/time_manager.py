import time
from datetime import datetime
from datetime import timedelta
from typing import ClassVar

from macuitest.lib.operating_system.shell_executor import ShellExecutor


class TimeManager:
    time_format: ClassVar[str] = "%Y.%m.%d-%H:%M:%S"

    def __init__(self, executor: ShellExecutor, ntp_server: str = "ua.pool.ntp.org"):
        self.ntp_server = ntp_server
        self.executor = executor

    def move_time(self, days: int = 0, hours: int = 0, minutes: int = 5, seconds: int = 0) -> None:
        self.disable_using_network_time()
        start_point: datetime = datetime.now()
        delta = (
            start_point + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds + 1)
        ).strftime(self.time_format)
        self.executor.sudo(f"date -f {self.time_format} {delta}")
        time.sleep(3)
        elapsed, target_time_shift = (
            datetime.now() - start_point
        ).seconds, hours * 3600 + minutes * 60 + seconds
        if elapsed <= target_time_shift:
            raise EnvironmentError(f"Elapsed: {elapsed}, target: {target_time_shift}")

    def reset_time(self, ntp_server: str = "time.apple.com"):
        """Enable using network time and get it
        by Simple Network Time Protocol from an NTP server."""
        if self.executor.sudo(f"sntp -sS {ntp_server}").returncode != 0:
            self.executor.sudo(f"sntp -s {ntp_server}")
        self.enable_using_network_time()

    @property
    def is_network_time_used(self) -> bool:
        result = (
            self.executor.sudo_get_output("systemsetup -getusingnetworktime")
            .split(":")[-1]
            .strip()
            .lower()
        )
        return {"on": True, "off": False}.get(result)

    def enable_using_network_time(self):
        self.executor.sudo("systemsetup -setusingnetworktime on")

    def disable_using_network_time(self):
        self.executor.sudo("systemsetup -setusingnetworktime off")
