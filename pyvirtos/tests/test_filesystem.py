"""Tests for filesystem module."""

import pytest
import tempfile
from pathlib import Path

from pyvirtos.core.filesystem import VirtualFilesystem


class TestVirtualFilesystem:
    """Test VirtualFilesystem class."""

    @pytest.fixture
    def vfs(self):
        """Create a temporary VFS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield VirtualFilesystem(Path(tmpdir))

    def test_vfs_creation(self, vfs):
        """Test creating a VFS."""
        assert vfs.vfs_root.exists()
        assert vfs.db_path.exists()

    def test_root_directory_exists(self, vfs):
        """Test that root directory is created."""
        stat = vfs.stat("/", 0, 0)
        assert stat is not None
        assert stat["type"] == "directory"
        assert stat["path"] == "/"

    def test_mkdir(self, vfs):
        """Test creating a directory."""
        assert vfs.mkdir("/home", 0, 0)
        stat = vfs.stat("/home", 0, 0)
        assert stat is not None
        assert stat["type"] == "directory"

    def test_mkdir_nested(self, vfs):
        """Test creating nested directories."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.mkdir("/home/alice", 0, 0)
        stat = vfs.stat("/home/alice", 0, 0)
        assert stat is not None

    def test_mkdir_duplicate(self, vfs):
        """Test creating duplicate directory fails."""
        assert vfs.mkdir("/home", 0, 0)
        assert not vfs.mkdir("/home", 0, 0)

    def test_mkdir_nonexistent_parent(self, vfs):
        """Test creating directory with nonexistent parent fails."""
        assert not vfs.mkdir("/nonexistent/child", 0, 0)

    def test_touch(self, vfs):
        """Test creating a file."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        stat = vfs.stat("/home/test.txt", 0, 0)
        assert stat is not None
        assert stat["type"] == "file"

    def test_touch_duplicate(self, vfs):
        """Test creating duplicate file fails."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert not vfs.touch("/home/test.txt", 0, 0)

    def test_write_read(self, vfs):
        """Test writing and reading file."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)

        data = b"Hello, World!"
        assert vfs.write("/home/test.txt", data, 0, 0)

        read_data = vfs.read("/home/test.txt", 0, 0)
        assert read_data == data

    def test_read_nonexistent(self, vfs):
        """Test reading nonexistent file."""
        assert vfs.read("/nonexistent.txt", 0, 0) is None

    def test_listdir(self, vfs):
        """Test listing directory."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/file1.txt", 0, 0)
        assert vfs.touch("/home/file2.txt", 0, 0)

        contents = vfs.listdir("/home", 0, 0)
        assert contents is not None
        assert "file1.txt" in contents
        assert "file2.txt" in contents

    def test_listdir_root(self, vfs):
        """Test listing root directory."""
        assert vfs.mkdir("/home", 0, 0)
        contents = vfs.listdir("/", 0, 0)
        assert contents is not None
        assert "home" in contents

    def test_chmod(self, vfs):
        """Test changing file permissions."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert vfs.chmod("/home/test.txt", 0o600, 0, 0)

        stat = vfs.stat("/home/test.txt", 0, 0)
        assert stat is not None
        assert stat["permissions"] == "0o600"

    def test_chown(self, vfs):
        """Test changing file owner."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert vfs.chown("/home/test.txt", 1, 1, 0)  # Only root can chown

        stat = vfs.stat("/home/test.txt", 0, 0)
        assert stat is not None
        assert stat["owner_uid"] == 1

    def test_chown_non_root(self, vfs):
        """Test that non-root cannot chown."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert not vfs.chown("/home/test.txt", 1, 1, 1)  # Non-root cannot chown

    def test_rm(self, vfs):
        """Test deleting a file."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert vfs.rm("/home/test.txt", 0, 0)
        assert vfs.stat("/home/test.txt", 0, 0) is None

    def test_permissions_read(self, vfs):
        """Test read permission enforcement."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert vfs.write("/home/test.txt", b"secret", 0, 0)

        # Remove read permission for others
        assert vfs.chmod("/home/test.txt", 0o600, 0, 0)

        # User 1 should not be able to read
        assert vfs.read("/home/test.txt", 1, 1) is None

    def test_permissions_write(self, vfs):
        """Test write permission enforcement."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)

        # Remove write permission for others
        assert vfs.chmod("/home/test.txt", 0o444, 0, 0)

        # User 1 should not be able to write
        assert not vfs.write("/home/test.txt", b"data", 1, 1)

    def test_root_bypass_permissions(self, vfs):
        """Test that root bypasses permissions."""
        assert vfs.mkdir("/home", 0, 0)
        assert vfs.touch("/home/test.txt", 0, 0)
        assert vfs.write("/home/test.txt", b"secret", 0, 0)

        # Remove all permissions
        assert vfs.chmod("/home/test.txt", 0o000, 0, 0)

        # Root should still be able to read
        assert vfs.read("/home/test.txt", 0, 0) == b"secret"
