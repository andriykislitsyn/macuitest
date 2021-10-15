import time
from typing import ClassVar
from typing import Tuple

from macuitest.config.constants import DNSMapping


class Hosts:
    hosts_file: ClassVar[str] = "/etc/hosts"

    def __init__(self, executor, file_manager):
        self.executor = executor
        self.file_manager = file_manager

    def change_mapping(self, mapping: DNSMapping):
        """Configure local domain resolution for a certain resource."""
        self.file_manager.change_file_permissions(
            path=self.hosts_file, permissions="777", sudo=True
        )
        with open(self.hosts_file) as hosts:
            hosts_config = hosts.read().rstrip().splitlines()
        hosts_config.append(mapping)
        updated = "\n".join(hosts_config)
        with open(self.hosts_file, "w") as hosts:
            hosts.write(f"{updated}\n")
        self.file_manager.change_file_permissions(
            path=self.hosts_file, permissions="755", sudo=True
        )

    def reset(self, known_mappings: Tuple[DNSMapping, ...], disable_pause: bool = False):
        """Reset /etc/hosts by removing certain/all known mappings."""
        self.file_manager.change_file_permissions(
            path=self.hosts_file, permissions="777", sudo=True
        )
        with open(self.hosts_file, "r") as hosts:
            hosts_config = hosts.read().rstrip().splitlines()
        updated = "\n".join((line for line in hosts_config if line not in known_mappings))
        with open(self.hosts_file, "w") as hosts:
            hosts.write(f"{updated}\n")
        self.file_manager.change_file_permissions(
            path=self.hosts_file, permissions="755", sudo=True
        )
        self.flush_dns_cache(disable_pause=disable_pause)

    def flush_dns_cache(self, disable_pause: bool = False):
        """Flush DNS cache to remove stored website location details."""
        time.sleep(0 if disable_pause else 2)
        self.executor.execute("dscacheutil -flushcache")
        time.sleep(0 if disable_pause else 1)
        self.executor.sudo("killall -HUP mDNSResponder")
        time.sleep(0 if disable_pause else 5)  # For macOS to catch up.
