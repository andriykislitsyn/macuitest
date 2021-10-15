import json
import re
import time
from typing import ClassVar
from typing import Tuple
from urllib import error
from urllib import request


class Networking:
    ports_list: ClassVar[Tuple[str, ...]] = ("en0", "en1")  # Ethernet port and Wifi port.

    def __init__(self, executor):
        self.executor = executor

    def send_curl_request(self, request_):
        self.executor.execute(f"curl {request_}")

    @property
    def mac_address(self) -> str:
        _device = self.active_internet_device
        _mac_address_raw = self.executor.get_output(f"networksetup -getmacaddress {_device}")
        return (
            _mac_address_raw.replace("Ethernet Address: ", "")
            .replace(f" (Device: {_device})", "")
            .strip()
        )

    @property
    def active_internet_device(self) -> str:
        for device in self.network_service_order:
            _status = self.executor.get_output(f"ifconfig {device} |grep status").split(": ")[-1]
            if _status == "active":
                return device

    @property
    def network_service_order(self):
        _network_service_order = self.executor.get_output("networksetup listnetworkserviceorder")
        _devices = re.findall(r"Device: \w+-\w+|Device: \w+", _network_service_order)
        _devices = [d.split(": ")[-1] for d in _devices if "en" in d]
        return _devices

    def turn_internet_on(self):
        """Wait until the Internet connection is established."""
        for port in self.ports_list:
            self.executor.sudo(f"ifconfig {port} up")
        delta_time = time.time() + 30
        while time.time() < delta_time:
            try:
                resp = request.urlopen("https://apple.com")
                if resp.code != 404:
                    return
            except error.URLError:
                time.sleep(0.5)

    def turn_internet_off(self):
        for port in self.ports_list:
            self.executor.sudo(f"ifconfig {port} down")

    @property
    def ip_info(self) -> dict:
        """Get external ip information from: ipinfo.io
        :return dict: {'ip': ..., 'hostname': ..., 'city': ..., 'region': ..., 'country': ...}
        """
        for _ in range(5):
            try:
                return json.load(request.urlopen("https://ipinfo.io/json"))
            except error.URLError:
                continue
        return dict()
