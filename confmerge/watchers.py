"""Configuration file change watching using stat polling.

Provides a ConfigWatcher class that monitors configuration files for changes
using file stat polling. Includes callback support and debouncing for rapid
successive changes.
"""

import os
import time
from pathlib import Path


class WatcherError(Exception):
    """Raised when watcher operations fail."""
    pass


class ConfigWatcher:
    """Watch configuration files for changes using stat polling.

    Uses file modification time (mtime) to detect changes. Includes debouncing
    to avoid triggering callbacks multiple times for rapid successive changes.
    """

    def __init__(self, debounce_seconds=1.0):
        """Initialize a config file watcher.

        Args:
            debounce_seconds: Minimum time between change notifications for
                            the same file (default: 1.0 seconds)
        """
        self._watched = {}  # path -> (mtime, callback)
        self._last_triggered = {}  # path -> timestamp
        self._debounce_seconds = debounce_seconds

    def watch(self, path, callback=None):
        """Start watching a file for changes.

        Args:
            path: File path to watch (string or Path object)
            callback: Optional function to call when file changes.
                     Callback receives the file path as its only argument.

        Raises:
            WatcherError: If file doesn't exist or can't be accessed
        """
        path = Path(path).resolve()

        if not path.exists():
            raise WatcherError(f"Cannot watch non-existent file: {path}")

        if not path.is_file():
            raise WatcherError(f"Can only watch files, not directories: {path}")

        try:
            stat = path.stat()
            mtime = stat.st_mtime
        except OSError as e:
            raise WatcherError(f"Cannot access file {path}: {e}")

        self._watched[path] = (mtime, callback)

    def unwatch(self, path):
        """Stop watching a file.

        Args:
            path: File path to stop watching

        Returns:
            True if file was being watched, False otherwise
        """
        path = Path(path).resolve()

        if path in self._watched:
            del self._watched[path]
            if path in self._last_triggered:
                del self._last_triggered[path]
            return True

        return False

    def is_watching(self, path):
        """Check if a file is being watched.

        Args:
            path: File path to check

        Returns:
            True if file is being watched, False otherwise
        """
        path = Path(path).resolve()
        return path in self._watched

    def check_changes(self):
        """Check all watched files for changes.

        Compares current mtime with stored mtime for each watched file.
        Triggers callbacks for files that have changed, respecting debounce
        settings.

        Returns:
            List of paths that changed (after debouncing)
        """
        changed = []
        current_time = time.time()

        for path, (old_mtime, callback) in list(self._watched.items()):
            try:
                if not path.exists():
                    # File was deleted - trigger callback one last time
                    if self._should_trigger(path, current_time):
                        changed.append(path)
                        if callback:
                            callback(str(path))
                        self._last_triggered[path] = current_time
                    continue

                stat = path.stat()
                new_mtime = stat.st_mtime

                if new_mtime != old_mtime:
                    # File changed - update mtime and maybe trigger callback
                    self._watched[path] = (new_mtime, callback)

                    if self._should_trigger(path, current_time):
                        changed.append(path)
                        if callback:
                            callback(str(path))
                        self._last_triggered[path] = current_time

            except OSError:
                # If we can't stat the file, skip it for this check
                continue

        return changed

    def _should_trigger(self, path, current_time):
        """Check if enough time has passed since last trigger for debouncing.

        Args:
            path: File path to check
            current_time: Current timestamp

        Returns:
            True if callback should be triggered, False if debounced
        """
        if path not in self._last_triggered:
            return True

        last_trigger = self._last_triggered[path]
        elapsed = current_time - last_trigger

        return elapsed >= self._debounce_seconds

    def get_watched_files(self):
        """Get list of all watched file paths.

        Returns:
            List of Path objects for all watched files
        """
        return list(self._watched.keys())

    def clear(self):
        """Stop watching all files."""
        self._watched.clear()
        self._last_triggered.clear()

    def poll_once(self):
        """Convenience method to check for changes once.

        Returns:
            List of paths that changed
        """
        return self.check_changes()

    def poll_loop(self, interval=1.0, max_iterations=None):
        """Poll for changes in a loop.

        Args:
            interval: Seconds to wait between checks (default: 1.0)
            max_iterations: Maximum number of iterations (None for infinite)

        Yields:
            List of changed paths for each iteration that has changes
        """
        iteration = 0

        while max_iterations is None or iteration < max_iterations:
            changed = self.check_changes()
            if changed:
                yield changed

            time.sleep(interval)
            iteration += 1


def watch_file(path, callback=None):
    """Create a watcher and start watching a single file.

    Convenience function for simple use cases.

    Args:
        path: File path to watch
        callback: Optional callback function

    Returns:
        ConfigWatcher instance
    """
    watcher = ConfigWatcher()
    watcher.watch(path, callback)
    return watcher
