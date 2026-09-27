from pathlib import Path

# Here, not in settings, so reading it never loads the config file.
DEFAULT_FILE = Path(__file__).with_name("default.toml")
