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

    def test_single_string_glob_pattern(self, monkeypatch):
        """
        Test that the function correctly handles a single string glob pattern in the ignore settings.
        """
        monkeypatch.setattr(global_settings.ignore, 'glob', '*.py')
    
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


    def test_exception_handling(self, monkeypatch):
        """
        Test that exceptions are handled and the original file list is returned.
        """
        def mock_get_settings():
            raise Exception("Mocked exception")
    
        monkeypatch.setattr('pr_agent.algo.file_filter.get_settings', mock_get_settings)
    
        files = [
            type('', (object,), {'filename': 'file1.py'})(),
            type('', (object,), {'filename': 'file2.java'})(),
            type('', (object,), {'filename': 'file3.cpp'})(),
            type('', (object,), {'filename': 'file4.py'})(),
            type('', (object,), {'filename': 'file5.py'})()
        ]
    
        filtered_files = filter_ignored(files)
        assert filtered_files == files, "Expected the original list of files to be returned when an exception occurs."


    def test_azure_platform(self, monkeypatch):
        """
        Test files are ignored correctly for Azure platform.
        """
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^file[2-4]\..*$'])
    
        files = [
            'file1.py',
            'file2.java',
            'file3.cpp',
            'file4.py',
            'file5.py'
        ]
        expected = [
            'file1.py',
            'file5.py'
        ]
    
        filtered_files = filter_ignored(files, platform='azure')
        assert filtered_files == expected, f"Expected {expected}, but got {filtered_files}."


    def test_gitlab_platform(self, monkeypatch):
        """
        Test files are ignored correctly for GitLab platform.
        """
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^file[2-4]\..*$'])
    
        files = [
            {'new_path': 'file1.py', 'old_path': None},
            {'new_path': 'file2.java', 'old_path': None},
            {'new_path': None, 'old_path': 'file3.cpp'},
            {'new_path': 'file4.py', 'old_path': None},
            {'new_path': None, 'old_path': 'file5.py'}
        ]
        expected = [
            files[0],
            files[4]
        ]
    
        filtered_files = filter_ignored(files, platform='gitlab')
        assert filtered_files == expected, f"Expected {[file['new_path'] if file['new_path'] else file['old_path'] for file in expected]}, but got {[file['new_path'] if file['new_path'] else file['old_path'] for file in filtered_files]}."


    def test_bitbucket_platform(self, monkeypatch):
        """
        Test files are ignored correctly for Bitbucket platform.
        """
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^file[2-4]\..*$'])
    
        files = [
            type('', (object,), {'new': type('', (object,), {'path': 'file1.py'})(), 'old': None})(),
            type('', (object,), {'new': type('', (object,), {'path': 'file2.java'})(), 'old': None})(),
            type('', (object,), {'new': None, 'old': type('', (object,), {'path': 'file3.cpp'})()})(),
            type('', (object,), {'new': type('', (object,), {'path': 'file4.py'})(), 'old': None})(),
            type('', (object,), {'new': None, 'old': type('', (object,), {'path': 'file5.py'})()})()
        ]
        expected = [
            files[0],
            files[4]
        ]
    
        filtered_files = filter_ignored(files, platform='bitbucket')
        assert filtered_files == expected, f"Expected {[file.new.path if file.new else file.old.path for file in expected]}, but got {[file.new.path if file.new else file.old.path for file in filtered_files]}."

