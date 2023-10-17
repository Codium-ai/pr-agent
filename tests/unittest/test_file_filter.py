import pytest
from pr_agent.algo.file_filter import filter_ignored
from pr_agent.config_loader import global_settings

class TestIgnoreFilter:
    def test_no_ignores(self):
        """
        Test no files are ignored when no patterns are specified.
        """
        files = [
            type('', (object,), {'filename': 'file1.py'})(),
            type('', (object,), {'filename': 'file2.java'})(),
            type('', (object,), {'filename': 'file3.cpp'})(),
            type('', (object,), {'filename': 'file4.py'})(),
            type('', (object,), {'filename': 'file5.py'})()
        ]
        assert filter_ignored(files) == files, "Expected all files to be returned when no ignore patterns are given."

    def test_glob_ignores(self, monkeypatch):
        """
        Test files are ignored when glob patterns are specified.
        """
        monkeypatch.setattr(global_settings.ignore, 'glob', ['*.py'])

        files = [
            type('', (object,), {'filename': 'file1.py'})(),
            type('', (object,), {'filename': 'file2.java'})(),
            type('', (object,), {'filename': 'file3.cpp'})(),
            type('', (object,), {'filename': 'file4.py'})(),
            type('', (object,), {'filename': 'file5.py'})()
        ]
        expected = [
            files[1],
            files[2]
        ]

        filtered_files = filter_ignored(files)
        assert filtered_files == expected, f"Expected {[file.filename for file in expected]}, but got {[file.filename for file in filtered_files]}."

    def test_regex_ignores(self, monkeypatch):
        """
        Test files are ignored when regex patterns are specified.
        """
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^file[2-4]\..*$'])

        files = [
            type('', (object,), {'filename': 'file1.py'})(),
            type('', (object,), {'filename': 'file2.java'})(),
            type('', (object,), {'filename': 'file3.cpp'})(),
            type('', (object,), {'filename': 'file4.py'})(),
            type('', (object,), {'filename': 'file5.py'})()
        ]
        expected = [
            files[0],
            files[4]
        ]

        filtered_files = filter_ignored(files)
        assert filtered_files == expected, f"Expected {[file.filename for file in expected]}, but got {[file.filename for file in filtered_files]}."

    def test_invalid_regex(self, monkeypatch):
        """
        Test invalid patterns are quietly ignored.
        """
        monkeypatch.setattr(global_settings.ignore, 'regex', ['(((||', '^file[2-4]\..*$'])

        files = [
            type('', (object,), {'filename': 'file1.py'})(),
            type('', (object,), {'filename': 'file2.java'})(),
            type('', (object,), {'filename': 'file3.cpp'})(),
            type('', (object,), {'filename': 'file4.py'})(),
            type('', (object,), {'filename': 'file5.py'})()
        ]
        expected = [
            files[0],
            files[4]
        ]

        filtered_files = filter_ignored(files)
        assert filtered_files == expected, f"Expected {[file.filename for file in expected]}, but got {[file.filename for file in filtered_files]}."
