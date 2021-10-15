import threading
from typing import Dict
from typing import List
from typing import Optional

import biplist

from macuitest.lib import core


class MemoryManager:
    """Interface to memory (RAM) information and manipulations on it."""

    def __init__(self, executor):
        self._memory_slots: Optional[List[Dict[str, str]]] = None
        self.executor = executor

    def load_memory(self, percent_free: int, timeout: int = 15) -> None:
        """Simulate memory pressure on the system in background."""
        threading.Thread(
            target=self.executor.execute, args=(f"memory_pressure -p {percent_free}", timeout)
        ).start()

    @property
    def total_memory_bytes(self) -> int:
        return core.convert_file_size_to_bytes(self.total_memory_str)

    @property
    def total_memory_str(self) -> str:
        return f"{self.total_memory} GB"

    @property
    def total_memory(self) -> int:
        return sum((int(bank.get("dimm_size").split()[0]) for bank in self.memory_slots))

    @property
    def memory_banks(self) -> int:
        return len(self.memory_slots)

    @property
    def memory_speed(self) -> str:
        return self.memory_slots[0].get("dimm_speed")

    @property
    def memory_type(self) -> str:
        return self.memory_slots[0].get("dimm_type")

    @property
    def memory_slots(self) -> List[Dict[str, str]]:
        if self._memory_slots is not None:
            return self._memory_slots
        _info = bytes(
            self.executor.get_output("system_profiler -xml SPMemoryDataType"), encoding="utf-8"
        )
        _slots = biplist.readPlistFromString(_info)[0].get("_items")[0].get("_items")
        self._memory_slots = _slots
        return _slots
