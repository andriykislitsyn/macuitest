import glob
import os
from typing import List, Tuple

from macuitest.config.config_parser import config
from macuitest.lib.operating_system.env import env


class CrashReporter:

    def __init__(self, executor):
        self.executor = executor

    def publish_reports(self, logger, crash_reports, delete_reports: bool = True):
        for report in crash_reports:
            self.__publish_crash_report(logger, report, delete_on_send=delete_reports)

    def __publish_crash_report(self, logger, report: str, delete_on_send: bool):
        name = os.path.basename(report)
        self.executor.sudo(f'chmod 755 "{report}"')
        with open(report, 'r') as rep:
            logger.error(name, extra=dict(
                attachment={
                    "name": name,
                    "data": rep.read(),
                    "mime": "application/octet-stream",
                }))
        self.executor.execute(f'cp "{report}" "{config.artifacts.as_posix()}"')
        if delete_on_send:
            self.executor.sudo(f'rm "{report}"')

    @staticmethod
    def collect_reports(search_patterns: Tuple[str, ...]) -> List[str]:
        """Collect crash reports grouped by a glob search pattern."""
        crash_reports = []
        for directory in (env.user_diag_reports, env.system_diag_reports):
            for search_pattern in search_patterns:
                for report in glob.glob(f'{directory}/{search_pattern}'):
                    crash_reports.append(report)
        return crash_reports
