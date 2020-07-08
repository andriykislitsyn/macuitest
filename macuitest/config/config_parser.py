import os
import pathlib


class Config:
    """Automation Framework Configuration Object."""

    def __init__(self):
        self.project_root: pathlib.Path = pathlib.Path(__file__).parent.parent
        self.artifacts: pathlib.Path = self.project_root.joinpath('artifacts')
        self.password: str = os.environ.get('MACUITEST_PASSWORD')


config = Config()
