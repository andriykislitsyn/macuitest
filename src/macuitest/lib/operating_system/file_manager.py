import datetime
import hashlib
import math
import os
import shutil
import zipfile
from pathlib import Path
from pwd import getpwuid
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


class FileManager:
    permissions = {
        "all": 0o777,
        "default": 0o755,
        "read_only": 0o444,
        "write_only": 0o222,
        "no_access": 0o000,
    }

    def __init__(self, executor):
        self.executor = executor

    def clear_quarantine_attribute(self, path: str):
        self.executor.sudo(f'xattr -r -d com.apple.quarantine "{path}"')

    def read_metadata(self, path: str, key: Optional[str] = None):
        if key is None:
            return self.executor.get_output(f'mdls "{path}"')
        return self.executor.get_output(f'mdls -raw -name {key} "{path}"')

    def touch(self, path):
        """
        Sets the modification and access times of files.
        If any file does not exist, it is created with default permissions.
        """
        self.executor.execute(f'touch "{path}"')

    def dump_text_to_file(self, text: str, file_: str):
        command = f'printf "{text}" > "{file_}"'
        if self.executor.execute(command).returncode != 0:
            self.executor.sudo(command)

    def make_file(self, path: str, size: str = "8m", sudo: bool = False):
        """Create a file with size `size`[b|k|m|g] in `path`."""
        execute = self.executor.sudo if sudo else self.executor.execute
        return execute(f'mkfile {size} "{path}"')

    def make_dir(self, path: str, sudo: bool = False):
        execute = self.executor.sudo if sudo else self.executor.execute
        return execute(f'mkdir -p "{path}"')

    def last_modified__timedelta(self, path: str):
        timedelta = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            self.last_modified(path)
        )
        return int(timedelta.total_seconds())

    @staticmethod
    def last_modified(path: str):
        return os.path.getmtime(path)

    @staticmethod
    def is_path_exists(path: str) -> bool:
        return os.path.exists(path)

    @staticmethod
    def is_dir(path: str) -> bool:
        return os.path.isdir(path)

    @staticmethod
    def is_file(path: str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def read_file(source: str) -> str:
        with open(source, "r", encoding="ISO-8859-1") as f:
            return f.read()

    @staticmethod
    def write_to_file(source: str, data: str) -> None:
        with open(source, "w") as f:
            f.write(data)

    def move_tree(self, source, destination):
        """Move `source` file to `destination`."""
        self.copy_tree(source, destination)
        self.remove_tree(source)

    def remove_content_from(self, content, directory) -> None:
        """Remove `content` from `directory`"""
        if not content:
            return
        for item in content:
            self.remove_tree(os.path.join(directory, item))

    @staticmethod
    def rename_file(default_file_path, updated_file_path):
        return os.rename(default_file_path, updated_file_path)

    def clear_directory(
        self, directory: str, pattern: str = "*", sudo: bool = False
    ):  # Clear all files, by default.
        return (self.executor.sudo if sudo else self.executor.execute)(
            f"rm -rf {directory}/{pattern}"
        )

    def remove_tree(self, tree_path):
        """Delete a directory tree or a file."""
        if not os.path.exists(tree_path):
            return
        try:
            (shutil.rmtree if os.path.isdir(tree_path) else os.unlink)(tree_path)
        except (OSError, PermissionError):
            self.executor.sudo(f'rm -r "{tree_path}"')

    def copy_file(self, source: str, destination: str):
        self.executor.execute(f'cp "{source}" "{destination}"')

    def move_file(self, source: str, destination: str):
        self.executor.execute(f'mv "{source}" "{destination}"')

    def copy_tree(self, source: str, destination: str):
        """Copy a directory tree or folder's content to the destination."""
        self.makedir(destination)
        execute = (
            self.executor.sudo
            if self.__are_elevated_rights_needed(destination)
            else self.executor.execute
        )
        execute(f'rsync -q -ahP "{source}" "{destination}"')

    def __are_elevated_rights_needed(self, destination: Union[Path, str]):
        result = False
        protected_folders = ("dev", "var", "usr", "private", "Library", "System")
        _destination_ = str(destination)
        if (
            self.get_file_owner(_destination_) == "root"
            or _destination_.split("/")[1] in protected_folders
        ):
            result = True
        return result

    def get_size(self, file_path) -> int:
        """Total size, in KB"""
        if Path(file_path).exists():
            return int(self.executor.get_output(f'du -hk "{file_path}"').split()[0].strip())
        raise FileNotFoundError(file_path)

    def folder_newest_file(self, folder: str) -> str:
        if Path(folder).is_dir():
            return max(self.folder_content(folder), key=os.path.getctime)
        raise NotADirectoryError(folder)

    @staticmethod
    def folder_content(folder: str) -> List[str]:
        if Path(folder).is_dir():
            return [
                path_.as_posix()
                for path_ in Path(folder).glob("*")
                if not path_.name.startswith(".")
            ]
        raise NotADirectoryError(folder)

    def get_bundle_content_owners(self, path: str) -> List[Tuple[str, str, str]]:
        raw = (line for line in self.executor.get_output(f'ls -R -l "{path}"').splitlines())
        payload = (
            line.split()
            for line in raw
            if line and not (line.startswith("total") or line.startswith("/"))
        )
        return [(line[-1], line[2], line[3]) for line in payload]

    @staticmethod
    def get_file_owner(file_path):
        try:
            return getpwuid(os.stat(file_path).st_uid).pw_name
        except OSError as e:
            if e.errno == 2:
                return "missing"
            else:
                raise

    @staticmethod
    def unzip_file(src, dst):
        with zipfile.ZipFile(src) as z:
            z.extractall(dst)

    def unzip_app(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)
        self.executor.execute(f'unzip -qq -o "{src}" -d "{dst}"')

    @staticmethod
    def zip_file(src, dst):
        relroot = os.path.abspath(os.path.join(src, os.pardir))
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zip_:
            for root, dirs, files in os.walk(src):
                zip_.write(root, os.path.relpath(root, relroot))
                for file_ in files:
                    filename = os.path.join(root, file_)
                    if os.path.isfile(filename):
                        arcname = os.path.join(os.path.relpath(root, relroot), file_)
                        zip_.write(filename, arcname)

    def makedir(self, destination):
        if not os.path.exists(destination):
            if self.executor.execute(f'mkdir -p "{destination}"').returncode != 0:
                self.executor.sudo(f'mkdir -p "{destination}"')

    def lock_file(self, path: str):
        if isinstance(path, Path):
            path = path.as_posix()
        return self.executor.sudo(f'chflags uchg "{path}"')

    def change_file_owner(self, file: str, owner: str):
        return self.executor.sudo(f'chown {owner} "{file}"')

    def change_file_permissions(self, path: str, permissions, sudo: bool = False):
        """Change file permissions."""
        (self.executor.sudo if sudo else self.executor.execute)(f'chmod {permissions} "{path}"')

    @staticmethod
    def change_files_permissions(folder, permissions):
        """Change file permissions in `folder`."""
        for root, subfolders, files in os.walk(folder):
            [os.chmod(os.path.join(root, file_), permissions) for file_ in files]

    @staticmethod
    def convert_file_size_to_human_readable(size):
        if size == "":
            result = 0
        else:
            size = float(size)
            if size == 0:
                return "0B"
            size_name = ("bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(size, 1000)))
            p = math.pow(1000, i)
            s = round(size / p, 2)
            result = "{} {}".format(s, size_name[i])
        return result

    @staticmethod
    def convert_file_size_to_bytes(string):
        _size, _unit = string.strip().lower().replace("zero", "0").replace(",", "").split()
        return int(float(_size) * 1000 ** ("bytes", "kb", "mb", "gb", "tb").index(_unit))

    def find_duplicates_number(self, folders):
        """Return duplicates in format {filename:number of duplicates}"""
        if isinstance(folders, str):
            folders = [
                folders,
            ]
        hashes: dict = dict()
        duplicates: dict = dict()
        for folder in folders:
            for dirpath, dirnames, files_list in os.walk(folder):
                for filename in files_list:
                    if not filename.startswith("."):
                        full_path = os.path.join(dirpath, filename)
                        if not os.path.islink(full_path) and os.path.exists(full_path):
                            file_id = self._generate_md5_checksum(full_path)
                            duplicate = hashes.get(file_id)
                            if duplicate:
                                counter = duplicates.get(filename, 1)
                                duplicates[filename] = counter + 1
                                hashes[file_id].append(full_path)
                            else:
                                hashes[file_id] = [full_path]
        return duplicates

    @staticmethod
    def _generate_md5_checksum(file_name, chunk_size=1024):
        """Calculate md5 checksum of `file_name`."""
        hash_ = hashlib.md5()
        with open(file_name, "rb") as f:
            chunk = f.read(chunk_size)
            while chunk:
                hash_.update(chunk)
                chunk = f.read(chunk_size)
        return hash_.hexdigest()
