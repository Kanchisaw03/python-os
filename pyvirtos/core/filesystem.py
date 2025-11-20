"""Virtual filesystem for PyVirtOS."""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FileType(Enum):
    """File type enumeration."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


@dataclass
class FileMetadata:
    """File metadata."""

    inode: int
    name: str
    path: str
    file_type: str
    owner_uid: int
    owner_gid: int
    permissions: int  # Unix-style permissions (e.g., 0o644)
    size: int
    created_at: float
    modified_at: float
    accessed_at: float
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class VirtualFilesystem:
    """Virtual filesystem implementation."""

    def __init__(self, vfs_root: Path):
        """Initialize virtual filesystem.

        Args:
            vfs_root: Root directory for VFS storage
        """
        self.vfs_root = vfs_root
        self.vfs_root.mkdir(parents=True, exist_ok=True)

        # Database for metadata
        self.db_path = self.vfs_root / "vfs_meta.sqlite"
        self.next_inode = 1

        self._init_database()
        self._init_root_directory()

    def _init_database(self) -> None:
        """Initialize metadata database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inodes (
                inode INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                owner_uid INTEGER NOT NULL,
                owner_gid INTEGER NOT NULL,
                permissions INTEGER NOT NULL,
                size INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                modified_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                content_hash TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS open_files (
                fd INTEGER PRIMARY KEY,
                inode INTEGER NOT NULL,
                mode TEXT NOT NULL,
                position INTEGER DEFAULT 0,
                FOREIGN KEY(inode) REFERENCES inodes(inode)
            )
        """
        )

        conn.commit()
        conn.close()

    def _init_root_directory(self) -> None:
        """Initialize root directory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", ("/",))
        if cursor.fetchone() is None:
            now = datetime.now().timestamp()
            cursor.execute(
                """
                INSERT INTO inodes
                (inode, name, path, file_type, owner_uid, owner_gid, permissions,
                 size, created_at, modified_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (1, "", "/", "directory", 0, 0, 0o755, 0, now, now, now),
            )

        conn.commit()
        conn.close()

    def _get_next_inode(self) -> int:
        """Get next available inode number."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(inode) FROM inodes")
        max_inode = cursor.fetchone()[0]
        conn.close()
        return (max_inode or 0) + 1

    def _check_permissions(
        self, inode: int, uid: int, gid: int, required_perm: str
    ) -> bool:
        """Check if user has permission for file operation.

        Args:
            inode: File inode
            uid: User ID
            gid: Group ID
            required_perm: Required permission ('r', 'w', 'x')

        Returns:
            True if user has permission
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT owner_uid, owner_gid, permissions FROM inodes WHERE inode = ?",
            (inode,),
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False

        owner_uid, owner_gid, perms = result

        # Root always has access
        if uid == 0:
            return True

        # Map permission character to bit position
        perm_map = {"r": 2, "w": 1, "x": 0}
        perm_bit = perm_map.get(required_perm, -1)

        if perm_bit == -1:
            return False

        # Check owner permissions
        if uid == owner_uid:
            return bool((perms >> (6 + perm_bit)) & 1)

        # Check group permissions
        if gid == owner_gid:
            return bool((perms >> (3 + perm_bit)) & 1)

        # Check other permissions
        return bool((perms >> perm_bit) & 1)

    def mkdir(
        self, path: str, uid: int, gid: int, permissions: int = 0o755
    ) -> bool:
        """Create a directory.

        Args:
            path: Directory path
            uid: Owner user ID
            gid: Owner group ID
            permissions: Directory permissions

        Returns:
            True if successful
        """
        path = path.rstrip("/")
        if not path:
            path = "/"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if already exists
        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        if cursor.fetchone():
            conn.close()
            return False

        # Check parent directory exists and has write permission
        parent_path = str(Path(path).parent).replace("\\", "/")
        if parent_path == ".":
            parent_path = "/"

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (parent_path,))
        parent = cursor.fetchone()
        if not parent:
            conn.close()
            return False

        parent_inode = parent[0]
        # Root (uid=0) can always create directories
        if uid != 0 and not self._check_permissions(parent_inode, uid, gid, "w"):
            conn.close()
            return False

        # Create directory
        now = datetime.now().timestamp()
        inode = self._get_next_inode()

        try:
            cursor.execute(
                """
                INSERT INTO inodes
                (inode, name, path, file_type, owner_uid, owner_gid, permissions,
                 size, created_at, modified_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    inode,
                    Path(path).name,
                    path,
                    "directory",
                    uid,
                    gid,
                    permissions,
                    0,
                    now,
                    now,
                    now,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError as e:
            conn.close()
            import logging
            logging.error(f"mkdir failed for {path}: {e}")
            return False

    def touch(self, path: str, uid: int, gid: int, permissions: int = 0o644) -> bool:
        """Create an empty file.

        Args:
            path: File path
            uid: Owner user ID
            gid: Owner group ID
            permissions: File permissions

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if already exists
        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        if cursor.fetchone():
            conn.close()
            return False

        # Check parent directory
        parent_path = str(Path(path).parent).replace("\\", "/")
        if parent_path == ".":
            parent_path = "/"

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (parent_path,))
        parent = cursor.fetchone()
        if not parent:
            conn.close()
            return False

        parent_inode = parent[0]
        # Root (uid=0) can always create files
        if uid != 0 and not self._check_permissions(parent_inode, uid, gid, "w"):
            conn.close()
            return False

        # Create file
        now = datetime.now().timestamp()
        inode = self._get_next_inode()

        try:
            cursor.execute(
                """
                INSERT INTO inodes
                (inode, name, path, file_type, owner_uid, owner_gid, permissions,
                 size, created_at, modified_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    inode,
                    Path(path).name,
                    path,
                    "file",
                    uid,
                    gid,
                    permissions,
                    0,
                    now,
                    now,
                    now,
                ),
            )

            # Create empty file in storage
            file_path = self.vfs_root / f"file_{inode}"
            file_path.touch()

            conn.commit()
            conn.close()
            return True
        except (sqlite3.IntegrityError, OSError):
            conn.close()
            return False

    def write(self, path: str, data: bytes, uid: int, gid: int) -> bool:
        """Write data to a file.

        Args:
            path: File path
            data: Data to write
            uid: User ID
            gid: Group ID

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        inode = result[0]

        if not self._check_permissions(inode, uid, gid, "w"):
            conn.close()
            return False

        try:
            file_path = self.vfs_root / f"file_{inode}"
            file_path.write_bytes(data)

            now = datetime.now().timestamp()
            cursor.execute(
                "UPDATE inodes SET size = ?, modified_at = ? WHERE inode = ?",
                (len(data), now, inode),
            )
            conn.commit()
            conn.close()
            return True
        except OSError:
            conn.close()
            return False

    def read(self, path: str, uid: int, gid: int) -> Optional[bytes]:
        """Read data from a file.

        Args:
            path: File path
            uid: User ID
            gid: Group ID

        Returns:
            File data or None if error
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None

        inode = result[0]

        if not self._check_permissions(inode, uid, gid, "r"):
            conn.close()
            return None

        try:
            file_path = self.vfs_root / f"file_{inode}"
            data = file_path.read_bytes()

            now = datetime.now().timestamp()
            cursor.execute(
                "UPDATE inodes SET accessed_at = ? WHERE inode = ?", (now, inode)
            )
            conn.commit()
            conn.close()
            return data
        except OSError:
            conn.close()
            return None

    def listdir(self, path: str, uid: int, gid: int) -> Optional[List[str]]:
        """List directory contents.

        Args:
            path: Directory path
            uid: User ID
            gid: Group ID

        Returns:
            List of filenames or None if error
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None

        inode = result[0]

        if not self._check_permissions(inode, uid, gid, "r"):
            conn.close()
            return None

        # Get all files with this path as parent
        if path == "/":
            prefix = "/"
        else:
            prefix = path.rstrip("/") + "/"

        cursor.execute(
            "SELECT name FROM inodes WHERE path LIKE ? AND path != ?",
            (prefix + "%", path),
        )
        results = cursor.fetchall()
        conn.close()

        # Filter to direct children only
        children = set()
        for (name,) in results:
            # Get the relative path
            rel_path = name
            if "/" in rel_path:
                rel_path = rel_path.split("/")[0]
            children.add(rel_path)

        return sorted(list(children))

    def stat(self, path: str, uid: int, gid: int) -> Optional[Dict]:
        """Get file statistics.

        Args:
            path: File path
            uid: User ID
            gid: Group ID

        Returns:
            File metadata dictionary or None if error
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT inode, name, file_type, owner_uid, owner_gid, permissions,
                   size, created_at, modified_at, accessed_at
            FROM inodes WHERE path = ?
        """,
            (path,),
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        (
            inode,
            name,
            file_type,
            owner_uid,
            owner_gid,
            permissions,
            size,
            created_at,
            modified_at,
            accessed_at,
        ) = result

        return {
            "inode": inode,
            "name": name,
            "path": path,
            "type": file_type,
            "owner_uid": owner_uid,
            "owner_gid": owner_gid,
            "permissions": oct(permissions),
            "size": size,
            "created_at": created_at,
            "modified_at": modified_at,
            "accessed_at": accessed_at,
        }

    def chmod(self, path: str, permissions: int, uid: int, gid: int) -> bool:
        """Change file permissions.

        Args:
            path: File path
            permissions: New permissions
            uid: User ID (must be owner or root)
            gid: Group ID

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode, owner_uid FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        inode, owner_uid = result

        # Only owner or root can chmod
        if uid != owner_uid and uid != 0:
            conn.close()
            return False

        cursor.execute("UPDATE inodes SET permissions = ? WHERE inode = ?", (permissions, inode))
        conn.commit()
        conn.close()
        return True

    def chown(self, path: str, new_uid: int, new_gid: int, uid: int) -> bool:
        """Change file owner.

        Args:
            path: File path
            new_uid: New owner UID
            new_gid: New owner GID
            uid: User ID (must be root)

        Returns:
            True if successful
        """
        # Only root can chown
        if uid != 0:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        inode = result[0]
        cursor.execute(
            "UPDATE inodes SET owner_uid = ?, owner_gid = ? WHERE inode = ?",
            (new_uid, new_gid, inode),
        )
        conn.commit()
        conn.close()
        return True

    def rm(self, path: str, uid: int, gid: int) -> bool:
        """Delete a file or empty directory.

        Args:
            path: File path
            uid: User ID
            gid: Group ID

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT inode, owner_uid FROM inodes WHERE path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        inode, owner_uid = result

        # Check write permission on parent
        parent_path = str(Path(path).parent).replace("\\", "/")
        if parent_path == ".":
            parent_path = "/"

        cursor.execute("SELECT inode FROM inodes WHERE path = ?", (parent_path,))
        parent = cursor.fetchone()
        if parent and not self._check_permissions(parent[0], uid, gid, "w"):
            conn.close()
            return False

        # Delete file
        try:
            file_path = self.vfs_root / f"file_{inode}"
            if file_path.exists():
                file_path.unlink()

            cursor.execute("DELETE FROM inodes WHERE inode = ?", (inode,))
            conn.commit()
            conn.close()
            return True
        except OSError:
            conn.close()
            return False
