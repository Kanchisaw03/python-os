"""User management and authentication for PyVirtOS."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import bcrypt


@dataclass
class User:
    """Represents a user in the system."""

    uid: int
    username: str
    gid: int
    groups: List[str]
    home_directory: str
    shell: str
    password_hash: bytes

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "uid": self.uid,
            "username": self.username,
            "gid": self.gid,
            "groups": self.groups,
            "home_directory": self.home_directory,
            "shell": self.shell,
        }


@dataclass
class UserSession:
    """Represents an authenticated user session."""

    uid: int
    username: str
    gid: int
    groups: List[str]
    home_directory: str
    shell: str


class UserManager:
    """Manages users and authentication."""

    def __init__(self, db_path: Path):
        """Initialize user manager.

        Args:
            db_path: Path to user database
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._init_root_user()

    def _init_database(self) -> None:
        """Initialize user database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                uid INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                gid INTEGER NOT NULL,
                password_hash BLOB NOT NULL,
                home_directory TEXT NOT NULL,
                shell TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                gid INTEGER PRIMARY KEY,
                groupname TEXT NOT NULL UNIQUE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_groups (
                uid INTEGER NOT NULL,
                gid INTEGER NOT NULL,
                PRIMARY KEY (uid, gid),
                FOREIGN KEY(uid) REFERENCES users(uid),
                FOREIGN KEY(gid) REFERENCES groups(gid)
            )
        """
        )

        conn.commit()
        conn.close()

    def _init_root_user(self) -> None:
        """Initialize root user if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT uid FROM users WHERE username = ?", ("root",))
        if cursor.fetchone() is None:
            # Create root group
            cursor.execute("INSERT OR IGNORE INTO groups (gid, groupname) VALUES (?, ?)", (0, "root"))

            # Create root user with default password
            password_hash = bcrypt.hashpw(b"rootpass", bcrypt.gensalt())
            import time

            cursor.execute(
                """
                INSERT INTO users (uid, username, gid, password_hash, home_directory, shell, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (0, "root", 0, password_hash, "/root", "/bin/bash", time.time()),
            )

            # Add root to root group
            cursor.execute("INSERT INTO user_groups (uid, gid) VALUES (?, ?)", (0, 0))

            conn.commit()

        conn.close()

    def create_user(
        self,
        username: str,
        password: str,
        groups: Optional[List[str]] = None,
        home_directory: Optional[str] = None,
        shell: str = "/bin/bash",
    ) -> bool:
        """Create a new user.

        Args:
            username: Username
            password: Password (plain text, will be hashed)
            groups: List of group names
            home_directory: Home directory path
            shell: Default shell

        Returns:
            True if successful
        """
        if groups is None:
            groups = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT uid FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False

        # Get next UID
        cursor.execute("SELECT MAX(uid) FROM users")
        max_uid = cursor.fetchone()[0]
        new_uid = (max_uid or 0) + 1

        # Get next GID for user's primary group
        cursor.execute("SELECT MAX(gid) FROM groups")
        max_gid = cursor.fetchone()[0]
        new_gid = (max_gid or 0) + 1

        # Create user's primary group
        try:
            cursor.execute(
                "INSERT INTO groups (gid, groupname) VALUES (?, ?)",
                (new_gid, username),
            )

            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

            # Set home directory
            if home_directory is None:
                home_directory = f"/home/{username}"

            # Create user
            import time

            cursor.execute(
                """
                INSERT INTO users (uid, username, gid, password_hash, home_directory, shell, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (new_uid, username, new_gid, password_hash, home_directory, shell, time.time()),
            )

            # Add user to primary group
            cursor.execute("INSERT INTO user_groups (uid, gid) VALUES (?, ?)", (new_uid, new_gid))

            # Add user to additional groups
            for group_name in groups:
                cursor.execute("SELECT gid FROM groups WHERE groupname = ?", (group_name,))
                group = cursor.fetchone()
                if group:
                    cursor.execute(
                        "INSERT OR IGNORE INTO user_groups (uid, gid) VALUES (?, ?)",
                        (new_uid, group[0]),
                    )

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def authenticate(self, username: str, password: str) -> Optional[UserSession]:
        """Authenticate a user.

        Args:
            username: Username
            password: Password (plain text)

        Returns:
            UserSession if successful, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT uid, username, gid, home_directory, shell, password_hash
            FROM users WHERE username = ?
        """,
            (username,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        uid, username, gid, home_directory, shell, password_hash = result

        # Verify password
        if not bcrypt.checkpw(password.encode(), password_hash):
            conn.close()
            return None

        # Get user's groups
        cursor.execute(
            """
            SELECT g.groupname FROM groups g
            JOIN user_groups ug ON g.gid = ug.gid
            WHERE ug.uid = ?
        """,
            (uid,),
        )
        groups = [row[0] for row in cursor.fetchall()]

        conn.close()

        return UserSession(
            uid=uid,
            username=username,
            gid=gid,
            groups=groups,
            home_directory=home_directory,
            shell=shell,
        )

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT uid, username, gid, home_directory, shell, password_hash
            FROM users WHERE username = ?
        """,
            (username,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        uid, username, gid, home_directory, shell, password_hash = result

        # Get user's groups
        cursor.execute(
            """
            SELECT g.groupname FROM groups g
            JOIN user_groups ug ON g.gid = ug.gid
            WHERE ug.uid = ?
        """,
            (uid,),
        )
        groups = [row[0] for row in cursor.fetchall()]

        conn.close()

        return User(
            uid=uid,
            username=username,
            gid=gid,
            groups=groups,
            home_directory=home_directory,
            shell=shell,
            password_hash=password_hash,
        )

    def get_user_by_uid(self, uid: int) -> Optional[User]:
        """Get user by UID.

        Args:
            uid: User ID

        Returns:
            User object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT uid, username, gid, home_directory, shell, password_hash
            FROM users WHERE uid = ?
        """,
            (uid,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        uid, username, gid, home_directory, shell, password_hash = result

        # Get user's groups
        cursor.execute(
            """
            SELECT g.groupname FROM groups g
            JOIN user_groups ug ON g.gid = ug.gid
            WHERE ug.uid = ?
        """,
            (uid,),
        )
        groups = [row[0] for row in cursor.fetchall()]

        conn.close()

        return User(
            uid=uid,
            username=username,
            gid=gid,
            groups=groups,
            home_directory=home_directory,
            shell=shell,
            password_hash=password_hash,
        )

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password.

        Args:
            username: Username
            old_password: Current password
            new_password: New password

        Returns:
            True if successful
        """
        # Authenticate first
        session = self.authenticate(username, old_password)
        if not session:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, username),
        )
        conn.commit()
        conn.close()
        return True

    def list_users(self) -> List[User]:
        """List all users.

        Returns:
            List of User objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT uid, username, gid, home_directory, shell, password_hash
            FROM users ORDER BY uid
        """
        )
        results = cursor.fetchall()

        users = []
        for uid, username, gid, home_directory, shell, password_hash in results:
            # Get user's groups
            cursor.execute(
                """
                SELECT g.groupname FROM groups g
                JOIN user_groups ug ON g.gid = ug.gid
                WHERE ug.uid = ?
            """,
                (uid,),
            )
            groups = [row[0] for row in cursor.fetchall()]

            users.append(
                User(
                    uid=uid,
                    username=username,
                    gid=gid,
                    groups=groups,
                    home_directory=home_directory,
                    shell=shell,
                    password_hash=password_hash,
                )
            )

        conn.close()
        return users
