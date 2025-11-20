"""Tests for user management module."""

import pytest
import tempfile
from pathlib import Path

from pyvirtos.core.users import UserManager


class TestUserManager:
    """Test UserManager class."""

    @pytest.fixture
    def user_manager(self):
        """Create a temporary user manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield UserManager(Path(tmpdir) / "users.db")

    def test_user_manager_creation(self, user_manager):
        """Test creating a user manager."""
        assert user_manager.db_path.exists()

    def test_root_user_exists(self, user_manager):
        """Test that root user is created."""
        user = user_manager.get_user("root")
        assert user is not None
        assert user.uid == 0
        assert user.username == "root"

    def test_authenticate_root(self, user_manager):
        """Test authenticating root user."""
        session = user_manager.authenticate("root", "rootpass")
        assert session is not None
        assert session.uid == 0
        assert session.username == "root"

    def test_authenticate_wrong_password(self, user_manager):
        """Test authentication with wrong password."""
        session = user_manager.authenticate("root", "wrongpass")
        assert session is None

    def test_authenticate_nonexistent_user(self, user_manager):
        """Test authentication of nonexistent user."""
        session = user_manager.authenticate("nonexistent", "password")
        assert session is None

    def test_create_user(self, user_manager):
        """Test creating a new user."""
        assert user_manager.create_user("alice", "alicepass")
        user = user_manager.get_user("alice")
        assert user is not None
        assert user.username == "alice"

    def test_create_duplicate_user(self, user_manager):
        """Test creating duplicate user fails."""
        assert user_manager.create_user("alice", "alicepass")
        assert not user_manager.create_user("alice", "alicepass")

    def test_authenticate_new_user(self, user_manager):
        """Test authenticating newly created user."""
        assert user_manager.create_user("alice", "alicepass")
        session = user_manager.authenticate("alice", "alicepass")
        assert session is not None
        assert session.username == "alice"

    def test_get_user_by_uid(self, user_manager):
        """Test getting user by UID."""
        user_manager.create_user("alice", "alicepass")
        alice = user_manager.get_user("alice")
        user = user_manager.get_user_by_uid(alice.uid)
        assert user is not None
        assert user.username == "alice"

    def test_change_password(self, user_manager):
        """Test changing password."""
        user_manager.create_user("alice", "oldpass")
        assert user_manager.change_password("alice", "oldpass", "newpass")

        # Old password should not work
        session = user_manager.authenticate("alice", "oldpass")
        assert session is None

        # New password should work
        session = user_manager.authenticate("alice", "newpass")
        assert session is not None

    def test_change_password_wrong_old(self, user_manager):
        """Test changing password with wrong old password."""
        user_manager.create_user("alice", "oldpass")
        assert not user_manager.change_password("alice", "wrongpass", "newpass")

    def test_list_users(self, user_manager):
        """Test listing users."""
        user_manager.create_user("alice", "alicepass")
        user_manager.create_user("bob", "bobpass")

        users = user_manager.list_users()
        usernames = [u.username for u in users]
        assert "root" in usernames
        assert "alice" in usernames
        assert "bob" in usernames

    def test_user_home_directory(self, user_manager):
        """Test user home directory."""
        user_manager.create_user("alice", "alicepass")
        user = user_manager.get_user("alice")
        assert user.home_directory == "/home/alice"

    def test_user_custom_home_directory(self, user_manager):
        """Test user with custom home directory."""
        user_manager.create_user("alice", "alicepass", home_directory="/custom/home")
        user = user_manager.get_user("alice")
        assert user.home_directory == "/custom/home"

    def test_user_groups(self, user_manager):
        """Test user groups."""
        user_manager.create_user("alice", "alicepass")
        user = user_manager.get_user("alice")
        assert "alice" in user.groups  # Primary group

    def test_user_session_info(self, user_manager):
        """Test user session information."""
        user_manager.create_user("alice", "alicepass")
        session = user_manager.authenticate("alice", "alicepass")
        assert session.username == "alice"
        assert session.home_directory == "/home/alice"
        assert session.shell == "/bin/bash"
