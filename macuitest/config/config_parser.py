import configparser
import pathlib
from typing import Optional, Dict


class Config:
    """Automation Framework Configuration Object."""
    default_config: str = 'default_config.conf'
    local_config: str = '.local_config.conf'

    def __init__(self, config_filename: Optional[str] = None):
        self.home: pathlib.Path = pathlib.Path('~').expanduser()
        self.project_root: pathlib.Path = pathlib.Path(__file__).parent.parent
        self._cfile_default = config_filename or self.project_root.joinpath(f'config/{self.default_config}')
        self._cfile_local = self.project_root.joinpath(f'config/{self.local_config}')

        self.config, self.__config = configparser.ConfigParser(), configparser.ConfigParser()
        self.config.optionxform, self.__config.optionxform = str, str
        self.config.read(self._cfile_default), self.__config.read(self._cfile_local)
        self.__transfer_from_local()
        # Env
        self.config.set('env', 'home_dir', self.home.as_posix())
        self.artifacts: pathlib.Path = self.project_root.joinpath('artifacts')
        self.work_dir: str = self.get("env", "work_dir")
        self.install_dir: str = self.get("env", "install_dir")
        self.logs_dir: str = self.get("env", "logs_dir")
        self.crash_report_dir: str = self.get('env', 'crash_reports_dir')
        self.smoke_test_reports_dir: str = self.get('env', 'smoke_test_reports_dir')
        self.test_data_dir: str = self.get("env", "test_data_dir")
        self.test_data_applications_path: str = self.get("env", "test_data_applications_path")
        self.password: str = self.get("env", "password")

    def get(self, section: str, option: str) -> str:
        """Get option value for a given section."""
        return self.config.get(section, option)

    def __transfer_from_local(self):
        """Transfer data from local config to default config."""
        if pathlib.Path(self._cfile_local).exists():
            self.__config.set('local', 'home_dir', self.home.as_posix())
            to_append = {}
            for section in (section for section in self.__config.sections()):
                for k, v in self.__config.items(section=section):
                    to_append['env'] = {k: v}
                    self.__update_configparser_object(to_append)

    def __update_configparser_object(self, config_dict: Dict[str, Dict[str, str]]):
        """Update config object."""
        for section in config_dict.keys():
            for (key, val) in config_dict[section].items():
                self.config.set(section, key, val)


config = Config()
