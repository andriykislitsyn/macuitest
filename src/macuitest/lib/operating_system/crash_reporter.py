import glob
import os
from typing import List
from typing import Tuple

from macuitest.lib.operating_system.env import env


class CrashReporter:
    def __init__(self, executor):
        self.executor = executor

    def publish_reports(self, logger, crash_reports: List[str]):
        for report in crash_reports:
            self.__publish_crash_report(logger, report)

    def __publish_crash_report(self, logger, report: str):
        name = os.path.basename(report)
        self.executor.sudo(f'chmod 755 "{report}"')
        with open(report) as rep:
            logger.error(
                name,
                extra=dict(
                    attachment={
                        "name": name,
                        "data": rep.read(),
                        "mime": "application/octet-stream",
                    }
                ),
            )

    def archive_crash_reports(self, search_patterns: Tuple[str], where: str):
        for report in self.collect_reports(search_patterns):
            self.executor.execute(f'cp "{report}" "{where}"')
            self.executor.sudo(f'rm "{report}"')

    @staticmethod
    def collect_reports(search_patterns: Tuple[str, ...]) -> List[str]:
        """Collect crash reports grouped by a glob search pattern."""
        crash_reports = []
        for directory in (env.user_diag_reports, env.system_diag_reports):
            for search_pattern in search_patterns:
                for report in glob.glob(f"{directory}/{search_pattern}"):
                    crash_reports.append(report)
        return crash_reports
