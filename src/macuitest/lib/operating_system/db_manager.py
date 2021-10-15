import logging
import sqlite3
from typing import Optional


class SQLite3DataBaseManager:
    """SQLite database manager."""

    def __init__(self, db_location: str):
        self.db = db_location
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.connect(self.db)

    def connect(self, database) -> None:
        try:
            self.connection = sqlite3.connect(database)
            self.cursor = self.connection.cursor()
        except sqlite3.OperationalError:
            logging.warning(f"Could not connect to TCC database: {self.db}")

    def disconnect(self) -> None:
        try:
            self.cursor.close()
            self.connection.close()
        except (AttributeError, sqlite3.ProgrammingError):
            logging.warning(f"Could not disconnect from TCC database: {self.db}")


class DataBaseManager:
    """Database manager factory."""

    def __new__(cls, db_location: str, db_type: str = "sqlite3"):
        databases = {
            "sqlite3": SQLite3DataBaseManager,
        }
        database = databases.get(db_type)
        if not database:
            raise LookupError(f'Database: "{db_type}" is not found')
        return database(db_location)
