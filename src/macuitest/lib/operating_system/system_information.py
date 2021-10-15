from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


class SystemInformation:
    def __init__(self, executor):
        self.executor = executor
        self.__version: Optional[Tuple[int, ...]] = None
        self.__sphardwaredatatype: Optional[Dict[str, str]] = None

    @property
    def uptime(self) -> int:
        timestamp = self.executor.get_output("date +%s")
        boot_time = self.executor.get_output(
            "sysctl -n kern.boottime | awk '{print $4}' | sed 's/,//g'"
        )
        return int(timestamp) - int(boot_time)

    @property
    def iousb_devices(self) -> List[str]:
        command: str = "ioreg -p IOUSB -w0 | sed 's/[^o]*o //; s/@.*$//' |grep -v '^Root.*'"
        return self.executor.get_output(command).splitlines()

    @property
    def serial(self) -> str:
        return self._sphardwaredatatype.get("Serial Number")

    @property
    def computer_name(self) -> str:
        return self.executor.get_output("scutil --get ComputerName")

    @property
    def model_name(self) -> str:
        return self._sphardwaredatatype.get("Model Name")

    @property
    def hw_uuid(self) -> str:
        return self._sphardwaredatatype.get("Hardware UUID")

    @property
    def mac_model(self) -> str:
        return self._sphardwaredatatype.get("Model Identifier")

    @property
    def uuid(self) -> str:
        return self.executor.get_output("dsmemberutil getuuid -U ${USER}")

    @property
    def _sphardwaredatatype(self) -> Dict[str, str]:
        """'Serial Number', 'Model Identifier', 'Boot ROM Version', 'L3 Cache', 'Processor Name',
        'Total Number of Cores', 'Number of Processors', 'Hardware UUID', 'SMC Version',
        'Model Name', 'Memory', 'L2 Cache (per Core)', 'Processor Speed'."""
        if self.__sphardwaredatatype is None:
            output = self.executor.get_output("system_profiler SPHardwareDataType")
            items = (line.strip() for line in output[output.find("Model Name") :].splitlines())
            _sphardwaredatatype = dict(
                self.__process_sphardwaredatatype_item(item) for item in items
            )
            self.__sphardwaredatatype = _sphardwaredatatype
        return self.__sphardwaredatatype

    @staticmethod
    def __process_sphardwaredatatype_item(item) -> Tuple[str, str]:
        return tuple(item.replace(" (system)", "").split(": ")[:2])
