from time import sleep

import Quartz

from macuitest.config import config
from macuitest.lib.applescript_lib import as_wrapper
from macuitest.lib.operating_system.env import env


class LoginWindow:
    def __init__(self, executor):
        self.executor = executor

    @staticmethod
    def lock_screen():
        if env.version_major > (10, 12):
            as_wrapper.send_keystroke('q', 'command', 'control')
        else:
            raise NotImplemented

    def unlock_screen(self, password=config.password):
        if not self.is_screen_locked:
            return
        self.wake_up()
        as_wrapper.send_keystroke('a', 'command')
        sleep(0.2)
        as_wrapper.send_keycode(as_wrapper.key_codes['delete'])
        sleep(0.2)
        as_wrapper.typewrite(password)
        sleep(0.5)
        self._confirm_login()

    def wake_up(self):
        self.executor.execute('caffeinate -u -t 2')
        for _ in range(3):
            as_wrapper.send_keycode(as_wrapper.key_codes['left'])
            sleep(0.3)
        sleep(1)

    @staticmethod
    def _confirm_login():
        as_wrapper.send_keycode(as_wrapper.key_codes['return'])
        sleep(1)

    @property
    def is_screen_locked(self):
        return dict(Quartz.CGSessionCopyCurrentDictionary()).get('CGSSessionScreenIsLocked') is not None
