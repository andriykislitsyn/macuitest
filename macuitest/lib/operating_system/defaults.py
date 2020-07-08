import time
from typing import Union, Tuple, ClassVar

from macuitest.lib.operating_system.env import env


class Defaults:
    preferences_daemon: ClassVar[str] = 'cfprefsd'

    def __init__(self, executor, service_manager):
        self.executor = executor
        self.service_manager = service_manager

    def clear_application_preferences(self, bundle_ids: Tuple[str, ...]):
        """Clear application preferences.
            :param bundle_ids: Tuple of target bundle ids."""
        for bundle_id in bundle_ids:
            self.remove_property_list_by_id(bundle_id, flush_pref_cache=False)
            self.executor.execute(f'rm -f {env.user_preferences}/{bundle_id}*')

    def remove_property_list_by_id(self, bundle_id, flush_pref_cache=True):
        self.executor.execute(f'defaults delete {bundle_id}')
        if flush_pref_cache:
            self.flush_preferences_cache()

    def read(self, domain: str, property_: str = 'MKIntroWasShown') -> str:
        return self.executor.get_output(f'defaults read {domain} {property_}')

    def delete_defaults(self, domain: str, property_: str = 'MKIntroWasShown'):
        self.executor.execute(f'defaults delete {domain} {property_}')
        time.sleep(2)

    def set_defaults(self, domain: str, property_: str = 'MKIntroWasShown 1', pause: int = 2):
        self.executor.execute(f'defaults write {domain} {property_}')
        time.sleep(pause)

    def flush_preferences_cache(self, pause: Union[int, float] = 3):
        time.sleep(pause)
        self.service_manager.kill_process(self.preferences_daemon)
        time.sleep(pause)
