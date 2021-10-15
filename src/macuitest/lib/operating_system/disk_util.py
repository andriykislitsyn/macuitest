import os
from typing import Optional


class DiskMountFailed(Exception):
    pass


class DiskUtil:
    def __init__(self, executor):
        self.executor = executor

    def mount_disk_image(self, disk_image: str, mountpoint: Optional[str] = None) -> None:
        """Mount `disk_image`."""
        if not os.path.exists(disk_image):
            raise FileNotFoundError(f"File: {disk_image} does not exist")
        cmd = (
            f"hdiutil mount {disk_image} -mountpoint {mountpoint}"
            if mountpoint
            else f"hdiutil mount {disk_image}"
        )
        if self.executor.execute(cmd).returncode != 0:
            raise DiskMountFailed(f"Disk mount failed: {disk_image}")

    def detach_disk_image(self, mountpoint: str) -> None:
        """Unmount attached disk image."""
        self.executor.execute(f'hdiutil detach "{mountpoint}" -force')
