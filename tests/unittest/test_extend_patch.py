import pytest
from pr_agent.algo.git_patch_processing import extend_patch
from pr_agent.algo.pr_processing import pr_generate_extended_diff
from pr_agent.algo.token_handler import TokenHandler


class TestExtendPatch:
    # Tests that the function works correctly with valid input
    def test_happy_path(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5'
        patch_str = '@@ -2,2 +2,2 @@ init()\n-line2\n+new_line2\nline3'
        num_lines = 1
        expected_output = '@@ -1,4 +1,4 @@ init()\nline1\n-line2\n+new_line2\nline3\nline4'
        actual_output = extend_patch(original_file_str, patch_str,
                                     patch_extra_lines_before=num_lines, patch_extra_lines_after=num_lines)
        assert actual_output == expected_output

    # Tests that the function returns an empty string when patch_str is empty
    def test_empty_patch(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5'
        patch_str = ''
        num_lines = 1
        expected_output = ''
        assert extend_patch(original_file_str, patch_str,
                            patch_extra_lines_before=num_lines, patch_extra_lines_after=num_lines) == expected_output

    # Tests that the function returns the original patch when num_lines is 0
    def test_zero_num_lines(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5'
        patch_str = '@@ -2,2 +2,2 @@ init()\n-line2\n+new_line2\nline3'
        num_lines = 0
        assert extend_patch(original_file_str, patch_str,
                            patch_extra_lines_before=num_lines, patch_extra_lines_after=num_lines) == patch_str

    # Tests that the function returns the original patch when patch_str contains no hunks
    def test_no_hunks(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5'
        patch_str = 'no hunks here'
        num_lines = 1
        expected_output = 'no hunks here'
        assert extend_patch(original_file_str, patch_str, num_lines) == expected_output

    # Tests that the function extends a patch with a single hunk correctly
    def test_single_hunk(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5'
        patch_str = '@@ -2,3 +2,3 @@ init()\n-line2\n+new_line2\nline3\nline4'
        num_lines = 1
        expected_output = '@@ -1,5 +1,5 @@ init()\nline1\n-line2\n+new_line2\nline3\nline4\nline5'
        actual_output = extend_patch(original_file_str, patch_str,
                                     patch_extra_lines_before=num_lines, patch_extra_lines_after=num_lines)
        assert actual_output == expected_output

    # Tests the functionality of extending a patch with multiple hunks.
    def test_multiple_hunks(self):
        original_file_str = 'line1\nline2\nline3\nline4\nline5\nline6'
        patch_str = '@@ -2,3 +2,3 @@ init()\n-line2\n+new_line2\nline3\nline4\n@@ -4,1 +4,1 @@ init2()\n-line4\n+new_line4'  # noqa: E501
        num_lines = 1
        expected_output = '@@ -1,5 +1,5 @@ init()\nline1\n-line2\n+new_line2\nline3\nline4\nline5\n@@ -3,3 +3,3 @@ init2()\nline3\n-line4\n+new_line4\nline5'  # noqa: E501
        actual_output = extend_patch(original_file_str, patch_str,
                                     patch_extra_lines_before=num_lines, patch_extra_lines_after=num_lines)
        assert actual_output == expected_output


class TestExtendedPatchMoreLines:
    class File:
        def __init__(self, base_file, patch, filename):
            self.base_file = base_file
            self.patch = patch
            self.filename = filename

    @pytest.fixture
    def token_handler(self):
        # Create a TokenHandler instance with dummy data
        th = TokenHandler(system="System prompt", user="User prompt")
        th.prompt_tokens = 100
        return th

    @pytest.fixture
    def pr_languages(self):
        # Create a list of languages with files containing base_file and patch data
        return [
            {
                'files': [
                    self.File(base_file="line000\nline00\nline0\nline1\noriginal content\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10",
                              patch="@@ -5,5 +5,5 @@\n-original content\n+modified content\nline2\nline3\nline4\nline5",
                              filename="file1"),
                    self.File(base_file="original content\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10",
                              patch="@@ -6,5 +6,5 @@\nline6\nline7\nline8\n-line9\n+modified line9\nline10",
                              filename="file2")
                ]
            }
        ]

    def test_extend_patches_with_extra_lines(self, token_handler, pr_languages):
        patches_extended_no_extra_lines, total_tokens, patches_extended_tokens = pr_generate_extended_diff(
            pr_languages, token_handler, add_line_numbers_to_hunks=False,
            patch_extra_lines_before=0,
            patch_extra_lines_after=0
        )

        # Check that with no extra lines, the patches are the same as the original patches
        p0 = patches_extended_no_extra_lines[0].strip()
        p1 = patches_extended_no_extra_lines[1].strip()
        assert p0 == '## file1\n\n' + pr_languages[0]['files'][0].patch.strip()
        assert p1 == '## file2\n\n' + pr_languages[0]['files'][1].patch.strip()

        patches_extended_with_extra_lines, total_tokens, patches_extended_tokens = pr_generate_extended_diff(
            pr_languages, token_handler, add_line_numbers_to_hunks=False,
            patch_extra_lines_before=2,
            patch_extra_lines_after=1
        )

        p0_extended = patches_extended_with_extra_lines[0].strip()
        assert p0_extended == '## file1\n\n@@ -3,8 +3,8 @@ \nline0\nline1\n-original content\n+modified content\nline2\nline3\nline4\nline5\nline6'
