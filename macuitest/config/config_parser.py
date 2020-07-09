import os
import pathlib
import subprocess


class Config:
    def __init__(self):
        self.__password = None
        self.project_root: pathlib.Path = pathlib.Path(__file__).parent.parent
        self.artifacts: pathlib.Path = self.project_root.joinpath('artifacts')
        self.password: str = self.__get_admin_password()

    def __get_admin_password(self, auto_keychain: str = 'com.macuitest.automation'):
        if self.__password is None:
            subprocess.call('sudo -k', shell=True)
            _password = subprocess.getoutput(f'security find-generic-password -a {auto_keychain} -w 2>/dev/null')
            if subprocess.call(f'echo "{_password}" |sudo -S -p "" -v --', shell=True, stderr=-3) == 0:
                self.__password = _password
            else:  # Fallback. Reading environment variables.
                _password = os.environ.get('MACUITEST_PASSWORD')
                if subprocess.call(f'echo "{_password}" |sudo -S -p "" -v --', shell=True, stderr=-3) == 0:
                    self.__password = _password
                else:
                    raise SystemExit(
                        f'\nCANNOT USE SPECIFIED ADMIN PASSWORD:\n'
                        f'a) Add your actual password to environment variables\n'
                        f'b) Create a login keychain item with account name "{auto_keychain}" in Keychain Access.app\n'
                        f'https://support.apple.com/en-gb/guide/keychain-access/kyca1120/mac\n'
                    )
        return self.__password


config = Config()
