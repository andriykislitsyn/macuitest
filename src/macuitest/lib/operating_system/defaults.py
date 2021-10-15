from typing import ClassVar
from typing import Optional
from typing import Tuple

from macuitest.lib.core import slow_down
from macuitest.lib.operating_system.env import env


class Defaults:
    preferences_daemon: ClassVar[str] = "cfprefsd"

    def __init__(self, executor, service_manager):
        self.executor = executor
        self.service_manager = service_manager

    def clear_application_preferences(self, bundle_ids: Tuple[str, ...]):
        """Clear application preferences.
        :param bundle_ids: Tuple of target bundle ids."""
        for bundle_id in bundle_ids:
            self.remove_property_list_by_id(bundle_id, flush_pref_cache=False)
            self.executor.execute(f"rm -f {env.user_preferences}/{bundle_id}*")

    def remove_property_list_by_id(self, bundle_id: str, flush_pref_cache: bool = True):
        self.delete_defaults(bundle_id)
        if flush_pref_cache:
            self.flush_preferences_cache()

    def read_defaults(
        self, domain: str = "NSGlobalDomain", key: Optional[str] = None
    ) -> Optional[str]:
        command: str = f"defaults read {domain} {key}" if key else f"defaults read {domain}"
        response = self.executor.execute(command)
        if response.returncode == 0:
            return response.stdout.decode(encoding="utf-8").strip()

    def delete_defaults(self, domain: str = "NSGlobalDomain", key: Optional[str] = None) -> int:
        command: str = f"defaults delete {domain} {key}" if key else f"defaults delete {domain}"
        return self.executor.execute(command.strip()).returncode

    @slow_down(seconds=0.5)
    def write_defaults(
        self, domain: str = "NSGlobalDomain", key: str = "KeyRepeat", value="0.02"
    ) -> int:
        return self.executor.execute(f"defaults write {domain} {key} {value}").returncode

    @slow_down(seconds=2)
    def flush_preferences_cache(self):
        self.service_manager.kill_process(self.preferences_daemon)
