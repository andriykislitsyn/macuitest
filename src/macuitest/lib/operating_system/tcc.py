from typing import ClassVar
from typing import Dict

from macuitest.lib.operating_system.db_manager import DataBaseManager
from macuitest.lib.operating_system.env import env


class TCCManager:
    """
    TCCManager manages the privacy database, which stores decisions
    the user has made about whether apps may access personal data.
    """

    sys_db: ClassVar[str] = f"{env.system_app_support}/com.apple.TCC/TCC.db"
    usr_db: ClassVar[str] = f"{env.home}{sys_db}"
    services: ClassVar[Dict[str, str]] = {
        "full_disk_access": "kTCCServiceSystemPolicyAllFiles",
        "camera_access": "kTCCServiceCamera",
        "documents_folder_access": "kTCCServiceSystemPolicyDocumentsFolder",
        "desktop_folder_access": "kTCCServiceSystemPolicyDesktopFolder",
        "downloads_folder_access": "kTCCServiceSystemPolicyDownloadsFolder",
    }

    def __init__(self, domain: str = "system"):
        self.db: str = self.sys_db if domain == "system" else self.usr_db
        self.db_manager = DataBaseManager(self.db)

    def list_access_policies(self, client: str) -> Dict[str, int]:
        is_allowed = "allowed" if env.version < (11, 0) else "auth_value"
        query = f'SELECT service, {is_allowed} FROM access WHERE client is "{client}"'
        return dict(self.db_manager.cursor.execute(query).fetchall())

    def revoke_access_to_service(self, service: str, client: str) -> None:
        query = f'DELETE FROM access WHERE service is "{service}" AND client is "{client}"'
        self.db_manager.cursor.execute(query)
        self.db_manager.connection.commit()
