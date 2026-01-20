"""Platform-agnostic file locking utilities with timeout support."""
import sys
import os
import time
from typing import Optional

# Determine which locking backend to use
if sys.platform == "win32":
    _LOCK_BACKEND = "msvcrt"
else:
    _LOCK_BACKEND = "fcntl"

# Default lock timeout in seconds (used for stale lock detection)
DEFAULT_LOCK_TIMEOUT = 300  # 5 minutes


class FileLock:
    """Platform-agnostic file lock using fcntl on Unix and msvcrt on Windows.

    Supports exclusive locking with optional timeout for stale lock detection.
    """

    def __init__(self, filepath: str, timeout: float = DEFAULT_LOCK_TIMEOUT):
        """Initialize file lock.

        Args:
            filepath: Path to the lock file.
            timeout: Lock timeout in seconds for stale detection. 0 means no timeout.
        """
        self.filepath = filepath
        self.timeout = timeout
        self.fd: Optional[int] = None
        self._acquired = False

    def acquire(self, blocking: bool = False) -> bool:
        """Acquire an exclusive lock on the file.

        Args:
            blocking: If False, return immediately if lock is held by another process.
                     If True, block until lock is available.

        Returns:
            True if lock was acquired, False otherwise.
        """
        try:
            self.fd = os.open(self.filepath, os.O_CREAT | os.O_WRONLY)

            if _LOCK_BACKEND == "fcntl":
                import fcntl
                flags = fcntl.LOCK_EX
                if not blocking:
                    flags |= fcntl.LOCK_NB
                fcntl.flock(self.fd, flags)
            else:
                import msvcrt
                # Lock the first byte of the file (non-blocking)
                msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)

            self._acquired = True
            return True
        except (BlockingIOError, OSError, PermissionError, IOError):
            self._cleanup_fd()
            return False

    def release(self) -> None:
        """Release the lock and close the file descriptor."""
        try:
            if self._acquired:
                if _LOCK_BACKEND == "fcntl":
                    import fcntl
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                # On Windows, msvcrt locking is automatically released when file is closed

                self._acquired = False
        except Exception:
            pass
        finally:
            self._cleanup_fd()

    def _cleanup_fd(self) -> None:
        """Close file descriptor if open."""
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None

    def is_expired(self, now: Optional[float] = None) -> bool:
        """Check if the lock is expired based on timeout.

        Note: This only works if the lock file contains a timestamp.
        Use read_timestamp() to get the timestamp.

        Args:
            now: Current time in seconds. Defaults to time.time().

        Returns:
            True if lock is expired or has no timestamp, False otherwise.
        """
        if self.timeout <= 0:
            return False

        timestamp = self.read_timestamp()
        if timestamp is None:
            return True  # No timestamp means expired

        if now is None:
            now = time.time()

        return (now - timestamp) > self.timeout

    def read_timestamp(self) -> Optional[float]:
        """Read the timestamp from the lock file.

        Returns:
            Timestamp as float, or None if not found or invalid.
        """
        if not os.path.exists(self.filepath):
            return None

        try:
            with open(self.filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    return None

                parts = content.split('\n')
                if len(parts) >= 2:
                    return float(parts[1])
        except (ValueError, IOError, OSError):
            pass

        return None

    def write_timestamp(self, timestamp: float, pid: int = 0) -> bool:
        """Write timestamp and PID to the lock file.

        Args:
            timestamp: Timestamp to write.
            pid: Process ID to write (optional).

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.filepath, 'w') as f:
                if pid > 0:
                    f.write(f"{pid}\n{timestamp}\n")
                else:
                    f.write(f"{timestamp}\n")
            return True
        except (IOError, OSError):
            return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def is_file_locked(filepath: str, timeout: float = DEFAULT_LOCK_TIMEOUT) -> bool:
    """Check if a file is currently locked by another process.

    Args:
        filepath: Path to the lock file.
        timeout: Lock timeout in seconds for checking expiration.

    Returns:
        True if the file is locked (including expired locks), False otherwise.
    """
    if not os.path.exists(filepath):
        return False

    lock = FileLock(filepath, timeout=timeout)

    # First check if lock is expired
    if lock.is_expired():
        return False  # Expired lock is considered not locked

    # Try to acquire
    acquired = lock.acquire(blocking=False)
    if acquired:
        lock.release()
        return False  # Successfully acquired means not locked

    return True


def acquire_lock_file(filepath: str, timeout: float = 0,
                      pid: Optional[int] = None) -> Optional[FileLock]:
    """Acquire a lock file with optional timeout and PID tracking.

    This is a convenience function that combines locking with timestamp writing.

    Args:
        filepath: Path to the lock file.
        timeout: Lock timeout in seconds. 0 means no timeout.
        pid: Process ID to store in the lock file.

    Returns:
        FileLock instance if acquired, None otherwise.
    """
    lock = FileLock(filepath, timeout=timeout)

    if lock.acquire(blocking=False):
        # Write timestamp and PID
        now = time.time()
        lock.write_timestamp(now, pid if pid else os.getpid())
        return lock

    return None


class LockManager:
    """Manages file locks with automatic cleanup and expiration detection.

    This class provides a higher-level interface for managing locks
    across multiple platforms with built-in expiration support.
    """

    def __init__(self, lock_dir: str, timeout: float = DEFAULT_LOCK_TIMEOUT):
        """Initialize lock manager.

        Args:
            lock_dir: Directory for lock files.
            timeout: Default lock timeout in seconds.
        """
        self.lock_dir = lock_dir
        self.timeout = timeout
        self._active_locks: dict[str, FileLock] = {}

        # Ensure lock directory exists
        os.makedirs(lock_dir, exist_ok=True)

    def get_lock_path(self, name: str) -> str:
        """Get the full path for a lock file.

        Args:
            name: Lock name (will be used as filename).

        Returns:
            Full path to the lock file.
        """
        return os.path.join(self.lock_dir, f"{name}.lock")

    def acquire(self, name: str, pid: Optional[int] = None,
                blocking: bool = False) -> Optional[FileLock]:
        """Acquire a named lock.

        Args:
            name: Lock name.
            pid: Process ID to store.
            blocking: Whether to block waiting for the lock.

        Returns:
            FileLock instance if acquired, None otherwise.
        """
        lock_path = self.get_lock_path(name)

        # Check for stale lock first
        if self.timeout > 0:
            stale_lock = FileLock(lock_path, timeout=self.timeout)
            if stale_lock.is_expired():
                # Try to clean up stale lock by acquiring it
                if stale_lock.acquire(blocking=False):
                    stale_lock.release()
                    # Remove stale lock file
                    try:
                        os.unlink(lock_path)
                    except OSError:
                        pass

        lock = FileLock(lock_path, timeout=self.timeout)
        if lock.acquire(blocking=blocking):
            # Write timestamp and PID
            now = time.time()
            lock.write_timestamp(now, pid if pid else os.getpid())
            self._active_locks[name] = lock
            return lock

        return None

    def release(self, name: str) -> None:
        """Release a named lock.

        Args:
            name: Lock name.
        """
        if name in self._active_locks:
            lock = self._active_locks.pop(name)
            lock.release()

        # Also try to clean up any leftover lock file
        try:
            lock_path = self.get_lock_path(name)
            if os.path.exists(lock_path):
                os.unlink(lock_path)
        except OSError:
            pass

    def is_locked(self, name: str) -> bool:
        """Check if a named lock is held.

        Args:
            name: Lock name.

        Returns:
            True if locked, False otherwise.
        """
        lock_path = self.get_lock_path(name)

        if not os.path.exists(lock_path):
            return False

        # Check for expiration
        lock = FileLock(lock_path, timeout=self.timeout)
        if lock.is_expired():
            return False

        # Try to acquire
        if lock.acquire(blocking=False):
            lock.release()
            return False

        return True

    def cleanup_expired(self) -> int:
        """Clean up all expired lock files.

        Returns:
            Number of lock files cleaned up.
        """
        cleaned = 0

        if not os.path.exists(self.lock_dir):
            return 0

        for filename in os.listdir(self.lock_dir):
            if not filename.endswith('.lock'):
                continue

            lock_path = os.path.join(self.lock_dir, filename)
            lock = FileLock(lock_path, timeout=self.timeout)

            if lock.is_expired():
                try:
                    # Try to remove expired lock
                    os.unlink(lock_path)
                    cleaned += 1
                except OSError:
                    pass

        return cleaned

    def __contains__(self, name: str) -> bool:
        """Check if a lock is held using 'in' operator."""
        return self.is_locked(name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Release all active locks
        for name in list(self._active_locks.keys()):
            self.release(name)
