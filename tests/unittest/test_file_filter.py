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

    def test_bitbucket_platform_old_paths(self, monkeypatch):
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^test.*\.py$'])
        
        class BitbucketFile:
            def __init__(self, old_path=None):
                self.new = None
                self.old = type('Path', (), {'path': old_path})() if old_path else None
        
        files = [
            BitbucketFile('test_old1.py'),
            BitbucketFile('main_old.py'),
            BitbucketFile(None),  # Edge case with no path
            BitbucketFile('src_old.py')
        ]
        
        filtered_files = filter_ignored(files, platform='bitbucket')
        assert len(filtered_files) == 2
        assert any(f.old and f.old.path == 'main_old.py' for f in filtered_files)
        assert any(f.old and f.old.path == 'src_old.py' for f in filtered_files)


    def test_gitlab_platform_new_paths(self, monkeypatch):
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^test.*\.py$'])
        
        files = [
            {'new_path': 'test1.py'},
            {'new_path': 'main.py'},
            {'new_path': None},  # Edge case with no path
            {'new_path': 'src.py'}
        ]
        
        filtered_files = filter_ignored(files, platform='gitlab')
        assert len(filtered_files) == 2
        assert any(f['new_path'] == 'main.py' for f in filtered_files)
        assert any(f['new_path'] == 'src.py' for f in filtered_files)


    def test_bitbucket_platform_new_paths(self, monkeypatch):
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^test.*\.py$'])
        
        class BitbucketFile:
            def __init__(self, new_path=None):
                self.new = type('Path', (), {'path': new_path})() if new_path else None
                self.old = None
        
        files = [
            BitbucketFile('test1.py'),
            BitbucketFile('main.py'),
            BitbucketFile(None),  # Edge case with no path
            BitbucketFile('src.py')
        ]
        
        filtered_files = filter_ignored(files, platform='bitbucket')
        assert len(filtered_files) == 2
        assert any(f.new and f.new.path == 'main.py' for f in filtered_files)
        assert any(f.new and f.new.path == 'src.py' for f in filtered_files)


    def test_string_pattern_handling(self, monkeypatch):
        # Test single string regex pattern
        monkeypatch.setattr(global_settings.ignore, 'regex', '^test.*\.py$')
        monkeypatch.setattr(global_settings.ignore, 'glob', '[*.txt]')
        
        files = [
            type('', (object,), {'filename': 'test1.py'})(),
            type('', (object,), {'filename': 'main.py'})(),
            type('', (object,), {'filename': 'data.txt'})()
        ]
        
        filtered_files = filter_ignored(files)
        assert len(filtered_files) == 1
        assert filtered_files[0].filename == 'main.py'


    def test_azure_platform_and_error_handling(self, monkeypatch):
        monkeypatch.setattr(global_settings.ignore, 'regex', ['^test.*\.py$'])
        
        # Test Azure platform
        files = ['test1.py', 'main.py', 'test2.py', 'src.py']
        filtered_files = filter_ignored(files, platform='azure')
        assert len(filtered_files) == 2
        assert 'main.py' in filtered_files
        assert 'src.py' in filtered_files
        
        # Test error handling
        monkeypatch.setattr(global_settings.ignore, 'regex', None)
        result = filter_ignored(files, platform='azure')
        assert result == files  # Should return original files on error

