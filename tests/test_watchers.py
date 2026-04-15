"""Tests for configuration file watching."""

import pytest
import tempfile
import time
from pathlib import Path
from confmerge.watchers import ConfigWatcher, WatcherError, watch_file


class TestConfigWatcher:
    def test_watch_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            path = f.name

        try:
            watcher = ConfigWatcher()
            watcher.watch(path)
            assert watcher.is_watching(path)
        finally:
            Path(path).unlink()

    def test_watch_nonexistent_file(self):
        watcher = ConfigWatcher()
        with pytest.raises(WatcherError, match="non-existent"):
            watcher.watch("/nonexistent/file.txt")

    def test_watch_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = ConfigWatcher()
            with pytest.raises(WatcherError, match="not directories"):
                watcher.watch(tmpdir)

    def test_unwatch_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            path = f.name

        try:
            watcher = ConfigWatcher()
            watcher.watch(path)
            assert watcher.unwatch(path)
            assert not watcher.is_watching(path)
            assert not watcher.unwatch(path)  # Second unwatch returns False
        finally:
            Path(path).unlink()

    def test_detect_file_change(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original")
            path = f.name

        try:
            watcher = ConfigWatcher(debounce_seconds=0.1)
            watcher.watch(path)

            # No changes yet
            changed = watcher.check_changes()
            assert len(changed) == 0

            # Modify file
            time.sleep(0.15)  # Wait for debounce
            with open(path, "w") as f:
                f.write("modified")

            # Should detect change
            changed = watcher.check_changes()
            assert len(changed) == 1
            assert Path(path).resolve() in changed
        finally:
            Path(path).unlink()

    def test_callback_on_change(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original")
            path = f.name

        try:
            callback_calls = []

            def callback(p):
                callback_calls.append(p)

            watcher = ConfigWatcher(debounce_seconds=0.1)
            watcher.watch(path, callback=callback)

            # Modify file
            time.sleep(0.15)
            with open(path, "w") as f:
                f.write("modified")

            # Check for changes
            watcher.check_changes()
            assert len(callback_calls) == 1
            assert callback_calls[0] == str(Path(path).resolve())
        finally:
            Path(path).unlink()

    def test_debouncing(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original")
            path = f.name

        try:
            callback_calls = []

            def callback(p):
                callback_calls.append(p)

            watcher = ConfigWatcher(debounce_seconds=0.5)
            watcher.watch(path, callback=callback)

            # First change
            time.sleep(0.1)
            with open(path, "w") as f:
                f.write("change1")
            watcher.check_changes()
            assert len(callback_calls) == 1

            # Second change immediately (should be debounced)
            time.sleep(0.1)
            with open(path, "w") as f:
                f.write("change2")
            watcher.check_changes()
            assert len(callback_calls) == 1  # Still 1, debounced

            # Wait for debounce period and change again
            time.sleep(0.5)
            with open(path, "w") as f:
                f.write("change3")
            watcher.check_changes()
            assert len(callback_calls) == 2  # Now 2
        finally:
            Path(path).unlink()

    def test_get_watched_files(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            path1 = f1.name
            path2 = f2.name

        try:
            watcher = ConfigWatcher()
            watcher.watch(path1)
            watcher.watch(path2)

            watched = watcher.get_watched_files()
            assert len(watched) == 2
            assert Path(path1).resolve() in watched
            assert Path(path2).resolve() in watched
        finally:
            Path(path1).unlink()
            Path(path2).unlink()

    def test_clear_watcher(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            path = f.name

        try:
            watcher = ConfigWatcher()
            watcher.watch(path)
            assert len(watcher.get_watched_files()) == 1

            watcher.clear()
            assert len(watcher.get_watched_files()) == 0
        finally:
            Path(path).unlink()

    def test_poll_once(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original")
            path = f.name

        try:
            watcher = ConfigWatcher(debounce_seconds=0.1)
            watcher.watch(path)

            # Modify and poll
            time.sleep(0.15)
            with open(path, "w") as f:
                f.write("modified")

            changed = watcher.poll_once()
            assert len(changed) == 1
        finally:
            Path(path).unlink()


class TestWatchFileHelper:
    def test_watch_file_helper(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            path = f.name

        try:
            watcher = watch_file(path)
            assert isinstance(watcher, ConfigWatcher)
            assert watcher.is_watching(path)
        finally:
            Path(path).unlink()
